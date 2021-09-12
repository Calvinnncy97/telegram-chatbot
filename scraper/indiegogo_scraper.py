import requests
from bs4 import BeautifulSoup
import json
from server.url import URL
from server.product import Product
from selenium import webdriver
from time import sleep
import re

def indiegogo_scraper(category):
    product_list = []
    driver = webdriver.Chrome(r"chromedriver.exe")

    for url in URL.get(category).get("indiegogo"):
        driver.get(url)

        soup = BeautifulSoup(driver.page_source, "lxml", exclude_encodings=["ISO-8859-7"])
        for i in soup.find_all("discoverable-card"):
            product = Product(category, "indiegogo")
            product.title = str(i.find("div", {"class":"discoverableCard-title"}).contents[0])
            product.description = str(i.find("div", {"class":"discoverableCard-description"}).contents[0])
            product.link = "https://www.indiegogo.com" + str(i.find("div", {"class":"discoverableCard"}).a['href']).replace("/pica", "#/").strip()
            product.pictures.append(str(i.find("div", {"class":"discoverableCard-image"})['data-bgset']))
            product.pictures.extend(scrape_pictures(driver, product.link))
            product_list.append(product)
          
    driver.quit()
    return product_list



def scrape_pictures (driver, url):
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "lxml", exclude_encodings=["ISO-8859-7"])
    pic_list = []
    content = soup.find("div", {"class":"routerContentStory-storyBody"})
    if content != None:
        pic_list = [str(x['data-src']) for x in content.find_all("img", {"data-src":True})]
    
    return pic_list
