
from function import analys_per_link, click_consent, convert_sheet_csv, forebet, forebet_scrap_history, save_to_excel, scrap_selenium_v1


def ffunc():

    """ 
    
    1- Va sur le site https://www.forebet.com/en/football-tips-and-predictions-for-today
    2. Scrollez et charger tous les matchs et mettre "ALL BOOKMAKER"
    3. Copier la div <div class="schema"> TOUS LES SPORTS POSSIBLESPORTS POSSIBLES
        
    """
         
    file_html = 'forebet/data.html' 
    excel_file = 'forebet.xlsx'
    
    """#content_html = forebet_scrap_history(driver)
    game = forebet("forebet/history-log.html", types="folder", folder="forebet/file/")
    save_to_excel(game, excel_file)
    print('done ')"""
    driver = scrap_selenium_v1()
    click_consent(driver, 'en')
    game = convert_sheet_csv("2024-12-24", excel_file)
    diff_analyse = analys_per_link(game, driver)
    save_to_excel(diff_analyse, "IA_forebet.xlsx")
    
ffunc()