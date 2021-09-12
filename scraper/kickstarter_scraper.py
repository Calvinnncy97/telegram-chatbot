import requests
from bs4 import BeautifulSoup
import json
from server.url import URL
from server.product import Product
from selenium import webdriver
from time import sleep
import random

def kickstarter_scraper(category):
    product_list = []
    driver = webdriver.Chrome(r"chromedriver.exe")
    for url in URL.get(category).get("kickstarter"):
        driver.get(url)
        sleep(random.randint(0,5))
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        data = [
            (json.loads(i["data-project"]), i["data-ref"])
            for i in soup.find_all("div")
            if i.get("data-project")
        ]

        for i in data:
            product = Product(category, "kickstarter")
            product.link = (f'{i[0]["urls"]["web"]["project"]}?ref={i[1]}')
            product.title = (f'{i[0]["name"]}')
            product.description = (f'{i[0]["blurb"]}')
            product.pictures.append((f'{i[0]["photo"]["full"]}'))
            product.pictures.extend(scrape_pictures(driver, (f'{i[0]["urls"]["web"]["project"]}?ref={i[1]}')))
            product_list.append(product)
            #sleep(5)
    driver.quit()
    return product_list

def scrape_pictures (driver, url):
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "lxml")
    pic_list = []
    pic_list = [x['data-src'] for x in soup.find_all("img", {"data-src":True})]
    
    return pic_list

