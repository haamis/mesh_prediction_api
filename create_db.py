import json, re, sqlite3, sys
from tqdm import tqdm

db = sqlite3.connect(sys.argv[2])
#c = db.cursor()

db.execute("CREATE TABLE authors (f_name text, l_name text, affiliation text, mesh_terms text)")
db.execute("CREATE TABLE articles (pubmed_id integer, abstract text, pub_year integer, title text)")
db.execute("CREATE TABLE article_mesh (pubmed_id integer, mesh text)")
db.execute("CREATE TABLE article_authors (pubmed_id integer, f_name text, l_name text, affiliation text)")

with open(sys.argv[1]) as f:
    data = json.load(f)

#articles = []

with db:
    fin_count = 0
    for article in tqdm(data, desc="Processing"):
        if any([re.search(r"Finland", author[2]) for author in article["author_list"]]):            
            fin_count += 1
            abstract = article["abstract"]
            authors = ( (author[0], author[1], author[2])  for author in article["author_list"] )
            mesh_list = ( part["mesh_name"] for part in article["mesh_list"] )
            pub_year = article["pub_year"]
            pubmed_id = article["pubmed_id"]
            title = article["title"]

            db.execute("INSERT INTO articles(pubmed_id, abstract, pub_year, title) VALUES (?,?,?,?)", (pubmed_id, abstract, pub_year, title) )
            for author in authors:
                db.execute("INSERT INTO article_authors(pubmed_id, f_name, l_name, affiliation) VALUES (?,?,?,?)", (pubmed_id, author[0], author[1], author[2]) )
                if re.search(r"Finland", author[2]):
                    print("Finnish author:", author[:])
            for mesh in mesh_list:
                db.execute("INSERT INTO article_mesh(pubmed_id, mesh) VALUES (?,?)", (pubmed_id, mesh) )

            #articles.append({"abstract": abstract, "authors": authors, "mesh_terms": mesh_list, "pub_year": pub_year, "pubmed_id": pubmed_id})

print(fin_count)