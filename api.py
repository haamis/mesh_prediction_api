import  sqlite3
from flask import Flask, Response, request, json, jsonify, url_for

app = Flask(__name__)

db = sqlite3.connect("../test.db", check_same_thread=False)
db.row_factory = sqlite3.Row
#c = db.cursor()

@app.route('/', methods=['GET'])
def root():
    response = {}
    response["articles"] = "params: author, mesh"
    response["authors"] = "params: author, mesh"
    response["article_info"] = "params: pubmed_id"
    return jsonify(response)

@app.route('/articles', methods=["GET"])
def articles():
    print(request.args)
    sql = "SELECT DISTINCT articles.pubmed_id FROM articles \
            INNER JOIN article_authors ON articles.pubmed_id=article_authors.pubmed_id \
            INNER JOIN article_mesh ON articles.pubmed_id=article_mesh.pubmed_id WHERE "
    where_strs = []
    params = []
    if request.args.get("author"):
        where_strs.append("article_authors.l_name LIKE ? \
                        OR article_authors.f_name LIKE ?")
        params.extend([request.args.get("author")]*2)
        print(params)
    if request.args.get("mesh"):
        for mesh in request.args.getlist("mesh"):
            where_strs.append("articles.pubmed_id IN (SELECT pubmed_id FROM article_mesh WHERE mesh = ?)")
            params.append(mesh)
        print(params)
        print(sql + " AND ".join(where_strs))
    rows = db.execute(sql + " AND ".join(where_strs), params).fetchall()

    return jsonify([dict(zip(row.keys(), row)) for row in rows ])

@app.route("/article_info", methods=["GET"])
def article_info():
    authors = db.execute("SELECT f_name, l_name, affiliation FROM article_authors WHERE pubmed_id=?",
                        (request.args.get("pubmed_id"),)).fetchall()
    authors = [{"f_name": author[0], "l_name": author[1], "affiliation": author[2]} for author in authors]
    print(authors)

    mesh_terms = db.execute("SELECT group_concat(mesh, ';') FROM article_mesh WHERE pubmed_id=?",
                            (request.args.get("pubmed_id"),)).fetchone()
    mesh_terms = mesh_terms[0].split(";")
    print(mesh_terms)
    
    info = db.execute("SELECT * FROM articles WHERE pubmed_id=?",
                            (request.args.get("pubmed_id"),)).fetchone()
    print(info)

    response = {thing[0]: thing[1] for thing in zip(info.keys(), info)}
    response["authors"] = authors
    response["mesh"] = mesh_terms

    return jsonify(response)

@app.route("/authors", methods=["GET"])
def authors():
    sql = "SELECT DISTINCT * FROM authors \
            INNER JOIN article_authors ON authors.f_name=article_authors.f_name \
            INNER JOIN article_mesh ON article_authors.pubmed_id=article_mesh.pubmed_id WHERE "
    where_strs = []
    params = []
    if request.args.get("name"):
        where_strs.append("(article_authors.l_name LIKE ? \
                        OR article_authors.f_name LIKE ?)")
        params.extend([request.args.get("author")]*2)
        print(params)
    if request.args.get("mesh"):
        for mesh in request.args.getlist("mesh"):
            where_strs.append("articles.pubmed_id IN (SELECT pubmed_id FROM article_mesh WHERE mesh = ?)")
            params.append(mesh)
        print(params)
        print(sql + " AND ".join(where_strs))
    rows = db.execute(sql + " AND ".join(where_strs), params).fetchall()

    return jsonify([dict(zip(row.keys(), row)) for row in rows ])

# @app.route("/binary_prediction", methods=["POST"])
# def binary_prediction():
    
#     ret_val = []
#     for entry in request.json:
#         if re.search(r"Finland", entry["country"]):
#             ret_val.append(make_binary_prediction(entry["abstract"]))

#         # Check for "Finland" in any of the author strings.
#         if any([re.search(r"Finland", author) for author in entry["authors"]]):
#             print(entry["authors"])
#             ret_val.append(make_binary_prediction(entry["abstract"]))
#         else:
#             ret_val.append(False)

#     #results = make_binary_prediction(request.json[])
#     return Response(json.dumps(ret_val, indent=2, sort_keys=True), status=200, mimetype="application/json")

if __name__ == '__main__':
    app.run()
