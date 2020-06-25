"""The arbitrary module contains functions for building a codex of arbitrary
subject matter. The arbitrary codex represents content scraped from the web 
that has no tie to any single specific topic.
"""

import asyncio
import json
import os.path
from random import choice
import time

from google import google
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
    BATCH_BUFFER_MULTIPLIER = 2
    SEARCH_PAGE_COUNT = 5
    MIN_DOC_LENGTH = 200

    subjects_file = os.path.join(
        os.getcwd(), subjects_dir, "usnews_subjects.json")
    with open(subjects_file, 'r') as f:
        subjects = json.load(f)

    def search():
        search_results = []
        while len(search_results) < SUBJECT_BATCH_SIZE * BATCH_BUFFER_MULTIPLIER:
            subject = choice(subjects) + " news"
            prush("Searching for subject '{}'...".format(subject))
            try:
                search_results = google.search(subject, pages=SEARCH_PAGE_COUNT)
            except Exception as e:
                prush(e)
                time.sleep(5)

        prush("Found {} results for subject '{}'.".format(
            len(search_results), subject))
        return search_results

    success_count = 0
    search_results = search()
    while success_count < doc_count:
        if success_count % SUBJECT_BATCH_SIZE == 0:
            search_results = search()
        success = False
        while not success:
            result = choice(search_results)
            if not result.link:
                continue
            prush("Accessing {}...".format(result.link))
            file_name = os.path.join(
                os.getcwd(), destination_dir, hash(result.link) + ".txt")
            if os.path.exists(file_name):
                prush("  File previously processed. Trying another...")
                continue
            try:
                response = urllib.request.urlopen(result.link)
                raw_document = doc.Doc(response.read()).clean
                document = raw_document.decode("utf-8", "strict")
            except Exception as e:
                prush("  Error. {}\n  Trying another...".format(e))
                continue
            if len(document) < MIN_DOC_LENGTH:
                prush(" Document too short. Trying another...")
                continue
            with open(file_name, 'w') as f:
                f.write(document)
            prush("  Success! Written to {}".format(hash(result.link) + ".txt"))
            success = True
            success_count = success_count + 1
    prush("Done")
