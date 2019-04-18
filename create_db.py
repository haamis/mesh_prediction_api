import json, re, sqlite3, sys
from tqdm import tqdm

db = sqlite3.connect(sys.argv[2])
c = db.cursor()

c.execute("CREATE TABLE authors (f_name text, l_name text, affiliation text, mesh_terms text)")
c.execute("CREATE TABLE articles (pubmed_id integer, abstract text, pub_year integer, title text)")
c.execute("CREATE TABLE mesh_list (pubmed_id integer, mesh text)")
c.execute("CREATE TABLE author_list (pubmed_id integer, f_name text, l_name text, affiliation text)")

with open(sys.argv[1]) as f:
    data = json.load(f)

articles = []

for article in tqdm(data, desc="Processing"):
    if any([re.search(r"Finland", author[2]) for author in article["author_list"]]):            
        abstract = "\n".join( [ part["text"] for part in article["abstract"] ] )
        authors = [ {"name": author[0] + " " + author[1], "affiliation": author[2]} for author in article["author_list"]]
        mesh_list = [ part["mesh_name"] for part in article["mesh_list"] ]
        pub_year = article["pub_year"]
        pubmed_id = article["pubmed_id"]
        title = article["title"]

        articles.append({"abstract": abstract, "authors": authors, "mesh_terms": mesh_list, "pub_year": pub_year, "pubmed_id": pubmed_id})
