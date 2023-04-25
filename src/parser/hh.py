import requests
import json
import logging
from datetime import date, timedelta, datetime
import time
import numpy as np
from bs4 import BeautifulSoup
from typing import Tuple, List, Dict, Union
import csv
import os
import argparse
logging.basicConfig(filename='parser.log', level=logging.INFO)


#Делаем выгрузку из HeadHunter
#Ссылка на API HH: https://github.com/hhru/api \
#Для того, чтобы написать запрос используется язык поисковых запросов, задокументированный тут: https://hh.ru/article/1175 \
#Создадим необходимые константы:

BASE_URL = "https://api.hh.ru/"
TEXT = f'SQL NAME:("Аналитик" or "Analyst" or "Data Scientist" or "Дата саентист" or "ML")'
dt_now = datetime.now().date()
dt_from = dt_now - timedelta(days=1)
DATE_TO = dt_now.isoformat()
DATE_FROM = dt_from.isoformat()
VAC_URL = BASE_URL + f'vacancies?text={TEXT}&date_from={DATE_FROM}&date_to={DATE_TO}&responses_count_enabled=True&per_page=100'

#В выдаче API HH нет опыта работы, поэтому мы укажем его в запросе самостоятельно.Нам нужны вокансии уровня junior

experiences = ['noExperience', 'between1And3']
vacancy_list = []

for exp in experiences:
    page = 0
    url = VAC_URL + f'&experience={exp}'
    try:
        r = requests.get(url+f'&page={page}')
        data = json.loads(r.text)
        logging.info(f'Request for experience {exp}, page {page} returned status {r.status_code}')
        logging.info(f'Total pages for experience {exp}: {data["pages"]}')
        items = data['items']
        for page in range(1, data['pages']):
            r = requests.get(url+ f'&page={page}')
            data = json.loads(r.text)
            logging.info(f'Request for experience {exp}, page {page} returned status {r.status_code}')
            items += data['items']
        vacancy_list += items
        logging.info(f'Added {len(items)} vacancies with experience {exp} to the list')
    except Exception as e:
        logging.error(f'Request for experience {exp}, page {page} failed with error: {e}')
        time.sleep(5)


def return_id(x, key='id', nan_value=np.nan):
    '''Функция дастает информацию из словарей '''
    if x is not None:
        return x.get(key, nan_value)
    else:
        return None

def extract_salary_info(vacancy):
    '''Функция для обработки зарплаты '''
    salary = vacancy.get('salary')
    if salary is not None:
        salary_from = salary.get('from')
        salary_to = salary.get('to')
        currency = salary.get('currency')
        if salary_from is not None and salary_to is not None:
            salaries = str(salary_from) + '-' + str(salary_to) + ' ' + currency
        elif salary_from is not None:
            salaries = 'от ' + str(salary_from) + ' ' + currency
        elif salary_to is not None:
            salaries = 'до ' + str(salary_to) + ' ' + currency
        else:
            salaries = None
    else:
        salaries = None
    return salaries

url = [vacancy['url'] for vacancy in vacancy_list]

text = []
def get_description(cell):
    '''Функция находит описание вакансии '''
    try:
        return BeautifulSoup(json.loads(requests.get(cell).text)['description']).get_text()
    except:
        text.append(f'{cell} doesnt work')
        return None
for link in url:
    description = get_description(link)
    text.append(description)


results = []
for vacancy in vacancy_list:
    info_vacancy = []
    info_vacancy.append([vacancy['name'] for vacancy in vacancy_list])
    info_vacancy.append([vacancy['alternate_url'] for vacancy in vacancy_list])

    info_vacancy.append(
            [datetime.strptime(vacancy['published_at'], '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d') for vacancy in
             vacancy_list])

    info_vacancy.append([return_id(v.get('employer', {}), 'name') for v in vacancy_list])
    info_vacancy.append([return_id(v.get('area', {}), 'name') for v in vacancy_list])
    info_vacancy.append([return_id(v.get('employment', {}), 'name') for v in vacancy_list])
    info_vacancy.append([return_id(v.get('department', {}), 'name') for v in vacancy_list])
    info_vacancy.append('Russia')
    info_vacancy.append('hh')
    info_vacancy.append('')
    info_vacancy.append([extract_salary_info(vacancy) for vacancy in vacancy_list])
    info_vacancy.append(get_description([vacancy['url'] for vacancy in vacancy_list]))
    results.append(info_vacancy)


def write_to_csv(results: List[Tuple[str, str, str, str, str, str, str, str, str, str, str, str]], filename: str):
    """Функция для записи в файл"""
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
    """ функция используется для получения аргументов командной строки, которые передаются скрипту"""
    parser = argparse.ArgumentParser(description='Scrapes job postings from hh.ru')
    parser.add_argument('-f', '--filename', type=str, help='Name of output file', default=f'{date.today()}_hh.csv')
    parser.add_argument('-d', '--days', type=int, help='Number of days to subtract from the current date',
                        default=1)
    return vars(parser.parse_args())

def main(args):
    write_to_csv(results, args['filename'])

if __name__ == '__main__':
    args = parse_args()
    main(args)