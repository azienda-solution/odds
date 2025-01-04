
from function import analys_per_link, append_new_line, forebet, forebet_scrap, forebet_scrap_trend, save_to_excel, scrap_selenium_v1, cleaner
from upload_drive import upload_file_to_drive, upload_text_file_to_drive



def ffunc():

    """ 
    
    1- Va sur le site https://www.forebet.com/en/football-tips-and-predictions-for-today
    2. Scrollez et charger tous les matchs et mettre "ALL BOOKMAKER"
    3. Copier la div <div class="schema"> TOUS LES SPORTS POSSIBLESPORTS POSSIBLES
        
    """
         
    file_html = 'forebet/data.html'
    excel_file = 'forebet.xlsx'
    
    cleaner('forebet/data.html')
    driver = scrap_selenium_v1()
    content_html = forebet_scrap(driver)
    append_new_line(r'forebet/data.html', str(content_html))
    game_oddspedia = forebet(content_html)
    save_to_excel(game_oddspedia, excel_file)
    #upload_text_file_to_drive("1iAwsrdawNPeww_FrSmB0AimH0Vzhz8L4",excel_file)
    print('done ')
    diff_analyse = analys_per_link(game_oddspedia, driver)
    save_to_excel(diff_analyse, "IA_forebet.xlsx")
    upload_text_file_to_drive("1iAwsrdawNPeww_FrSmB0AimH0Vzhz8L4","IA_forebet.xlsx")
    #trend_content = forebet_scrap_trend(driver, "https://www.forebet.com/en/football-tips-and-predictions-for-today/stat-trends")
    #append_new_line(r'analyse-log.txt', str(trend_content))
    #forebet_trend = analyse_trend(trend_content)
    
ffunc()