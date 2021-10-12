import os

from django.http import HttpResponse
from django.shortcuts import render
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

from django.utils.datastructures import MultiValueDictKeyError

from .models import Amazon, Flipcart, Compare

# Global Declarations
user_agent = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}


def index(request):
    if request.method == "POST":
        try:
            if request.POST['amazon_page_size']:
                amazon_result = (amazon_scrap(search=(request.POST['search']), size=request.POST['amazon_page_size']))
                return render(request, "index.html", amazon_result)
        except MultiValueDictKeyError:
            pass

        try:
            if request.POST['flipcart_page_size']:
                flipcart_result = (
                    flipcart_scrap(search=(request.POST['search']), size=request.POST['flipcart_page_size']))
                return render(request, "index.html", flipcart_result)

        except MultiValueDictKeyError:
            pass
    return render(request, "index.html")


def flipcart_fetch_page(url):
    page = requests.get(url, headers=user_agent)
    soup = BeautifulSoup(page.content, "html.parser")
    multi_locations = soup.find_all("div", {"class": "_3pLy-c row"})
    return multi_locations


def amazon_fetch_page(url):
    page = requests.get(url, headers=user_agent)
    soup = BeautifulSoup(page.content, "html.parser")
    multi_locations = soup.find_all("div", {"class": "sg-col sg-col-4-of-12 sg-col-8-of-16 sg-col-12-of-20"})
    return multi_locations


def flipcart_scrap(search, size):
    multi_pages = []
    for i in range(int(size)):
        print("Fetching Page", i + 1)
        page_url = "https://www.flipkart.com/search?q=" + search.lower() + "&page=" + str(i)
        page_location = flipcart_fetch_page(page_url)
        while len(page_location) == 0:
            print("in While")
            page_location = flipcart_fetch_page(page_url)
        multi_pages.append(page_location)
    print("...Completed...")

    data_sample = []
    for multi_location in multi_pages:
        for src in multi_location:
            source = src.find("div", {"class": "_4rR01T"}).text
            name = source.split("(")[0].strip().upper()
            if len(name) > 35:
                continue
            if "POWER BANK" in name:
                continue
            try:
                color = source.split("(")[1].replace(")", "").strip().split(",")[0].strip().upper()
                ram = re.search(r'\d+',
                                src.find("div", {"class": "fMghEO"}).find_all("li", {"class": "rgWa7D"})[0].text.split(
                                    "|")[0].strip()).group()
                rom = re.search(r'\d+',
                                src.find("div", {"class": "fMghEO"}).find_all("li", {"class": "rgWa7D"})[0].text.split(
                                    "|")[1].strip()).group()
            except(IndexError, AttributeError):
                continue

            try:
                price = src.find("div", {"class": "_3tbKJL"}).text[1:].split("₹")[0].replace(",", "")
            except AttributeError:
                continue
            in_data = [name, color, ram, rom, int(price)]
            data_sample.append(in_data)
    df_sample = pd.DataFrame(data_sample)
    df_sample.columns = ["Mobile", "Colour", "Ram", "Storage", "Flipcart_Price"]
    df_sample.drop_duplicates(subset=['Mobile', 'Colour'], inplace=True)
    flipcart = df_sample
    flipcart.to_csv("download_flipcart.csv", index=False)
    print(flipcart.count())
    save_to_flipcart_db(flipcart)
    return flipcart_dataset()


def save_to_flipcart_db(flipcart):
    name = [x for x in flipcart['Mobile']]
    color = [x for x in flipcart['Colour']]
    ram = [x for x in flipcart['Ram']]
    rom = [x for x in flipcart['Storage']]
    price = [x for x in flipcart['Flipcart_Price']]
    Flipcart.objects.all().delete()
    for i in range(len(name)):
        Flipcart.objects.create(
            name=name[i],
            color=color[i],
            ram=ram[i],
            rom=rom[i],
            price=price[i]
        )
    return


def amazon_scrap(search, size):
    multi_pages = []
    for i in range(int(size)):
        print("Fetching Page", i + 1)
        page_url = "https://www.amazon.in/s?k=" + search.lower() + "&page=" + str(i)
        page_location = amazon_fetch_page(page_url)
        while len(page_location) == 0:
            page_location = amazon_fetch_page(page_url)
        multi_pages.append(page_location)

    data_sample = []
    for each_location in multi_pages:
        for src in each_location:
            source = src.find("span", {"class": "a-size-medium a-color-base a-text-normal"}).text.split(")")[0]
            name = source.split("(")[0].strip()
            if len(name) > 35:
                continue

            if search.upper() not in name.upper():
                continue
            try:
                spec = source.split("(")[1].strip().split(",")
                color = spec[0]
                ram = re.search(r'\d+', spec[1]).group()
                rom = re.search(r'\d+', spec[2]).group()
            except(IndexError, AttributeError):
                continue
            try:
                price = src.find("span", {"class": "a-offscreen"}).text.replace("₹", "")
            except AttributeError:
                continue
            in_data = [name.upper(), color.upper(), ram, rom, int(price.replace(",", ""))]
            data_sample.append(in_data)
    df_sample = pd.DataFrame(data_sample)
    df_sample.columns = ["Mobile", "Colour", "Ram", "Storage", "Amazon_Price"]
    df_sample.drop_duplicates(subset=['Mobile', 'Colour'], inplace=True)
    amazon = df_sample
    amazon.to_csv('download_amazon.csv', index=False)
    print(amazon.count())
    save_to_amazon_db(amazon)
    return amazon_dataset()


def save_to_amazon_db(amazon):
    name = [x for x in amazon['Mobile']]
    color = [x for x in amazon['Colour']]
    ram = [x for x in amazon['Ram']]
    rom = [x for x in amazon['Storage']]
    price = [x for x in amazon['Amazon_Price']]
    Amazon.objects.all().delete()
    for i in range(len(name)):
        Amazon.objects.create(
            name=name[i],
            color=color[i],
            ram=ram[i],
            rom=rom[i],
            price=price[i]
        )
    return


def amazon_dataset():
    amazon_result = {"amazon_result": Amazon.objects.all()}
    return amazon_result


def flipcart_dataset():
    flipcart_result = {"flipcart_result": Flipcart.objects.all()}
    return flipcart_result


def compared_dataset():
    compared_result = {"compared_result": Compare.objects.all()}
    return compared_result


def compare(request):
    compared_result = {}
    if request.method == "POST":
        amazon_result = (amazon_compare(search=(request.POST['search']), size=request.POST['page_size']))
        flipcart_result = (flipcart_compare(search=(request.POST['search']), size=request.POST['page_size']))
        compared_db = pd.merge(amazon_result, flipcart_result, how='inner')
        compared_db["Price_Difference"] = abs(compared_db["Amazon_Price"] - compared_db["Flipcart_Price"])
        print(compared_db)
        save_to_compared_db(compared_db)
        compared_db.to_csv("download_compared.csv", index=False)
        compared_result = compared_dataset()
    return render(request, "compare.html", compared_result)


def save_to_compared_db(compared_result):
    name = [x for x in compared_result['Mobile']]
    color = [x for x in compared_result['Colour']]
    ram = [x for x in compared_result['Ram']]
    rom = [x for x in compared_result['Storage']]
    amazon_price = [x for x in compared_result['Amazon_Price']]
    flipcart_price = [x for x in compared_result['Flipcart_Price']]
    diff = [x for x in compared_result['Price_Difference']]

    Compare.objects.all().delete()
    for i in range(len(name)):
        Compare.objects.create(
            name=name[i],
            color=color[i],
            ram=ram[i],
            rom=rom[i],
            amazon_price=amazon_price[i],
            flipcart_price=flipcart_price[i],
            diff=diff[i]
        )
    return


def amazon_compare(search, size):
    multi_pages = []
    for i in range(int(size)):
        print("Fetching Page", i + 1)
        page_url = "https://www.amazon.in/s?k=" + search.lower() + "&page=" + str(i)
        page_location = amazon_fetch_page(page_url)
        while len(page_location) == 0:
            page_location = amazon_fetch_page(page_url)
        multi_pages.append(page_location)

    data_sample = []
    for each_location in multi_pages:
        for src in each_location:
            source = src.find("span", {"class": "a-size-medium a-color-base a-text-normal"}).text.split(")")[0]
            name = source.split("(")[0].strip()
            if len(name) > 35:
                continue

            if search.upper() not in name.upper():
                continue
            try:
                spec = source.split("(")[1].strip().split(",")
                color = spec[0]
                ram = re.search(r'\d+', spec[1]).group()
                rom = re.search(r'\d+', spec[2]).group()
            except(IndexError, AttributeError):
                continue
            try:
                price = src.find("span", {"class": "a-offscreen"}).text.replace("₹", "")
            except AttributeError:
                continue
            in_data = [name.upper(), color.upper(), ram, rom, int(price.replace(",", ""))]
            data_sample.append(in_data)
    df_sample = pd.DataFrame(data_sample)
    df_sample.columns = ["Mobile", "Colour", "Ram", "Storage", "Amazon_Price"]
    df_sample.drop_duplicates(subset=['Mobile', 'Colour'], inplace=True)
    amazon = df_sample
    return amazon


def flipcart_compare(search, size):
    multi_pages = []
    for i in range(int(size)):
        print("Fetching Page", i + 1)
        page_url = "https://www.flipkart.com/search?q=" + search.lower() + "&page=" + str(i)
        page_location = flipcart_fetch_page(page_url)
        while len(page_location) == 0:
            print("in While")
            page_location = flipcart_fetch_page(page_url)
        multi_pages.append(page_location)
    print("...Completed...")

    data_sample = []
    for multi_location in multi_pages:
        for src in multi_location:
            source = src.find("div", {"class": "_4rR01T"}).text
            name = source.split("(")[0].strip().upper()
            if len(name) > 35:
                continue
            if "POWER BANK" in name:
                continue
            try:
                color = source.split("(")[1].replace(")", "").strip().split(",")[0].strip().upper()
                ram = re.search(r'\d+',
                                src.find("div", {"class": "fMghEO"}).find_all("li", {"class": "rgWa7D"})[0].text.split(
                                    "|")[0].strip()).group()
                rom = re.search(r'\d+',
                                src.find("div", {"class": "fMghEO"}).find_all("li", {"class": "rgWa7D"})[0].text.split(
                                    "|")[1].strip()).group()
            except(IndexError, AttributeError):
                continue

            try:
                price = src.find("div", {"class": "_3tbKJL"}).text[1:].split("₹")[0].replace(",", "")
            except AttributeError:
                continue
            in_data = [name, color, ram, rom, int(price)]
            data_sample.append(in_data)
    df_sample = pd.DataFrame(data_sample)
    df_sample.columns = ["Mobile", "Colour", "Ram", "Storage", "Flipcart_Price"]
    df_sample.drop_duplicates(subset=['Mobile', 'Colour'], inplace=True)
    flipcart = df_sample
    return flipcart


def download_compared(request):
    response = HttpResponse(open('download_compared.csv', 'rb').read(), content_type='text/csv')
    response['Content-Length'] = os.path.getsize('download_compared.csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % 'download_compared.csv'
    return response


def download_amazon(request):
    response = HttpResponse(open('download_amazon.csv', 'rb').read(), content_type='text/csv')
    response['Content-Length'] = os.path.getsize('download_amazon.csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % 'download_amazon.csv'
    return response


def download_flipcart(request):
    response = HttpResponse(open('download_flipcart.csv', 'rb').read(), content_type='text/csv')
    response['Content-Length'] = os.path.getsize('download_flipcart.csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % 'download_flipcart.csv'
    return response
