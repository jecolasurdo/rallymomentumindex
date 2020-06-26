from research.analysis import nlp

docs, labels = nlp.load_documents(n=20)
entity_map = nlp.extract_entity_id_map(docs)
bag = nlp.bag_of_entities(docs, entity_map)
tfidf = nlp.tfidf(bag)
print(bag.shape, tfidf.shape)
