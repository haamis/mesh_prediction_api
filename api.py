import pickle, re
from flask import Flask, Response, request, json

def load_data(file_name):

    with open(file_name, "rb") as f:
        return pickle.load(f)

app = Flask(__name__)

pubmed_data = load_data("../tiny_output.dump")

@app.route('/articles', methods=["GET"])
def articles():
    print(request.args)
    ret_val = []
    if request.args.get("author"):
        print(request.args.get("author"))
        for article in pubmed_data:
            if any( [ request.args["author"] in author["name"] for author in article["authors"] ] ):
                ret_val.append(article)

    if request.args.get("mesh"):
        for article in pubmed_data:
            for term in request.args.getlist("mesh"):
                if any( [ author == term for author in article["mesh_terms"] ] ):
                    ret_val.append(article)
    
    ret_val = list(ret_val)

    return Response(json.dumps(ret_val, indent=2, sort_keys=True), status=200, mimetype="application/json")

@app.route("/all_finnish_authors", methods=["GET"])
def all_finnish_authors():
    ret_val = set()
    for article in pubmed_data:
        for author in article["authors"]:
            if re.search(r"Finland", author["affiliation"]):
                ret_val.add((author["name"], author["affiliation"]))

    ret_val = list(ret_val)

    return Response(json.dumps(ret_val, indent=2, sort_keys=True), status=200, mimetype="application/json")

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
