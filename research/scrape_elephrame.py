from selenium import webdriver
import time
import hashlib

BASE_URL = "https://elephrame.com/textbook/BLM/chart"
LAST_PAGE = 165

browser = webdriver.Chrome()
browser.get(BASE_URL)
page_num = 1
previous_num = 0
wait = 1
successes = 0
previous_hash = hash("")

while page_num <= LAST_PAGE:
    try:
        time.sleep(wait)

        page_input = browser.find_elements_by_xpath(
            "//div[@id='blm-results']/div/ul/li[3]/input")[0]
        page_num = int(page_input.get_attribute("value"))
        if page_num == previous_num:
            raise Exception("same page number")

        html_source = browser.page_source
        current_hash = hash(html_source)
        if current_hash == previous_hash:
            raise Exception("duplicate page")

        print(page_num, current_hash)
        previous_hash = current_hash

        next_page_button = browser.find_element_by_xpath(
            "//div[@id='blm-results']/div/ul/li[4]")
        next_page_button.click()

        successes = successes + 1
        if successes % 10 == 0 and wait > 1:
            wait = wait - 1
            print("decrement wait", wait)
    except Exception as e:
        wait = wait + 2
        print("increment wait", wait)
        print(page_num, e)
browser.quit()

def hash(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()