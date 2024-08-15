
from function import oddspedia, save_to_excel


def ffunc():

    """ 
    
    1- Va sur le site [https://oddspedia.com/](https://oddspedia.com/)
    2. Scrollez et charger tous les matchs et mettre "ALL BOOKMAKER"
    3. Copier la div <main class="content-inner"> TOUS LES SPORTS POSSIBLESPORTS POSSIBLES
        
    """
         
    file_html = 'daily_data/oddspedia.html' 
    excel_file = 'oddspedia.xlsx'
    
    game_oddspedia = oddspedia(file_html)
    save_to_excel(game_oddspedia, excel_file)
    print('done ')
    
ffunc()