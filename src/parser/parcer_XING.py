from selenium.webdriver import ActionChains, Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import undetected_chromedriver
from pyvirtualdisplay import Display

from bs4 import BeautifulSoup

from time import sleep
from datetime import datetime, timedelta, date

import requests
import csv
import pandas as pd
import numpy as np
import re

if __name__ == "__main__":
    main()

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

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Is-Ajax-Request": "X-Is-Ajax-Request",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36"
}

# Определяем ссылку для парсинга
url = 'https://www.xing.com/jobs/search?careerLevel=1.795d28&careerLevel=2.24d1f6&careerLevel=3.2ebf16&keywords=junior%20data%20analyst%20scientist&sort=date'


# Прогружаем страницу: драйвер по урлу пытается получить страницу и скроллит до низа страницы.
# Если не получилось - предполагаем, что появились всплывающие окна и пробуем их закрыть.
# Закрыв все окна - можем получить все вакансии на странице.

def get_vacations(url):
    driver.get(url)
    sleep(5)
    try:
        driver.find_element(By.XPATH, '//button[@class="sc-6z95j0-1 eUZDeX consent-banner-button-accept-all"]').click()
    except:
        ActionChains(driver).move_to_element_with_offset(
            driver.find_element(By.XPATH, '//html'), 0, 10
        ).click().perform()
    sleep(5)
    offers = driver.find_element(By.XPATH, "//section/ul")
    return offers


# Собираем ссылки на подходящие вакансии: если вакансия опубликована сегодня (ключевые слова just now, hour, gerade eben, stunde) - забираем ее индекс.

def get_links(offers):
    job_num = []
    offer_list = offers.find_elements(By.XPATH, '//li/article')
    for i in range(len(offer_list)):
        # Часто подходящих вакансий нет. Чтобы проверить работоспособность, можно прописать not in
        if (('stunde') in offer_list[i].text.lower()
                # if (('stunde') not in offer_list[i].text.lower()
                or ('gerade eben') in offer_list[i].text.lower()
                or ('just now') in offer_list[i].text.lower()
                or ('hour') in offer_list[i].text.lower()):
            job_num.append(i)
    # Для проверки, что скрипт работает - получаем индексы подходящих вакансий
    return job_num


def make_table(job_num):
    jobs = []
    title = ''
    city = ''
    company = ''
    salary = ''
    employment = ''
    link = ''
    for n in job_num:
        # title
        try:
            title = offer_list[n].find_element(By.CSS_SELECTOR, 'h3').text
        except:
            title = None

            # city
        try:
            city = offer_list[n].find_elements(By.XPATH,
                                               '//p[@class = "x85e3j-0 iSjcXV list-item-job-teaser-list-item-location-a5b28738"]')[
                n].text
        except:
            city = None
            # company name
        try:
            company = offer_list[n].find_elements(By.XPATH,
                                                  '//p[@class = "x85e3j-0 iSjcXV list-item-job-teaser-list-item-company-e73bb356 utils-line-clamp-lineClamp2-dfe26aab"]')[
                n].text
        except:
            company = None
            # salary
        try:
            salary = offer_list[n].find_elements(By.XPATH,
                                                 '//p[@class = "x85e3j-0 fzPhvn y4z6ql-0 byZVfY list-item-job-teaser-list-item-salary-dba9b61f"]')[
                n].text
        except:
            salary = None
            # employment type
        try:
            employment = offer_list[n].find_elements(By.XPATH,
                                                     '//p[@class = "x85e3j-0 fzPhvn y4z6ql-0 byZVfY list-item-job-teaser-list-item-employmentType-b3e353d9"]')[
                n].text
        except:
            employment = None
            # link
        link = \
        offer_list[n].find_elements(By.XPATH, '//a[@class = "list-item-job-teaser-list-item-listItem-f04c772e"]')[
            n].get_attribute('href')
        jobs.append([title, city, company, salary, employment, link])
    driver.quit()
    data = pd.DataFrame(jobs, columns=['title', 'location', 'company', 'salary', 'job_type', 'link'])

    # Часть информации доступна только на странице вакансии.
    # Напишем функцию, чтобы спарсить эту информацию.
    def get_description(cell, headers=headers):
        re = requests.get(cell, headers)
        re.encoding = 'utf-8'
        soup = BeautifulSoup(re.text)
        desc = soup.find('div', class_='html-description-html-description-header-c7005820').text.strip().replace('\n',
                                                                                                                 ' ')
        country = soup.find_all('p', class_='body-copystyles__BodyCopy-x85e3j-0 hrEVrk')[-1].text.strip()
        field = soup.find_all('li', class_='info-iconstyles__StyledInfoIcon-j1dfh-0 gtKNWf')[-1].text.strip()
        return desc, country, field

    data[['description', 'country', 'company_field']] = data['link'].apply(lambda x: pd.Series(get_description(x)))
    # Дописываем в датафрейм оставшиеся столбцы.
    data['skills'] = None
    data['source'] = 'xing.com'
    data['date'] = date.today()
    data = data[
        ['title', 'company', 'country', 'location', 'salary', 'source', 'link', 'date', 'company_field', 'description',
         'skills', 'job_type']]
    return data

# #loading to csv
# from google.colab import drive
# drive.mount("/content/drive")
# final_res.to_csv (f'/content/drive/MyDrive/xing_{date.today()}.csv', index = None, header=True, sep='\t', encoding='utf-8')

