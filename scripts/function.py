   
import mimetypes
import os
import re
from urllib.request import urlopen
import requests
import pandas as pd
from bs4 import BeautifulSoup
import openpyxl

from logging import exception
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import InvalidSelectorException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import Select
from webdriver_manager.firefox import GeckoDriverManager
################

import sys
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from datetime import datetime

from env import API_KEY, BASE_URL, COMMENCE_TIME_FROM, COMMENCE_TIME_TO, DIFFERENC, MARKETS, REGIONS

def append_new_line(file_name, text_to_append):
    # Check if the directory exists, if not, create it
    directory = os.path.dirname(file_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Append the new line to the file
    with open(file_name, "a+", encoding="utf-8", errors="ignore") as file_object:
        file_object.seek(0)
        data = file_object.read(100)
        if len(data) > 0:
            file_object.write("\n")
        file_object.write(text_to_append)
        
def can_open_yt(url):
    try:
        res = requests.get(url, timeout=10)
        resp = urlopen(url)
        return True
    except Exception as e:
        print(e)
        return False
    
    
# fonction pour donner du délai et cliquer les xpath
def waitBeforeClickOnXpath(driver, xPath):
    time.sleep(1)
    print("clicking on " + xPath + "...")
    button = driver.find_element(By.XPATH, xPath)
    driver.execute_script("arguments[0].click();", button)
    time.sleep(1)
    print("Continue the script")

def waitBeforeClickOnClass(driver, className):
    print("waiting page loading")
    time.sleep(3)
    print("clicking on " + className + "...")
    button = driver.find_element(By.CLASS_NAME, className)
    driver.execute_script("arguments[0].click();", button)
    print("button clicked")
    print("now waiting server response..")
    time.sleep(3)
    print("Continue the script")

def waitBeforeClickOnId(driver, id):
    print("waiting page loading")
    time.sleep(3)
    print("clicking on " + id + "...")
    button = driver.find_element(By.ID, id)
    driver.execute_script("arguments[0].click();", button)
    print("button clicked")
    print("now waiting server response..")
    time.sleep(3)
    print("Continue the script")

# rempli de texte la case formulaire avec l'id correspondant
def fillById(driver, id, filler):
    print("waiting page loading")
    time.sleep(3)
    driver.find_element(By.ID, id).send_keys(filler)
    print("form filled")
    print("now waiting server response..")
    time.sleep(3)
    print("Continue the script")

def fillByIdWithSteps(driver, id ,filler):
    print("waiting page loading")
    time.sleep(3)
    driver.find_element(By.ID, id).send_keys(Keys.CONTROL + "a")
    print("Taking all that already exist")
    time.sleep(1)
    driver.find_element(By.ID, id).send_keys(Keys.DELETE)
    print("Cleaning")
    time.sleep(1)
    driver.find_element(By.ID, id).send_keys(filler)
    print("Fill with our value")
    time.sleep(1)
    print("Complete")
    print("now waiting server response..")
    time.sleep(3)
    print("Continue the script")

def fillByClass(driver, clss ,filler):
    print("waiting page loading")
    time.sleep(3)
    element = driver.find_element_by_class_name(clss).click()
    time.sleep(1)
    element.send_keys(filler)
    print("Fill with our value")
    time.sleep(1)
    print("Complete")
    print("now waiting server response..")
    time.sleep(3)
    print("Continue the script")

def fillByXpath(driver, xpath, filler):
    print("waiting page loading")
    time.sleep(3)
    driver.find_element(By.XPATH, xpath).send_keys(filler)
    time.sleep(3)
    print("Continue the script")

def tryAndRetryClickXpath(driver, xPath):
    try : 
        waitBeforeClickOnXpath(driver, xPath)
    except NoSuchElementException:
        print("the element needs to be charged...")
        time.sleep(10)
        waitBeforeClickOnXpath(driver, xPath)

def tryAndRetryClickClassName(class_name):
    try : 
        waitBeforeClickOnClass(class_name)
    except NoSuchElementException:
        print("the element needs to be charged...")
        time.sleep(10)
        waitBeforeClickOnClass(class_name)

def tryAndRetryClickID(driver, id):
    try : 
        waitBeforeClickOnClass(driver, id)
    except NoSuchElementException:
        print("the element needs to be charged...")
        time.sleep(10)
        waitBeforeClickOnClass(driver, id)


def tryAndRetryFillById(driver, id, value):
    try:
        fillById(driver,id, value)
    except NoSuchElementException:
        print("the element needs to be charged...")
        time.sleep(10)
        fillById(driver,id, value)

def tryAndRetryFillByIdWithSteps(driver, idStep1, id, value):
    try:
        button = driver.find_element(By.ID, idStep1)
        driver.execute_script("arguments[0].click();", button)
        fillById(id, value)
    except NoSuchElementException:
        button = driver.find_element(By.ID, idStep1)
        driver.execute_script("arguments[0].click();", button)
        print("the element needs to be charged...")
        time.sleep(10)
        fillById(id, value)
    except ElementNotInteractableException:
        button = driver.find_element(By.ID, idStep1)
        driver.execute_script("arguments[0].click();", button)
        print("the element needs to be charged...")
        time.sleep(10)
        fillById(id, value)

def writeLetterByLetterId(driver, id, word):
    print("waiting page loading")
    time.sleep(3)
    driver.find_element(By.ID, id).send_keys(Keys.CONTROL + "a")
    print("Taking all that already exist")
    time.sleep(1)
    driver.find_element(By.ID, id).send_keys(Keys.DELETE)
    print("Cleaning")
    for i in word:
        driver.find_element(By.ID, id).send_keys(i)
        
def getinnertextXpath(driver, xPath):
    try:
        result = ""
        result = driver.find_element(By.XPATH, xPath)
        result = (result.get_attribute('innerText'))
    except NoSuchElementException:  #spelling error making this code not work as expected
        result = "ZZZZZZZZZZZ"
        pass
    return str(result)


    
def tryAndRetryFillByIdWithExtraSteps(driver, idStep1, id, value):
    try:
        button = driver.find_element(By.ID, idStep1)
        driver.execute_script("arguments[0].click();", button)
        writeLetterByLetterId(id, value)
    except NoSuchElementException:
        button = driver.find_element(By.ID, idStep1)
        driver.execute_script("arguments[0].click();", button)
        print("the element needs to be charged...")
        time.sleep(10)
        writeLetterByLetterId(id, value)
    except ElementNotInteractableException:
        button = driver.find_element(By.ID, idStep1)
        driver.execute_script("arguments[0].click();", button)
        print("the element needs to be charged...")
        time.sleep(10)
        writeLetterByLetterId(id, value)

def tryAndRetryFillByXpath(driver, xpath, value):
    try:
        fillByXpath(driver, xpath, value)
    except NoSuchElementException:
        print("the element needs to be charged...")
        time.sleep(5)
        tryAndRetryFillByXpath(driver, xpath, value)

def if_as_value_FillByXpath(driver, xpath, value):
    if(len(value) > 2):
        try:
            fillByXpath(driver, xpath, value)
        except NoSuchElementException:
            pass
    else:
        pass

    
    
def american_to_european_odds(american_odds):
    if american_odds < 0:
        return 1 + (100 / abs(american_odds))
    else:
        return 1 + (american_odds / 100)
    
def check_price_difference(events):
    result = []
    for event in events:
        home_team = event["home_team"]
        away_team = event["away_team"]
        for bookmaker in event["bookmakers"]:
            for market in bookmaker["markets"]:
                outcomes = market["outcomes"]
                prices = []
                for outcome in outcomes:
                    price = outcome["price"]
                    # Vérifier le format des cotes et convertir si nécessaire
                    if price > -100 and price < 100:
                        prices.append(price)  # Cotes européennes
                    else:
                        prices.append(american_to_european_odds(price))  # Convertir les cotes américaines en cotes européennes
                
                if abs(prices[0] - prices[1]) > DIFFERENC:
                    result.append({
                        "home_team": home_team,
                        "away_team": away_team,
                        "bookmaker": bookmaker["title"],
                        "market": market["key"],
                        "home_team_price": prices[1],
                        "away_team_price": prices[0]
                    })
    return result


def download_video(url, save_path):
    # Send a GET request to the video URL
    response = requests.get(url, stream=True)
    
    # Raise an exception if the request was unsuccessful
    response.raise_for_status()
    
    # Get the Content-Type from the response headers
    content_type = response.headers.get('Content-Type')
    
    # Guess the file extension from the Content-Type
    extension = mimetypes.guess_extension(content_type) if content_type else '.mp4'
    
    # Get the video file name from the URL and ensure it has the correct extension
    video_filename = url.split('/')[-1].split('?')[0]
    if not video_filename.endswith(extension):
        video_filename += extension
    
    # Create the full path to save the video
    full_path = os.path.join(save_path, video_filename)
    directory = os.path.dirname(full_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Write the content of the response to a file
    with open(full_path, 'wb') as video_file:
        for chunk in response.iter_content(chunk_size=8192):
            video_file.write(chunk)
    
    # Return the path of the saved video
    return full_path

def get_content_type(file_name):
    mime_type, _ = mimetypes.guess_type(file_name)
    if mime_type is not None:
        return mime_type
    return 'application/octet-stream'

def get_extension_from_mime_type(mime_type):
    mime_to_extension = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'video/mp4': 'mp4',
        'video/webm': 'webm',
        'video/x-matroska': 'mkv',
        'video/x-msvideo': 'avi',
        'application/octet-stream': 'bin'
    }
    return mime_to_extension.get(mime_type, 'bin')

def convet_to_european_odds(_odd):
    if _odd > -100 and _odd < 100:
        _odd = _odd
    else:
        _odd = american_to_european_odds(_odd)
    return _odd

def calcul_diff(home_odd, away_odd):
    home_odd = convet_to_european_odds(home_odd)
    away_odd = convet_to_european_odds(away_odd)
    
    if home_odd and away_odd:
        difference = abs(home_odd - away_odd)
        return difference

def check_price_difference_onfileJson(events):
    result = []
    for sport_key, sport_events in events.items():
        for event in sport_events:
            home_team = event["home_team"]
            away_team = event["away_team"]
            for bookmaker in event["bookmakers"]:
                for market in bookmaker["markets"]:
                    outcomes = market["outcomes"]
                    prices = []
                    for outcome in outcomes:
                        price = outcome["price"]
                        # Vérifier le format des cotes et convertir si nécessaire
                        if price > -100 and price < 100:
                            prices.append(price)  # Cotes européennes
                        else:
                            prices.append(american_to_european_odds(price))  # Convertir les cotes américaines en cotes européennes
                    
                    if abs(prices[0] - prices[1]) > DIFFERENC:
                        result.append({
                            "home_team": home_team,
                            "away_team": away_team,
                            "bookmaker": bookmaker["title"],
                            "market": market["key"],
                            "home_team_price": prices[1],
                            "away_team_price": prices[0]
                        })
    return result

def initGoogle(driver):
    driver.get('https://www.google.com/')
    waitloading(4, driver=driver)
    cookieGoogle = driver.find_element(By.ID, 'L2AGLb').click()
    try:
        driver.find_element(By.CLASS_NAME, 'h-captcha')
    except NoSuchElementException:
        print("No captcha")

    if cookieGoogle:
        print("GOOGLE a changé l'id recupere le nouveau")
    else:
        print("Init Google...")
        
def waitloading(times, driver):
    times = int(times)
    time.sleep(times)
    wait = WebDriverWait(driver, times)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

def clear_element(driver, xpath):
    elem2 = driver.find_element(By.XPATH, xpath)
    driver.execute_script('arguments[0].value = "";', elem2)
    
def check_exists_by_xpath(driver, xpath):
    try:
        time.sleep(3)
        driver.find_element(By.XPATH, xpath)
        return 0
    except NoSuchElementException:
        return 1
    
def findATTR(driver, xpath, attr):
    try:
        value_attr = driver.find_element(By.XPATH, xpath)
        value_attr = value_attr.get_attribute(attr)
    except NoSuchElementException:
        value_attr = ' '
        pass
    return str(value_attr)

def get_all_a_link_in_tag(driver, xpath, attr):
    my_list = list()
    links = driver.find_elements(By.XPATH, xpath)
    for i in links:
        step1 = (i.get_attribute(attr))
        my_list.append(step1)
    return my_list

def clean_url(url):
    # Remove the protocol (http or https) and the domain
    cleaned_url = re.sub(r'^https?://[^/]+/', '', url)
    # Remove all slashes from the remaining part of the URL
    cleaned_url = cleaned_url.replace('/', '-')
    return cleaned_url

def json_to_excel(json_data, excel_file):
    # Aplatir les données JSON
    flattened_data = []
    for match in json_data:
        home_team = match["home_team"]
        away_team = match["away_team"]
        date = match["date"]
        for bookmaker in match["bookmakers"]:
            if len(bookmaker)> 0:
                bookmaker_title = bookmaker["title"]
                for outcome in bookmaker["outcomes"]:
                    flattened_data.append({
                        "home_team": home_team,
                        "away_team": away_team,
                        "date": date,
                        "bookmaker": bookmaker_title,
                        "outcome_name": outcome["name"]  if "name" in outcome else '',
                        "odds": outcome["odds"]  if "odds" in outcome else '',
                        "difference": outcome["difference"] if "difference" in outcome else ''
                    })
    
    # Convertir les données JSON aplaties en DataFrame pandas
    df = pd.DataFrame(flattened_data)
    
    # Enregistrer le DataFrame en fichier Excel
    df.to_excel(excel_file, index=False)
    
    print(f"Data successfully written to {excel_file}")
    
def json_to_csv(json_data, csv_file):
        # Aplatir les données JSON
    flattened_data = []
    for match in json_data:
        home_team = match["home_team"]
        away_team = match["away_team"]
        date = match["date"]
        for bookmaker in match["bookmakers"]:
            bookmaker_title = bookmaker["title"]
            for outcome in bookmaker["outcomes"]:
                flattened_data.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "date": date,
                    "bookmaker": bookmaker_title,
                    "outcome_name": outcome["name"]  if "name" in outcome else '',
                    "odds": outcome["odds"]  if "odds" in outcome else '',
                    "difference": outcome["difference"] if "difference" in outcome else ''
                })
    
    # Convertir les données JSON aplaties en DataFrame pandas
    df = pd.DataFrame(flattened_data)
    
    # Enregistrer le DataFrame en fichier CSV
    df.to_csv(csv_file, index=False)
    
    print(f"Data successfully written to {csv_file}")
    
    
def convert_to_number(text):
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return None
       
def fetch_odds(sport):
    url = f"{BASE_URL}{sport}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': 'american',
        'commenceTimeFrom': COMMENCE_TIME_FROM,
        'commenceTimeTo': COMMENCE_TIME_TO
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch odds for {sport}. Status code: {response.status_code}, Response: {response.text}")
        return None

# Fetching all sports
def fetch_all_sports():
    url = f"{BASE_URL}?apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch sports. Status code: {response.status_code}, Response: {response.text}")
        return None

def json_to_excel_all(json_data, excel_file):
    # A list to hold all the rows of data
    rows = []
    
    # Iterate through each sport in the JSON data
    for sport_key, games in json_data.items():
        for game in games:
            base_info = {
                "sport_key": game["sport_key"],
                "sport_title": game["sport_title"],
                "commence_time": game["commence_time"],
                "home_team": game["home_team"],
                "away_team": game["away_team"]
            }
            for bookmaker in game["bookmakers"]:
                for market in bookmaker["markets"]:
                    for outcome in market["outcomes"]:
                        row = {
                            **base_info,
                            "bookmaker_key": bookmaker["key"],
                            "bookmaker_title": bookmaker["title"],
                            "market_key": market["key"],
                            "outcome_name": outcome["name"],
                            "price": convet_to_european_odds(convert_to_number(outcome["price"]))
                        }
                        # Include point if it exists
                        if "point" in outcome:
                            row["point"] = outcome["point"]
                        else:
                            row["point"] = None
                        rows.append(row)
    
    # Convert list of rows to DataFrame
    df = pd.DataFrame(rows)
    
    # Save DataFrame to Excel file
    df.to_excel(excel_file, index=False)
    
    print(f"Data successfully written to {excel_file}")
    
def scrap_selenium():
    option = FirefoxOptions()
    option.add_argument('--disable-notifications')
    option.add_argument("--mute-audio")
    #option.add_argument("--headless")
    option.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1")
    
    driverinstance = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=option)
    driverinstance.set_page_load_timeout(12)
    driverinstance.maximize_window()
    initGoogle(driverinstance)
    waitloading(2, driver=driverinstance)
    return driverinstance


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

# Function to parse the HTML file and extract the data
def parse_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        
    games = []
    prints = []
    current_date = None
    match_info = {}
    today_date = datetime.now().strftime('%Y-%m-%d')

    for row in soup.select('#odds_tb tr'):
        cells = row.find_all('td')
        
        # Check for date row
        if len(cells) == 1 and 'colspan' in cells[0].attrs:
            current_date = cells[0].get_text(strip=True)
            print(f"Found date: {current_date}")
            continue
        
        # Process match rows
        if len(cells) == 8:
            initial_odds_home = cells[3].get_text(strip=True)
            initial_draw_odds = cells[4].get_text(strip=True)
            initial_odds_away = cells[5].get_text(strip=True)
            
            if is_float(initial_odds_home) and is_float(initial_draw_odds) and is_float(initial_odds_away):
                match_info = {
                    'home_team': cells[2].get_text(strip=True),
                    'away_team': cells[6].get_text(strip=True),
                    'date': current_date,
                    'initial_odds_home': float(initial_odds_home),
                    'initial_draw_odds': float(initial_draw_odds),
                    'initial_odds_away': float(initial_odds_away),
                    'initial_difference': abs(float(initial_odds_home) - float(initial_odds_away))
                }
                #print(f"Initial match info: {match_info}")
        
        # Process odds update rows
        elif len(cells) == 3 and match_info:
            actual_odds_home = cells[0].get_text(strip=True)
            draw_odds_actual = cells[1].get_text(strip=True)
            actual_odds_away = cells[2].get_text(strip=True)
            
            if is_float(actual_odds_home) and is_float(draw_odds_actual) and is_float(actual_odds_away):
                match_info.update({
                    'actual_odds_home': float(actual_odds_home),
                    'draw_odds_actual': float(draw_odds_actual),
                    'actual_odds_away': float(actual_odds_away),
                    'actual_difference': abs(float(actual_odds_home) - float(actual_odds_away))
                })
                if match_info["initial_difference"] > DIFFERENC or match_info["actual_difference"] > DIFFERENC:
                    prints.append(match_info.copy())
                games.append(match_info.copy())  # Use copy to ensure we don't overwrite previous entries
                #print(f"Updated match info: {match_info}")
                match_info = {}  # Reset match_info for the next match
    
    print(f"Total games found: {len(games)}")
    if len(prints) > 0:
        df = pd.DataFrame(prints)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        # Affichage du DataFrame
        print(df)
        file_path = os.path.join('daily_data', str(today_date), f'{today_date}.txt')
        append_new_line(file_path, str(df))
    return games

# Function to save the data to an Excel sheet
"""def save_to_excel(games, excel_file):
    # Convert the list of games to a DataFrame
    df = pd.DataFrame(games)
    
    # Get today's date
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    # Load the workbook if it exists, otherwise create a new one
    try:
        workbook = openpyxl.load_workbook(excel_file)
        sheetnames = workbook.sheetnames
    except FileNotFoundError:
        workbook = None
        sheetnames = []
    
    # Check if the sheet with today's date already exists
    sheet_name = today_date
    counter = 1
    while sheet_name in sheetnames:
        sheet_name = f"{today_date}_{counter}"
        counter += 1

    # Write the DataFrame to the Excel file
    if workbook:
        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a') as writer:
            writer.book = workbook
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)"""
            
def save_to_excel(games, excel_file):
    # Convert the list of games to a DataFrame
    df = pd.DataFrame(games)
    
    # Get today's date
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    # Write the DataFrame to an Excel file
    try:
        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a') as writer:
            df.to_excel(writer, sheet_name=today_date, index=False)
    except Exception as e:
        print(e)
        today_date = str(today_date) + '-1'
        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a') as writer:
            df.to_excel(writer, sheet_name=today_date, index=False)
