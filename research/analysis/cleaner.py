# lowercase
# Irrelevant files / words
# alternate spellings
# lemmatization

import os.path

import spacy
from spacy.symbols import nsubj, VERB

nlp = spacy.load("en_core_web_lg")

with open(os.path.join(os.getcwd(), "research/data/codex/", "4de376ce8b1e2b383860437345caf437.txt"), 'r') as f:
    doc = nlp(f.read())

for ent in doc.ents[:20]:
    print(ent, ent.vector)