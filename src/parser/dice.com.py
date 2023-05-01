import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests
import argparse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from utils import setup_logging
from utils import write_to_csv
import logging

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', type=str, help='Name of output file',
                        default=f'dice.com_{datetime.now().strftime("%Y-%m-%d-%H-%M")}')
    return vars(parser.parse_args())

# Функция инициализирует драйвер selenium с необходимыми параметрами
def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome("chromedriver", options=options)
    return driver

'''
Функция определяет __дату публикации__ исходя из прошедшего времени относительно московского
работает только для вакансий за последние 24 часа
На вход получает строку типа:
- "Posted 2 hours ago"
- "Posted moments ago"
Возвращает дату публикации вакансии
'''
def dt_job(time_ago):
    if time_ago.split()[1] == 'moments':
        hours = -3
    else:
        hours = int(time_ago.split()[1]) - 3
    date = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d')
    return date

def main(filename):
    # Функция по переданному пути ищет элемент на сайте, получаем список строк
    def el_search(path):
        return driver.find_element(By.XPATH, path).text.splitlines()

    logging.info("Run the script")
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Is-Ajax-Request": "X-Is-Ajax-Request",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36")
    }
    # Список для сбора ссылок на вакансии
    list_href = []
    # Список для сбора данных со страницы поиска
    job_data = []
    # Список для сбора данных со страницы вакансии
    df = []
    vpp = 300  # количество вакансий на одной странице
    dice_url = ('https://www.dice.com/jobs?q=junior%20'
                'data%20analyst%20OR%20scientist&countryCode=US'
                f'&radius=30&radiusUnit=mi&page=1&pageSize={vpp}&filters.'
                'postedDate=ONE&language=en&eid=S2Q_')

    driver = init_driver()
    driver.get(dice_url)
    driver.maximize_window()
    time.sleep(7)

    for elem in driver.find_elements(By.XPATH, '//*[@class="card-title-link bold"]'):
        list_href.append(elem.get_attribute('href'))
    cnt = len(list_href)
    for i in range(1, cnt + 1):

        job_post = el_search('//*[@id="searchDisplay-div"]/div[3]/dhi-search-'
                             f'cards-widget/div/dhi-search-card[{i}]')[0]

        comp_loc = el_search('//*[@id="searchDisplay-div"]/div[3]/dhi-search-'
                             f'cards-widget/div/dhi-search-card[{i}]'
                             '/div/div[1]/div/div[2]/div[1]/div')
        company = comp_loc[0]

        if len(comp_loc) > 1:
            location = comp_loc[1].split(',')[0]
        else:
            location = ''

        working_conditions = el_search('//*[@id="searchDisplay-div"]/div[3]'
                                       f'/dhi-search-cards-widget/div/dhi-search-card[{i}]'
                                       '/div/div[2]/div[1]')[0]

        posted = el_search('//*[@id="searchDisplay-div"]/div[3]/dhi-search'
                           f'-cards-widget/div/dhi-search-card[{i}]/div/div[2]/div[1]')[1]

        info_another = el_search('//*[@id="searchDisplay-div"]/div[3]/dhi-'
                                 f'search-cards-widget/div/dhi-search-card[{i}]'
                                 '/div/div[2]/div[2]')[0]

        df.append({'title': job_post,
                   'company': company,
                   'country': 'USA',
                   'location': location,
                   'date': dt_job(posted),
                   'company_field': '',
                   'job_type': working_conditions,
                   'info_another': info_another})
    driver.close()
    driver.quit()
    logging.info("Search page - success")

    for url in list_href:
        time.sleep(1)
        # некоторые ссылки ведут на сторонние сайты, поэтому проверяем домен
        # прежде чем продолжить
        if url[:20] == 'https://www.dice.com':
            logging.info(f'Requested url: {url}')
            req = requests.get(url=url, headers=headers)
            soup = BeautifulSoup(req.text, "lxml")

            skills = ''
            for skill in soup.find_all(class_="skill-badge"):
                skills += skill.text + ', '
            skills = skills.strip(', ')

            dscr = soup.find('div', class_="mb-16 min-h-[300px]").text

            # зарплата указана не во всех вакансиях,
            # сначала проверяю наличие информации
            salary = ''
            salary_div = soup.find('div',
                                   class_='job-info order-4 col-span-2 mb-10 md:mb-0 '
                                          'sm:col-span-1 md:col-span-4 lg:col-span-5 lg:mb-0')

            for element in salary_div:
                if element.get('data-cy') == 'compensationText':
                    salary = (soup.find('div',
                                        class_='job-info order-4 col-span-2 mb-10 md:mb-0 sm:'
                                               'col-span-1 md:col-span-4 lg:col-span-5 lg:mb-0').
                              find('p').
                              text)
        else:
            skills = ''
            dscr = ''
            salary = ''
        data = {
            'salary': salary,
            'source': 'dice.com',
            'link': url,
            'description': dscr,
            'skills': skills
        }
        job_data.append(data)

    # для вакансий, где ссылка вела на другой сайт, вставляем обрезанное описание со страницы поиска, объединяем данные
    for i in range(cnt):
        df[i] = job_data[i] | df[i]
        if df[i]['description'] == '':
            df[i]['description'] = df[i]['info_another']
        del df[i]['info_another']
    write_to_csv(df, filename)



if __name__ == "__main__":
    setup_logging("log.txt")
    args = parse_args()
    main(args["filename"])

