import pickle, sys
import tensorflow as tf
import numpy as np

from keras.models import load_model

from bert import tokenization

maxlen = 384

def load_data(file_name):

    with open(file_name, "rb") as f:
        return pickle.load(f)

def tokenize(abstracts, maxlen=512):
    tokenizer = tokenization.FullTokenizer("../biobert_pubmed/vocab.txt", do_lower_case=False)
    ret_val = []
    for abstract in abstracts:
        abstract = ["[CLS]"] + tokenizer.tokenize(abstract[0:maxlen-2]) + ["[SEP]"]
        ret_val.append(abstract)
    return ret_val, tokenizer.vocab

def binary_prediction(abstracts):

    abstracts, vocab = tokenize(abstracts, maxlen=maxlen)

    token_vectors = np.asarray( [np.asarray( [vocab[token] for token in abstract] + [0] * (maxlen - len(abstract)) ) for abstract in abstracts] )
    del abstracts
 
    model = load_model(sys.argv[1])
    model.predict(token_vectors)