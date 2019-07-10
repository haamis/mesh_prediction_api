import gzip, json, re, sqlite3, sys
#import xml.etree.cElementTree as ET
import lxml.etree as ET
from tqdm import tqdm
from timeit import default_timer as timeit
import bert_multilabel_predictor

# Note to self: using `set()` here makes the `mesh in neuro_mesh_ids`
# later in the code WAY faster, by about 70x!
with open("../mesh_ids.json") as f:
    neuro_mesh_ids = set(json.load(f))

db = sqlite3.connect("../neuro2.db", timeout=30)

def get_mesh(input_file):
    
    with gzip.open(input_file, "rt") as f:
        root = ET.parse(f).getroot()

    articles = []

    for doc in root.findall("PubmedArticle"):
        
        article = {}
        
        article["pubmed_id"] = doc.find("MedlineCitation/PMID").text
        
        article["title"] = "".join(doc.find("MedlineCitation/Article/ArticleTitle").itertext())
        
        abstract = doc.find("MedlineCitation/Article/Abstract")
        if abstract is None:
            article["abstract"] = ""
        else:
            abstract = abstract.findall("AbstractText")
            abstract_parts = []
            for part in abstract:
                if part.get("NlmCategory"):
                    abstract_parts.append(part.get("NlmCategory") + ": " + "".join(part.itertext()))
                else:
                    abstract_parts.append("".join(part.itertext()))
            
            article["abstract"] = "".join(abstract_parts)

        article["author_list"] = []
        last_affiliations = ""
        for author in doc.findall("MedlineCitation/Article/AuthorList/Author"):
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
                assert False
            
            aff_nodes = author.findall("AffiliationInfo/Affiliation")

            # In case of no affiliation info, assume the affiliation of an earlier author in the article info.
            if len(aff_nodes) == 0:
                affiliations = last_affiliations
            else:
                affiliations = ["".join(aff.itertext()) for aff in aff_nodes]
                last_affiliations = affiliations

            article["author_list"].append( (firstname, lastname, "; ".join(affiliations)) )
        
        # If there are no Finnish authors in the article, we move on.
        if not any(re.search(r"Finland", author[2]) for author in article["author_list"]):
            continue

        mesh_node_list = doc.find("MedlineCitation/MeshHeadingList")
        article["mesh_list"] = []
        if mesh_node_list is not None:
            for mesh_node in mesh_node_list:
                desc = mesh_node.find("DescriptorName")
                mesh_name = desc.text
                mesh_id = desc.get("UI")
                article["mesh_list"].append({"mesh_name": mesh_name, "mesh_id": mesh_id})
        else:
            print("Predicting mesh", article["pubmed_id"])
            start = timeit()
            article["mesh_list"] = bert_multilabel_predictor.make_multilabel_prediction(article["title"] + '\n' + article["abstract"])
            end = timeit()
            print(end - start)

        # If there is no neuro mesh present, we move on.
        if not any(mesh["mesh_id"] in neuro_mesh_ids for mesh in article["mesh_list"]):
            continue

        # Add ArticleDate as first choice, then parse PubDate in <JournalIssue>.
        pub_date_node = doc.find("MedlineCitation/Article/Journal/JournalIssue/PubDate")
        # if pub_date_node.find("Year") is None:
        #     print("wat", pub_date_node.find("MedlineDate").text)
        
        article_date_node = doc.find("MedlineCitation/Article/ArticleDate")

        if article_date_node is None:
            if pub_date_node.find("Year") is None:
                article["pub_year"] = ""
            else:
                article["pub_year"] = ( article_date_node or pub_date_node ).find("Year").text
        else:
            article["pub_year"] = ( article_date_node or pub_date_node ).find("Year").text

        
        articles.append(article)

    return articles

if __name__ == "__main__":
    all_articles = []
    for arg in tqdm(sys.argv[1:]):
        all_articles.extend(get_mesh(arg))
    if len(all_articles) > 0:
        with db:   
            for article in all_articles:
                abstract = article["abstract"]
                #authors = [ (author[0], author[1], author[2]) for author in article["author_list"] ]
                mesh_list = [ mesh["mesh_name"] for mesh in article["mesh_list"] ]
                pub_year = article["pub_year"]
                pubmed_id = article["pubmed_id"]
                title = article["title"]

                db.execute("INSERT OR REPLACE INTO articles(pubmed_id, abstract, pub_year, title) VALUES (?,?,?,?)",
                            (pubmed_id, abstract, pub_year, title) )

                db.executemany("INSERT OR IGNORE INTO article_mesh(pubmed_id, mesh) VALUES (?,?)", zip((pubmed_id for _ in mesh_list), mesh_list) )
                
                for author in article["author_list"]:
                    db.execute("INSERT OR REPLACE INTO article_authors(pubmed_id, f_name, l_name, affiliation) VALUES (?,?,?,?)",
                                (pubmed_id, author[0], author[1], author[2]) )
                    if re.search(r"Finland", author[2]):
                        db.execute("INSERT OR REPLACE INTO authors(f_name, l_name) VALUES (?,?)",
                                    (author[0], author[1]) )
