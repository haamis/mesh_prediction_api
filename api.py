import pickle, re, sys
import tensorflow as tf
import numpy as np

import keras_metrics

from keras.backend.tensorflow_backend import set_session
from keras.models import load_model

from keras_bert import get_custom_objects

from bert import tokenization

# Prediction part

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
set_session(tf.Session(config=config))

maxlen = 384

custom_objects = get_custom_objects()
custom_objects["tf"] = tf
custom_objects["keras_metrics"] = keras_metrics
custom_objects["binary_precision"] = keras_metrics.binary_precision()
custom_objects["binary_recall"] = keras_metrics.binary_recall()

model = load_model(sys.argv[1], custom_objects=custom_objects)

graph = tf.get_default_graph()
tokenizer = tokenization.FullTokenizer("../biobert_pubmed/vocab.txt", do_lower_case=False)

def load_data(file_name):

    with open(file_name, "rb") as f:
        return pickle.load(f)

def tokenize(abstracts, maxlen=512):
    ret_val = []
    for abstract in abstracts:
        abstract = ["[CLS]"] + tokenizer.tokenize(abstract[0:maxlen-2]) + ["[SEP]"]
        ret_val.append(abstract)
    return ret_val, tokenizer.vocab

def make_binary_prediction(abstract):

    #print(abstracts)

    # if not isinstance(abstracts, list):
    #     abstracts = [abstracts]
    #     print("listified")

    print("Tokenizing")
    abstract = ["[CLS]"] + tokenizer.tokenize(abstract[0:maxlen-2]) + ["[SEP]"]
    vocab = tokenizer.vocab

    print("Vectorizing")
    #token_vectors = np.asarray( [np.asarray( [vocab[token] for token in abstract] + [0] * (maxlen - len(abstract)) ) for abstract in abstracts] )
    token_vectors = np.asarray( [vocab[token] for token in abstract] + [0] * (maxlen - len(abstract)) )
    #del abstracts
    
    # with graph.as_default():
    #     print("Predicting probs")
    #     probs = model.predict([token_vectors, np.zeros_like(token_vectors)])
        
    #     print("Probs to binary")
    #     preds = np.zeros_like(probs)
    #     preds[probs>0.5] = 1
        
    #     #print(probs)
    #     #print(preds)
    #     print("Aggregating results")
    #     results = []
    #     for prediction in preds:
    #         if prediction[1] == 1:
    #             results.append(True)
    #         else:
    #             results.append(False)        
    #     return results

    # Model expects a list of samples, we only have one.
    token_vectors = [token_vectors]
    
    with graph.as_default():
        print("Predicting probs")
        probs = model.predict([token_vectors, np.zeros_like(token_vectors)])
        
        print("Probs to binary")
        preds = np.zeros_like(probs)
        preds[probs>0.5] = 1
        
        #print(probs)
        #print(preds)
        print("Aggregating results")
        if preds[0][1] == 1:
            return True
        else:
            return False

# Web server part. Yes, this is a bit messy.

from flask import Flask, Response, request, json

app = Flask(__name__)

@app.route('/binary_prediction', methods = ['POST'])
def binary_prediction():
    
    ret_val = []
    for entry in request.json:
        if re.search(r"Finland", entry["country"]):
            ret_val.append(make_binary_prediction(entry["abstract"]))

        # Check for "Finland" in any of the author strings.
        if any([re.search(r"Finland", author) for author in entry["authors"]]):
            print([re.search(r"Finland", author) for author in entry["authors"]])
            print(entry["authors"])
            ret_val.append(make_binary_prediction(entry["abstract"]))
        else:
            ret_val.append(False)

    #results = make_binary_prediction(request.json[])
    return Response(json.dumps(ret_val), status=200, mimetype='application/json')

if __name__ == '__main__':
    app.run()
