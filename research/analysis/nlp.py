import os
import random
from concurrent.futures import ThreadPoolExecutor, wait

import numpy as np
import spacy
from scipy import sparse
from sklearn.model_selection import train_test_split

PATH_TO_ARBITRARY = "research/data/arbitrary/codex"
PATH_TO_BLM = "research/data/elephrame/codex"
AXIS_DOCS = 0
AXIS_ENTS = 1

nlp = spacy.load("en_core_web_lg")


def _get_random_documents(base_path, count):
    def pathto(base_path, *args):
        return os.path.join(os.getcwd(), base_path, *args)

    docs = []
    file_names = [f for f in os.listdir(
        pathto(base_path)) if os.path.isfile(pathto(base_path, f))]
    for file_name in random.choices(file_names, k=count):
        with open(pathto(base_path, file_name), 'r') as f:
            docs.append(f.read())
    return docs


def load_documents(n=500, doc_accessor=_get_random_documents):
    """Returns the contents of n random documents from the arbitrary codex
    and n random documents from the elephrame codex (total documents == 2*n).
    The documents are returned as a single list with the arbitrary documents
    appearing first in the list, followed by the elephrame documents.

    Parameters
    ----------
    n: int
        The number of documents to return for each codex (arbitrary and elephrame).

    doc_accessor: func(str, int): list(str)
        Something that knows how to return the contents of some number of documents
        given a relative path and a number.

    Returns
    -------
    docs: list(str)
        The content of each requested document.
    labels: array(int)
        An array specifying the labels for the documents.
        0 == arbitrary, 1 == elephrame
    """
    arbitrary_docs = doc_accessor(PATH_TO_ARBITRARY, n)
    blm_docs = doc_accessor(PATH_TO_BLM, n)
    docs = [*arbitrary_docs, *blm_docs]
    labels = np.concatenate((np.zeros(n), np.ones(n)))
    return docs, labels


def _text_to_entities(text):
    """Extract a set of named entities from the supplied text."""
    doc = nlp(text)
    spans = spacy.util.filter_spans(
        set(doc.ents).union(set(doc.noun_chunks)))
    entities = {t.lower_ for t in [span for span in spans]}
    pruned_entities = set()
    for entity in entities:
        if len(entity) < 4:
            continue
        tokens = entity.split()
        if len(tokens) > 4:
            continue
        if tokens[0] in ["a", "an", "the"]:
            if len(tokens) == 1:
                continue
            tokens = tokens[1:]
        ok = True
        for token in tokens:
            if len(token) > 30:
                ok = False
                break
        if ok:
            entity = " ".join(tokens)
        else:
            continue
        pruned_entities.add(entity)
    return pruned_entities


def extract_entity_id_map(documents, extractor=_text_to_entities):
    """Returns a dictionary of named entities extracted from the supplied
    documents along with an id (factor) representing each entity.

    Parameters
    ----------
    documents: list(str)
        List of texts from which to extract the entities.

    extractor: func(str)->str
        Entity extraction behavior (mostly overridden for testing).

    Returns
    -------
    dict(str:int)
    """

    entity_set = set()
    futures = []
    with ThreadPoolExecutor() as e:
        for document in documents:
            futures.append(e.submit(extractor, document))
    done, not_done = wait(futures, return_when="FIRST_EXCEPTION")
    for d in done:
        if d.exception():
            [n.cancel() for n in not_done]
            raise d.exception()
        entity_set = entity_set.union(d.result())
    return {entity_id: entity for (entity, entity_id) in enumerate(entity_set)}


def _doc_to_vector(document, factorized_entities):
    vector = np.zeros(len(factorized_entities))
    for entity, entity_id in factorized_entities.items():
        vector[entity_id] = document.count(entity)
    return vector


def bag_of_entities(documents, factorized_entities, vectorizer=_doc_to_vector):
    """Converts a list of raw documents into a sparse matrix of the entity
    vectors for each document.

    Parameters
    ----------
    documents: list(str)

    factorized_entities: dict(str:int)

    vectorizer: func(str, dict(str:int)) -> array(int)

    Returns
    -------
    scipy.sparse.csr_matrix
    """

    # using a csr matrix because sp.sparse.vstack is optimized for csr matrices.
    M = sparse.csr_matrix((0, len(factorized_entities)))
    for document in documents:
        v = sparse.csr_matrix(_doc_to_vector(document, factorized_entities))
        M = sparse.vstack([M, v])
    return M


def tfidf(M):
    tf = sparse.csr_matrix(M / M.sum(axis=AXIS_ENTS))
    N = M.shape[AXIS_DOCS]
    Nt = np.ravel(M.astype(bool).sum(axis=AXIS_DOCS))
    idf = sparse.csr_matrix(np.log10(N/Nt))
    M1 = tf.multiply(idf)
    M1.data = np.nan_to_num(M1.data)
    M1.eliminate_zeros()
    return M1