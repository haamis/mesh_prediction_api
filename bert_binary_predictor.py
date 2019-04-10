import sys
import tensorflow as tf
import numpy as np

import keras_metrics

from keras.backend.tensorflow_backend import set_session
from keras.models import load_model

from keras_bert import get_custom_objects

from bert import tokenization


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

def tokenize(abstracts, maxlen=512):
    ret_val = []
    for abstract in abstracts:
        abstract = ["[CLS]"] + tokenizer.tokenize(abstract[0:maxlen-2]) + ["[SEP]"]
        ret_val.append(abstract)
    return ret_val, tokenizer.vocab

def make_binary_prediction(abstract):

    print("Tokenizing")
    abstract = ["[CLS]"] + tokenizer.tokenize(abstract[0:maxlen-2]) + ["[SEP]"]
    vocab = tokenizer.vocab

    print("Vectorizing")
    token_vectors = np.asarray( [vocab[token] for token in abstract] + [0] * (maxlen - len(abstract)) )

    # Model expects a list of samples, we only have one.
    token_vectors = [token_vectors]
    
    with graph.as_default():
        print("Predicting probs")
        probs = model.predict([token_vectors, np.zeros_like(token_vectors)])
        
        print("Probs to binary")
        preds = np.zeros_like(probs)
        preds[probs>0.5] = 1
        
        print("Aggregating results")
        if preds[0][1] == 1:
            return True
        else:
            return False