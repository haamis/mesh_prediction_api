import gzip, json, lzma, re, sqlite3, sys
import xml.etree.ElementTree as ET
from tqdm import tqdm

# Note to self: using `set()` here makes the `mesh in neuro_mesh_ids`
# later in the code WAY faster, by about 70x!
with open("../mesh_ids.json") as f:
    neuro_mesh_ids = set(json.load(f))

db = sqlite3.connect("../neuro.db")

def get_mesh(input_file):
    
    with gzip.open(input_file, "rt") as f:
        root = ET.parse(f).getroot()

    articles = []

    for doc in root.findall("PubmedArticle"):
        
        article = {}
        
        abstract = doc.find(".//Abstract")
        if abstract is None:
            article["abstract"] = ""
        else:
            abstract = abstract.findall("AbstractText")
            abstract_parts = []
            for part in abstract:
                if part.text == None:
                    continue
                if part.get("NlmCategory"):
                    abstract_parts.append(part.get("NlmCategory") + ": " + "".join(part.itertext()))
                else:
                    abstract_parts.append("".join(part.itertext()))
            
            article["abstract"] = "".join(abstract_parts)

        mesh_list = doc.find(".//MeshHeadingList")
        article["mesh_list"] = []
        if mesh_list is not None:
            for mesh in mesh_list:
                desc = mesh.find("DescriptorName")
                mesh_id = desc.get("UI")
                mesh_name = desc.text
                major_topic = desc.get("MajorTopicYN")
                article["mesh_list"].append({"mesh_id":mesh_id, "mesh_name":mesh_name, "major_topic":major_topic})

        # Add ArticleDate as first choice, then parse PubDate in <JournalIssue>.
        pub_date_node = doc.find(".//PubDate")
        if pub_date_node.find("Year") is None:
            print("wat", pub_date_node.find("MedlineDate").text)
        
        article_date_node = doc.find(".//ArticleDate")


        if article_date_node is None:
            if pub_date_node.find("Year") is None:
                article["pub_year"] = ""
            else:
                article["pub_year"] = ( article_date_node or pub_date_node ).find("Year").text
        else:
            article["pub_year"] = ( article_date_node or pub_date_node ).find("Year").text

        article["pubmed_id"] = doc.find(".//PMID").text

        article["title"] = "".join(doc.find(".//ArticleTitle").itertext())

        article["journal"] = "".join(doc.find(".//Journal/Title").itertext())

        

        article["author_list"] = []
        last_affiliations = ""
        for author in doc.findall(".//AuthorList/Author"):
            if author.find("LastName") is not None:
                lastname = author.find("LastName").text
                if author.find("ForeName") is not None:
                    firstname = author.find("ForeName").text
                else:
                    firstname = ""
            elif author.find("CollectiveName") is not None:
                lastname = author.find("CollectiveName").text
                firstname = "Collective"
            else:
                # Debug.
                print("Debug print", author.find("ForeName"), author.find("LastName"), author.find("CollectiveName"))
                continue
            
            aff_nodes = author.findall("AffiliationInfo/Affiliation")

            # In case of no affiliation info, assume the affiliation of an earlier author in the article info.
            if len(aff_nodes) == 0:
                affiliations = last_affiliations
            else:
                affiliations = [aff.text for aff in aff_nodes]
                last_affiliations = affiliations

            article["author_list"].append( (firstname, lastname, "; ".join(affiliations)) )
        
        articles.append(article)
    
    if len(articles) > 0:
        with db:   
            for article in tqdm(articles, desc="Processing"):
                mesh_ids = [ part["mesh_id"] for part in article["mesh_list"] ]
                if any(mesh in neuro_mesh_ids for mesh in mesh_ids):
                    if any(re.search(r"Finland", author[2]) for author in article["author_list"]):
                        abstract = article["abstract"]
                        authors = [ (author[0], author[1], author[2]) for author in article["author_list"] ]
                        mesh_list = [ part["mesh_name"] for part in article["mesh_list"] ]
                        pub_year = article["pub_year"]
                        pubmed_id = article["pubmed_id"]
                        title = article["title"]

                        db.execute("INSERT OR REPLACE INTO articles(pubmed_id, abstract, pub_year, title) VALUES (?,?,?,?)",
                                    (pubmed_id, abstract, pub_year, title) )

                        db.executemany("INSERT OR IGNORE INTO article_mesh(pubmed_id, mesh) VALUES (?,?)", zip((pubmed_id for _ in mesh_list), mesh_list) )
                        
                        for author in authors:
                            db.execute("INSERT OR REPLACE INTO article_authors(pubmed_id, f_name, l_name, affiliation) VALUES (?,?,?,?)",
                                        (pubmed_id, author[0], author[1], author[2]) )
                            if re.search(r"Finland", author[2]):
                                db.execute("INSERT OR REPLACE INTO authors(f_name, l_name) VALUES (?,?)",
                                            (author[0], author[1]) )

if __name__ == "__main__":
    get_mesh(sys.argv[1])