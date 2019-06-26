import  sqlite3
from flask import Flask, Response, request, json, jsonify, url_for

app = Flask(__name__)

db = sqlite3.connect("../test.db", check_same_thread=False)
db.row_factory = sqlite3.Row

@app.route('/', methods=['GET'])
def root():

    response = {}
    response["articles"] = "params: affiliation, author_name, mesh"
    response["authors"] = "params: affiliation, author_name, mesh"
    response["article_info"] = "params: pubmed_id"

    return jsonify(response)


@app.route('/articles', methods=["GET"])
def articles():

    sql = "SELECT DISTINCT abstract, pub_year, articles.pubmed_id, title FROM articles \
            INNER JOIN article_authors ON articles.pubmed_id=article_authors.pubmed_id \
            INNER JOIN article_mesh ON articles.pubmed_id=article_mesh.pubmed_id WHERE "
    
    where_strs = []
    params = []

    if request.args.get("affiliation"):
        where_strs.append("article_authors.affiliation LIKE ?")
        params.append('%' + request.args.get("affiliation") + '%')

    if request.args.get("author_name"):
        where_strs.append("article_authors.f_name || ' ' || article_authors.l_name LIKE ?")
        params.append('%' + request.args.get("author_name") + '%')

    for mesh in request.args.getlist("mesh"):
        where_strs.append("articles.pubmed_id IN (SELECT pubmed_id FROM article_mesh WHERE mesh = ?)")
        params.append(mesh)

    # Default limit. Start from 0, return first 100 results
    limit_start = 0
    limit_size = 20

    if request.args.get("per_page"):
        limit_size = request.args.get("per_page")
        if limit_size > 100:
            limit_size = 100

    if request.args.get("page_number"):
        limit_start = request.args.get("page_number") * limit_size
    
    sql += " AND ".join(where_strs)
    sql += " ORDER BY articles.pub_year"
    sql += " LIMIT " + str(limit_start) + ", " + str(limit_size)

    print(sql)
    print(params)

    article_rows = db.execute(sql, params).fetchall()
    
    # Change the sqlite3 Rows into dicts so they're mutable and JSON-able.
    article_rows = [dict(zip(row.keys(), row)) for row in article_rows]

    author_rows_list = []
    for row in article_rows:
        author_rows = db.execute("SELECT f_name, l_name, affiliation FROM article_authors WHERE pubmed_id=?",
                                (row["pubmed_id"],)
                                ).fetchall()
        author_rows_list.append(author_rows)

    mesh_terms_list = []
    for row in article_rows:
        mesh_terms = db.execute("SELECT DISTINCT group_concat(mesh, '¤') FROM article_mesh \
                                INNER JOIN article_authors ON article_mesh.pubmed_id=article_authors.pubmed_id \
                                WHERE article_mesh.pubmed_id = ?",
                                (str(row["pubmed_id"]),)
                                ).fetchone()
        mesh_terms = mesh_terms[0].split("¤")
        mesh_terms = sorted(list(set(mesh_terms)))
        mesh_terms_list.append(mesh_terms)

    for article, author_rows, mesh_terms in zip(article_rows, author_rows_list, mesh_terms_list):
        article["authors"] = [ {"f_name": author["f_name"], "l_name": author["l_name"],
                                "affiliation": author["affiliation"]} for author in author_rows ]
        article["mesh"] = mesh_terms

    return jsonify(article_rows)


@app.route("/authors", methods=["GET"])
def authors():

    sql = "SELECT DISTINCT authors.f_name, authors.l_name FROM authors \
            INNER JOIN article_authors ON authors.f_name=article_authors.f_name \
            INNER JOIN article_mesh ON article_authors.pubmed_id=article_mesh.pubmed_id WHERE "
    
    where_strs = []
    params = []
    
    if request.args.get("affiliation"):
        where_strs.append("article_authors.affiliation LIKE ?")
        params.append('%' + request.args.get("affiliation") + '%')

    if request.args.get("author_name"):
        where_strs.append("authors.f_name || ' ' || authors.l_name LIKE ?")
        params.append('%' + request.args.get("author_name") + '%')

    for mesh in request.args.getlist("mesh"):
        where_strs.append("article_mesh.pubmed_id IN (SELECT pubmed_id FROM article_mesh WHERE mesh = ?)")
        params.append(mesh)

    # Default limit. Start from 0, return first 20 results
    limit_start = 0
    limit_size = 20

    if request.args.get("per_page"):
        limit_size = int(request.args.get("per_page"))
        if limit_size > 100:
            limit_size = 100

    if request.args.get("page_number"):
        # `page_number - 1` to start page numbering from 1.
        limit_start = (int(request.args.get("page_number")) - 1) * (limit_size)
    
    sql += " AND ".join(where_strs)
    #sql += " ORDER BY authors.l_name"
    sql += " LIMIT " + str(limit_start) + ", " + str(limit_size)

    author_rows = db.execute(sql, params).fetchall()

    mesh_terms_list = []
    for row in author_rows:
        # Use the `¤` symbols as a delimiter
        mesh_terms = db.execute("SELECT DISTINCT group_concat(mesh, '¤') FROM article_mesh \
                                INNER JOIN article_authors ON article_mesh.pubmed_id=article_authors.pubmed_id \
                                WHERE (article_authors.f_name LIKE ? AND article_authors.l_name LIKE ?)",
                                (row["f_name"], row["l_name"])
                                ).fetchone()
        mesh_terms = mesh_terms[0].split("¤")
        mesh_terms = sorted(list(set(mesh_terms)))
        mesh_terms_list.append(mesh_terms)

    affiliations_list = []
    for row in author_rows:
        affiliations = db.execute("SELECT DISTINCT group_concat(affiliation, '¤') FROM article_authors \
                                    WHERE (article_authors.f_name LIKE ? AND article_authors.l_name LIKE ?)",
                                    (row["f_name"], row["l_name"])
                                    ).fetchone()
        affiliations = affiliations[0].split("¤")
        affiliations = sorted(list(set(affiliations)))
        affiliations_list.append(affiliations)

    author_rows = [dict(zip(row.keys(), row)) for row in author_rows]

    for author, mesh_terms, affiliations in zip(author_rows, mesh_terms_list, affiliations_list):
        author["mesh"] = mesh_terms
        author["affiliations"] = affiliations
        test = json.dumps(affiliations)
        print(json.loads(test))

    return jsonify(author_rows)


@app.route("/article_info", methods=["GET"])
def article_info():
    author_rows = db.execute("SELECT f_name, l_name, affiliation FROM article_authors WHERE pubmed_id=?",
                        (request.args.get("pubmed_id"),)
                        ).fetchall()
    author_rows = [{"f_name": author[0], "l_name": author[1], "affiliation": author[2]} for author in author_rows]
    print(author_rows)

    mesh_terms = db.execute("SELECT group_concat(mesh, '¤') FROM article_mesh WHERE pubmed_id=?",
                            (request.args.get("pubmed_id"),)
                            ).fetchone()
    mesh_terms = mesh_terms[0].split("¤")
    print(mesh_terms)
    
    info = db.execute("SELECT * FROM articles WHERE pubmed_id=?",
                        (request.args.get("pubmed_id"),)
                        ).fetchone()
    print(info)

    response = {thing[0]: thing[1] for thing in zip(info.keys(), info)}
    response["authors"] = author_rows
    response["mesh"] = mesh_terms

    return jsonify(response)

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
