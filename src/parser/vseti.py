import requests
# from pyvirtualdisplay import Display
import re
import argparse
import csv
import logging
from datetime import date, timedelta, datetime
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from typing import Tuple, List, Dict, Union
from utils import setup_logging
import os

headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Is-Ajax-Request": "X-Is-Ajax-Request",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36"
}


def set_driver():
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


driver = webdriver.Chrome()

# for Linux
# driver = set_driver()
url = 'https://www.vseti.app/jobs?jobstype=Аналитика'


def get_company_field(level: str) -> str:
    """returns the field of activity of the company, which is in the same tag as the grade"""
    company_field = level.rsplit('\n')[-1].strip()
    if re.compile('[а-яА-ЯёЁ]+').fullmatch(company_field):
        return ''
    else:
        return company_field


def get_description_date(link: str) -> Tuple[str, Union[date, None]]:
    """opens a link for each vacancy and retrieves information about the vacancy description
    and the date of its publication, which are not in the jobcard"""
    try:
        response = requests.get(link, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        description = find_element_text(soup, 'div', attrs={'class': 'content_vacancy_div'})
        date_publication = soup.find_all('p', class_='paragraph-21 date-tag')
        if date_publication is not None:
            date_publication = datetime.strptime(date_publication[1].text.strip(), '%d/%m/%Y').date()
        else:
            date_publication = None
        return description, date_publication
    except requests.exceptions.RequestException as e:
        logging.error(f'Error retrieving contents of {link}: {e}')
        return '', None


def find_element_text(soup: BeautifulSoup, tag: str, attrs: dict = None, attribute: str = None) -> str:
    """Find element by tag and attributes, and get text or attribute by name"""
    if attrs:
        element = soup.find(tag, attrs)
    else:
        element = soup.find(tag)
    if element:
        if attribute:
            return element.get(attribute)
        else:
            return element.text.strip()
    else:
        logging.info(f'For {soup} element not found - {tag}, {attrs}, {attribute}')
        return ''


def scrape_job_cards(url: str) -> List[Tuple[str, str, str, str, str, str, str, date, str, str, str, str]]:
    """returns information about vacancies with filtering for interns and juniors and given period of time,
    which cannot be set in filters with selenium or directly in the url"""
    period = date.today() - timedelta(days=int(args['days']))
    try:
        driver.get(url)
        driver.maximize_window()
        sleep(60)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(60)
        try:
            jobs = driver.find_elements(By.XPATH, "//div[@class='collection-item w-dyn-item']")
            results = []
            for job in jobs:
                soup = BeautifulSoup(job.get_attribute('innerHTML'), 'html.parser')
                level = find_element_text(soup, 'div', attrs={'class': 'div-block-32'})
                # стаЖер, дЖун
                if 'ж' in level.lower():
                    title = find_element_text(soup, 'h1', attrs={'class': 'heading-3'})
                    company = find_element_text(soup, 'div', attrs={'class': 'company-titile'})
                    link = find_element_text(soup, 'a', attribute='href')
                    location_type = find_element_text(soup, 'p', attrs={'class': 'paragraph-8'})
                    company_field = get_company_field(level)
                    description, date_publication = get_description_date(link)
                    country = 'Russia'
                    source = 'vseti'
                    location = location_type.split(',', 1)[0]
                    skills = ''
                    job_type = str(location_type.rsplit(',', 1)[-1])
                    salary = soup.find('a').find_all('p', class_='paragraph-8')
                    if salary is not None:
                        salary = salary[1].text.strip()
                    else:
                        salary = ''
                    if date_publication >= period:
                        results.append((title, company, country, location, salary, source, link, date_publication,
                                        company_field, description, skills, job_type))

            driver.quit()
            return results
        except NoSuchElementException as e:
            logging.error(f'Job cards changed their tags: {e}')
            exit(1)
    except WebDriverException as e:
        logging.error(f'Error connecting with site: {e}')
        exit(1)


def write_to_csv(results: List[Tuple[str, str, str, str, str, str, str, date, str, str, str, str]], filename: str):
    """writes information to a file"""
    if not results:
        logging.error(f'No results for the choosen period')
    filepath = os.path.join('data', filename)
    with open(filepath, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['title', 'company', 'country', 'location', 'salary', 'source', 'link', 'date',
                         'company_field', 'description', 'skills', 'job_type'])
        writer.writerows(results)
    logging.info(f"Data written to file {filepath}")


def parse_args() -> Dict[str, str]:
    """receives input arguments - the name of the file to be written
     and the number of days for which vacancies should be viewed"""
    parser = argparse.ArgumentParser(description='Scrapes job postings from vseti.app')
    parser.add_argument('-f', '--filename', type=str, help='Name of output file', default=f'{date.today()}_vseti.csv')
    parser.add_argument('-d', '--days', type=int, help='Number of days to subtract from the current date',
                        default=1)
    return vars(parser.parse_args())


def main(args):
    """it is final countdown"""
    results = scrape_job_cards(url)
    write_to_csv(results, args['filename'])


if __name__ == '__main__':
    setup_logging("log.txt")
    args = parse_args()
    main(args)
