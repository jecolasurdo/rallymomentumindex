"""The arbitrary module contains functions for building a codex of arbitrary
subject matter. The arbitrary codex represents content scraped from the web 
that has no tie to any single specific topic.
"""

import asyncio
import json
import os.path
import random
import time

from googlesearch import search, get_random_user_agent
from lxml import html
from selenium import webdriver

from research.acquisition.utils import prush, hash
import urllib
from textpipe import doc

USNEWS = "http://usnews.com/topics/subjects"
REQUEST_TIMEOUT = 30
ASYNC_REQUEST_LIMIT = 25
PAGE_LOAD_WAIT = 1
SUBJECT_XPATH = "//div[{}]/ul/li/a/text()"


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
    SUBJECT_BATCH_SIZE = 5
    MAX_SEARCH_RESULTS = 100
    SEARCH_RESULTS_PER_PAGE = 100
    MIN_DOC_LENGTH = 200

    subjects_file = os.path.join(
        os.getcwd(), subjects_dir, "usnews_subjects.json")
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)

    def _search():
        # Waiting a moment before hitting the search API again
        # trying to avoid rate limits. Using a guass distribution to give
        # some jitter to the wait times to make us look a little less
        # uniform to google. googlesearch.search() implements an internal
        # waiter, but we need to control the waits from outside the function
        # since the internal waiter doesn't account for successive calls to the
        # function itself.
        random.seed()
        pause = random.gauss(3, 1)
        prush("Pausing for {} seconds to avoid rate limits...".format(round(pause,2)))
        time.sleep(pause)
        subject = random.choice(subjects) + " news"
        prush("Searching for subject '{}'...".format(subject))
        search_results = list(search(subject, num=SEARCH_RESULTS_PER_PAGE, stop=MAX_SEARCH_RESULTS, user_agent=get_random_user_agent()))
        prush("Found {} results for subject '{}'.".format(
            len(search_results), subject))
        return search_results

    success_count = 0
    search_results = _search()
    while success_count < doc_count:
        if success_count % SUBJECT_BATCH_SIZE == 0 and success_count != 0:
            search_results = _search()
        success = False
        while not success:
            random.seed()
            search_result = random.choice(search_results)
            prush("Accessing {}...".format(search_result))
            file_name = os.path.join(
                os.getcwd(), destination_dir, hash(search_result) + ".txt")
            if os.path.exists(file_name):
                prush("  File previously processed. Trying another...")
                continue
            try:
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
            prush("  Success! Written to {}".format(hash(search_result) + ".txt"))
            success = True
            success_count = success_count + 1
    prush("Done")
