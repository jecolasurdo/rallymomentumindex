from research.analysis import nlp

docs, labels = nlp.load_documents(n=10)
entity_map = nlp.extract_entity_id_map(docs)
pass
