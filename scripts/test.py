
from function import analys_per_link, click_consent, convert_sheet_csv, forebet, save_to_excel, scrap_selenium_v1, to_percentage
from upload_drive import upload_text_file_to_drive

excel_file = 'forebet.xlsx'
"""game_oddspedia = forebet("forebet/SAF.html", types="file")
save_to_excel(game_oddspedia, excel_file)"""

driver = scrap_selenium_v1()
game = convert_sheet_csv("2024-12-28-1", excel_file)
diff_analyse = analys_per_link(game, driver)
save_to_excel(diff_analyse, "IA_forebet.xlsx")
