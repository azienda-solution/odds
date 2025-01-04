
def analys_per_link(array, driver):
    matches = []
    filtered_array = [
        match__ for match__ in array
        if (
            (float(match__['initial_difference']) > 35 and "football" in str(match__['sport']).lower())
            or (float(match__['initial_difference']) > 51)
            or (float(match__['initial_difference']) > 15 and "american" in str(match__['sport']).lower())
        )
    ]
    for match__ in filtered_array:
            link = match__['link'] if (match__ and len(match__['link'])>2) else None
            if link:
                try:
                    print(str(link))
                    driver.get(link)
                    waitloading(2, driver=driver)
                    content = driver.find_element(By.XPATH, '//table[contains(@class, "allcontent")]//td[contains(@class, "contentmiddle")]')
                    try:
                        divs = content.find_elements(By.XPATH, './/div[contains(@class, "st_scrblock")]')
                        if not divs:
                            divs = content.find_elements(By.XPATH, './/div[contains(@class, "mx-width_hc")]')
                    except Exception as e:
                        divs = []
                    if divs:
                        div_count = len(divs)
                        first_divs = divs[:3] if div_count > 3 else divs
                        last_match = forebet_add_title_on_htmlElement(match__['home_team'], match__['away_team'], first_divs)
                        trend = clean_text(get_trend_forebet(driver))
                        if check_exists_by_xpath(driver, '//table[contains(@class, "allcontent")]//td[contains(@class, "contentmiddle")]//div[contains(@class, "match_intro_tab")]') == 0:
                            trend += getinnertextXpath(driver, '//table[contains(@class, "allcontent")]//td[contains(@class, "contentmiddle")]//div[contains(@class, "match_intro_tab")]')
                        #find result if present
                        if check_exists_by_xpath(driver, '//table[contains(@class, "allcontent")]//td[contains(@class, "contentmiddle")]//div[@class="lscr_td"]//span') == 0:
                            final_score = getinnertextXpath(driver, '//table[contains(@class, "allcontent")]//td[contains(@class, "contentmiddle")]//div[@class="lscr_td"]//span')
                        else:
                            final_score = ""
                            
                            
                        GPT_prompt = f"""
                            Ok chat, you are a highly skilled sports analyst specializing in the analysis of all sports. Your task is to evaluate and refine the given forecast based on an advanced analysis of the following data:

                            ### Match Details:
                            - **Home Team**: {match__['home_team']}
                            - **Away Team**: {match__['away_team']}
                            - **Date**: {match__['date']}
                            - **Sport**: {match__['sport']}

                            ### My Forecast:
                            - **Prediction**: {match__['prediction']}
                            - **Correct Score**: {match__['correct_score']}
                            - **Average Score**: {match__['average_score']}

                            ### Recent Team Performance:
                            {last_match}
                            - **Key Trends**:
                            {trend}

                            ### Task:
                            1. Analyze the **consistency of the provided forecast** (`prediction` and `correct_score`) using the probabilities, recent matches, and trends.
                            2. Use the information to provide a **realistic prediction** based on:
                                - The team's recent performance (e.g., win/loss streaks, goal trends).
                                - Head-to-head performance.
                                - Player performance (if applicable) and external factors.
                                - Focus on using the teams' last performances and their average goals scored in recent matches to provide a prediction. Avoid relying on my provided prediction for your analysis.
                            3. Provide the following outputs in JSON format:
                            ```json
                            {{
                                "home_probability_api": <float>,
                                "draw_probability_api": <float>,
                                "away_probability_api": <float>,
                                "prediction_api": "<string>",
                                "correct_score_api": "<string>",
                                "average_score_api": <float>
                            }}
                            """
                        json_result = get_gpt_response_name(" ", GPT_prompt)
                        if json_result:
                            if len(json_result) > 0:
                                home_probability = to_percentage(match__['home_probability'])
                                draw_probability = to_percentage(match__['draw_probability'])
                                away_probability = to_percentage(match__['away_probability'])
                                average_score = match__['average_score']
                                home_probability_api = to_percentage(json_result["home_probability_api"]) if json_result["home_probability_api"] else ''
                                draw_probability_api = to_percentage(json_result["draw_probability_api"]) if json_result["draw_probability_api"] else ''
                                away_probability_api = to_percentage(json_result["away_probability_api"]) if json_result["away_probability_api"] else ''
                                average_score_api = json_result["average_score_api"] if json_result["average_score_api"] else ''
                                match_info = {
                                    'home_team': match__['home_team'],
                                    'away_team': match__['away_team'],
                                    'date': match__['date'],
                                    'home_probability': home_probability,
                                    'draw_probability': draw_probability,
                                    'away_probability': away_probability,
                                    'prediction': match__['prediction'],
                                    'correct_score': match__['correct_score'],
                                    'average_score': average_score,
                                    'sport': match__['sport'],
                                    'initial_difference': match__['initial_difference'],
                                    "home_probability_api": home_probability_api if home_probability_api else '',
                                    "draw_probability_api": draw_probability_api if draw_probability_api else '',
                                    "away_probability_api": away_probability_api if away_probability_api else '',
                                    "prediction_api": json_result["prediction_api"] if json_result["prediction_api"] else '',
                                    "correct_score_api": json_result["correct_score_api"] if json_result["correct_score_api"] else '',
                                    "average_score_api": average_score_api if average_score_api else '',
                                    "final_score": final_score,
                                    "space1": "-",
                                    'home_probability_INITIAL': home_probability,
                                    "Home_method_Bayesian": bayesian_inference(home_probability, (home_probability_api)),
                                    "Home_method_weighted_average": weighted_average(home_probability, (home_probability_api)),
                                    "Home_method_logarithmic_opinion_pool": logarithmic_opinion_pool(home_probability, (home_probability_api)),
                                    "Home_Probability_PONDERE": "",
                                    "space2": "-",
                                    'draw_probability_INITIAL': draw_probability,
                                    "draw_method_Bayesian": bayesian_inference(draw_probability, (draw_probability_api)),
                                    "draw_method_weighted_average": weighted_average(draw_probability, (draw_probability_api)),
                                    "draw_method_logarithmic_opinion_pool": logarithmic_opinion_pool(draw_probability, (draw_probability_api)),
                                    "draw_Probability_PONDERE": "",
                                    "space3": "-",
                                    'away_probability_INITIAL': away_probability,
                                    "away_method_Bayesian": bayesian_inference(away_probability, (away_probability_api)),
                                    "away_method_weighted_average": weighted_average(away_probability, (away_probability_api)),
                                    "away_method_logarithmic_opinion_pool": logarithmic_opinion_pool(away_probability, (away_probability_api)),
                                    "away_Probability_PONDERE": "",
                                    "space4": "-",
                                    'average_score_INITIAL': average_score,
                                    "average_score_method_Bayesian": bayesian_inference(average_score, average_score_api, type_call='average'),
                                    "average_score_method_weighted_average": weighted_average(average_score, average_score_api, type_call='average'),
                                    "average_score_method_logarithmic_opinion_pool": logarithmic_opinion_pool(average_score, average_score_api, type_call='average'),
                                    "average_score_Probability_PONDERE": "",
                                    'link': match__['link']
                                }
                                match_info['Home_Probability_PONDERE'] = calcul_ponderation(match_info['home_probability_INITIAL'],match_info['Home_method_Bayesian'],match_info['Home_method_weighted_average'],match_info['Home_method_logarithmic_opinion_pool'])
                                match_info['draw_Probability_PONDERE'] = calcul_ponderation(match_info['draw_probability_INITIAL'],match_info['draw_method_Bayesian'],match_info['draw_method_weighted_average'],match_info['draw_method_logarithmic_opinion_pool'] )
                                match_info['away_Probability_PONDERE'] = calcul_ponderation(match_info['away_probability_INITIAL'],match_info['away_method_Bayesian'],match_info['away_method_weighted_average'],match_info['away_method_logarithmic_opinion_pool'] )
                                match_info['average_score_Probability_PONDERE'] = calcul_ponderation(match_info['average_score_INITIAL'],match_info['average_score_method_Bayesian'],match_info['average_score_method_weighted_average'],match_info['average_score_method_logarithmic_opinion_pool'] , type_call='average')
                                append_new_line('analyse-log.txt', str(match_info))
                                matches.append(match_info)
                                check_and_refresh(driver, link, timeout=120)
                        else:
                            append_new_line('content.txt', str(set_text(match__)))
                except Exception as e:
                    print(e)
                    append_new_line('error_by_link.txt', str(set_text(match__)))
                    append_new_line('error_by_link.txt', str(e))
                    continue
    return matches
