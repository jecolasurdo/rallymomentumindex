import os
import random

import numpy as np
import scipy as sp
import spacy

PATH_TO_ARBITRARY = "research/data/arbitrary/codex"
PATH_TO_BLM = "research/data/elephrame/codex"

nlp = spacy.load("en_core_web_lg")


def load_documents(n=500):
    """Returns the contents of n random documents from the arbitrary codex
    and n random documents from the elephrame codex (total documents == 2*n).
    The documents are returned as a single list with the arbitrary documents
    appearing first in the list, followed by the elephrame documents.

    Parameters
    ----------
    n: int
        The number of documents to return for each codex (arbitrary and elephrame).

    Returns
    -------
    docs: list(str)
        The content of each requested document.
    labels: array(int)
        An array specifying the labels for the documents.
        0 == arbitrary, 1 == elephrame
    """
    def pathto(base_path, *args):
        return os.path.join(os.getcwd(), base_path, *args)

    def get_random_documents(base_path, count):
        docs = []
        file_names = [f for f in os.listdir(
            pathto(base_path)) if os.path.isfile(pathto(base_path, f))]
        for file_name in random.choices(file_names, k=count):
            with open(pathto(base_path, file_name), 'r') as f:
                docs.append(f.read())
        return docs

    arbitrary_docs = get_random_documents(PATH_TO_ARBITRARY, n)
    blm_docs = get_random_documents(PATH_TO_BLM, n)
    docs = [*arbitrary_docs, *blm_docs]
    labels = np.concatenate((np.zeros(n), np.ones(n)))
    return docs, labels


def text_to_entities(text):
    """Extract a set of named entities from the supplied text."""
    doc = nlp(text)
    spans = spacy.util.filter_spans(
        set(doc.ents).union(set(doc.noun_chunks)))
    entities = {t.lower_ for t in [span for span in spans]}
    return entities


def extract_entity_id_map(documents, extractor=text_to_entities):
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
    for d in documents:
        entity_set = entity_set.union(extractor(d))
    return {entity: entity_id for (entity, entity_id) in enumerate(entity_set)}


def bag_of_entities(documents, factorized_entities):
    """Converts a list of raw documents into a sparse matrix of the entity
    vectors for each document.

    Parameters
    ----------
    documents: list(str)

    factorized_entities: dict(str:int)

    Returns
    -------
    scipy.sparse.csr_matrix
    """
    def doc_to_vector(document, factorized_entities):
        vector = np.zeros(len(factorized_entities))
        for entity, entity_id in factorized_entities.items():
            vector[entity_id] = document.count(entity)
        return vector

    # using a csr matrix because sp.sparse.vstack is optimized for csr matrices.
    M = sp.sparse.csr_matrix()
    for document in documents:
        v = sp.sparse.csr_matrix(doc_to_vector(document, factorized_entities))
        M = sp.sparse.vstack([M, v])
    return M
