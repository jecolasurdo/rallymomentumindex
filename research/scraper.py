import json
import os
import os.path
import time
import urllib
from datetime import datetime
import asyncio
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


def hydrate_codex(clean_file="research/data/cleaned.json", url_timeout=10, max_consecutive_exceptions=10):
    prush("Loading cleaned data...")
    with open(os.path.join(os.getcwd(), clean_file), 'r') as f:
        reports = json.load(f)

    prush("Counting distinct URLs to process...")
    urldict = dict()
    for report in reports:
        for u in report["urls"]:
            urldict[u["hash"]] = True
    url_count = len(urldict.keys())
    prush("Distinct URL Count:", url_count)
    urldict = None

    consecutive_unhandled = 0
    processed_urls = 0
    for report in reports:
        for u in report["urls"]:
            processed_urls = processed_urls + 1
            pct = round(processed_urls/url_count*100, 2)
            url, hsh = u["url"], u["hash"]
            prush("{} - {}/{} ({}%) - Processing {}: {}".format(datetime.now(),
                                                               processed_urls,
                                                               url_count,
                                                               pct,
                                                               hsh,
                                                               url))
        result = _process_url(hsh, url, url_timeout)
        if result["successful"]:
            consecutive_unhandled = 0
        else:
            consecutive_unhandled = consecutive_unhandled + 1
            if consecutive_unhandled > max_consecutive_exceptions:
                prush("Consecutive exception limit exceeded. Halting.")
                raise Exception(result["msg"])

    prush("Done.")

    
# def _process_url(hsh, url, url_timeout):
#     def ret(successful, msg):
#         return {
#             "hsh":hsh,
#             "url":url,
#             "successful":successful,
#             "msg":msg
#         }

#     if "twitter" in url:
#         return ret(True, "Skipping twitter.")

#     hsh_file = os.path.join(
#         os.getcwd(), "research/data/codex", hsh + ".txt")
#     if os.path.exists(hsh_file):
#         return ret(True, "URL already processed. Skipping.")

#     try:
#         with utils.time_limit(url_timeout):
#             response = urllib.request.urlopen(url)
#     except urllib.error.HTTPError as e:
#         return ret(True, e)
#     except TimeoutError:
#         return ret(True, "Timeout. Skipping.")
#     except Exception as e:
#         return ret(False, e)

#     document = doc.Doc(response.read()).clean
#     with open(os.path.join(os.getcwd(), "research/data/codex", hsh_file), 'w') as f:
#         f.write(document)
#     return ret(True, "Success")

# def _process_url(hsh, url, url_timeout):
#     def ret(successful, msg):
#         return {
#             "hsh":hsh,
#             "url":url,
#             "successful":successful,
#             "msg":msg
#         }

#     if "twitter" in url:
#         return ret(True, "Skipping twitter.")

#     hsh_file = os.path.join(
#         os.getcwd(), "research/data/codex", hsh + ".txt")
#     if os.path.exists(hsh_file):
#         return ret(True, "URL already processed. Skipping.")

#     try:
#         with utils.time_limit(url_timeout):
#             response = urllib.request.urlopen(url)
#     except urllib.error.HTTPError as e:
#         return ret(True, e)
#     except TimeoutError:
#         return ret(True, "Timeout. Skipping.")
#     except Exception as e:
#         return ret(False, e)

#     document = doc.Doc(response.read()).clean
#     with open(os.path.join(os.getcwd(), "research/data/codex", hsh_file), 'w') as f:
#         f.write(document)
#     return ret(True, "Success")

def hydrate_codex(clean_file="research/data/cleaned.json", url_timeout=10, max_consecutive_exceptions=10):
    prush("Loading cleaned data...")
    with open(os.path.join(os.getcwd(), clean_file), 'r') as f:
        reports = json.load(f)

    prush("Counting distinct URLs to process...")
    urldict = dict()
    for report in reports:
        for u in report["urls"]:
            urldict[u["hash"]] = True
    url_count = len(urldict.keys())
    prush("Distinct URL Count:", url_count)
    urldict = None

    work = []
    for report in reports:
        for u in report["urls"]:
            work.append(get_html(u["url"]))
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(work))
    prush("Done.")

async def get_html(url):
    async with aiohttp.ClientSession() as session:
        return await fetch(session, url)

async def fetch(session, url):
    async with session.get(url) as response:
        print("getting", url)
        return await response.text()