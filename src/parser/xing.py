from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver import ActionChains, Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime, date
import requests
import csv
import argparse
import logging
from utils import setup_logging, set_driver

headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Is-Ajax-Request": "X-Is-Ajax-Request",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36"
    }

url = 'https://www.xing.com/jobs/search?\
    careerLevel=1.795d28&careerLevel=2.24d1f6&careerLevel=3.2ebf16&keywords=junior%20data%20analyst%20scientist&sort=date'

def get_jobs(url):
    '''
    The function gets job list from the page and puts information about today's jobs into a list of dictionaries.
    The fields collected if available: job title, job city, company name, salary, type of employment (full-time, part-time,
    contract, etc.), link to the full job description
    '''
    driver = set_driver()
    driver.get(url)
    sleep(5)
    try:
        driver.find_element(By.CSS_SELECTOR, "button[class*='consent-banner-button-accept-all']").click()  
    except:
        ActionChains(driver).move_to_element_with_offset(
        driver.find_element(By.XPATH, '//html'), 0, 10
        ).click().perform()
    sleep(5)
    offers = driver.find_element(By.XPATH, "//section/ul")  
    job_num = []
    offer_list = offers.find_elements(By.XPATH, '//li/article')
    for i, offer in enumerate(offer_list):
    #Часто подходящих вакансий нет. Чтобы проверить работоспособность, можно прописать not in  
        if ('stunde' in offer_list[i].text.lower()
        #if (('stunde') not in offer_list[i].text.lower()
            or 'gerade eben' in offer_list[i].text.lower()
            or 'just now' in offer_list[i].text.lower()
            or 'hour' in offer_list[i].text.lower()):
            job_num.append(i)

    jobs = {}
    jobs_list = []
    title = '' 
    city = ''
    company = '' 
    salary = ''
    employment = ''
    link = ''
    for n in job_num:
        #title
        try:
            title = offer_list[n].find_element(By.CSS_SELECTOR, 'h3').text    
        except:
            title = ''      
        #city
        try:
            city = offer_list[n].find_element(By.CSS_SELECTOR, "p[class*='list-item-job-teaser-list-item-location']").text
        except:
            city = ''
        #company name
        try:
            company = offer_list[n].find_element(By.CSS_SELECTOR, "p[class*='list-item-job-teaser-list-item-company']").text
        except:
            company = ''     
        #salary
        try:
            salary = offer_list[n].find_element(By.CSS_SELECTOR, "p[class*='list-item-job-teaser-list-item-salary']").text
    
        except:
            salary = ''     
        #employment type
        try:
            employment = offer_list[n].find_element(By.CSS_SELECTOR, "p[class*='list-item-job-teaser-list-item-employmentType']").text        
        except:
            employment = ''   
        #link
        link = offer_list[n].find_elements(
            By.XPATH, '//a[@class = "list-item-job-teaser-list-item-listItem-f04c772e"]')[n].get_attribute('href')
        jobs_list.append({'title': title, 
                            'location': city, 
                            'company': company, 
                            'salary': salary, 
                            'job_type': employment, 
                            'link': link})
    driver.quit()
    return jobs_list    
def get_description(cell, headers=headers):
    '''
    The function gets information about job from the job page.
    The fields collected if available: job description, country, industry.
    '''
    re = requests.get(cell, headers)
    re.encoding = 'utf-8'
    try:
        soup = BeautifulSoup(re.text, features="lxml")
    except:
        soup = ''
    if soup != '':  
        try:
            desc = soup.find('div', class_ = 'html-description-html-description-header-c7005820').text.strip().replace('\n',' ')
        except:
            desc = ''
        try:
            country = soup.select('div[class*=styles-grid-col-b728475a] > p[class*="body-copystyles__BodyCopy-"]')[-1].text.strip()
        except:
            country = ''    
        try:
            field = soup.select('li[class*="info-iconstyles"]')[-1].text.strip()
        except:
            field = ''    
        return desc, country, field
    else:
        logging.error(f'Something wrong with text at {cell}')
        return '', '', ''     


def add_more_info(jobs):
    '''
    The function reorder fields in the dictionary and adds new fields: skills, source and date.
    '''
    new_order = ['title', 'company', 'country', 'location', 'salary', 'source', 'link', 
              'date', 'company_field', 'description', 'skills', 'job_type']
    new_jobs = []             
    if len(jobs) > 0:
        for job in jobs:
            new_fields = get_description(job['link'])
            job['description'] = new_fields[0]
            job['country'] = new_fields[1] 
            job['company_field'] = new_fields[2]
            job['skills'] = ''
            job['source'] = 'xing.com'
            job['date'] = date.today()
            job = {k: job[k] for k in new_order}
            new_jobs.append(job)
    else:
        new_jobs = {}
    return new_jobs 

def write_jobs(new_jobs):
    '''
    The functions saves information about found jobs in a .csv file.
    '''
    today_date = date.today()
    if len(new_jobs) > 0:
        with open(f'jobs_{today_date}.csv', mode='w', encoding='utf-8', newline='') as f: 
            csv.DictWriter(f, new_jobs[0].keys()).writeheader()
            for job in new_jobs:
                w = csv.DictWriter(f, job.keys())
                w.writerow(job)
    else:
        logging.error(f'No results for {today_date}') 

def main():
    '''
    The function parses job list, puts them into a list of dictionaries, adds more info and writes saved jobs in a .csv file.
    '''
    jobs = get_jobs(url)
    new_jobs = add_more_info(jobs)
    write_jobs(new_jobs)

if __name__ == "__main__":
    setup_logging("log.txt")
    main()          