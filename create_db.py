import json, lzma, re, sqlite3, sys
from tqdm import tqdm

print("Reading file..", file=sys.stderr)

with lzma.open(sys.argv[1]) as f:
    data = json.load(f)

# Note to self: using `set()` here makes the `mesh in neuro_mesh_ids`
# later in the code WAY faster, by about 70x!
with open("../mesh_ids.json") as f:
    neuro_mesh_ids = set(json.load(f))

print("Creating DB..", file=sys.stderr)

db = sqlite3.connect(sys.argv[2])

with db:

    db.execute("CREATE TABLE articles ( \
                    pubmed_id INTEGER PRIMARY KEY, \
                    abstract TEXT, \
                    pub_year INTEGER, \
                    title TEXT \
                )")
    db.execute("CREATE TABLE article_authors ( \
                    pubmed_id INTEGER REFERENCES articles(pubmed_id), \
                    f_name TEXT, \
                    l_name TEXT, \
                    affiliation TEXT, \
                    UNIQUE(pubmed_id, f_name, l_name) \
                )")
    db.execute("CREATE TABLE article_mesh ( \
                    pubmed_id INTEGER REFERENCES articles(pubmed_id), \
                    mesh TEXT, \
                    UNIQUE(pubmed_id, mesh) \
                )")

    db.execute("CREATE TABLE authors ( \
                    f_name TEXT, \
                    l_name TEXT, \
                    UNIQUE(f_name, l_name) \
                )")
    
    print(len(neuro_mesh_ids), file=sys.stderr)
    fin_count = 0
    for article in tqdm(data, desc="Processing"):
        mesh_ids = [ part["mesh_id"] for part in article["mesh_list"] ]
        if any(mesh in neuro_mesh_ids for mesh in mesh_ids):
            if any(re.search(r"Finland", author[2]) for author in article["author_list"]):
                fin_count += 1
                abstract = article["abstract"]
                authors = [ (author[0], author[1], author[2]) for author in article["author_list"] ]
                mesh_list = [ part["mesh_name"] for part in article["mesh_list"] ]
                pub_year = article["pub_year"]
                pubmed_id = article["pubmed_id"]
                title = article["title"]

                db.execute("INSERT OR REPLACE INTO articles(pubmed_id, abstract, pub_year, title) VALUES (?,?,?,?)",
                            (pubmed_id, abstract, pub_year, title) )
                for mesh in mesh_list:
                    db.execute("INSERT OR IGNORE INTO article_mesh(pubmed_id, mesh) VALUES (?,?)", (pubmed_id, mesh) )
                
                for author in authors:
                    db.execute("INSERT OR REPLACE INTO article_authors(pubmed_id, f_name, l_name, affiliation) VALUES (?,?,?,?)",
                                (pubmed_id, author[0], author[1], author[2]) )
                    if re.search(r"Finland", author[2]):
                        db.execute("INSERT OR REPLACE INTO authors(f_name, l_name) VALUES (?,?)",
                                    (author[0], author[1]) )
                        print("Finnish author:", author[:])

print(fin_count)