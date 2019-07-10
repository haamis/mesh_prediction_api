import  sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

db = sqlite3.connect("../neuro2.db", check_same_thread=False)
db.row_factory = sqlite3.Row

def page_limits(per_page=None, page_number=None):
    # Default limit. Start from 0, return first 20 results
    limit_start = 0
    limit_size = 20

    if per_page:
        limit_size = int(per_page)
        if limit_size > 100:
            limit_size = 100

    if page_number:
        limit_start = (int(page_number) - 1) * limit_size

    return limit_start, limit_size


@app.route('/', methods=['GET'])
def root():

    response = {}
    response["articles"] = "params: affiliation, author_name, mesh, per_page, page_number, sort=[date_asc|date_desc]"
    response["authors"] = "params: affiliation, author_name, mesh, per_page, page_number, sort=[f_name_asc|f_name_desc|l_name_asc|l_name_desc]"
    response["all_mesh_terms"] = "returns all unique mesh terms in the database"

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

    limit_start, limit_size = page_limits(request.args.get("per_page"), request.args.get("page_number"))

    order_by = ""
    if request.args.get("sort"):
        order_by = " ORDER BY "
        arg = request.args.get("sort")
        if arg == "date_asc":
            order_by += "articles.pub_year ASC"
        if arg == "date_desc":
            order_by += "articles.pub_year DESC"
    
    sql += " AND ".join(where_strs)
    sql += order_by
    sql += " LIMIT " + str(limit_start) + ", " + str(limit_size)

    article_rows = db.execute(sql, params).fetchall()
    
    author_rows_list = []
    for row in article_rows:
        author_rows = db.execute("SELECT f_name, l_name, affiliation FROM article_authors WHERE pubmed_id=?",
                                (row["pubmed_id"],)
                                ).fetchall()
        author_rows_list.append(author_rows)

    mesh_terms_list = []
    for row in article_rows:
        mesh_terms = db.execute("SELECT DISTINCT mesh FROM article_mesh \
                                INNER JOIN article_authors ON article_mesh.pubmed_id=article_authors.pubmed_id \
                                WHERE article_mesh.pubmed_id = ? \
                                ORDER BY mesh",
                                (row["pubmed_id"],)
                                ).fetchall()
        mesh_terms_list.append([mesh_term[0] for mesh_term in mesh_terms])
    
    # Change the sqlite3 Rows into dicts so they're mutable and JSON-able.
    article_rows = [dict(row) for row in article_rows]

    for article, author_rows, mesh_terms in zip(article_rows, author_rows_list, mesh_terms_list):
        article["authors"] = [ {"f_name": author["f_name"], "l_name": author["l_name"],
                                "affiliation": author["affiliation"]} for author in author_rows ]
        article["mesh"] = mesh_terms

    
    return jsonify(article_rows)


@app.route("/authors", methods=["GET"])
def authors():

    sql = "SELECT DISTINCT authors.f_name, authors.l_name FROM authors \
            INNER JOIN article_authors ON authors.f_name=article_authors.f_name AND authors.l_name=article_authors.l_name \
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

    limit_start, limit_size = page_limits(request.args.get("per_page"), request.args.get("page_number"))

    order_by = ""
    if request.args.get("sort"):
        order_by = " ORDER BY "
        arg = request.args.get("sort")
        if arg == "f_name_asc":
            order_by += "authors.f_name ASC"
        if arg == "f_name_desc":
            order_by += "authors.f_name DESC"
        if arg == "l_name_asc":
            order_by += "authors.l_name ASC"
        if arg == "l_name_desc":
            order_by += "authors.l_name DESC"
    
    sql += " AND ".join(where_strs)
    sql += order_by
    sql += " LIMIT " + str(limit_start) + ", " + str(limit_size)

    author_rows = db.execute(sql, params).fetchall()
    
    mesh_terms_list = []
    for row in author_rows:
        mesh_terms = db.execute("SELECT DISTINCT mesh FROM article_mesh \
                                INNER JOIN article_authors ON article_mesh.pubmed_id=article_authors.pubmed_id \
                                WHERE (article_authors.f_name = ? AND article_authors.l_name = ?) \
                                ORDER BY mesh",
                                (row["f_name"], row["l_name"])
                                ).fetchall()
        mesh_terms_list.append([mesh_term[0] for mesh_term in mesh_terms])

    affiliations_list = []
    for row in author_rows:
        affiliations = db.execute("SELECT DISTINCT affiliation FROM article_authors \
                                    WHERE (article_authors.f_name = ? AND article_authors.l_name = ?) \
                                    ORDER BY affiliation",
                                    (row["f_name"], row["l_name"])
                                    ).fetchall()
        affiliations_list.append([affiliation[0] for affiliation in affiliations])

    author_rows = [dict(row) for row in author_rows]

    for author, mesh_terms, affiliations in zip(author_rows, mesh_terms_list, affiliations_list):
        author["mesh"] = mesh_terms
        author["affiliations"] = affiliations

    return jsonify(author_rows)


@app.route("/all_mesh_terms", methods=["GET"])
def all_mesh_terms():
    mesh_terms = db.execute("SELECT DISTINCT mesh FROM article_mesh")
    mesh_terms = [mesh[0] for mesh in mesh_terms]

    return jsonify(mesh_terms)


if __name__ == '__main__':
    app.run()
