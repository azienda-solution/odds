
import os
import time
import requests
import pandas as pd
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from datetime import datetime, timedelta

from function import add_row_sheet, append_new_line, array_to_csv_string, check_fitness_state, extract_content, fing_google, flashscore_player, remove_accents, scrap_selenium, scrap_selenium_v1

    
GPT_CONFIG_FR_NAMES = '''Ok chat, you are an intelligent text processor that can extract names of athletes from a block of text.

Your task is to carefully analyze the text and return only the unique names of the players mentioned in an array format. The output should be an array of names in the following format: ['name player one', 'name player two', ...].

Make sure to:
- Ignore any non-player-related information like URLs or titles.
- Properly format the names by trimming any extra whitespace and separating first names from last names.
- If any name contains numbers or extra characters (like 'Merino88'), return just the name without the numbers or extra characters (e.g., 'Merino').
- Ensure that each player's name appears only once in the array (no duplicates).

Now, analyze the text below and extract the unique player names.

TEXT:
'''


GPT_CONFIG_FR = '''Ok chat, you are a sports analyst who determines the fitness state of athletes based on the information you receive from texts.

Given the following text about a handball player, your task is to analyze it and classify the player's fitness state into one of these three categories:
- 'fit' (if the player is healthy and performing well),
- 'neutral' (if there is no clear indication about the player's fitness),
- 'injury' (if there is an indication of an injury or absence from the game or a important problem ).

After determining the state, provide a brief explanation summarizing why you classified the player's fitness this way, based on the details in the text.

Now, analyze the text below and return the fitness state of the player.

TEXT:
'''


import requests
import json

def get_gpt_response_name(title):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": OPENAI_KEY
    }
    data = {
        "model": "gpt-3.5-turbo-1106",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": GPT_CONFIG_FR_NAMES + title}
        ],
        "temperature": 0.7
    }

    try:
        # Send request to OpenAI API
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()  # Check for HTTP errors

        # Parse the response to JSON
        response_json = response.json()

        # Extract the content from the response
        content = response_json['choices'][0]['message']['content']

        # Remove markdown formatting (triple backticks and "json" keyword)
        if content.startswith("```json") and content.endswith("```"):
            content = content.strip("```json").strip("```")

        # Unescape characters like \n, \", etc.
        unescaped_content = content.encode('utf-8').decode('unicode_escape')
        content_json = json.loads(unescaped_content)

        return content_json['playerNames']  # Return the array of player names

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing response: {e}")
        return None


def get_gpt_response(title):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": OPENAI_KEY
    }
    data = {
        "model": "gpt-3.5-turbo-1106",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": GPT_CONFIG_FR + title}
        ],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=data, timeout=30)
    response_json = response.json()
    try:
        content = response_json['choices'][0]['message']['content']
        content_json = json.loads(content)
        fitness_state = content_json.get("fitness_state", "neutral")
        explanation = content_json.get("explanation", "No explanation provided.")
        
        return fitness_state, explanation
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing response: {e}")
        return None, None


def download_and_read_excel(sheet_url):
    try:
        # Send a GET request to download the Excel file
        response = requests.get(sheet_url)
        if response.status_code == 200:
            excel_data = pd.read_excel(BytesIO(response.content), engine='openpyxl', header=0) 
            #print("Columns detected:", excel_data.columns)
            filtered_data = excel_data.dropna(how='all', axis=1)  # Removes columns with all NaN values
            
            return filtered_data
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

def search_player_by_team(driver, team, country, sport):
    dicts = []
    list_player_home = flashscore_player(driver, team, country, sport)
    
    if len(list_player_home) < 2:
        google_query = f'List Player of {team} {sport} {country}'
        html_list_player_home = fing_google(driver, google_query)
        list_player_home = get_gpt_response_name(html_list_player_home)
        
    if list_player_home:
        for pla in list_player_home:
            pla = remove_accents(pla)
            today = datetime.today().strftime('%Y-%m-%d')
            one_week_ago = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
            google_query = f'"{pla}" "{team}" "{sport}" "news" after:{one_week_ago} before:{today}'
            html_content_by_player = fing_google(driver, google_query)
            state_by_player, explain = get_gpt_response(html_content_by_player)
            if state_by_player:
                fitness_state = check_fitness_state(state_by_player)
                var_intermediare = pla + " -- " + fitness_state
                dicts.append(str(var_intermediare))
                
    return dicts
    
def search_by_game(driver, filtered_sheet, ia_xlsx):
    final_result = []
    for index, row in filtered_sheet.iterrows():
        home = row['home']
        away = row['away']
        sport = row['sport']
        country_home = row['country_home'] if 'country_home' in row else ''
        country_away = row['country_away'] if 'country_away' in row else ''
        lang_home = row['lang_home'] if 'lang_home' in row else ''
        lang_away = row['lang_away'] if 'lang_away' in row else ''
        list_player_home = search_player_by_team(driver, home, country_home, sport)
        #add_row_sheet(ia_xlsx, [home, sport, country_home])
        #add_row_sheet(ia_xlsx, list_player_home)
        append_new_line('ia.csv', str(array_to_csv_string([home, sport, country_home])))
        append_new_line('ia.csv', str(array_to_csv_string(list_player_home)))
        list_player_away = search_player_by_team(driver, away, country_away, sport)
        #add_row_sheet(ia_xlsx, [away, sport, country_away])
        #add_row_sheet(ia_xlsx, list_player_away)
        append_new_line('ia.csv', str(array_to_csv_string([away, sport, country_away])))
        append_new_line('ia.csv', str(array_to_csv_string(list_player_away)))
    
    
driver = scrap_selenium_v1()
def run():
    ia_xlsx = "ia.xlsx"
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSGRlwEXjLOMxHbVSMIWTypXa6lyM-uATIWPOjJbSSKwBERV2zXJe4Hn3xSsFwoI9W4bJmRhqwZyrH3/pub?output=xlsx"
    filtered_sheet = download_and_read_excel(sheet_url)
    search_by_game(driver, filtered_sheet, ia_xlsx)
    
        
        
        
        
run()