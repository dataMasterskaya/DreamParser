from utils import setup_logging
import logging
import argparse

import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
# Визуализируем этапы выполнения кода, оборачиваем цикл for
from tqdm.notebook import tqdm
import datetime
import dateparser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from pyvirtualdisplay import Display


# !Функция, которая закрывает всплывающие окна
def close_popup():
    try:
        driver.find_elements(
            By.XPATH, "//button[@class='icl-CloseButton icl-Modal-close']").click()
    except:
        pass

    try:
        driver.find_elements(
            By.XPATH, "//svg[@class='icl-Icon icl-Icon--black icl-Icon--sm']").click()
    except:
        pass


# !Функция, которая собирает список стран для парсера
def all_available_countries(url_worldwide, retry=5):
    # Список доступных стран, данные с сайта https://www.indeed.com/worldwide
    list_available_countries = []
    dict_country_code = {}

    try:
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
        # options.add_argument("--headless")
        options.add_argument('--disable-gpu')
        options.add_argument("--log-level=3")

        driver = webdriver.Chrome(options=options)
        driver.get(url_worldwide)
        time.sleep(3)
        close_popup()

        offers_worldwide = (BeautifulSoup(driver.find_element(By.XPATH, "//div[@class='worldwide__main']")
                                                .get_attribute('innerHTML'), "html.parser")
                            )

        # Проходим в цикле по блоку кода и добавляем страна - ключ, значение - код страны, а так же страну в список
        close_popup()
        for i in tqdm(offers_worldwide.find_all('li')):
            close_popup()
            key_country = i.find(
                'span', {'class': 'worldwide__name'}).get_text()
            value_country_code = i.find(
                'a', {'class': 'worldwide__link'}).get('data-country-code')
            dict_country_code[key_country] = value_country_code
            list_available_countries.append(key_country)

        # Находим длину словаря и умножаем на 2, т к код страны две буквы
        sum_key = len(dict_country_code) * 2
        sum_value = 0

        # Проверяем длину кода для страны
        for key, value in dict_country_code.items():
            if len(value) == 2:
                sum_value += 2

            else:
                logging.warning('Attention, country code not 2 letters.')
                logging.warning(
                    f'Perhaps the code does not work correctly for this country : {key} - {value}')

        # Выводим сообщение в зависимости от длины кода страны, т.к. далее используется срез для ссылки
        if sum_key == sum_value:
            logging.info('Code for all countries 2 letters.')
        else:
            logging.warning(
                'Attention !. It is possible that the code does not work correctly! Check all nodes with links!')

    except Exception as ex:
        if retry:
            logging.error(
                'Crash in "all_available_countries" function. Restart code automatically')
            logging.error(
                'Check if the website address is correct ! Former link - "https://www.indeed.com/worldwide" ')
            logging.error(f'Attempts = {retry}')
            time.sleep(3)
            driver.close()
            driver.quit()
            return all_available_countries(url_worldwide, retry=(retry - 1))

        else:
            raise

    # Делаем список кода стран
    list_country_code = list(dict_country_code.values())

    return list_available_countries, list_country_code


# !Функция, которая создаёт готовую ссылку на страницу для сбора информации
def get_url(country_abbreviated, position, retry=5):
    # Создаем URL позиции и локации
    try:
        template = 'https://{}.indeed.com/jobs?q={}&fromage=1'
        position = position.replace(' ', '+')
        url = template.format(country_abbreviated, position)
        return url

    except Exception as ex:
        logging.error(
            'Error in function "get_url". Restart code automatically')
        logging.error(f'Attempts = {retry}')

        return get_url(country_abbreviated, position, retry=(retry - 1))


# !Функция, которая собирает информацию с карточек
def collection_information(link):
    # Получаем индекс буквы "m", в сокращении страны всегда 2-е буквы!
    index_end_m = link.find('.com/') + 4

    # Списки для сбора нужной информации
    vacancy_name = []
    company_name = []
    company_location = []
    salary = []
    employment = []
    href_vacancy = []
    job_description = []

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
    # options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    options.add_argument("--log-level=3")

    # Отключаем обнаружение автоматизации (3 строки ниже)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("—disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)

    # Скрипт, который удаляет методы помогающие определить автоматизированное ПО.
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })

    # Так же помогает скрыть обнаружение автоматизации
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    # Сделал дополнительно try-except т.к. есть битые ссылки
    try:
        driver.get(link)
        logging.info(f'Start: {link}')
        close_popup()
        time.sleep(3)
        close_popup()

        while True:
            try:
                offers = (BeautifulSoup(driver.find_element(By.XPATH, "//div[@class='jobsearch-LeftPane']")
                                              .get_attribute('innerHTML'), "html.parser")
                          )

                close_popup()
                for i in offers.find_all('h2'):
                    close_popup()
                    if i.find('span').get("title"):
                        vacancy_name.append(i.find('span').get("title"))
                    else:
                        vacancy_name.append('None')

                    # Делаем готовую ссылку на вакансию
                    close_popup()
                    if i.find('a').get('href'):
                        href_vacancy.append(
                            link[:index_end_m] + i.find('a').get('href'))
                    else:
                        href_vacancy.append('None')

                close_popup()
                for i in offers.find_all('td', {'class': 'resultContent'}):
                    close_popup()
                    # Имя компании, если указана, то добавляем, если нет то - "не указано"
                    if i.find_all('div', {'class': 'heading6 company_location tapItem-gutter companyInfo'}):
                        company_name.append(
                            i.find('span', {'class': 'companyName'}).get_text())
                    else:
                        company_name.append('None')

                    # Локация, если указана, то добавляем, если нет то - "не указано"
                    close_popup()
                    if i.find_all('div', {'class': 'heading6 company_location tapItem-gutter companyInfo'}):
                        company_location.append(
                            i.find('div', {'class': 'companyLocation'}).get_text())
                    else:
                        company_location.append('None')

                close_popup()
                for i in offers.find_all('td', {'class': 'resultContent'}):
                    close_popup()
                    # Зарплата, если указана, то добавляем, если нет то - "не указано"
                    if i.find_all('div', {'class': 'metadata salary-snippet-container'}):
                        salary.append(
                            i.find('div', {'class': 'attribute_snippet'}).get_text())
                    else:
                        salary.append('None')

                    # Добавляем занятость в список
                    close_popup()
                    if i.find_all('ul', {'class': 'attributes-list'}):
                        employment.append(i.find('li').get_text())
                    else:
                        employment.append('None')

                '''
                Собираем полное описание вакансии
                '''

                close_popup()
                blocks = driver.find_elements(
                    By.XPATH, '//div[@class = "css-1m4cuuf e37uo190"]')

                close_popup()
                for text in tqdm(blocks):
                    close_popup()
                    # Делаем скрол вниз
                    text.location_once_scrolled_into_view
                    close_popup()
                    # Нажимаем на название вакансии
                    text.click()
                    time.sleep(2)
                    close_popup()

                    try:
                        close_popup()
                        job_description.append(driver.find_element(By.XPATH, '//div[@class = "jobsearch-jobDescriptionText jobsearch-JobComponent-description"]')
                                               .text)
                        close_popup()

                    except:
                        logging.error(
                            'Block - "jobsearch-jobDescriptionText ..." not found, code execution continues ...')
                        job_description.append('None')
                        # continue
                        break

                # Если есть кнопка "Следующая страница", то кликаем, иначе, завершаем цикл.
                try:
                    close_popup()
                    driver.find_element(
                        By.XPATH, '//a[@data-testid="pagination-page-next"]').click()
                    # link = link[:index_end_m] + offers.find('a', {'aria-label': 'Next Page'}).get('href')
                    time.sleep(2)

                except Exception:
                    logging.warning('Last page')
                    break

            except Exception:
                vacancy_name.append('None')
                company_name.append('None')
                company_location.append('None')
                salary.append('None')
                employment.append('None')
                href_vacancy.append('None')
                job_description.append('None')
                logging.warning('No vacancies')
                break

    except Exception:
        vacancy_name.append('None')
        company_name.append('None')
        company_location.append('None')
        salary.append('None')
        employment.append('None')
        href_vacancy.append('None')
        job_description.append('None')
        logging.warning('No vacancies or invalid link')

    # Добавляем все переменные в наш итоговый dataframe
    df = [vacancy_name, company_name, company_location,
          salary, employment, href_vacancy, job_description]

    return df


# !Функция, которая собирает итоговый dataframe
def creation_final_df(df):
    now = datetime.datetime.now()

    # Списки для сбора информации по типу собранной информации
    vacancy_name_2 = []
    company_name_2 = []
    company_location_2 = []
    salary_2 = []
    employment_2 = []
    href_vacancy_2 = []
    job_description_2 = []

    # Проходимся по списку с количеством страниц, далее по каждой странице и собираем информацию в зависимости от ее типа
    for num_list in df:
        for index, liss in enumerate(num_list):
            if index == 0:
                vacancy_name_2.extend(liss)
            elif index == 1:
                company_name_2.extend(liss)
            elif index == 2:
                company_location_2.extend(liss)
            elif index == 3:
                salary_2.extend(liss)
            elif index == 4:
                employment_2.extend(liss)
            elif index == 5:
                href_vacancy_2.extend(liss)
            elif index == 6:
                job_description_2.extend(liss)

    data_dict = {'title': vacancy_name_2,
                 'company': company_name_2,
                 'location': company_location_2,
                 'salary': salary_2,
                 'link': href_vacancy_2,
                 'description': job_description_2,
                 'job_type': employment_2}

    df_final = pd.DataFrame(data_dict)

    # Добавляем и заполняем недостающие столбцы
    df_final.insert(2, "country", 'None', allow_duplicates=True)
    df_final.insert(5, "source", 'www.indeed.com', allow_duplicates=True)
    df_final.insert(7, "date", now.strftime('%d-%m-%Y'), allow_duplicates=True)
    df_final.insert(8, "company_field", 'None', allow_duplicates=True)
    df_final.insert(10, "skills", 'None', allow_duplicates=True)

    df_final = df_final.drop_duplicates()
    df_final = df_final.dropna(subset=['title'])

    return df_final


def main(retry=5):
    now_date = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
    record_file = '_www.indeed.com_' + now_date + '.csv'
    df_list = []
    # Получаем список и словарь со странами - функция "all_available_countries"
    list_countr, list_countr_cod = all_available_countries(
        'https://www.indeed.com/worldwide')
    position_liss = ['junior data analyst', 'junior data science']

    for position_input in position_liss:
        for code_country in list_countr_cod:
            # Переведем нужную вакансию и страну в get_url - функция "get_url"
            url = get_url(code_country, position_input)
            logging.info(url)

            df_list.append(collection_information(url))

    final_dataframe = creation_final_df(df_list)
    final_dataframe.to_csv(record_file, index=False)

    return final_dataframe


if __name__ == "__main__":
    setup_logging("log.log")
    main()
