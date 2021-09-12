import requests
from bs4 import BeautifulSoup
import json
from server.url import URL
from server.product import Product
from selenium import webdriver
from time import sleep
import re

url = "https://www.producthunt.com/"

def product_hunt_scraper():
    product_list = []

    driver = webdriver.Chrome(r"chromedriver.exe")
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "lxml", exclude_encodings=["ISO-8859-7"])
    for link in soup.find_all("div", {"class":"styles_postContent__3Sqgf"}):
        project_url = "https://www.producthunt.com/"+str(link.find("a")["href"])
        print (project_url)
        driver.get(project_url)
        soup = BeautifulSoup(driver.page_source, "lxml", exclude_encodings=["ISO-8859-7"])
        header = soup.find("div", {"class":"styles_headerInfo__3h0jF"})
        content = soup.find("div", {"class":"styles_content__2SyXA styles_white__13AB5 styles_descriptionContent__RyP4x styles_padding__2Z8vM styles_ignoreTheme__1-EME"})

        product = Product("", "product hunt")
        product.title = str(header.a.contents[0] + "\n" + header.h2.contents[0])
        product.description = str(content.find("div", {"class": "styles_description__2-RUk"}).find("div", attrs=None).contents[0])
        product.link = project_url
        product.pictures = [pic['href'] for pic in content.find("div", {"class":"styles_canvas__3UCB9"}).find_all("a", {"href":True})]
        product_list.append(product)

        
    driver.quit()
    return product_list

