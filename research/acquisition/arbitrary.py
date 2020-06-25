"""The arbitrary module contains functions for building a codex of arbitrary
subject matter. The arbitrary codex represents content scraped from the web 
that has no tie to any single specific topic.
"""

import asyncio
import json
import os.path

from lxml import html

from research.acquisition.utils import prush
from selenium import webdriver
import time

USNEWS = "http://usnews.com/topics/subjects"
REQUEST_TIMEOUT = 30
ASYNC_REQUEST_LIMIT = 25
PAGE_LOAD_WAIT = 1
SUBJECT_XPATH = "//div[{}]/ul/li/a/text()"

def scrape_subjects(destination_dir="research/data/arbitrary"):
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
    for div_number in range(3,30):
        subjects = subjects.union({s.lower() for s in tree.xpath(SUBJECT_XPATH.format(div_number))})

    file_name = os.path.join(os.getcwd(), destination_dir, "usnews_subjects.json")
    with open(file_name, 'w') as f:
        json.dump(list(subjects), f) 

def scrape(doc_count=10, destination_dir="research/data/arbitrary/codex"):
    pass
