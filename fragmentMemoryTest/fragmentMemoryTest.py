from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

DRIVER = r'C:\Users\friedrich\PycharmProjects\Screenshotter_manual\venv\chromedriver\chromedriver.exe'
service_object = Service(executable_path=DRIVER)

new_driver = Chrome(service=service_object)

new_driver.get('http://localhost:8081/calendar_lab/special/login.xhtml?zofar_token=part1')

time.sleep(1)

episode_index_input = new_driver.find_element(By.CSS_SELECTOR, '#form\:index\:mqsc\:responsedomain\:response\:oq')
episode_index_input.send_keys('0')

new_driver.find_element(By.CSS_SELECTOR, '#form\:btPanel\:forward\:forwardBt').click()

print()