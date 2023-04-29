import logging
import platform
from selenium import webdriver
from typing import List, Tuple
from datetime import date
import os
import csv


def setup_logging(logfile=None, loglevel="INFO"):
    """

    :param logfile:
    :param loglevel:
    :return:
    """

    loglevel = getattr(logging, loglevel)

    logger = logging.getLogger()
    logger.setLevel(loglevel)
    fmt = '%(asctime)s: %(levelname)s: %(filename)s: ' + \
          '%(funcName)s(): %(lineno)d: %(message)s'
    formatter = logging.Formatter(fmt)

    ch = logging.StreamHandler()
    ch.setLevel(loglevel)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if logfile is not None:
        fh = logging.FileHandler(filename=logfile)
        fh.setLevel(loglevel)
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def get_driver() -> webdriver.Chrome:
    """
    Init Chromium drive
    :return:
    """
    logging.info("Init driver")
    if platform.system() == "Windows":
        driver = webdriver.Chrome()
    else:
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1200))
        display.start()
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('start-maximized')
        options.add_argument('enable-automation')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument('--disable-gpu')
        options.add_argument("--log-level=3")
        driver = webdriver.Chrome("./driver/chromedriver", options=options)
    return driver


def write_to_csv(results: List[Tuple[str, str, str, str, str, str, str, date, str, str, str, str]], filename: str):
    """
    Writes information to a file
    :param results: list of lists with vacancies information
    :param filename: name of output file
    """
    if not results:
        logging.error(f'No results for the choosen period')
        return None

    filepath = os.path.join(os.path.dirname(__file__), 'data', filename)

    with open(filepath, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        try:
            writer.writerow(['title', 'company', 'country', 'location', 'salary', 'source', 'link', 'date',
                             'company_field', 'description', 'skills', 'job_type'])
            writer.writerows(results)
        except Exception as err:
            logging.error(repr(err))
    logging.info(f"Data written to file {filepath}")