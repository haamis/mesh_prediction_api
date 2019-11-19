import sys, json
import tensorflow as tf
import numpy as np

from scipy.sparse import lil_matrix

from keras.backend.tensorflow_backend import set_session
from keras.models import load_model

from keras_bert import get_custom_objects

from bert import tokenization

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
set_session(tf.Session(config=config))

maxlen = 512

custom_objects = get_custom_objects()
custom_objects["tf"] = tf

model = load_model("../bert_best_finetuned.h5", custom_objects=custom_objects)

with open("../old_complete_output.json_class_labels.txt") as f:
    label_mapping = np.array(json.load(f))

with open("../mesh_mapping.json") as f:
    mesh_mapping = json.load(f)

graph = tf.get_default_graph()
tokenizer = tokenization.FullTokenizer("../biobert_pubmed/vocab.txt", do_lower_case=False)

def make_multilabel_prediction(abstract):

    abstract = ["[CLS]"] + tokenizer.tokenize(abstract)[0:maxlen-2] + ["[SEP]"]
    vocab = tokenizer.vocab

    print(abstract)

    token_vectors = np.asarray( [vocab[token] for token in abstract] + [0] * (maxlen - len(abstract)) )

    # Model expects a list of samples, we only have one.
    token_vectors = np.asarray([token_vectors])
    
    with graph.as_default():

        labels_prob = model.predict([token_vectors, lil_matrix(token_vectors.shape)])

        labels_pred = np.zeros_like(labels_prob, dtype='b')
        labels_pred[labels_prob>0.5] = 1

        mesh_ids = label_mapping[labels_pred[0] == 1].tolist()

        print([{"mesh_id": mesh_id, "mesh_name": mesh_mapping[mesh_id]} for mesh_id in mesh_ids])
        print()

        return [{"mesh_id": mesh_id, "mesh_name": mesh_mapping[mesh_id]} for mesh_id in mesh_ids]

if __name__ == "__main__":
    make_multilabel_prediction(sys.argv[1])