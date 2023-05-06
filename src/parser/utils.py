import logging
import csv
import platform
from selenium import webdriver
from pyvirtualdisplay import Display



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
        
        
def write_to_csv(data, filename):
    with open(filename, mode="w", encoding='utf-8') as w_file:
        names = ['title',
                 'company',
                 'country',
                 'location',
                 'salary',
                 'source',
                 'link',
                 'date',
                 'company_field',
                 'description',
                 'skills',
                 'job_type']
        file_writer = csv.DictWriter(w_file, delimiter=",",
                                     lineterminator="\r", fieldnames=names)
        file_writer.writeheader()
        file_writer.writerows(data)
    logging.info(f"Data written to file {filename}")


def set_driver():
    if platform.system() == "Windows":
        driver = webdriver.Chrome()
    else:
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
        driver = webdriver.Chrome(options=options)
    return driver
