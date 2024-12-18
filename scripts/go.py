from datetime import datetime, timedelta
import json
import os
import pandas as pd
import requests
from selenium.webdriver.common.by import By
import random

from function import american_to_european_odds, append_new_line, calcul_diff, check_exists_by_xpath, check_price_difference, check_price_difference_onfileJson, oddsportal, clean_url, convert_to_number, convet_to_european_odds, fetch_all_sports, fetch_odds, get_all_a_link_in_tag, json_to_csv, json_to_excel, json_to_excel_all, merge_result, oddspedia, parse_html, save_to_excel, scrap_selenium, tryAndRetryClickXpath, waitloading

# Get today's date
today = datetime.today()
day_today = today.day
month_today = today.month

def by_json():
    with open('eu.json', encoding='utf-8') as f:
        d = json.load(f)
    data = d

    # Appel de la fonction
    price_difference_results = check_price_difference(data)
    df = pd.DataFrame(price_difference_results)

    # Affichage du DataFrame
    print(df)
    
def on_web(webiste='https://sportsbook-odds-comparer.vercel.app/'):
        SELECTIONS = []
        driver = scrap_selenium()
        driver.get(webiste)
        waitloading(1, driver=driver)
    #if check_exists_by_xpath(driver, '//nav//svg') == 0:
        #tryAndRetryClickXpath(driver, '//svg[1]')
        input('please open side bar')
        a_links = get_all_a_link_in_tag(driver, "//div[contains(@class, 'scroll')]//a[contains(@href, 'odds')]", 'href')
        append_new_line(r'Liens_pages.txt', str(a_links))
        for page in a_links:
            if len(SELECTIONS) > 0:
                filename = f"{page}-{day_today:02d}-{month_today:02d}.csv"
                json_to_csv(SELECTIONS,   clean_url(filename))
            driver.get(page)
            waitloading(3, driver=driver)
            if check_exists_by_xpath(driver, '//h1') == 0:
                print(str(page))
            else:
                waitloading(3, driver=driver)
                
            matches = driver.find_elements(By.CLASS_NAME, "m-5")
            for match in matches:
                try:
                    home_team = match.find_element(By.XPATH, "./div[contains(@class, 'p-3')][1]//span[1]").text
                    away_team = match.find_element(By.XPATH, "./div[contains(@class, 'p-3')][2]//span[1]").text
                    date = match.find_element(By.TAG_NAME, "p").text

                    home_odds_container = match.find_elements(By.XPATH, ".//div[contains(@class, 'p-3')][1]//div[@data-cy='odds-ml-item']")
                    away_odds_container = match.find_elements(By.XPATH, ".//div[contains(@class, 'p-3')][2]//div[@data-cy='odds-ml-item']")
                    
                    bookmakers = []

                    for odds in home_odds_container:
                        try:
                            bookmaker = odds.find_elements(By.TAG_NAME, "span")[2].text
                            home_team_odds = odds.find_elements(By.TAG_NAME, "span")[0].text
                            away_team_odds = next((o.find_elements(By.TAG_NAME, "span")[0].text for o in away_odds_container if o.find_elements(By.TAG_NAME, "span")[2].text == bookmaker), None)
                            difference = 0
                            if away_team_odds:
                                difference = calcul_diff(convert_to_number(home_team_odds), convert_to_number(away_team_odds) )
                                bookmakers.append({
                                    "title": bookmaker,
                                    "outcomes": [
                                        {"name": home_team, "odds": convet_to_european_odds(convert_to_number(home_team_odds))},
                                        {"name": away_team, "odds": convet_to_european_odds(convert_to_number(away_team_odds))},
                                        {"difference": difference}
                                    ]
                                })
                        except IndexError:
                            print('--------------------------Odds problem -----------')
                            append_new_line(r'Log-a-voir.txt', str(home_team)+' ; '+str(away_team))
                            continue

                    SELECTIONS.append({
                        "home_team": home_team,
                        "away_team": away_team,
                        "date": date,
                        "bookmakers": bookmakers
                    })
                except Exception as e:
                    # Log the exception or handle it as needed
                    print(f"Error processing match: {e}")
                    print('--------------------------Odds problem -----------')
                    continue
    
    
        random_name = f"matches-{day_today:02d}-{month_today:02d}-{random.randint(50, 250)}"
        json_to_excel(SELECTIONS, random_name+'.xlsx')
        json_to_csv(SELECTIONS, random_name+'.csv')
        
#on_web()

    


def convert():
    today_date = datetime.now().strftime('%Y-%m-%d')
    random_name = f"all-{day_today:02d}-{month_today:02d}-{random.randint(50, 250)}"
    file_path = os.path.join('daily_data', str(today_date), f'{today_date}.json')
    with open(file_path, encoding='utf-8') as f:
        SELECTIONS = json.load(f)
        
    
    price_difference_results = check_price_difference_onfileJson(SELECTIONS)
    df = pd.DataFrame(price_difference_results)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    print(df)



def main():
    
    sports = fetch_all_sports()
    if not sports:
        return
    
    all_odds = {}
    
    for sport in sports:
        sport_key = sport['key']
        odds = fetch_odds(sport_key)
        if odds:
            all_odds[sport_key] = odds
    
    # Save all odds to a JSON file
    with open('all_sports_odds.json', 'w') as f:
        json.dump(all_odds, f, indent=4)
    
    print("Odds data has been successfully saved to all_sports_odds.json")
    
#main()

    
def lucksport_1x2_mmatch():
        
    file_path = 'daily_data/111.html'
    excel_file = 'games.xlsx'

    games = parse_html(file_path)
    save_to_excel(games, excel_file)
    print('53')
    
def three_func():
    
    """
    
1. Allez sur le site [1x2 Lucksport](https://1x2.lucksport.com/com_index_en.shtml?cid=740).
2. Copiez le HTML extérieur de la div avec `id="odds_tb"`.
3. Collez-le dans le fichier `daily_data/111.html`.
    
    
    
1. Allez sur le site [oddsportal](https://www.oddsportal.com/matches/football/).
2. Scrollez et charger tous les matchs
3. Copiez avec la souris le 1er match qui n'a pas encore commencé au dernier match 


1- Va sur le site [https://oddspedia.com/](https://oddspedia.com/)
2. Scrollez et charger tous les matchs et mettre "ALL BOOKMAKER"
3. Copier la div <main class="content-inner"> TOUS LES SPORTS POSSIBLES
    
    """
        
    file_path = 'daily_data/111.html'
    file_txt = 'daily_data/oddsportal.txt'
    file_html = 'daily_data/oddspedia.html'
    excel_file = 'games.xlsx'


    games = parse_html(file_path)
    game_oddspedia = oddspedia(file_html)
    game_oddsportal = oddsportal(file_txt)
    

    result = []
    result = merge_result(result, games)
    result = merge_result(result, game_oddsportal)
    result = merge_result(result, game_oddspedia)
    
    
    save_to_excel(result, excel_file)
    print('53')
"""

env.py i can change DIFFERENC = 7

1 run just main() for get all upcoming by sport, after run convert()


2 Run on_web() for just scrap all page on https://sportsbook-odds-comparer.vercel.app and prepare bet 
  Check Result in file matches- .... .csv
  
  
3   Run five.py for get just next 24 hours and print 


4 Run 
    1- Go on the website https://1x2.lucksport.com/com_index_en.shtml?cid=740 .
    2- copy div id="odds_tb" outer html
    3- paste on file daily_data / 111.html
    4- RUN lucksport_1x2_mmatch() for export match and odds from https://1x2.lucksport.com/com_index_en.shtml?cid=740

"""

lucksport_1x2_mmatch()