from selenium import webdriver
import time
import hashlib
import os


NUM_PAGES = 165
BASE_URL = "https://elephrame.com/textbook/BLM/chart"
RAW_DIRECTORY = "research/raw"
PAGE_XPATH = "//div[@id='blm-results']/div/ul/li[3]/input"
NEXT_XPATH = "//div[@id='blm-results']/div/ul/li[4]"


def scrape():
    page_num = 1
    previous_num = 0
    wait = 1
    successes = 0
    previous_hash = hash("")
    cwd = os.getcwd()

    driver = webdriver.Chrome()
    driver.get(BASE_URL)
    while page_num < NUM_PAGES:
        try:
            time.sleep(wait)

            page_input = driver.find_elements_by_xpath(PAGE_XPATH)[0]
            page_num = int(page_input.get_attribute("value"))
            if page_num == previous_num:
                raise Exception("same page number")

            html_source = driver.page_source
            current_hash = _hash(html_source)
            if current_hash == previous_hash:
                raise Exception("duplicate page")
            previous_hash = current_hash

            filename = "{}/{}/page_{}.html".format(cwd, RAW_DIRECTORY, page_num)
            print("writing", filename)
            with open(filename, "w") as f:
                f.write(html_source)

            next_page_button = driver.find_element_by_xpath(NEXT_XPATH)
            next_page_button.click()

            successes = successes + 1
            if successes % 10 == 0 and wait > 1:
                wait = wait - 1
                print("decrement wait", wait)
        except Exception as e:
            wait = wait + 1
            print("increment wait", wait)
            print(page_num, e)
    driver.quit()


def _hash(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


if __name__ == "__main__":
    scrape()
