
import pandas as pd
from datetime import datetime, timedelta

import requests

from env import API_KEY, COMMENCE_TIME_FROM, COMMENCE_TIME_TO

# List of URLs to fetch data from
urls = [
    f'https://api.the-odds-api.com/v4/sports/upcoming/odds/?regions=eu&markets=h2h&apiKey={API_KEY}&commenceTimeFrom={COMMENCE_TIME_FROM}&commenceTimeTo={COMMENCE_TIME_TO}',
    f'https://api.the-odds-api.com/v4/sports/upcoming/odds/?regions=us&markets=h2h&oddsFormat=american&apiKey={API_KEY}&commenceTimeFrom={COMMENCE_TIME_FROM}&commenceTimeTo={COMMENCE_TIME_TO}',
    f'https://api.the-odds-api.com/v4/sports/upcoming/odds/?regions=uk&markets=h2h&apiKey={API_KEY}&commenceTimeFrom={COMMENCE_TIME_FROM}&commenceTimeTo={COMMENCE_TIME_TO}',
    f'https://api.the-odds-api.com/v4/sports/upcoming/odds/?regions=au&markets=h2h&apiKey={API_KEY}&commenceTimeFrom={COMMENCE_TIME_FROM}&commenceTimeTo={COMMENCE_TIME_TO}'
]

def fetch_data_from_urls(urls):
    all_data = []

    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Will raise an HTTPError for bad responses
            data = response.json()
            all_data.extend(data)
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data from {url}. Error: {e}")

    return all_data

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
                
                if abs(prices[0] - prices[1]) > 7:
                    result.append({
                        "home_team": home_team,
                        "away_team": away_team,
                        "bookmaker": bookmaker["title"],
                        "market": market["key"],
                        "home_team_price": prices[1],
                        "away_team_price": prices[0]
                    })
    return result


def main():
    all_data = fetch_data_from_urls(urls)
    """for item in all_data:
        print(item)"""
        
    # Appel de la fonction
    price_difference_results = check_price_difference(all_data)
    df = pd.DataFrame(price_difference_results)

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    # Affichage du DataFrame
    print(df)
    
if __name__ == '__main__':
    main()
    print('5')
