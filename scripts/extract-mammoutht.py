import re
from bs4 import BeautifulSoup

from function import scrap_selenium_v1

def extract_links_from_html(html_file_path, base_url="https://mammouth.ai"):
    """
    Extrait tous les liens <a href="/app/a/default/c/..."> 
    et les transforme en URLs complètes
    """
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    links = []
    seen = set()
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '')
        
        # Filtre uniquement les liens du pattern /app/a/default/c/XXXXXXXX
        if re.match(r'^/app/a/default/c/\d+', href):
            full_url = base_url + href
            
            # Évite les doublons
            if full_url not in seen:
                seen.add(full_url)
                
                # Récupère le titre du lien si disponible
                title_div = a_tag.find('div', class_='inline-block')
                title = title_div.get_text(strip=True) if title_div else "Sans titre"
                
                links.append({
                    'url': full_url,
                    'href': href,
                    'title': title,
                    'id': re.search(r'\d+$', href).group()
                })
    
    print(f" {len(links)} liens extraits")
    for link in links:
        print(f"  [{link['id']}] {link['title'][:50]} → {link['url']}")
    
    return links

import os
import re
import time
import unicodedata
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup


# ════════════════════════════════════════════════════════════════════════════
#  UTILITAIRES
# ════════════════════════════════════════════════════════════════════════════

def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Transforme un titre en nom de fichier valide."""
    # Normalise les accents
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    # Retire les caractères invalides
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = re.sub(r'\s+', '_', name.strip())
    name = re.sub(r'_+', '_', name)
    return name[:max_length] or "page_sans_titre"


def scroll_to_bottom(driver, pause: float = 1.5, max_scrolls: int = 30):
    """
    Scroll progressif vers le bas pour charger tout le contenu lazy-loaded.
    Retourne quand la page ne grandit plus.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0

    while scroll_count < max_scrolls:
        # Scroll d'un écran
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.9);")
        time.sleep(pause)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # Vérifie encore une fois après une pause plus longue
            time.sleep(pause * 1.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # Plus rien à charger

        last_height = new_height
        scroll_count += 1

    # Retour en haut puis re-scroll pour s'assurer
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(pause)


def get_element_vertical_position(element) -> int:
    """Retourne la position Y approximative d'un élément via son index dans le DOM."""
    try:
        return element.location.get('y', 0)
    except Exception:
        return 0


# ════════════════════════════════════════════════════════════════════════════
#  EXTRACTION DU CONTENU TEXTUEL
# ════════════════════════════════════════════════════════════════════════════

# Seuil de distance verticale (px) entre deux blocs pour insérer un saut de ligne
VERTICAL_GAP_THRESHOLD = 60  # ajuste selon le site


def extract_page_content(driver) -> tuple[str, str]:
    """
    Extrait le contenu textuel de la page en préservant la structure spatiale.
    
    Returns:
        (title, content_text)
    """
    # ── Titre ──────────────────────────────────────────────────────────────
    try:
        title = driver.title.strip()
        if not title:
            raise ValueError("Titre vide")
    except Exception:
        title = "page_sans_titre"

    # ── Récupération des blocs textuels avec position ──────────────────────
    # On cible les éléments porteurs de texte "terminal" (feuilles du DOM)
    SELECTORS = [
        "p", "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "td", "th", "blockquote", "pre", "code",
        "span", "div", "article", "section",
        # Sélecteurs spécifiques aux messages de chat
        "[class*='message']", "[class*='content']",
        "[class*='turn']", "[class*='chat']",
        "[class*='bubble']", "[class*='response']",
        "[class*='user']", "[class*='assistant']",
    ]

    # Utilise BeautifulSoup sur le HTML courant (plus rapide et plus fiable)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Supprime les balises inutiles
    for tag in soup(["script", "style", "noscript", "meta", "head",
                     "nav", "footer", "button", "svg", "img"]):
        tag.decompose()

    # ── Stratégie : récupération des blocs Selenium avec position Y ────────
    # On utilise Selenium pour avoir les coordonnées réelles
    text_blocks = []

    try:
        elements = driver.find_elements(
            By.CSS_SELECTOR,
            "p, h1, h2, h3, h4, h5, h6, li, blockquote, pre, "
            "[class*='message'], [class*='turn'], [class*='bubble']"
        )

        prev_bottom = 0

        for el in elements:
            try:
                text = el.text.strip()
                if not text or len(text) < 2:
                    continue

                rect = driver.execute_script(
                    "const r = arguments[0].getBoundingClientRect();"
                    "const scrollY = window.scrollY || document.documentElement.scrollTop;"
                    "return {top: r.top + scrollY, bottom: r.bottom + scrollY, "
                    "height: r.height};",
                    el
                )

                top_y = rect.get('top', 0)
                bottom_y = rect.get('bottom', 0)

                # Calcule le gap avec le bloc précédent
                gap = top_y - prev_bottom if prev_bottom > 0 else 0

                text_blocks.append({
                    'text': text,
                    'top': top_y,
                    'bottom': bottom_y,
                    'gap': gap,
                    'tag': el.tag_name.lower()
                })

                prev_bottom = bottom_y

            except Exception:
                continue

    except Exception as e:
        print(f"  ⚠️  Fallback BeautifulSoup (Selenium échoué : {e})")
        # Fallback : extraction simple depuis BeautifulSoup sans position
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                                   'li', 'blockquote', 'pre']):
            text = tag.get_text(separator=' ', strip=True)
            if text and len(text) > 2:
                text_blocks.append({'text': text, 'top': 0, 'bottom': 0,
                                     'gap': 0, 'tag': tag.name})

    # ── Déduplication et assemblage ────────────────────────────────────────
    content_lines = []
    seen_texts = set()
    prev_text = ""

    for block in text_blocks:
        text = block['text']
        gap = block['gap']
        tag = block['tag']

        # Déduplique les textes identiques consécutifs
        if text == prev_text:
            continue
        # Déduplique les textes déjà vus (évite sidebar/nav répétés)
        text_key = text[:80]
        if text_key in seen_texts:
            continue
        seen_texts.add(text_key)

        # Ajoute une ligne vide si grand espace vertical entre les blocs
        if gap > VERTICAL_GAP_THRESHOLD and content_lines:
            content_lines.append("")  # ligne vide = séparation visuelle

        # Préfixe les titres
        if tag in ('h1', 'h2', 'h3'):
            content_lines.append("")
            content_lines.append(f"{'#' * {'h1':1,'h2':2,'h3':3}.get(tag, 3)} {text}")
            content_lines.append("")
        elif tag in ('h4', 'h5', 'h6'):
            content_lines.append(f"\n--- {text} ---")
        elif tag == 'li':
            content_lines.append(f"• {text}")
        elif tag in ('pre', 'code'):
            content_lines.append(f"\n```\n{text}\n```")
        elif tag == 'blockquote':
            content_lines.append(f"> {text}")
        else:
            content_lines.append(text)

        prev_text = text

    content = "\n".join(content_lines)

    # Nettoyage final : max 3 lignes vides consécutives → 2
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    content = content.strip()

    return title, content


# ════════════════════════════════════════════════════════════════════════════
#  SCRAPER PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════

def wait_for_page_content(driver, timeout: int = 20):
    """Attend que le contenu principal soit chargé."""
    try:
        # Attend que le body soit présent
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Attend la fin du chargement JS
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # Pause supplémentaire pour le rendu React/Vue
        time.sleep(2)

        # Attend qu'il y ait du texte réel (évite les spinners)
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_element(By.TAG_NAME, "body").text.strip()) > 100
        )
    except TimeoutException:
        print("  ⚠️  Timeout en attendant le contenu — on continue quand même")


def scrape_all_pages(links: list, output_dir: str = "scraped_pages"):
    """
    Scrape toutes les pages de la liste de liens.
    
    Args:
        links: liste de dicts {'url': ..., 'title': ..., 'id': ...}
        output_dir: dossier de sortie pour les fichiers .txt
    """
    os.makedirs(output_dir, exist_ok=True)

    # ── Initialise le driver ───────────────────────────────────────────────
    driver = scrap_selenium_v1(links[0]['url'])
    if driver is None:
        print("❌ Impossible d'initialiser le driver")
        return

    results = []

    try:
        for i, link in enumerate(links, 1):
            url = link['url']
            print(f"\n[{i}/{len(links)}] ▶ {url}")

            try:
                # ── Navigation ────────────────────────────────────────────
                driver.uc_open_with_reconnect(url, reconnect_time=4)

                # Gestion éventuelle du captcha
                try:
                    driver.uc_gui_click_captcha()
                except Exception:
                    pass

                # ── Attente du contenu ────────────────────────────────────
                wait_for_page_content(driver, timeout=25)

                # ── Scroll complet ────────────────────────────────────────
                print("  📜 Scroll en cours...")
                scroll_to_bottom(driver, pause=1.2, max_scrolls=40)

                # Pause finale pour s'assurer que tout est rendu
                time.sleep(1.5)

                # ── Extraction ────────────────────────────────────────────
                print("  🔍 Extraction du contenu...")
                title, content = extract_page_content(driver)

                if not content.strip():
                    print("  ⚠️  Contenu vide — page peut-être protégée")
                    continue

                # ── Sauvegarde ────────────────────────────────────────────
                filename = sanitize_filename(title) + ".txt"
                filepath = os.path.join(output_dir, filename)

                # Évite les collisions de noms de fichiers
                if os.path.exists(filepath):
                    filepath = os.path.join(
                        output_dir,
                        f"{sanitize_filename(title)}_{link['id']}.txt"
                    )

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"URL: {url}\n")
                    f.write(f"Titre: {title}\n")
                    f.write(f"{'═' * 60}\n\n")
                    f.write(content)

                print(f"  ✅ Sauvegardé → {filepath}")
                print(f"     {len(content)} caractères extraits")

                results.append({
                    'url': url,
                    'title': title,
                    'file': filepath,
                    'chars': len(content)
                })

                # Pause entre les pages pour ne pas surcharger le serveur
                time.sleep(1.5)

            except Exception as e:
                print(f"  ❌ Erreur sur {url} : {e}")
                continue

    finally:
        driver.quit()
        print(f"\n{'═' * 60}")
        print(f"✅ Terminé ! {len(results)}/{len(links)} pages scrapées")
        print(f"📁 Fichiers sauvegardés dans : {output_dir}/")
        for r in results:
            print(f"   • {r['title'][:50]} ({r['chars']} chars) → {r['file']}")

    return results


# ════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # ── Étape 1 : Extraction des liens ────────────────────────────────────
    HTML_FILE = "D:\Documents\Advanced-Python\lab\mammouth.html"          # ← ton fichier HTML source
    OUTPUT_DIR = "scraped_pages"     # ← dossier de sortie

    links = extract_links_from_html(HTML_FILE)

    if not links:
        print("❌ Aucun lien trouvé dans le fichier HTML")
        exit(1)

    # ── Étape 2 : Scraping ────────────────────────────────────────────────
    scrape_all_pages(links, output_dir=OUTPUT_DIR)

