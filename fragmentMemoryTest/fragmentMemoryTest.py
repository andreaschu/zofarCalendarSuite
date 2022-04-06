from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import urllib.parse
import string
import random


def return_random_string(length: int) -> string:
    all_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + ' []{}()_-'
    tmp_str = ''
    for i in range(length):
        tmp_str += random.choice(all_chars)
    return tmp_str



DRIVER = r'C:\Users\friedrich\PycharmProjects\Screenshotter_manual\venv\chromedriver\chromedriver.exe'
service_object = Service(executable_path=DRIVER)

new_driver = Chrome(service=service_object)


url_stem = 'http://localhost:8081/calendar_lab/'

new_driver.get(urllib.parse.urljoin(url_stem, 'special/login.xhtml?zofar_token=part1'))
try:
    new_driver.get(urllib.parse.urljoin(url_stem, 'set_episode_index.xhtml'))
    episode_index_element = new_driver.find_element(By.CSS_SELECTOR, '#form\:set_episode_index\:mqsc\:responsedomain\:response\:oq')
    episode_index_element.clear()
    episode_index_element.send_keys('0')

    new_driver.find_element(By.CSS_SELECTOR, '#form\:btPanel\:forward\:forwardBt').click()

    # reset the whole json array
    new_driver.get(urllib.parse.urljoin(url_stem, 'reset_json_array.xhtml'))
    new_driver.find_element(By.CSS_SELECTOR, '#form\:btPanel\:forward\:forwardBt').click()

    # confirm that the json array is empty
    new_driver.get(urllib.parse.urljoin(url_stem, 'inspect_episode_data.xhtml'))
    tmp_text = new_driver.find_element(By.CSS_SELECTOR, '#form\:inspect_episode_data\:t1').text
    search_str = 'whole json array: '
    if tmp_text.find(search_str) == -1:
        raise ValueError(f'expected text not found: "{search_str}"\nin website text: "{tmp_text}"')
    else:

        index_start = tmp_text.find(search_str) + len(search_str)
        if '\n' in tmp_text[index_start:]:
            index_end = tmp_text[index_start:].find('\n') + index_start
        else:
            index_end = len(tmp_text[index_start:]) + index_start
        json_text = tmp_text[index_start:index_end].strip()
        assert json_text == '[]'

    new_driver.get(urllib.parse.urljoin(url_stem, 'set_episode_data.xhtml'))
    for element in new_driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]'):
        element.send_keys(return_random_string(1000))
    new_driver.find_element(By.CSS_SELECTOR, '#form\:btPanel\:forward\:forwardBt').click()

    new_driver.get(urllib.parse.urljoin(url_stem, 'inspect_episode_data.xhtml'))
    new_driver.get(urllib.parse.urljoin(url_stem, 'set_fragment.xhtml'))
    new_driver.get(urllib.parse.urljoin(url_stem, 'inspect_fragment.xhtml'))
finally:
    new_driver.get(urllib.parse.urljoin(url_stem, 'j_spring_security_logout'))
time.sleep(1)

episode_index_input = new_driver.find_element(By.CSS_SELECTOR, '#form\:index\:mqsc\:responsedomain\:response\:oq')
episode_index_input.send_keys('0')

new_driver.find_element(By.CSS_SELECTOR, '#form\:btPanel\:forward\:forwardBt').click()

print()