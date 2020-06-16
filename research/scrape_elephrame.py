from selenium import webdriver
import time
import hashlib
import os


BASE_URL = "https://elephrame.com/textbook/BLM/chart"
PAGE_XPATH = "//div[@id='blm-results']/div/ul/li[3]/input"
NEXT_XPATH = "//div[@id='blm-results']/div/ul/li[4]"
MAX_FAILURES = 10
SUCCESS_DOWNGRADE_INTERVAL = 5
MINIMUM_LOAD_WAIT_SECS = 1
WAIT_DECREMENT_INTEVAL = 1
WAIT_INCREMENT_INTEVAL = 1


def scrape(raw_directory="research/raw", num_pages=165):
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
            current_hash = _hash(html_source)
            if current_hash == previous_hash:
                raise Exception("Page content hasn't changed yet.")
            previous_hash = current_hash

            filename = "{}/{}/page_{}.html".format(cwd,
                                                   raw_directory, page_num)
            print("writing", filename)
            with open(filename, "w") as f:
                f.write(html_source)

            driver.find_element_by_xpath(NEXT_XPATH).click()

            consecutive_successes = consecutive_successes + 1
            consecutive_failures = 0
            if consecutive_successes >= SUCCESS_DOWNGRADE_INTERVAL and wait - WAIT_DECREMENT_INTEVAL >= MINIMUM_LOAD_WAIT_SECS:
                consecutive_successes = 0
                wait = wait - WAIT_DECREMENT_INTEVAL
                print("Decrementing wait to", wait)
        except Exception as e:
            print(page_num, e)
            consecutive_failures = consecutive_failures + 1
            consecutive_successes = 0
            if consecutive_failures >= MAX_FAILURES:
                raise Exception("Reached max number of consecutive failures.")
            wait = wait + WAIT_INCREMENT_INTEVAL
            print("Incrementing wait to", wait)
    driver.quit()


def _hash(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


if __name__ == "__main__":
    scrape()
