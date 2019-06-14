import  sqlite3
from flask import Flask, Response, request, json, jsonify, url_for

app = Flask(__name__)

db = sqlite3.connect("../test.db", check_same_thread=False)
db.row_factory = sqlite3.Row
#c = db.cursor()

@app.route('/', methods=['GET'])
def root():
    response = {}
    response["articles"] = url_for("articles")
    return jsonify(response)

@app.route('/articles', methods=["GET"])
def articles():
    print(request.args)
    sql = "SELECT DISTINCT articles.* FROM articles \
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
        where_strs.append("article_mesh.mesh=?")
        params.append(request.args.get("mesh"))
    rows = db.execute(sql + " AND ".join(where_strs), params).fetchall()

    return jsonify([dict(zip(row.keys(), row)) for row in rows ])

# @app.route("/all_finnish_authors", methods=["GET"])
# def all_finnish_authors():
#     ret_val = db.execute("SELECT * FROM authors")
#     return jsonify(ret_val)

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
