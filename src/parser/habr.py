from time import sleep
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import logging
from utils import setup_logging, get_driver, write_to_csv


headers = ({'user-agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36'
            '(KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'})


def scan(url, dt):
    response = requests.get(url, headers=headers)
    sleep(1)                  # when time decreases, more links give no information
    soup = BeautifulSoup(response.text, "lxml")
    title = soup.find("h1", class_=("page-title__title")).text
    company = soup.find("div", class_="vacancy-company").find_all("a")[1].text
    location = soup.find_all("span", class_="inline-list")[2].text.split('•')[0]

    company_field = soup.find("div", class_="vacancy-company__sub-title").text
    description = soup.find("div", class_="basic-section--appearance-vacancy-description").text
    skills = soup.find("span", class_="inline-list").text
    job_type = soup.find_all("span", class_="inline-list")[2].text.split('•')[1]

    country = "Россия"
    salary = ""
    source = "Хабр"
    return [title,  company, country, location, salary, source, url, dt, company_field, description, skills, job_type]


def main():
    dataname = (datetime.now()).date()
    day = dataname.day  # нужно что бы парсить только за вчерашние вакансии

    links = []
    data = []
    for page_id in range(1,5):
        url = f'https://career.habr.com/vacancies?page={page_id}&q=data%20science&qid=3&remote=1&sort=date&type=all'
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.warning("Request error")
            continue
        soup = BeautifulSoup(response.text, "lxml")
        for vacancy in soup.find_all("div", class_="section-box"):
            try:
                # записиваем ссылки вакансии за сегодня и прошлый день
                if int(vacancy.find("time").text.split()[0]) > day-2:
                    links.append('https://career.habr.com'+(vacancy.find("div", class_='vacancy-card__title').find('a')).get('href'))
            except:
                sleep(0.1)

    # теперь в links у нас ссылки вакансии
    # пройдемся по ним циклом
    for link in links:
        data.append(scan(link, dataname))

    write_to_csv(data, f'habr_{dataname}.csv')


if __name__ == "__main__":
    setup_logging()
    main()