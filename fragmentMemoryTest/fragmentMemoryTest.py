__version__ = '0.0.1'

# # DEV using seleniumrequests instead (see below)
# from selenium.webdriver import Chrome
# pip install selenium-requests
from seleniumrequests import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import datetime
import urllib.parse
import string
import random
import uuid
from pathlib import Path
from typing import Optional, Union
from threading import Thread
import os
from influxDBWriter.influxDBWriter import writeDataToInflux

_here = Path(__file__).parent

run_uid = uuid.uuid4()
timestamp_float = time.time()


def find(f, seq):
    """Return first item in sequence where f(item) == True."""
    for item in seq:
        if f(item):
            return item


def return_random_string(length: int) -> string:
    all_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + ' []{}()_-'
    tmp_str = ''
    for i in range(length):
        tmp_str += random.choice(all_chars)
    return tmp_str


class TestRun:
    def __init__(self,
                 uri_stem: str,
                 chromedriver_executable: Union[str, Path],
                 token: str,
                 length_of_random_strings: int,
                 reload_and_save_episode_data_count: int,
                 number_of_input_fields_to_fill: int = 0,
                 number_of_episodes_to_fill: int = 1,
                 generate_new_data: bool = True,
                 uid: Optional[uuid.UUID] = None,
                 timestamp: Optional[float] = None,
                 ):
        if uid is None:
            self.uid = uuid.uuid4()
        else:
            self.uid = uid

        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

        self.timestamp_str = datetime.datetime.fromtimestamp(self.timestamp, datetime.timezone.utc)

        self.url_stem = uri_stem
        self.token = token

        self.generate_new_data = generate_new_data

        self.length_of_random_strings = length_of_random_strings
        self.reload_and_save_episode_data_count = reload_and_save_episode_data_count
        self.number_of_input_fields_to_fill = number_of_input_fields_to_fill
        self.number_of_episodes_to_fill = number_of_episodes_to_fill

        self.number_of_fragment_variables = -1
        self.number_of_episode_data_text_fields = -1
        self.average_characters_in_text_fields = -1

        self.chromedriver = Path(chromedriver_executable)
        service_object = Service(executable_path=str(self.chromedriver))
        self.driver = Chrome(service=service_object)

    @staticmethod
    def write_data_to_influx(data: list):
        writeDataToInflux(database_name='zofartestsuite', host='localhost', port=8086, data_input=data)

    def login(self):
        self.driver.get(urllib.parse.urljoin(url_stem, 'special/login.xhtml?zofar_token=' + self.token))

    def logout(self):
        self.driver.get(urllib.parse.urljoin(url_stem, 'j_spring_security_logout'))

    def reset_json(self):
        # reset the whole json array
        self.driver.get(urllib.parse.urljoin(url_stem, 'reset_json_array.xhtml'))
        self.driver.find_element(By.CSS_SELECTOR, '#form\:btPanel\:forward\:forwardBt').click()

        # confirm that the json array is empty
        self.assert_json_is_empty()

    def assert_json_is_empty(self):
        # confirm that the json array is empty
        self.driver.get(urllib.parse.urljoin(url_stem, 'inspect_episode_data.xhtml'))
        tmp_text = self.driver.find_element(By.CSS_SELECTOR, '#form\:inspect_episode_data\:t1').text
        try:
            search_str = 'whole json array: '
            assert tmp_text.find(search_str) != -1
        except AssertionError as e:
            raise ValueError(f'expected text not found: "{search_str}"\nin website text: "{tmp_text}"\ne')
        try:
            index_start = tmp_text.find(search_str) + len(search_str)
            if '\n' in tmp_text[index_start:]:
                index_end = tmp_text[index_start:].find('\n') + index_start
            else:
                index_end = len(tmp_text[index_start:]) + index_start
            json_text = tmp_text[index_start:index_end].strip()
            assert json_text == '[]'
        except AssertionError as e:
            raise AssertionError(f'empty JSON expected; string found: {tmp_text}\ne')

    def run_test(self):
        self.login()

        try:
            # delete old data and generate new if flag is set
            if self.generate_new_data:
                # iterate over all new episodes
                for i in range(self.number_of_episodes_to_fill):
                    # set episode index
                    self.set_episode_index(i)
                    # reset the json of current episode
                    self.reset_json()
                    # confirm that the current json is empty
                    self.assert_json_is_empty()
                    # generate new data
                    self.set_episode_data()

            # run the test
            self.set_episode_index(0)

            # determine number of text fields and average character count
            self.determine_number_of_text_fields()
            self.determine_number_of_fragment_variables()
            for i in range(self.reload_and_save_episode_data_count):
                self.open_set_episode_data_page_and_click_next()

        finally:
            self.logout()
            self.exit()

    def exit(self):
        self.driver.quit()

    def determine_number_of_fragment_variables(self):
        # determine how many fragment variable text fields are shown
        set_fragment_data_url = urllib.parse.urljoin(url_stem, 'set_fragment.xhtml')
        tmp_count, _ = self.count_number_of_input_fields_on_page(set_fragment_data_url)
        self.number_of_fragment_variables = tmp_count

    def determine_number_of_text_fields(self):
        # determine how many episde data text fields are shown
        set_episode_data_url = urllib.parse.urljoin(url_stem, 'set_episode_data.xhtml')
        self.number_of_episode_data_text_fields, self.average_characters_in_text_fields = \
            self.count_number_of_input_fields_on_page(set_episode_data_url)

    def count_number_of_input_fields_on_page(self, url: str):
        # count the number of text fields on a page and determine the average character count per text field
        self.driver.get(url)
        tmp_list_of_input_text_elements = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
        tmp_count = len(tmp_list_of_input_text_elements)
        text_length = 0
        for element in tmp_list_of_input_text_elements:
            text_length += len(element.get_attribute('value'))
        if tmp_count > 0:
            tmp_average = text_length / tmp_count
        else:
            tmp_average = -1
        return tmp_count, tmp_average

    def set_episode_index(self, index: int):
        # open page set_episode_index
        self.driver.get(urllib.parse.urljoin(url_stem, 'set_episode_index.xhtml'))
        # find input element by CSS selector
        episode_index_element = self.driver.find_element(By.CSS_SELECTOR,
                                                         '#form\:set_episode_index\:mqsc\:responsedomain\:response\:oq')
        # empty the input text field
        episode_index_element.clear()
        # enter episode_index value
        episode_index_element.send_keys(str(index))
        self.driver.find_element(By.CSS_SELECTOR, '#form\:btPanel\:forward\:forwardBt').click()

    def extract_variable_value_from_debug_text(self, debug_text: str) -> str:
        # ToDo
        pass

    def open_set_episode_data_page_and_click_next(self):
        set_episode_data_url = urllib.parse.urljoin(url_stem, 'set_episode_data.xhtml')

        # get page
        self.driver.get(set_episode_data_url)

        ''' Use Navigation Timing  API to calculate the timings that matter the most '''
        navigation_start = self.driver.execute_script("return window.performance.timing.navigationStart")
        response_start = self.driver.execute_script("return window.performance.timing.responseStart")
        dom_complete = self.driver.execute_script("return window.performance.timing.domComplete")

        backend_performance_calc = response_start - navigation_start
        frontend_performance_calc = dom_complete - response_start

        tmp_timestamp = time.time()
        tmp_timestamp_str = str(datetime.datetime.fromtimestamp(tmp_timestamp, datetime.timezone.utc))

        no_of_parallel_threads = [thread.is_alive() for thread in thread_list].count(True)

        # ToDo: write this into a database
        print(
            f'Back End: {backend_performance_calc}ms {self.uid=} {tmp_timestamp_str=} no. of alive threads: {no_of_parallel_threads}')
        print(
            f'Front End: {frontend_performance_calc}ms {self.uid=} {tmp_timestamp_str=} no. of alive threads: {no_of_parallel_threads}')

        now_ms = int(time.time() * 1000)
        data = [
            {
                "measurement": "backend_performance",
                "fields": {
                    "timing": backend_performance_calc,
                    "uid": str(self.uid),
                    "parallel_threads": no_of_parallel_threads,
                    "average_characters": self.average_characters_in_text_fields,
                    "input_fields": self.number_of_episode_data_text_fields,
                    "fragment_variables": self.number_of_fragment_variables
                },
                "time": now_ms
            },
            {
                "measurement": "frontend_performance",
                "fields": {
                    "timing": frontend_performance_calc,
                    "uid": str(self.uid),
                    "parallel_threads": no_of_parallel_threads,
                    "average_characters": self.average_characters_in_text_fields,
                    "input_fields": self.number_of_episode_data_text_fields,
                    "fragment_variables": self.number_of_fragment_variables
                },
                "time": now_ms
            }
        ]
        self.write_data_to_influx(data=data)

        # send the form
        self.driver.find_element(By.CSS_SELECTOR, '#form\:btPanel\:forward\:forwardBt').click()

    def set_episode_data(self):
        set_episode_data_url = urllib.parse.urljoin(url_stem, 'set_episode_data.xhtml')

        # get page
        self.driver.get(set_episode_data_url)

        # # DEV POST REQUESTS - not working :(
        #     # iterate over all input text fields, get their ids
        #     list_of_input_ids = []
        #     for element in self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]'):
        #         element_id = element.get_attribute("id")
        #         if element_id is not None and element_id not in list_of_input_ids:
        #             list_of_input_ids.append(element.get_attribute('id'))
        #
        #     tmp_dict = {input_id: val for input_id, val in zip(list_of_input_ids,
        #                                                        [return_random_string(self.length_of_random_strings) for i in
        #                                                         range(len(list_of_input_ids))])}
        #     # tmp_dict['form'] = 'form'
        #     # tmp_dict['form:btPanel:forward:forwardBt'] = 'Weiter'
        #
        #     self.driver.request('POST', set_episode_data_url, data=tmp_dict)
        # # element.send_keys(return_random_string(1000))

        # iterate over all input fields
        for index, element in enumerate(self.driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')):
            if index < self.number_of_input_fields_to_fill or self.number_of_input_fields_to_fill == 0:
                # clear the input field
                element.clear()
                # put random text into the input field
                element.send_keys(return_random_string(self.length_of_random_strings))
            else:
                break
        # send the form
        self.driver.find_element(By.CSS_SELECTOR, '#form\:btPanel\:forward\:forwardBt').click()

    def check_json_string(self, expected_str: str):
        # ToDo check JSON string
        self.driver.get(urllib.parse.urljoin(url_stem, 'inspect_episode_data.xhtml'))
        raise NotImplementedError()

    def set_fragment(self, expected_str: str):
        # ToDo set fragment variables
        self.driver.get(urllib.parse.urljoin(url_stem, 'set_fragment.xhtml'))
        raise NotImplementedError()

    def inspect_fragment(self):
        # # DEV without function (for now)
        self.driver.get(urllib.parse.urljoin(url_stem, 'inspect_fragment.xhtml'))
        raise NotImplementedError()


chromedriver_exe_str = r'C:\Users\friedrich\PycharmProjects\Screenshotter_manual\venv\chromedriver\chromedriver.exe'
url_stem = 'http://localhost:8081/calendar_lab/'
random_str_length = 1000
number_of_saves_and_reloads = 100
insert_new_data = False
number_of_episodes = 1
number_of_input_fields = 0
zofar_token_list = ['part1', 'part2', 'part3', 'part4', 'part5', 'part6', 'part7', 'part8', 'part9', 'part10']
#zofar_token_list = ['part1']

if __name__ == "__main__":
    thread_list = []

    for zofar_token in zofar_token_list:
        tmp_uid = uuid.uuid4()
        t = TestRun(uid=tmp_uid,
                    chromedriver_executable=chromedriver_exe_str,
                    uri_stem=url_stem,
                    token=zofar_token,
                    length_of_random_strings=random_str_length,
                    reload_and_save_episode_data_count=number_of_saves_and_reloads,
                    number_of_episodes_to_fill=number_of_episodes,
                    number_of_input_fields_to_fill=number_of_input_fields,
                    generate_new_data=insert_new_data)

        thread_list.append(Thread(name=str(tmp_uid), group=None, target=t.run_test))

    for thread_element in thread_list:
        thread_element.start()
exit()
