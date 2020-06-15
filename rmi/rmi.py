'''
register sources
call search on each source with appropriate terminology
raw text results are returned from each searcher
'''

import sources.googler

keywords = ["BLM", "black lives matter"]

# A searcher is any class that implements a `search` method that returns a list
# of raw text results for a given search criteria.
searchers = [
    sources.googler.Searcher(keywords, num_page=2)
]

for s in searchers:
    print(list(s.search()))
