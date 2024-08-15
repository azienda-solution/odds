from bs4 import BeautifulSoup


def is_float(value):
    """Vérifie si une chaîne peut être convertie en float."""
    try:
        float(value)
        return True
    except ValueError:
        return False

def clean_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    cleaned_lines = []
    skip_next = False

    for i in range(len(lines)):
        line = lines[i].strip()

        # Si on doit sauter la ligne, on continue
        if skip_next:
            skip_next = False
            continue

        # Vérifie si la ligne actuelle n'est pas un float, que la ligne suivante est identique
        # et que la ligne a plus de 2 caractères
        if (not is_float(line) and len(line) > 2 and 
            i + 1 < len(lines) and line == lines[i + 1].strip()):
            skip_next = True  # On saute la prochaine ligne (on garde la première)
        
        # Ajouter la ligne nettoyée
        cleaned_lines.append(line)

    # Joindre les lignes nettoyées en un seul bloc de texte
    cleaned_text = "\n".join(cleaned_lines)

    # Remplacer tous les "\n\n" par un seul "\n"
    cleaned_text = cleaned_text.replace("\n\n", "\n")

    # Supprimer les lignes vides restantes
    cleaned_text = "\n".join([line for line in cleaned_text.split("\n") if line.strip() != ""])

    match_info_list = []

    lines = cleaned_text.splitlines()

    for i in range(len(lines)):
        line = lines[i].strip()

        # Recherche du caractère "–"
        if "–" in line:
            parts = line.split("–")
            if len(parts) == 2:
                home_team = lines[i-1].strip()
                away_team = lines[i+1].strip()

                # Vérifie qu'il y a au moins trois lignes suivantes pour les cotes
                if i + 3 < len(lines):
                    odds_home = lines[i + 2].strip()
                    odds_draw = lines[i + 3].strip()
                    odds_away = lines[i + 4].strip()

                    # Convertir les cotes en float
                    try:
                        odds_home = float(odds_home)
                        odds_draw = float(odds_draw)
                        odds_away = float(odds_away)
                    except ValueError:
                        odds_home = ""
                        odds_draw = ""
                        odds_away = ""

                    match_info = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'initial_odds_home': odds_home,
                        'initial_draw_odds': odds_draw,
                        'initial_odds_away': odds_away,
                        'initial_difference': abs(float(odds_home) - float(odds_away)),
                        'actual_odds_home': "",
                        'draw_odds_actual': "",
                        'actual_odds_away': "",
                        'actual_difference': ""
                    }

                    match_info_list.append(match_info)

    return match_info_list
# Exemple d'utilisation
"""file_path = 'daily_data/oddsportal.txt'  # Remplacez par le chemin de votre fichier
cleaned_text = clean_text_from_file(file_path)
print(cleaned_text)"""

                