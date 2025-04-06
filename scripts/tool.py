import json
from function import clean_text, cleaner, click_consent, convert_sheet_csv, getinnertextXpath, save_to_excel, scrap_selenium_v1, waitloading

def find_result():
    json_array = []
    cleaner('forebet/data.html')
    driver = scrap_selenium_v1("forebet.com")
    click_consent(driver, 'en')
    data = convert_sheet_csv('one', 'echant.xlsx')
    matches = []
    for match__ in data:
        link = match__['link']
        try:
            driver.get(link)
            waitloading(2, driver=driver)
            final_score = getinnertextXpath(driver, '//table[contains(@class, "allcontent")]//td[contains(@class, "contentmiddle")]//div[contains(@class, "rcnt")]//div[@class="lscr_td"]//span')
            match__["final_score"] = clean_text(final_score)
            json_array.append(match__)
        except Exception as e:
            pass
    save_to_excel(json_array, "AI_RESULT.xlsx")

find_result()