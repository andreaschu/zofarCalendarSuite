from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import time
import sys


def set_viewport_size(driver, width, height):
    assert isinstance(driver, webdriver.Chrome)
    assert isinstance(width, int) and isinstance(height, int)

    window_size = driver.execute_script("""
               return [window.outerWidth - window.innerWidth + arguments[0],
                 window.outerHeight - window.innerHeight + arguments[1]];
               """, width, height)
    driver.set_window_size(*window_size)


class SeleniumWebdriverMinimal:
    def __init__(self, viewport_width: int = 1024, viewport_height: int = 1900,
                 end_when_done: bool = True,
                 headless: bool = False):
        self.logger = logging.getLogger('debug')
        self.startup_logger(log_level=logging.DEBUG)
        self.logger.info('starting up Screenshotter')

        self.cred_token = None
        self.cred_base_url_prefix = None
        self.cred_base_url_suffix_auth = None
        self.cred_base_url_suffix_token = None
        self.cred_user = None
        self.cread_password = None

        self.codes_list = []

        self.browser_width = viewport_width
        self.browser_height = viewport_height

        # init driver
        if sys.platform == 'linux':
            self.DRIVER = '/home/christian/chromedriver/chromedriver'
        elif sys.platform == 'win32':
            self.DRIVER = 'C:\\Users\\friedrich\\PycharmProjects\\Screenshotter_manual\\venv\\chromedriver\\chromedriver.exe'
        else:
            raise NotImplementedError(f'Platforn unknown: {sys.platform=}')

        # set options
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')

        # self.driver = webdriver.Chrome(self.DRIVER, chrome_options=self.options)
        self.driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver')
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self.end_when_done = end_when_done

        self.set_viewport()

    def startup_logger(self, log_level=logging.DEBUG):
        """
        CRITICAL: 50, ERROR: 40, WARNING: 30, INFO: 20, DEBUG: 10, NOTSET: 0
        """
        logging.basicConfig(level=log_level)
        fh = logging.FileHandler("{0}.log".format('log_' + __name__))
        fh.setLevel(log_level)
        fh_format = logging.Formatter('%(name)s\t%(module)s\t%(funcName)s\t%(asctime)s\t%(lineno)d\t'
                                      '%(levelname)-8s\t%(message)s')
        fh.setFormatter(fh_format)
        self.logger.addHandler(fh)

    def set_viewport(self):
        set_viewport_size(self.driver, self.viewport_width, self.viewport_height)

    def close_chromedriver(self):
        self.driver.quit()

    @staticmethod
    def timestamp():
        """
        :return: string timestamp: YYYY-MM-DD-hh-mm
        """
        t = time.localtime()
        return time.strftime('%Y-%m-%d_%H-%M-%S', t)

    def open_url(self, url):
        self.driver.get(url)
