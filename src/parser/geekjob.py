from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys
from bs4 import BeautifulSoup

import time
from datetime import datetime, timedelta
import csv
import logging
import argparse
from utils import setup_logging


def rename_date(date):
    #  Функция для получения текущей и предыдущей даты в виде число-месяц как на сайте
    date_dict = {"01": "января", "02": "февраля", "03": "марта",
                 "04": "апреля", "05": "мая", "06": "июня",
                 "07": "июля", "08": "августа", "09": "сентября",
                 "10": "октября", "11": "ноября", "12": "декабря"}
    list_date = date.split()
    return list_date[0].lstrip('0') + ' ' + date_dict.get(list_date[1])


def init_driver():
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
    return webdriver.Chrome(options=options)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--parse_date",
                        default=datetime.strftime(datetime.now(), '%Y-%m-%d'),
                        type=str,
                        dest="parse_date")

    parser.add_argument("--filename",
                        default=f"geekjob_{datetime.strftime(datetime.now(),'%Y-%m-%d-%H-%M')}.csv",
                        type=str,
                        dest="filename")

    parse_date = datetime.strptime(parser.parse_args().parse_date, '%Y-%m-%d')
    csv_file = parser.parse_args().filename

    #  Для поиска вакансий по дате получаем заданную дату в виде строки как на сайте
    current_date = rename_date(datetime.strftime(parse_date, '%d %m'))
    prev_date = rename_date(datetime.strftime(parse_date - timedelta(days=1), '%d %m'))

    #  В словаре date_dict ключ - дата в формате как на сайте для поиска вакансии,
    #  а значение - datetime, для записи результата в файл
    date_dict = {current_date: datetime.now(), prev_date: datetime.now() - timedelta(days=1)}

    #  Ссылка на сайт
    URL = 'https://geekjob.ru/'

    #  Список строк запроса для выбора по специальностям
    query_list = ['аналитик', 'analyst', 'дата сайентист', 'data scientist', 'DS']

    #  Список уровней интересующих вакансий
    level_list = ['Джуниор', 'Стажер']

    # Словарь тегов для парсинга
    tags_dict = {'vacancy': '//a[@href="/vacancies"]',
                 'queryinput': '//input[@name="queryinput"]',
                 'radio': '//section[@class="col s12 m4"][2]',
                 'find_button': '//section[@class="col s12 m12"]/button[@class="btn btn-small waves-effect"]',
                 'vacancies_num': '//div[@id="serp"]',
                 'items': '//li[@class="collection-item avatar"]',
                 'dates': '//p[@class="truncate datetime-info"]',
                 'vacancy_hrefs': '//p[@class="truncate vacancy-name"]/a[1]',
                 'element_present': '//article[@class="row vacancy"]',
                 'level': '//b[contains(text(), "Уровень должности")]/following-sibling::a',
                 'info': '//div[@id="vacancy-description"]',
                 'title': '//h1',
                 'company': '//h5[@class="company-name"]/a',
                 'location': '//div[@class="location"]',
                 'skills': '//b[contains(text(), "Отрасль и сфера применения")]/preceding-sibling::a',
                 'salary': '//span[@class="salary"]',
                 'jobformat': '//span[@class="jobformat"]',
                 'company_field': '//b[contains(text(), "Отрасль и сфера применения")]/following-sibling::a'}

    driver = init_driver()
    driver.get(URL)
    driver.maximize_window()

    #  Список строк длая записи в csv-файл
    rows = []

    #  Список для контроля уникальности обработанных вакансий
    find_list = []
    vacancy_index = 0

    for query in query_list:
        logging.info(f'Поиск вакансий по запросу "{query}"')

        vacancy = driver.find_element(By.XPATH, tags_dict.get('vacancy'))
        driver.execute_script("arguments[0].click();", vacancy)
        driver.find_element(By.XPATH, tags_dict.get('queryinput')).send_keys(query)
        time.sleep(1)
        driver.find_element(By.XPATH, tags_dict.get('radio')).click()
        time.sleep(1)
        driver.find_element(By.XPATH, tags_dict.get('find_button')).click()
        time.sleep(5)
        vacancies_num = driver.find_element(By.XPATH, tags_dict.get('vacancies_num')).text

        if vacancies_num == '':
            continue

        logging.info(f"{vacancies_num}, парсим из них только вакансии нужного уровня с отбором по дате:")
        main_window = driver.window_handles[0]
        items = driver.find_elements(By.XPATH, tags_dict.get('items'))
        dates = driver.find_elements(By.XPATH, tags_dict.get('dates'))
        vacancy_hrefs = driver.find_elements(By.XPATH, tags_dict.get('vacancy_hrefs'))

        for data, vacancy_href, item in zip(dates, vacancy_hrefs, items):
            link = vacancy_href.get_attribute('href')
            if data.text in date_dict and link not in find_list:
                date = data.text
                time.sleep(3)
                driver.execute_script("arguments[0].click();", vacancy_href)
                time.sleep(3)
                window_after = driver.window_handles[1]
                driver.switch_to.window(window_after)

                #  Ждем когда загрузятся данные по вакансии
                try:
                    element_present = EC.presence_of_element_located((By.XPATH,
                                                                      tags_dict.get('element_present')))
                    WebDriverWait(driver, 5).until(element_present)
                except Exception:
                    logging.error(f"Ошибка при загрузке страницы вакансии {link}")

                #  Парсим уровень специальности
                try:
                    level = driver.find_elements(By.XPATH,
                                                 tags_dict.get('level'))
                    level = ', '.join(elem.text for elem in level)
                except Exception as ex:
                    level = None
                    logging.error(f"Ошибка при парсинге level: {ex}")

                #  Если в уровень вакансии входит хотя бы один элемент списка level_list,
                #  парсим остальную информацию и записываем ее в файл
                if not (level is None) and any(el if el in level else None for el in level_list):
                    logging.info(f"Парсим вакансию по ссылке {link}")
                    try:
                        info = driver.find_element(By.XPATH,
                                                   tags_dict.get('info'))
                        description = BeautifulSoup(info.get_attribute('innerHTML'), 'lxml').text
                    except Exception as ex:
                        description = None
                        logging.error(f"Ошибка при парсинге description: {ex}")

                    try:
                        title = driver.find_element(By.XPATH,
                                                    tags_dict.get('title')).text
                    except Exception as ex:
                        title = None
                        logging.error(f"Ошибка при парсинге title: {ex}")

                    try:
                        company = driver.find_element(By.XPATH,
                                                      tags_dict.get('company')).text
                    except Exception as ex:
                        company = None
                        logging.error(f"Ошибка при парсинге company: {ex}")

                    try:
                        location = driver.find_element(By.XPATH,
                                                       tags_dict.get('location')).text.split(',')
                        country = location[-1].strip() if len(location) > 0 else ''
                        location = ', '.join(location[:-1])
                    except Exception as ex:
                        country = None
                        location = None
                        logging.error(f"Ошибка при парсинге location: {ex}")

                    try:
                        salary = driver.find_element(By.XPATH,
                                                     tags_dict.get('salary')).text
                    except Exception as ex:
                        salary = None
                        logging.error(f"Ошибка при парсинге salary: {ex}")

                    try:
                        jobformat = driver.find_element(By.XPATH,
                                                        tags_dict.get('jobformat')).text.split('\n')
                        job_type = ', '.join(jobformat[0].split(' • '))
                    except Exception as ex:
                        job_type = None
                        logging.error(f"Ошибка при парсинге job_type: {ex}")

                    try:
                        company_field = driver.find_elements(By.XPATH,
                                                             tags_dict.get('company_field'))
                        company_field = ', '.join(el.text for el in company_field)
                        company_field = company_field.rstrip(level).rstrip(', ')
                    except Exception as ex:
                        company_field = None
                        logging.error(f"Ошибка при парсинге company_field: {ex}")

                    try:
                        skills = driver.find_element(By.XPATH,
                                                     tags_dict.get('skills')).text
                        skills = ', '.join(skills.split(' • '))
                    except Exception as ex:
                        skills = None
                        logging.error(f"Ошибка при парсинге skills: {ex}")

                    rows.append([title, company, country, location, salary,
                                'GeekJob', link, date_dict.get(date),
                                company_field, description, skills, job_type])

                    find_list.append(link)
                    logging.info(f"Данные по вакансии успешно записаны в csv-файл (индекс {vacancy_index})")
                    vacancy_index += 1

                driver.close()
                driver.switch_to.window(main_window)

                vacancy_href.send_keys(Keys.DOWN)

    driver.quit()

    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file, delimiter=';')

        #  Записываем заголовки таблицы в файл
        writer.writerow(['title', 'company', 'country', 'location', 'salary',
                     'source', 'link', 'date', 'company_field', 'description',
                     'skills', 'job_type'])

        for row in rows:
            writer.writerow(row)

    logging.info(f'Парсинг закончен, результат помещен в файл {csv_file}')


if __name__ == "__main__":
    setup_logging("geekjob.log")
    main()
