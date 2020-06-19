import asyncio
import json
import os
import os.path
import time
import urllib
from datetime import datetime

import aiohttp
from lxml import html
from selenium import webdriver
from textpipe import doc

from research import fmt, utils
from research.utils import prush

BASE_URL = "https://elephrame.com/textbook/BLM/chart"
PAGE_XPATH = "//div[@id='blm-results']/div/ul/li[3]/input"
NEXT_XPATH = "//div[@id='blm-results']/div/ul/li[4]"
MAX_FAILURES = 10
SUCCESS_DOWNGRADE_INTERVAL = 5
MINIMUM_LOAD_WAIT_SECS = 1
WAIT_DECREMENT_INTEVAL = 1
WAIT_INCREMENT_INTEVAL = 1
EXTRACT_FILE_NAME = "extracted_data.json"
CODEX_DIRECTORY = "research/data/codex"
CODEX_SEMAPHORE_LIMIT = 50


def scrape(raw_directory="research/data/raw_html", num_pages=165):
    """Scrapes raw HTML BLM data for each page at https://elephrame.com/textbook/BLM/chart
    and saves the HTML for each page to a local directory.

    Parameters
    ----------
    raw_directory : str
        The directory into which the raw html files will be saved.

    num_pages : int
        The number of pages to scrape.

    Raises
    ------
    Exception
        The max number of consecutive failures (MAX_FAILURES) has been reached.

    Notes
    -----
    Since the main table in the scraped page loads asyncronously, it can be
    difficult to know that the content has been fully rendered prior to automating
    the click event to load the next page of the table. The function tries
    to cope with this by checking that the page content has changed since the
    last time it loaded, and by dynamically adjusting a wait timer to give the
    components sufficient time to load before processing. This approach
    is imperfect, but seems to be minimally sufficient to meet current needs.

    Since the waiting mechanisms currently employed here are fairly crude, the
    function may accidentally skip some pages as it moves along. This usually
    occurs if the function tries to submit a multiple click events too qucicky,
    in which case, the function thinks it had time to process a page that it
    never actually processed. The function will recover from this and move on to
    the next page cleanly, but nothing is done to try and recover the skipped
    page.

    This function currently runs chrome as the driver, and does not run 
    headless. The function is fragile to the size of the browser window that is 
    opened. Changing the browser window can cause the DOM to restructure, which
    can cause the XPATH assumptions to become invalid. Not worth fixing at the
    moment, but be warned.
    """

    page_num = 1
    previous_num = 0
    wait = MINIMUM_LOAD_WAIT_SECS
    consecutive_successes = 0
    consecutive_failures = 0
    previous_hash = hash("")
    cwd = os.getcwd()

    driver = webdriver.Chrome()
    driver.get(BASE_URL)
    while page_num < num_pages:
        try:
            time.sleep(wait)

            page_input = driver.find_elements_by_xpath(PAGE_XPATH)[0]
            page_num = int(page_input.get_attribute("value"))
            if page_num == previous_num:
                raise Exception("Page number hasn't changed yet.")

            html_source = driver.page_source
            current_hash = utils.hash(html_source)
            if current_hash == previous_hash:
                raise Exception("Page content hasn't changed yet.")
            previous_hash = current_hash

            filename = "{}/{}/page_{}.html".format(cwd,
                                                   raw_directory, page_num)
            prush("writing", filename)
            with open(filename, "w") as f:
                f.write(html_source)

            driver.find_element_by_xpath(NEXT_XPATH).click()

            consecutive_successes = consecutive_successes + 1
            consecutive_failures = 0
            if consecutive_successes >= SUCCESS_DOWNGRADE_INTERVAL and wait - WAIT_DECREMENT_INTEVAL >= MINIMUM_LOAD_WAIT_SECS:
                consecutive_successes = 0
                wait = wait - WAIT_DECREMENT_INTEVAL
                prush("Decrementing wait to", wait)
        except Exception as e:
            prush(page_num, e)
            consecutive_failures = consecutive_failures + 1
            consecutive_successes = 0
            if consecutive_failures >= MAX_FAILURES:
                raise Exception("Reached max number of consecutive failures.")
            wait = wait + WAIT_INCREMENT_INTEVAL
            prush("Incrementing wait to", wait)
    driver.quit()


def extract(raw_directory="research/data/raw_html"):
    """Extract the BLM data from raw HTML files in a directory and save the
    resulting data to disk.

    Parameters
    ----------
    raw_directory : str
        The directory to find raw html files to be extracted.
    """

    results = []
    raw_dir = os.path.join(os.getcwd(), raw_directory)
    prush("Getting list of raw html files...")
    file_names = [f for f in os.listdir(raw_dir) if os.path.isfile(
        os.path.join(raw_dir, f)) and f.endswith(".html")]
    prush("Extracting data from raw html...")
    for file_name in file_names:
        f = open(os.path.join(raw_dir, file_name), "r")
        tree = html.fromstring(f.read())
        f.close()
        items_list_div = tree.xpath('//div[@class="item chart"]')
        for item_div in items_list_div:
            results.append({
                "location": utils.first(item_div.xpath(
                    'div/div[@class="item-protest-location"]/text()')),
                "start": utils.first(item_div.xpath(
                    'div/div/div[@class="protest-start"]/text()')),
                "end": utils.first(item_div.xpath(
                    'div/div/div[@class="protest-end"]/text()')),
                "subject": utils.first(item_div.xpath(
                    'div/ul/li[@class="item-protest-subject"]/text()')),
                "participants": utils.first(item_div.xpath(
                    'div/ul/li[@class="item-protest-participants"]/text()')),
                "time": utils.first(item_div.xpath(
                    'div/ul/li[@class="item-protest-time"]/text()')),
                "description": utils.first(item_div.xpath(
                    'div/ul/li[@class="item-protest-description"]/text()')),
                "urls": item_div.xpath(
                    'div/ul/li[@class="item-protest-url"]/p/a/text()'),
            })
    prush("Writing to {}...".format(EXTRACT_FILE_NAME))
    with open(os.path.join(raw_dir, EXTRACT_FILE_NAME), "w") as f:
        f.write(json.dumps(results, indent=2))
    prush("Done.")


def clean(extracted_file="research/data/extracted.json"):
    with open(os.path.join(os.getcwd(), extracted_file), 'r') as f:
        extracted = json.load(f)

    cleaned = []
    for item in extracted:
        cleaned.append({
            "location": fmt.location(item["location"]),
            "active": fmt.active(item["start"]),
            "start": fmt.date(item["start"]),
            "end": fmt.date(item["end"]),
            "subject": fmt.subject(item["subject"]),
            "magnitude": fmt.participants(item["participants"]),
            "timeframe": fmt.timeframe(item["time"]),
            "description": fmt.description(item["description"]),
            "urls": list(fmt.urls(item["urls"]))
        })

    with open(os.path.join(os.getcwd(), "research/data/cleaned.json"), 'w') as f:
        f.write(json.dumps(cleaned, indent=2))


def hydrate_codex():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_hydrate_codex())
    loop.close()


async def _hydrate_codex(clean_file="research/data/cleaned.json", url_timeout=10, max_consecutive_exceptions=10):
    prush("Loading cleaned data...")
    with open(os.path.join(os.getcwd(), clean_file), 'r') as f:
        reports = json.load(f)

    prush("Counting distinct URLs to process...")
    sem = asyncio.Semaphore(CODEX_SEMAPHORE_LIMIT)
    urlset = set()
    pending = []
    for report in reports:
        for url_info in report["urls"]:
            urlset.add(url_info["hash"])
            pending.append(_get_html(url_info, sem))
    url_count_distinct = len(urlset)
    url_count = len(pending)
    prush("Distinct URL Count:", url_count_distinct)
    urlset = None

    url_count_processed = 0
    success_count = 0
    while len(pending) > 0:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for d in done:
            result = d.result()
            url_count_processed = url_count_processed + 1
            pct = round(url_count_processed/url_count*100, 2)
            prush("{} - {}/{} ({}%): {} {} {}".format(datetime.now(),
                                                      url_count_processed,
                                                      url_count,
                                                      pct,
                                                      result["hash"],
                                                      result["msg"],
                                                      result["url"]))
            if result["successful"]:
                success_count = success_count + 1
    prush("Done. {}/{} successully processed.".format(success_count, url_count))


async def _get_html(url_info, sem):
    async with aiohttp.ClientSession() as session:
        return await _fetch(session, url_info, sem)


async def _fetch(session, url_info, sem, url_timeout=30):
    def ret(successful, msg):
        return {
            "hash": url_info["hash"],
            "url": url_info["url"],
            "successful": successful,
            "msg": msg
        }

    if "twitter.com" in url_info["url"]:
        return ret(False, "Skipping twitter.")

    try:
        with utils.time_limit(url_timeout):
            async with sem, session.get(url_info["url"]) as response:
                html = await response.text()
    except Exception as e:
        return ret(False, "Exception: '{}'".format(e))

    hsh_file = os.path.join(
        os.getcwd(), CODEX_DIRECTORY, url_info["hash"] + ".txt")
    if os.path.exists(hsh_file):
        return ret(True, "URL already processed. Skipping.")

    document = doc.Doc(html).clean
    with open(os.path.join(os.getcwd(), CODEX_DIRECTORY, hsh_file), 'w') as f:
        f.write(document)
    return ret(True, "Success")
