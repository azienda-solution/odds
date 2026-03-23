
import re
import time
from function import analys_per_link, append_new_line, callAi, check_and_refresh, clean_html_and_return_innertext, clean_text, click_consent, compute_understandy, convert_sheet_csv_read_excel, extract_list_from_google, forebet, forebet_per_page, forebet_scrap, forebet_scrap_trend, get_gpt_response_name, last_line_simple, safe_odds_from_pct_str, save_to_excel, scrap_selenium_v1, cleaner, waitloading
from upload_drive import upload_file_to_drive, upload_text_file_to_drive
import argparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import unquote
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains


def xpath_literal(s: str) -> str:
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'
    parts = s.split("'")
    # concat('a', "'", 'b', "'", 'c')
    return "concat(" + ", ".join(sum(([f"'{p}'", "\"'\""] for p in parts[:-1]), []) + [f"'{parts[-1]}'"]) + ")"

def build_team_hints(first_word: str):
    # ex: 'sc-freiburg' -> ['sc freiburg', 'freiburg', 'sc']
    raw = unquote(first_word).strip()
    base = re.sub(r"[_\-]+", " ", raw).strip()
    parts = [p for p in base.split() if p]
    hints = []
    if base:
        hints.append(base)
    if parts:
        # token le plus long en priorité (souvent le nom distinctif)
        parts_sorted = sorted(parts, key=len, reverse=True)
        hints += parts_sorted
    # dédoublonner en gardant l'ordre
    seen = set()
    uniq = []
    for h in hints:
        k = h.lower()
        if k not in seen:
            uniq.append(h)
            seen.add(k)
    return uniq

def ffunc(page=None):

    
    matches = []
    driver = scrap_selenium_v1("https://www.sofascore.com/")
    if page:
        print('done ')
    else:
        """ 
        
        1- Va sur le site https://www.forebet.com/en/football-tips-and-predictions-for-today
        2. Scrollez et charger tous les matchs et mettre "ALL BOOKMAKER"
        3. Copier la div <div class="schema"> TOUS LES SPORTS POSSIBLESPORTS POSSIBLES
            
        """
        allcontent = str("")
        waitloading(2, driver=driver)
        click_consent(driver, 'en')
        waitloading(2, driver=driver)
        click_consent(driver, 'en')
        waitloading(8, driver=driver)
        games = convert_sheet_csv_read_excel(last_line_simple("last-sheet-on-excel-IA.txt"), "IA_forebet.xlsx")
        for game in games:
            try:
                list_link = extract_list_from_google(driver, game['home_team'] + " "  + game['away_team'] + " "  + game['date']  + " "  + game['sport'] +" in sofascore.com", True)
                if len(list_link) > 1 :
                    if 'sofascore' in list_link[0] and 'match' in list_link[0]:
                        vote = " "
                        driver.get(list_link[0])
                        waitloading(4, driver=driver)
                        
                        try:
                            first_word = re.search(r'/match/([^-/#?]+)', list_link[0]).group(1)
                            team_hints = build_team_hints(first_word)

                            # XPath pour trouver le bouton de l’option dont l’img @alt contient le hint
                            # ET qui est dans la même "card-component" que la question "Qui va gagner"
                            # On neutralise casse + espaces (et insécable) côté texte question
                            question_predicate = (
                                "contains(translate(normalize-space(.), "
                                "'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ? ', "
                                "'abcdefghijklmnopqrstuvwxyzàâäçéèêëîïôöùûüÿ  '), "
                                "'Qui va gagner ?')"
                            )

                            # On va essayer plusieurs hints jusqu’à trouver un bouton cliquable
                            target_btn = None
                            last_xpath = None
                            wait = WebDriverWait(driver, 10)

                            for hint in team_hints:
                                hint_lit = xpath_literal(hint)
                                # comparaison insensible à la casse sur @alt via translate()
                                img_predicate = (
                                    f"contains(translate(@alt, "
                                    f"'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ', "
                                    f"'abcdefghijklmnopqrstuvwxyzàâäçéèêëîïôöùûüÿ'), "
                                    f"translate({hint_lit}, "
                                    f"'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ', "
                                    f"'abcdefghijklmnopqrstuvwxyzàâäçéèêëîïôöùûüÿ'))"
                                )

                                xpath = (
                                    "//div[contains(@class,'card-component')][.//span[" + question_predicate + "]]"
                                    f"//button[.//img[{img_predicate}]]"
                                )
                                last_xpath = xpath

                                try:
                                    # attendre présence de la carte (utile pour récupérer le texte plus tard)
                                    card = wait.until(EC.presence_of_element_located((
                                        By.XPATH, "//div[contains(@class,'card-component')][.//span[" + question_predicate + "]]"
                                    )))
                                    # scroll jusqu’à la carte
                                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)

                                    # attendre que le bouton avec l'image soit visible/cliquable
                                    btn = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
                                    # bouger la souris dessus pour déclencher tout hover éventuel
                                    try:
                                        ActionChains(driver).move_to_element(btn).perform()
                                    except Exception:
                                        pass

                                    target_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                                    try:
                                        target_btn.click()
                                    except Exception:
                                        driver.execute_script("arguments[0].click();", target_btn)

                                    # si on a cliqué sans exception, on sort de la boucle
                                    break

                                except TimeoutException as te:
                                    # on essaye le hint suivant
                                    continue

                            if target_btn is None:
                                # rien trouvé/cliqué — diagnostics utiles
                                print("DEBUG: aucun bouton trouvé. Dernier XPath testé:\n", last_xpath)
                                # Log des alts présents dans la carte pour comprendre quoi matcher
                                try:
                                    card = driver.find_element(By.XPATH,
                                        "//div[contains(@class,'card-component')][.//span[" + question_predicate + "]]"
                                    )
                                    alts = [e.get_attribute("alt") for e in card.find_elements(By.XPATH, ".//img[@alt]")]
                                    print("DEBUG: alts détectés dans la carte:", alts)
                                    print("DEBUG: team_hints utilisés:", team_hints)
                                except Exception as _:
                                    print("DEBUG: carte non trouvée non plus.")
                                raise TimeoutException("Impossible de localiser/clicker le bouton de l’équipe.")

                            # petite pause si l’UI met à jour le texte
                            time.sleep(0.5)

                            # récupérer le texte de la même carte
                            card = target_btn.find_element(By.XPATH, "ancestor::div[contains(@class,'card-component')][1]")
                            vote_text = card.text
                            vote = clean_text(vote_text)

                        except TimeoutException as e:
                            print(f"Timeout while waiting for element. Details: {e}")
                            # optionnel: capture d’écran pour diagnostiquer
                            try:
                                driver.save_screenshot("debug_vote.png")
                                print("DEBUG: screenshot saved to debug_vote.png")
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"Unexpected error: {type(e).__name__}: {e}")

                        """if vote and len(vote) < 5:
                            
                            try:
                                first_word = re.search(r'/match/([^-/#?]+)', list_link[0]).group(1)
                                try:
                                    xpath__s = f"//span[contains(normalize-space(.), 'Who will win')]/following::img[contains(@alt, '{first_word}')][1]"

                                    elem = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, xpath__s))
                                    )
                                    elem.click()
                                except Exception as e:
                                    print(f"An error 00022 occurred: {e}")
                                time.sleep(3)
                                xpath = ("//div[contains(@class,'card-component')][.//span["
                                        "contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
                                        "'Who will win')]]")

                                card = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                                vote = card.get_attribute("innerHTML")
                                vote = clean_text(vote)
                            except Exception as e:
                                print(f"An 222 error occurred: {e}")"""

                        if vote and len(vote) > 5:
                            promt = f"""
                                You are a parser. Read the TEXT below and output only a compact JSON object with:

                                ```json
                                {{
                                "home_probability": number | null,   // first percentage found (without %)
                                "draw_probability": number | null,   // percentage for draw if present (labels like "X", "Match nul", "Draw"); otherwise null
                                "away_probability": number | null,   // last percentage found (without %)
                                "vote_count": number | null          // total number of votes if present, else null
                                }}
                                Rules:

                                Percentages:
                                Extract only numbers that have a % sign.
                                The first % in reading order → home_probability.
                                If a draw percentage is present (labels such as "X", "Match nul", "Draw"), set draw_probability to that value; otherwise null.
                                The last % in reading order → away_probability.
                                Accept comma or dot decimals (e.g., "32,5%" → 32.5). Output numbers, no % sign.


                                Vote count:
                                Look for phrases like "Total des votes", "Total votes", "Votes", "Votants", "Vote(s)".
                                Extract the number next to that phrase. Accept formats with spaces/nbsp (e.g., "1 234"), and suffixes "k"/"K" (×1,000) or "m"/"M" (×1,000,000), e.g., "1.6k" → 1600, "2,3M" → 2300000.
                                If multiple candidates appear, use the last such occurrence in the TEXT.
                                Output vote_count as an integer. If not found, null.


                                Ignore any other numbers (e.g., IDs, times, ranks).
                                Output strict JSON only, with no extra commentary.

                                TEXT: {vote}
                                """
                            json_result = get_gpt_response_name(" ", promt)
                            if json_result:
                                if len(json_result) > 0:
                                    
                                    json_result["draw_probability"] = 0 if json_result["draw_probability"] in (None, "") else json_result["draw_probability"]
                                    understandy = compute_understandy(total_votes=json_result["vote_count"], home_pct=json_result["home_probability"], away_pct=json_result["away_probability"], draw_pct=json_result["draw_probability"], bot_rate=0.20)
                                    
                                    odds_home_str = safe_odds_from_pct_str(understandy.get('home'))
                                    odds_draw_str = safe_odds_from_pct_str(understandy.get('draw'))
                                    odds_away_str = safe_odds_from_pct_str(understandy.get('away'))
                                    
                                    match_info = {
                                    'home_team': game['home_team'],
                                    'away_team': game['away_team'],
                                    'date': game['date'],
                                    'home_probability': game['home_probability'],
                                    'draw_probability': game['draw_probability'],
                                    'away_probability': game['away_probability'],
                                    'initial_difference': game['initial_difference'],
                                    'initial_difference_api': game['initial_difference_api'],
                                    "home_probability_api": game['home_probability_api'],
                                    "draw_probability_api": game['draw_probability_api'],
                                    "away_probability_api": game['away_probability_api'],
                                    'prediction': game['prediction'],
                                    "prediction_api": game["prediction_api"],
                                    'prediction_odds': game['prediction_odds'],
                                    'sofascore': f"1({odds_home_str}) ({understandy['home']}%) | X({odds_draw_str}) ({understandy['draw']}%) | 2({odds_away_str}) ({understandy['away']}%)",
                                    'votings': json_result["vote_count"],
                                    'correct_score': game['correct_score'],
                                    "correct_score_api": game['correct_score_api'],
                                    'average_score': game['average_score'],
                                    "average_score_api": game['average_score_api'],
                                    'sport': game['sport'],
                                    "final_score": game['final_score'],
                                    'link': game['link']
                                    }
                                    
                                    append_new_line('analyse-log-SOFASCORE.txt', str(match_info))
                                    matches.append(match_info)
                        else:
                            match_info = {
                            'home_team': game['home_team'],
                            'away_team': game['away_team'],
                            'date': game['date'],
                            'home_probability': game['home_probability'],
                            'draw_probability': game['draw_probability'],
                            'away_probability': game['away_probability'],
                            'initial_difference': game['initial_difference'],
                            'initial_difference_api': game['initial_difference_api'],
                            "home_probability_api": game['home_probability_api'],
                            "draw_probability_api": game['draw_probability_api'],
                            "away_probability_api": game['away_probability_api'],
                            'prediction': game['prediction'],
                            "prediction_api": game["prediction_api"],
                            'prediction_odds': game['prediction_odds'],
                            'sofascore': "",
                            'votings': "",
                            'correct_score': game['correct_score'],
                            "correct_score_api": game['correct_score_api'],
                            'average_score': game['average_score'],
                            "average_score_api": game['average_score_api'],
                            'sport': game['sport'],
                            "final_score": game['final_score'],
                            'link': game['link']
                            }
                            matches.append(match_info)
                            append_new_line('analyse-log-SOFASCORE.txt', str(match_info))
                
            except Exception as e:
                print(f"An error occurred: {e}")
    save_to_excel(matches, "IA_forebet.xlsx", False)
            
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some pages.")
    parser.add_argument('--page', type=str, help='URL of the page to process')
    args = parser.parse_args()
    ffunc(args.page)