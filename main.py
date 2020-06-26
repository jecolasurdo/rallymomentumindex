from research.analysis import nlp

docs, labels = nlp.load_documents(n=200)
entity_map = nlp.extract_entity_id_map(docs)
bag = nlp.bag_of_entities(docs, entity_map)
print(bag.shape)
