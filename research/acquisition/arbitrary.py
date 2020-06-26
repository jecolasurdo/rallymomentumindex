"""The arbitrary module contains functions for building a codex of arbitrary
subject matter. The arbitrary codex represents content scraped from the web 
that has no tie to any single specific topic.
"""

import asyncio
from datetime import datetime
import json
import os.path
import random
import time

from googlesearch import get_random_user_agent
from search_engines import *
from lxml import html
from selenium import webdriver

from research.acquisition.utils import prush, hash, time_limit
import urllib
from textpipe import doc

USNEWS = "http://usnews.com/topics/subjects"
REQUEST_TIMEOUT = 30
ASYNC_REQUEST_LIMIT = 25
PAGE_LOAD_WAIT = 1
SUBJECT_XPATH = "//div[{}]/ul/li/a/text()"

search_engines = [
    Ask,
    Bing,
    Dogpile,
    Duckduckgo,
    Google,
    Mojeek,
    Startpage,
    Yahoo
]


def gather_subjects(destination_dir="research/data/arbitrary"):
    """Scrapes a list of random news topics from usnews.com/topics and saves
    them in json format on disk.
    """
    driver = webdriver.Chrome()
    try:
        driver.get(USNEWS)
        tree = html.fromstring(driver.page_source)
    except Exception as e:
        raise e
    finally:
        driver.quit()

    subjects = set()
    for div_number in range(3, 30):
        subjects = subjects.union(
            {s.lower() for s in tree.xpath(SUBJECT_XPATH.format(div_number))})

    file_name = os.path.join(
        os.getcwd(), destination_dir, "usnews_subjects.json")
    with open(file_name, 'w') as f:
        json.dump(list(subjects), f)


def build_codex(doc_count=100, subjects_dir="research/data/arbitrary", destination_dir="research/data/arbitrary/codex"):
    """Builds a set of documents by collecting arbitrary content from the web
    based on a provided list of subjects.
    """
    SUBJECT_BATCH_SIZE = 10
    SEARCH_PAGES = 5
    MIN_DOC_LENGTH = 200

    subjects_file = os.path.join(
        os.getcwd(), subjects_dir, "usnews_subjects.json")
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)

    def _search():
        random.seed()
        pause = random.gauss(3, 1)
        prush("Pausing for {} seconds...".format(round(pause, 1)))
        time.sleep(pause)
        subject = random.choice(subjects) + " news"
        engine = random.choice(search_engines)()
        engine.set_headers({'User-Agent': get_random_user_agent()})
        # internally intepreted as sleep(random_uniform(*self._delay))
        # This value set low (or zero) since we pause between use of each
        # engine (above).
        engine._delay = (0, 0)
        prush("Searching for subject '{}'...".format(subject))
        search_results = engine.search(subject, pages=SEARCH_PAGES).links()
        prush("Found {} results for subject '{}'.".format(
            len(search_results), subject))
        return search_results

    success_count = 0
    search_results = _search()
    while success_count < doc_count:
        if success_count % 10 == 0:
            prush("\n{}: {} docs processed. {}% complete.\n".format(
                datetime.now(), success_count, 100 * round(success_count / doc_count, 2)))
        if success_count % SUBJECT_BATCH_SIZE == 0 and success_count != 0:
            search_results = _search()
        # We try to maintain a buffer above the minumum number of results required
        # so we 1) can choose some results at random (not just take all results) and
        # 2) can account for the fact that some of the links will not return 200.
        if len(search_results) < SUBJECT_BATCH_SIZE * 2:
            prush("Not enough results for subject. Trying another...")
            search_results = _search()
            continue
        success = False
        while not success:
            if len(search_results) == 0:
                prush("Exhausted search results for this subject. Trying another...")
                break
            random.seed()
            search_result = random.choice(search_results)
            search_results.remove(search_result)
            if "youtube.com" in search_result:
                prush("  Appears to be a YouTube result. Trying another...")
                continue
            if search_result[:-3] == "pdf":
                prush("  Appears to be a PDF. Trying another...")
                continue
            prush("Accessing {}...".format(search_result))
            file_name = os.path.join(
                os.getcwd(), destination_dir, hash(search_result) + ".txt")
            if os.path.exists(file_name):
                prush("  URL previously ingested. Trying another...")
                continue
            try:
                with time_limit(REQUEST_TIMEOUT):
                    response = urllib.request.urlopen(search_result)
                raw_document = bytes(doc.Doc(response.read()).clean, 'utf-8')
                document = raw_document.decode("utf-8", "strict")
            except Exception as e:
                prush("  Error. {}\n  Trying another...".format(e))
                continue
            if len(document) < MIN_DOC_LENGTH:
                prush(" Document too short. Trying another...")
                continue
            with open(file_name, 'w') as f:
                f.write(document)
            prush("  Success! Written to {}".format(
                hash(search_result) + ".txt"))
            success = True
            success_count = success_count + 1
    prush("Done")
