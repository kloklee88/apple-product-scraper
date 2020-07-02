# imgur_json_converter_scraper.py - Converts Imgur album to JSON for bracket website by scraping using BS4

import time
import csv
import traceback
import requests
import sys
import webbrowser
from tkinter import *
from tkinter import font as tkFont
from datetime import datetime
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from googletrans import Translator

class Record:
    def __init__(self, color, size, country, carrier, date, day_to_ship):
        self.color = color
        self.size = size
        self.country = country
        self.carrier = carrier
        self.date = date
        self.day_to_ship = day_to_ship

class CountryUrl:
    def __init__(self, country, url, date_format):
        self.country = country
        self.url = url
        self.date_format = date_format

###################
# CONFIGURABLE DATA
countries = []
countries.append(CountryUrl('US', 'https://www.apple.com/shop/buy-iphone/iphone-se', '%a, %b %d')) 
countries.append(CountryUrl('UK', 'https://www.apple.com/uk/shop/buy-iphone/iphone-se', '%a %d %b')) 
countries.append(CountryUrl('Canada', 'https://www.apple.com/ca/shop/buy-iphone/iphone-se', '%a %d %b')) #trade in first, no payment, might need postal code
countries.append(CountryUrl('HK', 'https://www.apple.com/hk/shop/buy-iphone/iphone-se', '%a %d/%m/%Y')) #no trade in
countries.append(CountryUrl('Germany', 'https://www.apple.com/de/shop/buy-iphone/iphone-se', '%a %d %b')) #Trade in first
countries.append(CountryUrl('France', 'https://www.apple.com/fr/shop/buy-iphone/iphone-se', '%a %d %b')) #no payment
countries.append(CountryUrl('Japan', 'https://www.apple.com/jp/shop/buy-iphone/iphone-se', '%a %Y/%m/%d')) #no payment
countries.append(CountryUrl('China', 'https://www.apple.com.cn/shop/buy-iphone/iphone-se', '%a %d/%m/%Y')) #trade in first, no payment
delay = 1 # in seconds
delay_long = 2 # in seconds
###################

records = []

def save_record(color, size, country, carrier, date, date_format):
    if country != 'US':
        carrier = None
    if country == 'Germany' or country == 'France' or country == 'China' or country == 'Japan':
        translator = Translator()
        date = translator.translate(date).text
    if date == 'In stock':
        records.append(Record(color, size, country, carrier, datetime.now().date(), 0))
        return
    if country == 'Germany' or country == 'France' or country == 'China':
        date_formatted = date.split('-')[0].strip()
    else:
        date_formatted = date.split('–')[0].strip()
    if date_formatted == 'Tomorrow':
        records.append(Record(color, size, country, carrier, (datetime.now()+timedelta(days=1)).date(), 1))
        return
    date_converted = datetime.strptime(date_formatted, date_format).replace(year=datetime.now().year)
    if country == 'HK' or country == 'China' or country == 'Japan':
        day_to_ship = (date_converted - datetime.now()).days
    else:
        day_to_ship = (date_converted - datetime.now()).days + 1
    print(date_converted)
    records.append(Record(color, size, country, carrier, date_converted, day_to_ship))

def before_color_loop(driver, country):
    if country == 'Canada' or country == 'Germany' or country == 'China':
        #Click "No" for trade in
        driver.find_element_by_xpath('//*[@id="tradeup-inline-app"]/div/div/fieldset/div/div[2]/div/div').click()
        time.sleep(delay_long)

def click_element(driver, xpath):
    element = driver.find_element_by_xpath(xpath)
    driver.execute_script("arguments[0].scrollIntoView();", element)
    element.click()
    time.sleep(delay)

def execute_scrape(countries):
    start_time = datetime.now()

    #Translate webpages to English
    options = Options()
    prefs = {
    "translate_whitelists": {"fr":"en", "de":"en" ,"ja":"en", "zh-CN":"en"},
    "translate":{"enabled":"true"}
    }
    options.add_experimental_option("prefs", prefs)

    try:
        print([country.country for country in countries])
        #Loop through countries
        for country_url in countries:
            country = country_url.country
            date_format = country_url.date_format
            print(f'Country: {country}')

            # Using Selenium to select dynamic content
            driver = webdriver.Chrome(chrome_options=options)
            driver.get(country_url.url)
            time.sleep(delay)

            #Delete overlap header causing problems
            header_element = driver.find_element_by_xpath('//*[@id="page"]/div[4]')
            driver.execute_script("""var element = arguments[0];element.parentNode.removeChild(element);""", header_element)

            color_length = len(driver.find_elements_by_xpath('//*[@id="Item1"]/div/fieldset/div[1]/*'))
            size_length = len(driver.find_elements_by_xpath('//*[@id="Item2"]/div/fieldset/div/*'))
            print(f'Color choices: {color_length}')
            print(f'Size choices: {size_length}')
            if country == 'US':
                carrier_length = len(driver.find_elements_by_xpath('//*[@id="Item3"]/div/fieldset/div[1]/div[2]/*'))
                print(f'Carrier choices: {carrier_length}')

            before_color_loop(driver, country)

            #Loop through color options
            for i in range(color_length):
                click_element(driver, '//*[@id="Item1"]/div/fieldset/div[1]/div['+ str(i+1) +']')
                color = driver.find_element_by_xpath('//*[@id="Item1"]/div/fieldset/div[1]/div['+ str(i+1) +']/div/div/label/span[2]').text
                print(color)
                #Loop through GB size options
                for j in range(size_length):
                    click_element(driver, '//*[@id="Item2"]/div/fieldset/div/div['+ str(j+1) +']')
                    size = driver.find_element_by_xpath('//*[@id="Item2"]/div/fieldset/div/div['+ str(j+1) +']/div/label/span[1]').text
                    size = size.replace('*', '')
                    print(size)
                    #Loop through carrier options
                    if country == 'US': #trade in and payment
                        need_trade_pay = True
                        for k in range(carrier_length):
                            click_element(driver,'//*[@id="Item3"]/div/fieldset/div[1]/div[2]/div['+ str(k+1) +']')
                            carrier = driver.find_element_by_xpath('//*[@id="Item3"]/div/fieldset/div[1]/div[2]/div['+ str(k+1) +']/div/label/span[2]').text
                            print(carrier)
                            if need_trade_pay:
                                click_element(driver,'//*[@id="tradeup-inline-heroselector"]/div/div/fieldset/div/div[1]')
                                time.sleep(delay)
                                click_element(driver,'//*[@id="primary"]/materializer/purchase-options/fieldset/materializer[1]/div/div[1]')
                                time.sleep(delay)
                                need_trade_pay = False
                            date = driver.find_element_by_xpath('//*[@id="primary"]/summary-builder/div[2]/div[1]/materializer/div[2]/div/div/ul/li/span').text
                            save_record(color, size, country, carrier, date, date_format)
                    elif country == 'UK': #trade in and payment
                        need_trade_pay = True
                        if need_trade_pay:
                            click_element(driver,'//*[@id="tradeup-inline-heroselector"]/div/div/fieldset/div/div[1]/div/div')
                            time.sleep(delay)
                            click_element(driver,'//*[@id="primary"]/materializer/purchase-options/fieldset/materializer[2]/div/div[2]/div/div')
                            time.sleep(delay)
                            need_trade_pay = False
                        date = driver.find_element_by_xpath('//*[@id="primary"]/summary-builder/div[2]/div[1]/materializer/div[2]/div/div/ul/li/span').text
                        save_record(color, size, country, None, date, date_format)
                    elif country == 'Germany': #payment
                        need_trade_pay = True
                        if need_trade_pay:
                            click_element(driver,'//*[@id="primary"]/materializer/purchase-options/fieldset/materializer[2]/div/div[2]/div/div')
                            time.sleep(delay)
                            need_trade_pay = False
                        date = driver.find_element_by_xpath('//*[@id="primary"]/summary-builder/div[2]/div[1]/materializer/div[2]/div/div/ul/li/span').text
                        save_record(color, size, country, None, date, date_format)
                    elif country == 'France' or country == 'Japan': #trade in
                        need_trade_pay = True
                        if need_trade_pay:
                            click_element(driver,'//*[@id="tradeup-inline-heroselector"]/div/div/fieldset/div/div[1]/div/div')
                            time.sleep(delay)
                            need_trade_pay = False
                        date = driver.find_element_by_xpath('//*[@id="primary"]/summary-builder/div[2]/div[1]/materializer/div[2]/div/div/ul/li/span').text
                        save_record(color, size, country, None, date, date_format)
                    elif country == 'China':
                        time.sleep(delay_long)
                        driver.find_element_by_xpath('//*[@id="primary"]/summary-builder/div[2]/div[1]/materializer/div/div/div/ul/li[1]/span').text
                        save_record(color, size, country, None, date, date_format)
                    else:
                        time.sleep(delay_long)
                        date = driver.find_element_by_xpath('//*[@id="primary"]/summary-builder/div[2]/div[1]/materializer/div[2]/div/div/ul/li/span').text
                        save_record(color, size, country, None, date, date_format)
                print('-----------------------------')
    except Exception as e:
        print("ERROR! did not complete scraping")
        print(e)
        traceback.print_exc()
    finally:
        completion_time = datetime.now() - start_time
        print(f'Time to complete (seconds): {completion_time.seconds}')
        #Store records into CSV file
        with open('data.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Color', 'Size', 'Country', 'Carrier', 'Date Delivered', 'Number of Days to Ship'])
            for record in records:
                writer.writerow([record.color, record.size, record.country, record.carrier, record.date, record.day_to_ship])

#execute_scrape(countries)

###################
# GUI 
###################
class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)                 
        self.master = master
        self.init_window()

    def init_window(self, side=LEFT, anchor=W):
        self.master.title("Apple Product Scraper")
        self.pack(fill=BOTH, expand=1)
        self.active_list = []
        self.urls = []
        self.date_formats = []
        helv = tkFont.Font(family='Helvetica', size=12, weight=tkFont.BOLD)
        for i,country in enumerate(countries):
            is_active = IntVar(value=1)
            Checkbutton(self, text=country.country, variable=is_active, font=helv).grid(row=i,column=0,sticky=W)
            self.active_list.append(is_active)
            url = StringVar(value=country.url)
            Entry(self, textvariable=url, font=helv, width=50).grid(row=i,column=1,sticky=W)
            self.urls.append(url)
            date_format = StringVar(value=country.date_format)
            Entry(self, textvariable=date_format, font=helv, width=20).grid(row=i,column=2,sticky=W)
            self.date_formats.append(date_format)
        Button(self, text="Run",command=self.execute_scrape, width=15, font=helv).place(relx=0.5, rely=0.7, anchor=CENTER)
        Button(self, text="Exit",command=self.client_exit, width=15, font=helv).place(relx=0.5, rely=0.8, anchor=CENTER)
    
    def client_exit(self):
        exit()

    def execute_scrape(self):
        updated_countries = self.update_country()
        #print([country.url for country in updated_countries])
        #print([country.date_format for country in updated_countries])
        filtered_countries = self.filter_country(updated_countries)
        execute_scrape(filtered_countries)

    def update_country(self):
        updated_countries = []
        for i,country in enumerate(countries):
            country.url = self.urls[i].get()
            country.date_format = self.date_formats[i].get()
            updated_countries.append(country)
        return updated_countries

    def filter_country(self, updated_countries):
        filtered_countries = []
        for i,country in enumerate(updated_countries):
            if self.active_list[i].get() == 1:
                filtered_countries.append(country)
        return filtered_countries

root = Tk()
root.geometry("800x400")
app = Window(root)
root.mainloop() 



