#pip install fake_useragent, selenium, webdriver_manager

#Планирую после проверки и правок добавить еще argparse

import argparse
import time
from typing import Tuple, List, Dict, Union
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import csv
import os
from selenium.webdriver.common.keys import Keys
import random
from fake_useragent import UserAgent
from datetime import date
import logging
from utils import setup_logging
import warnings
warnings.filterwarnings('ignore')

url_dict_today = {
    'Austria': [
        'https://www.monster.at/jobs/suche?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.s.sh',
                'Keine weiteren Ergebnisse'
                ],
    'Belgium': [
        'https://www.monster.be/nl/vacatures/zoeken?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
                'Geen verdere resultaten'
                ],
    'Canada': [
        'https://www.monster.ca/jobs/search?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
               'No More Results'
               ],
    'France': [
        'https://www.monster.fr/emploi/recherche?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
               'Fin des résultats'
               ],
    'Germany': [
        'https://www.monster.de/jobs/suche?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
                'Keine weiteren Ergebnisse'
                ],
    'Ireland': [
        'https://www.monster.ie/jobs/search?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
                'No More Results'
                ],
    'Italy': [
        'https://www.monster.it/lavoro/cerca?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
              'Nessun altro risultato'
              ],
    'Luxembourg': [
        'https://www.monster.lu/fr/emploi/recherche?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
                   'Fin des résultats'
                   ],
    'Netherlands': [
        'https://www.monsterboard.nl/vacatures/zoeken?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
                    'Geen verdere resultaten'
                    ],
    'Spain': [
        'https://www.monster.es/trabajo/buscar?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
              'No hay más resultados'
              ],
    'Sweden': [
        'https://www.monster.ch/de/jobs/suche?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
               'Inga fler resultat'
               ],
    'Switzerland': [
        'https://www.monster.ch/de/jobs/suche?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.lh',
                    'Keine weiteren Ergebnisse'
                    ],
    'United_Kingdom': [
        'https://www.monster.co.uk/jobs/search?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.s.sh',
                       'No More Results'
                       ],
    'United_States': [
        'https://www.monster.com/jobs/search?q=Data+Analyst+Scientist&where=&page=1&recency=today&so=m.h.s',
                      'No More Results'
                      ]
}

data =[]
url_vacancy = []
today = date.today()
test_junior = ['junior', 'jr', 'entry-level', 'intern', 'internship']
test_dads = ['analyst', 'scientist']

def web_driver_set(set_of_driver):
  if set_of_driver == 'mobile_set':
    desired_capabilities = DesiredCapabilities.CHROME
    desired_capabilities["goog:loggingPrefs"] = {"performance":"ALL"}
    mobile_emulation = {
        "deviceMetrics" : {"width": 760, "height": 1640, "pixelRatio": 3.0},
        "userAgent" : "Mozilla/5.0 (Linux; Android 4.2.1; en-US; \
         NEXUS 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) \
         Chrome/18.0.1025.166 Mobile Safari/535.19"
    }
    chrome_options = Options()
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    driver = webdriver.Chrome(chrome_options=chrome_options,
                               desired_capabilities=desired_capabilities)
  else:
    chrome_options = Options()
    useragent = UserAgent()
    chrome_options.add_argument(f"user-agent={useragent.random}")
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(chrome_options=chrome_options)
  return driver

def jobtype(row):
    if 'hybrid' in row.lower():
        return 'Hybrid'
    elif 'remote' in row.lower():
        return 'Remote'
    elif 'full-time' in row.lower() or 'full time' in row.lower():
        return 'Full-time'
    elif 'contract' in row.lower():
        return 'Contract'
    else:
        return None

def country_url(dictionary, set_driver):
  driver = web_driver_set(set_driver)
  try:
    for key,value in dictionary.items():
      c_url = [value[0]]
      for c in c_url:
        driver.get(c)
        time.sleep(3)
        counter = 0
        while True:
          win = driver.find_element(By.TAG_NAME, 'html')
          win.send_keys(Keys.END)
          time.sleep(2)
          counter += 1
          if f"<span>{value[1]}</span>" in driver.page_source or counter > 30:
            break
        time.sleep(5)
        links = driver.find_elements(
            By.CSS_SELECTOR,
             "a.job-cardstyle__JobCardComponent-sc-1mbmxes-0"
             )
        for l in links:
          url_vacancy.append(l.get_attribute("href") + ' ' + key)
      logging.info(f"End country {key}. Total vacancy {len(url_vacancy)}")
  except Exception as ex:
    logging.info(f"Something wrang in scrap country {key} : {ex}")
  finally:
    driver.close()
    driver.quit()

def scrap_links(match_dads,match_junior, list_url_vacancy,set_driver):
  cnt_vakancy = 0

  cnt_fail = 0
  driver = web_driver_set(set_driver)
  try:
    for item in list_url_vacancy:
      if cnt_vakancy % 10 == 0:
        logging.info(f"Viewed {cnt_vakancy} vacancies")
      value,key = item.split()
      driver.get(value)
      time.sleep(5)
      try:
        test_title = driver.find_element(By.CLASS_NAME,
                                         'JobViewTitle').text.lower()
      except:
        cnt_fail += 1
        logging.info(f"Fail in title. Total fails {cnt_fail}")
        test_title = 'Not found'
      dads = False
      junior = False
      for x in match_dads:
        if test_title.find(x) != -1:
          dads = True
          break
      for y in match_junior:
        if test_title.find(y) != -1:
          junior = True
          break
      if dads==True and junior==True:
        try:
          title = driver.find_element(By.CLASS_NAME,
                                         'JobViewTitle').text
        except:
          title = None
        try:
          company = driver.find_element(
              By.CLASS_NAME,
              'headerstyle__JobViewHeaderCompany-sc-1ijq9nh-6'
              ).text
        except:
          company = None
        link = value
        country = key
        date = today
        source = "https://www.monster.com/"
        try:
          location = driver.find_element(
              By.CLASS_NAME,
               'headerstyle__JobViewHeaderLocation-sc-1ijq9nh-4'
               ).text
        except:
          location = None
        try:
          company_field = (
              driver
              .find_element(
                  By.CLASS_NAME,
                   'jobview-containerstyles__CompanyInformation-sc-16af7k7-6'
                   )
              .find_element(
                  By.CLASS_NAME,
                   'detailsstyles__DetailsTableDetailBody-sc-1deoovj-5'
                   )
              .text
              )
        except:
          company_field = None
        try:
          description = driver.find_element(
              By.CLASS_NAME,
               'descriptionstyles__DescriptionContainer-sc-13ve12b-0'
               ).text
        except:
          description = None
        try:
          salary = driver.find_element(
              By.CLASS_NAME,
               'salarystyle__SalaryContainer-sc-1kub5et-7'
               ).text
        except:
          salary = None
        skills = None
        job_type = jobtype(title)
        data.append((title, company, country, location, salary, source, link,
                        date,company_field, description, skills, job_type))
        cnt_vakancy += 1
      else:
        cnt_vakancy += 1
  except Exception as ex:
    logging.info(f"Something wrang in scrap vacancy {value} : {ex}")
  finally:
    driver.close()
    driver.quit()

def write_to_csv(results: List[Tuple[str, str, str, str, str, str, str, date, str, str, str, str]]):
    """writes information to a file"""
    if not results:
        logging.error(f'No results for the choosen period')
    today = date.today()
    #filepath = os.path.join('data', f"monster {today}")
    with open(f"monster_{today}.csv", mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['title', 'company', 'country', 'location', 'salary', 'source', 'link', 'date',
                         'company_field', 'description', 'skills', 'job_type'])
        writer.writerows(results)
    logging.info(f"Data written to file {today}")

def main():
  country_url(url_dict_today,'mobile_set')
  scrap_links(test_dads, test_junior, url_vacancy, 'other')
  write_to_csv(data)

if __name__ == "__main__":
  setup_logging("log.txt")
  main()