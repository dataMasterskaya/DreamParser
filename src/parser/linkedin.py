from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
import csv
from pyvirtualdisplay import Display
from datetime import datetime
import logging

def main():



# Display is imported and used to enable the driver to run without headless mode
# pip install selenium, webdriver_manager, pyvirtualdisplay, bs4,lxml,requests
# sudo apt-get install xvfb 
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


    driver = webdriver.Chrome( options=options)

    dataname = (datetime.now()).date()

    # change keyword as needed
    # or just pass it streight in url
    # keyword1 ="data scientist junior"
    # keyword2 = "data analyst junior"
    keyword = 'data scientist junior or data analyst junior'
    url =(f"https://www.linkedin.com/jobs/search?_l=en_US&keywords={keyword}&location=%D0%92%20%D0%BB%D1%8E%D0%B1%D0%BE%D0%B9%20%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B5"
        "&locationId=&geoId=92000000&sortBy=R&f_TPR=r86400&f_E=2&position=1&pageNum=0")

    driver.get(url)
    sleep(3)

    # Commented out IPython magic to ensure Python compatibility.

    # scroll to the button Show more offers at the bottom of the page
    cont = driver.find_element(By.XPATH,f'/html/body/div[1]/div/main/section[2]/button')
    for i in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(1)
    # click on the button again and scroll (offer upload limit always = 1000)
    try:
        for i in range(0,50):
            sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                cont.click()
            except:
                sleep(0.1)
    except:
        sleep(0.1)

    # get links to all vacancies and add them to the list
    soup=BeautifulSoup(driver.page_source,"lxml")
    link=soup.find_all("a",class_="base-card__full-link")
    links=[]
    for l in link:
        links.append(l.get("href")+"&_l=en_US") # translate into english

    # check number of links
    # len(links)

    # function for getting information from the link to the offer by sending a request, converting the response into a soup object and processing it with bs methods

    headers=({'user-agent': 
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36'
            '(KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'})


    def scan(url):
        try:
            response = requests.get(url,headers=headers)
        except:
            logging.info(url,"response ERROR")
        sleep(1)                  # when time decreases, more links give no information
        soup = BeautifulSoup(response.text,"lxml")

        # company name
        try:
            company = " ".join(soup.find("a",
                class_="topcard__org-name-link topcard__flavor--black-link").text.split())
        except:
            company = None


        # title    
        try:
            title = soup.find("h1",
            class_=("top-card-layout__title font-sans text-lg papabear:text-xl"
            " font-bold leading-open text-color-text mb-0 topcard__title")).text
        except:
            title = None

        try:
            xxx = soup.find_all("ul",class_="description__job-criteria-list")
            for ii in xxx:
                y = " ".join(ii.text.split())
                
        except:
            sleep(0.5)
        
        
        # field of company
        try:
            ind = " ".join(y.split('Industries')[1].split())
            y = y.split('Industries')[0]
        except:
            ind = None


        # employment type
        try:
            emp = " ".join(y.split('Employment type')[1].split())
            y = y.split('Employment type')[0]
        except:
            emp = None


        # seniority level
        try:
            level = " ".join(y.split('Seniority level')[1].split())
        except:
            level= None

        # location
        try:
            loc = " ".join(soup.find("span",class_="topcard__flavor topcard__flavor--bullet").text.split())
        except:
            loc = None
        
        # publication time
        try:
            time = dataname
        #     " ".join(soup.find("span",
        #         class_="posted-time-ago__text posted-time-ago__text--new topcard__flavor--metadata").text.split())
        except:
            time = None

        # link
        link = url


        # description
        try:
            card_text = " ".join(soup.find("div",
                    class_="show-more-less-html__markup show-more-less-html__markup--clamp-after-5").text.split())
        except:
            card_text = None

        # country
        try:
            country = loc.split(',')[-1]
        except:
            country = None

        source = "linkedin.com"
        sol = None
            
        return ([title, company, country, loc, sol, 
                source, link, time, ind, card_text,level,emp])

    # Commented out IPython magic to ensure Python compatibility.
    # # scanning all links
    driver.quit()


    data = []
    data.append(['title',  'company', 'country',
                'location', 'salary', 'source', 
                'link', 'date', 'company_field', 
                'description', 'skills', 'job_type'])
    for i in links:
        data.append(scan(i)) 
        



    with open(f'linkedin_{dataname}.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerows(data)

if __name__ == "__main__":
    main()