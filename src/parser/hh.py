import logging

import requests
import argparse
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup
from utils import setup_logging, write_to_csv
import json
import logging
from typing import List

job_offer_title =  f'SQL NAME:("Аналитик" or "Analyst" or "Data Scientist" or "Дата саентист" or "ML")'
experiences = ['noExperience', 'between1And3']

_logger = logging.getLogger(__name__)


def get_url(job_offer_title: str, experiences: List, days_ago: int):
    """
    Здесь мы собираем ссылки на все вакансии в зависимости от опыта на выходе получаем список ссылок

    :param job_offer_title:
    :param experiences:
    :param days_ago:
    :return:
    """
    list_url = []
    base_url = "https://api.hh.ru/"
    dt_now = datetime.now().date()
    date_start = (dt_now - timedelta(days=days_ago)).isoformat()
    date_end = datetime.now().date().isoformat()
    for exp in experiences:
        url = base_url + f'vacancies?text={job_offer_title}&date_from={date_start}&date_to={date_end}&responses_count_enabled=True&per_page=100&experience={exp}'
        list_url.append(url)
    return list_url


def get_info(urls):
    """
    здесь мы учитываем количество страницы и с каждой страницы получаем список словарь items - каждый словарь это признаки вакансии
    и потом для каждой item находим нужные нам, помещая их в список, а затем заталкиваю каждый список еще в список

    :param urls:
    :return:
    """
    results = []
    for url in urls:
        page = 0
        try:
            r = requests.get(url + f'&page={page}')
        except Exception as err:
            _logger.error(repr(err))
            continue
        if r.status_code != 200:
            _logger.error("Response code is not 200")
            continue

        data = json.loads(r.text)
        items = data['items']
        for page in range(1, data['pages']):
            try:
                r = requests.get(url + f'&page={page}')
            except Exception as err:
                _logger.error(repr(err))
                continue

            data = json.loads(r.text)
            items += data['items']

        for item in items:
            list_offers = []
            list_offers.append(item['name'])
            list_offers.append(item['employer']['name'])
            list_offers.append('Russia')
            list_offers.append(item['area']['name'])
            try:
                if item["salary"]["from"] is None:
                    s = "?"
                else:
                    s = item["salary"]["from"]
                s = s + " - "
                if item["salary"]["to"] is None:
                    s = s + "?"
                else:
                    s = s + item["salary"]["to"]
                if item["salary"]["currency"] is not None:
                    s = s + item["salary"]["currency"]
                list_offers.append(s)
            except Exception as err:
                list_offers.append('')
                _logger.warning(repr(err))

            list_offers.append('hh.ru')
            list_offers.append(item['alternate_url'])
            #date
            list_offers.append(None)
            #company field
            try:
                list_offers.append(item['department']['name'])
            except Exception as err:
                list_offers.append('')
                _logger.warning(repr(err))

            # description
            try:
                list_offers.append(BeautifulSoup(json.loads(requests.get(item['url']).text)['description'], "html.parser").get_text())
            except Exception as err:
                _logger.warning("Parse html page error %r", err)
                list_offers.append('')

             # skils
            list_offers.append("")

            list_offers.append(item['employment']['name'])
            results.append(list_offers)

    return results


def parse_args():
    """
    функция используется для получения аргументов командной строки, которые передаются скрипту
    """
    parser = argparse.ArgumentParser(description='Scrapes job postings from hh.ru')
    parser.add_argument('-f', '--filename', type=str, help='Name of output file', default=f'{date.today()}_hh.csv')
    parser.add_argument('-d', '--days', type=int, help='Number of days to subtract from the current date',
                        default=1)
    return vars(parser.parse_args())


def main(filename, days):
    """it is final countdown"""
    urls = get_url(job_offer_title, experiences, days)
    results = get_info(urls)
    write_to_csv(results, filename)


if __name__ == '__main__':
    setup_logging("parser.log")
    args = parse_args()
    main(args["filename"], args["days"])
