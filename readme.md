```markdown
# Projet ODDS

-   -   -   -   -   

## Structure du Répertoire

```plaintext
ODDS/
│
├── .vscode/
├── 1x2lucksport/
├── config/
├── daily_data/
├── github/
├── logs/
├── other_files/
├── scripts/
│   ├── go.py
│   ├── five.py
├── venv/
├── __pycache__/
├── .gitignore
├── games.xlsx
└── readme.md
```

## Configuration

Le fichier `env.py` contient des variables de configuration importantes, par exemple :

```python

from datetime import datetime, timedelta


API_KEY = " show telegram homelander_off"


DIFFERENC = 7
# API base URL
BASE_URL = 'https://api.the-odds-api.com/v4/sports/'

# Regions and markets
REGIONS = 'us,us2,uk,au,eu'
MARKETS = 'h2h,spreads,totals'

NOW = datetime.utcnow()
COMMENCE_TIME_FROM = NOW.strftime('%Y-%m-%dT%H:%M:%SZ')
COMMENCE_TIME_TO =  (NOW + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
```

## Utilisation

### 1. Récupération des événements à venir par sport

Exécutez la fonction `main()` dans `scripts/go.py` pour récupérer tous les événements à venir par sport. Ensuite, exécutez `convert()` pour traiter ces données.

### 2. Scraper les pages de https://sportsbook-odds-comparer.vercel.app

Exécutez `on_web()` dans `scripts/go.py` pour scraper toutes les pages et préparer les paris. Les résultats seront enregistrés dans un fichier CSV nommé `matches-....csv`.

### 3. Obtenir les événements des prochaines 24 heures

Exécutez `scripts/five.py` pour récupérer les événements des prochaines 24 heures et les afficher.

### 4. Exporter les matchs et cotes de https://1x2.lucksport.com/com_index_en.shtml?cid=740

1. Allez sur le site [1x2 Lucksport](https://1x2.lucksport.com/com_index_en.shtml?cid=740).
2. Copiez le HTML extérieur de la div avec `id="odds_tb"`.
3. Collez-le dans le fichier `daily_data/111.html`.
4. Exécutez `lucksport_1x2_mmatch()` pour exporter les matchs et les cotes dans un fichier Excel.


### 5. Exporter les matchs et cotes de https://www.oddsportal.com/matches/football/

1. Allez sur le site [oddsportal](https://www.oddsportal.com/matches/football/).
2. Copiez avec la souris le 1er match qui n'a pas encore commencé au dernier match 

comme ca 

```
    img
    Football
    /
    br
    Brazil

    /
    Serie A
    Tomorrow, 12 Aug
    1
    X
    2
    B's
    00:00

    Internacional
    Internacional

    –
    Athletico-PR
    Athletico-PR

    1.89

    3.27

    4.31

    28
```


3. verifier 
4. Collez-le dans le fichier `daily_data\oddsportal.txt `.
5. Exécutez `oddsportal()` pour exporter les matchs et les cotes dans un fichier Excel.


### 6. Exporter les matchs et cotes de https://oddspedia.com/

1- Va sur le site [https://oddspedia.com/](https://oddspedia.com/)
2- Copier la div <main class="content-inner"> TOUS LES SPORTS POSSIBLES

### 7. run three_func in go.py


1. Allez sur le site [1x2 Lucksport](https://1x2.lucksport.com/com_index_en.shtml?cid=740).
2. Copiez le HTML extérieur de la div avec `id="odds_tb"`.
3. Collez-le dans le fichier `daily_data/111.html`.
    
    
    
1. Allez sur le site [oddsportal](https://www.oddsportal.com/matches/football/).
2. Copiez avec la souris le 1er match qui n'a pas encore commencé au dernier match 


1. Va sur le site [https://oddspedia.com/](https://oddspedia.com/)
2. Copier la div <main class="content-inner"> TOUS LES SPORTS POSSIBLES

## Instructions supplémentaires

- Installez les dépendances requises avec `pip install -r config/requirements.txt`.

## Auteur



## Licence

Ce projet est sous licence PRIVE. Voir le fichier LICENSE pour plus de détails.
```

