# Copyright 2020 TestProject (https://testproject.io)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote import webdriver
#from src.testproject.sdk.drivers.webdriver.base import BaseDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


# ToDo: modify this to zofar needs
raise NotImplementedError()


class ProfilePage:

    textlabel_greetings = (By.CSS_SELECTOR, "#greetings")
    textlabel_saved = (By.CSS_SELECTOR, "#saved")
    dropdown_country = (By.CSS_SELECTOR, "#country")
    textfield_address = (By.CSS_SELECTOR, "#address")
    textfield_email = (By.CSS_SELECTOR, "#email")
    textfield_phone = (By.CSS_SELECTOR, "#phone")
    button_save = (By.CSS_SELECTOR, "#save")
    button_logout = (By.CSS_SELECTOR, "#logout")

    def __init__(self, driver: webdriver):
        self._driver = driver

    def greetings_are_displayed(self):
        return self._driver.find_element(*self.textlabel_greetings).is_displayed()

    def saved_message_is_displayed(self):
        return self._driver.find_element(*self.textlabel_saved).is_displayed()

    def update_profile(self, country: str, address: str, email: str, phone: str):
        self.select_country(country)
        self.type_address(address)
        self.type_email(email)
        self.type_phone(phone)
        self.save()

    def save(self):
        self._driver.find_element(*self.button_save).click()

    def type_phone(self, phone):
        self._driver.find_element(*self.textfield_phone).send_keys(phone)

    def type_email(self, email):
        self._driver.find_element(*self.textfield_email).send_keys(email)

    def type_address(self, address):
        self._driver.find_element(*self.textfield_address).send_keys(address)

    def select_country(self, country):
        country_dropdown = WebDriverWait(self._driver, 60).until(ec.element_to_be_clickable(self.dropdown_country))
        Select(country_dropdown).select_by_visible_text(country)

    def is_saved(self):
        return self._driver.find_element(*self.textlabel_saved).is_displayed()

    def logout(self):
        self._driver.find_element(*self.button_logout).click()
