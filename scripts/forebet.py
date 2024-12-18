
from function import append_new_line, forebet, forebet_scrap, save_to_excel, scrap_selenium_v1
from upload_drive import upload_file_to_drive, upload_text_file_to_drive



def ffunc():

    """ 
    
    1- Va sur le site https://www.forebet.com/en/football-tips-and-predictions-for-today
    2. Scrollez et charger tous les matchs et mettre "ALL BOOKMAKER"
    3. Copier la div <div class="schema"> TOUS LES SPORTS POSSIBLESPORTS POSSIBLES
        
    """
         
    file_html = 'forebet/data.html' 
    excel_file = 'forebet.xlsx'
    
    driver = scrap_selenium_v1()
    content_html = forebet_scrap(driver)
    append_new_line(r'forebet/data.html', str(content_html))
    game_oddspedia = forebet(content_html)
    save_to_excel(game_oddspedia, excel_file)
    upload_text_file_to_drive("1iAwsrdawNPeww_FrSmB0AimH0Vzhz8L4",excel_file)
    print('done ')
    
ffunc()