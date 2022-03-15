import time

import SeleniumWebdriverMinimal
from selenium.webdriver.common.by import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction

x = SeleniumWebdriverMinimal.SeleniumWebdriverMinimal()

# login
x.open_url('https://presentation.dzhw.eu/Test_Modul/special/login.html?zofar_token=part41')
# open calendar page
x.open_url('https://presentation.dzhw.eu/Test_Modul/calendar.html')

# select first month/start month for touch event test
month1 = x.driver.find_element(by=By.CSS_SELECTOR, value='#calenderTable > table > tbody > tr.zofar-structure-table-row.year-container.zofar-months-container.year-container-2020 > td.zofar-structure-table-body-cell.month.zofar-month.zofar-month-5')
# get coordinates of first month/start month
x1_coord, y1_coord = month1.location['x'], month1.location['y']

# select second month/end month for touch event test
month2 = x.driver.find_element(by=By.CSS_SELECTOR, value='#calenderTable > table > tbody > tr.zofar-structure-table-row.year-container.zofar-months-container.year-container-2020 > td.zofar-structure-table-body-cell.month.zofar-month.zofar-month-8')
# get coordinates of second month/end month
x2_coord, y2_coord = month2.location['x'], month2.location['y']

# set up action chain for touch-and-move
actions = ActionChains(x.driver)
actions.w3c_actions = ActionBuilder(x.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
# move to location of first month
actions.w3c_actions.pointer_action.move_to_location(x=x1_coord, y=y1_coord)
# start touch event (down)
actions.w3c_actions.pointer_action.pointer_down()
# move to second month
actions.w3c_actions.pointer_action.move_to_location(x=x2_coord, y=y2_coord)
# end touch event (up)
actions.w3c_actions.pointer_action.pointer_up()

# run the whole action chain
actions.w3c_actions.perform()

# wait 1 sec
time.sleep(1)

# find event name field - using full XPATH because there are two identical modals on this page
event_name_field = x.driver.find_element(by=By.XPATH, value='/html/body/div[2]/form/div[2]/section/article[1]/div/div/div/div[2]/div/div/div[2]/div[1]/div/input')
# put some text in the field
event_name_field.send_keys('Test123')

# find type dropdown - using full XPATH because there are two identical modals on this page
type_dropdown_slot2 = x.driver.find_element(by=By.XPATH, value='/html/body/div[2]/form/div[2]/section/article[1]/div/div/div/div[2]/div/div/div[2]/div[2]/div/select/option[2]')
# select the value by clicking
type_dropdown_slot2.click()

# find "Save" button
save_button = x.driver.find_element(by=By.XPATH, value='/html/body/div[2]/form/div[2]/section/article[1]/div/div/div/div[2]/div/div/div[3]/button[2]')
# # [obsolete] get coordinates of button
# x3_coord, y3_coord = save_button.location['x'], save_button.location['y']

# click the "Save" button
save_button.click()

# ToDo: open context menu via touch events - not working yet (long touch does not seem to work)

# set up action chain
actions2 = ActionChains(x.driver)
actions2.w3c_actions = ActionBuilder(x.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
# move to first month
actions2.w3c_actions.pointer_action.move_to_location(x=x1_coord, y=y1_coord)
# start touch event (down)
actions2.w3c_actions.pointer_action.pointer_down()
# wait 1sex
actions2.pause(1)
# end touch event (up)
actions2.w3c_actions.pointer_action.pointer_up()

# run the whole action chain
actions2.w3c_actions.perform()


print()

