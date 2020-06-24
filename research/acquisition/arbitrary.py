"""The arbitrary module contains functions for building a codex of arbitrary
subject matter. The arbitrary codex represents content scraped from the web 
that has no tie to any single specific topic.
"""

import asyncio

import aiohttp

from research.acquisition.utils import prush

USNEWS = "http://usnews.com/topics/"
# TOPIC_INDICES = "a b c d e f g h i j k l m n o p q r s t u v w x y z 0-9"
TOPIC_INDICES = "a b"
REQUEST_TIMEOUT = 30
ASYNC_REQUEST_LIMIT = 25


def scrape_topics(destination_dir="research/data/arbitrary"):
    """Scrapes a list of random news topics from usnews.com/topics and saves
    them in json format on disk.
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_get_topics())
    loop.close()
    pass

async def _get_topics():
    result = await _fetch_topic_indices()
    pass

async def _fetch_topic_indices():
    sem = asyncio.Semaphore(ASYNC_REQUEST_LIMIT)
    pending = [_fetch_topic_index(idx, sem) for idx in TOPIC_INDICES.split()]
    indices = []
    while len(pending) > 0:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for d in done:
            if d.exception():
                for p in pending:
                    p.cancel()
                    raise d.exception()
            indices.append(d.result())
    return indices

async def _fetch_topic_index(topic_index, sem):
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = USNEWS + topic_index
        async with sem, session.get(url) as response:
            if response.status != 200:
                raise Exception(
                    "{} - {}".format(response.status, response.reason))
            return await response.text()
                

def scrape(doc_count=10, destination_dir="research/data/arbitrary/codex"):
    pass
