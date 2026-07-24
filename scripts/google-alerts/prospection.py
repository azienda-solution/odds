"""
Pipeline de prospection : extrait les liens d'alertes Google (collect.html),
récupère le contenu de chaque page en HTTP direct (rapide, pas de navigateur),
génère un résumé structuré via OpenAI, puis ajoute les résultats dans
resume.csv sans jamais supprimer les lignes existantes.

Les liens déjà présents dans resume.csv (colonne "lien") sont automatiquement
ignorés, ce qui permet de relancer le script plusieurs fois sans doublons.
"""

import asyncio
import csv
import json
import os
import sys
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import AsyncOpenAI

DOSSIER = Path(__file__).resolve().parent
FICHIER_HTML = DOSSIER / "collect.html"
FICHIER_CSV = DOSSIER / "resume.csv"
COLONNES_CSV = ["id", "date", "lien", "titre", "resume", "categorie"]

CONCURRENCE_MAX = 20
TIMEOUT_HTTP = 10.0
TAILLE_MAX_TEXTE = 4000  # caractères envoyés au modèle : suffisant pour résumer, plus rapide/moins cher
MODELE = "gpt-4o-mini"
MAX_TOKENS_REPONSE = 120  # force des réponses courtes -> plus rapide

SCHEMA_RESUME = {
    "name": "resume_prospection",
    "schema": {
        "type": "object",
        "properties": {
            "resume": {
                "type": "string",
                "description": (
                    "Une seule phrase courte et directe (20 mots maximum), en français : "
                    "de quoi ça parle et pourquoi c'est pertinent pour la prospection. "
                    "Style télégraphique, sans introduction ni fioritures."
                ),
            },
            "categorie": {
                "type": "string",
                "enum": ["Accessible pour une entreprise IT", "Complexe / réservé", "juste un article de presse"],
                "description": (
                    "Indique si le sujet est accessible pour une entreprise IT "
                    "généraliste, ou s'il est complexe/réservé à des spécialistes."
                    "sans-interet, ou s'il est juste un article de presse."
                ),
            },
        },
        "required": ["resume", "categorie"],
        "additionalProperties": False,
    },
    "strict": True,
}


def charger_cle_api() -> str:
    """Charge la clé API OpenAI depuis le fichier .env et la valide."""
    load_dotenv()
    cle = os.getenv("OPENAI_API_KEY")
    if not cle or not cle.strip():
        print("Erreur : la variable OPENAI_API_KEY est absente ou vide dans le fichier .env.")
        sys.exit(1)
    return cle.strip()


def resoudre_url_reelle(href: str) -> str | None:
    """Décode l'URL cible réelle depuis un lien de redirection Google (/url?...&url=...)."""
    parsed = urlparse(href)
    if "google." in parsed.netloc and parsed.path == "/url":
        params = parse_qs(parsed.query)
        cible = params.get("url") or params.get("q")
        return unquote(cible[0]) if cible else None
    return href


def nettoyer_champ(texte: str) -> str:
    """Aplati un texte sur une seule ligne (espaces/retours à la ligne collapsés) pour éviter
    toute ligne CSV qui semble "cassée" à l'ouverture dans un éditeur texte brut."""
    return " ".join(texte.split()).strip()


def charger_liens_deja_traites(fichier_csv: Path) -> set[str]:
    """Renvoie l'ensemble des URLs déjà présentes dans resume.csv (pour éviter les doublons)."""
    if not fichier_csv.exists() or fichier_csv.stat().st_size == 0:
        return set()
    with fichier_csv.open("r", encoding="utf-8", newline="") as f:
        lecteur = csv.DictReader(f)
        return {ligne["lien"] for ligne in lecteur if ligne.get("lien")}


def extraire_liens_a_traiter(
    fichier_html: Path, deja_traites: set[str]
) -> tuple[list[tuple[str, str]], int]:
    """Lit collect.html et ne garde que les liens pas encore dans resume.csv.

    Les liens déjà présents sont affichés et ignorés immédiatement pendant la lecture,
    plutôt que d'être filtrés dans un second temps.
    """
    soup = BeautifulSoup(
        fichier_html.read_text(encoding="utf-8", errors="ignore"), "html.parser"
    )
    a_traiter: list[tuple[str, str]] = []
    nb_deja_vus = 0
    for h4 in soup.select("h4.result_title"):
        lien_html = h4.find("a")
        if not lien_html or not lien_html.get("href"):
            continue
        url_reelle = resoudre_url_reelle(lien_html["href"])
        if not url_reelle:
            continue

        if url_reelle in deja_traites:
            nb_deja_vus += 1
            print(f"  Déjà dans le CSV, ignoré : {url_reelle}")
            continue

        titre = nettoyer_champ(lien_html.get_text(strip=True))
        a_traiter.append((titre, url_reelle))

    return a_traiter, nb_deja_vus


def prochain_id(fichier_csv: Path) -> int:
    """Calcule le prochain id disponible pour continuer la numérotation existante."""
    if not fichier_csv.exists() or fichier_csv.stat().st_size == 0:
        return 1
    with fichier_csv.open("r", encoding="utf-8", newline="") as f:
        lecteur = csv.DictReader(f)
        ids = [int(ligne["id"]) for ligne in lecteur if ligne.get("id", "").isdigit()]
    return max(ids, default=0) + 1


async def recuperer_texte_page(client_http: httpx.AsyncClient, url: str) -> str | None:
    """Télécharge une page et en extrait le texte principal (sans menus/pubs)."""
    try:
        reponse = await client_http.get(url, timeout=TIMEOUT_HTTP, follow_redirects=True)
        reponse.raise_for_status()
    except Exception as erreur:
        print(f"  Échec de récupération pour {url} : {erreur}")
        return None

    texte = trafilatura.extract(reponse.text, include_comments=False, include_tables=False)
    if not texte or len(texte.strip()) < 50:
        return None
    return texte[:TAILLE_MAX_TEXTE]  # on borne la taille envoyée au modèle (rapidité + coût)


async def resumer_page(client_ia: AsyncOpenAI, titre: str, texte: str) -> dict | None:
    """Demande au modèle un résumé structuré (résumé + catégorie) au format JSON strict."""
    try:
        reponse = await client_ia.chat.completions.create(
            model=MODELE,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu aides un prospecteur travaillant pour des ONG, associations et "
                        "entreprises de développement à évaluer rapidement des pages web."
                    ),
                },
                {"role": "user", "content": f"Titre : {titre}\n\nContenu de la page :\n{texte}"},
            ],
            response_format={"type": "json_schema", "json_schema": SCHEMA_RESUME},
            max_tokens=MAX_TOKENS_REPONSE,
        )
        resultat = json.loads(reponse.choices[0].message.content)
        resultat["resume"] = nettoyer_champ(resultat["resume"])
        return resultat
    except Exception as erreur:
        print(f"  Échec du résumé IA pour '{titre}' : {erreur}")
        return None


async def traiter_lien(
    semaphore: asyncio.Semaphore,
    client_http: httpx.AsyncClient,
    client_ia: AsyncOpenAI,
    titre: str,
    url: str,
) -> dict | None:
    async with semaphore:
        texte = await recuperer_texte_page(client_http, url)
        if not texte:
            return None
        resultat = await resumer_page(client_ia, titre, texte)
        if not resultat:
            return None
        return {"lien": url, "titre": titre, **resultat}


async def main() -> None:
    print("=== Pipeline de prospection (collect.html -> resume.csv) ===")

    cle_api = charger_cle_api()
    client_ia = AsyncOpenAI(api_key=cle_api)

    if not FICHIER_HTML.exists():
        print(f"Erreur : fichier introuvable : {FICHIER_HTML}")
        sys.exit(1)

    deja_traites = charger_liens_deja_traites(FICHIER_CSV)
    a_traiter, nb_deja_vus = extraire_liens_a_traiter(FICHIER_HTML, deja_traites)

    print(f"{nb_deja_vus} déjà présents dans le CSV (ignorés), {len(a_traiter)} à traiter.")

    if not a_traiter:
        print("Rien de nouveau à traiter.")
        return

    semaphore = asyncio.Semaphore(CONCURRENCE_MAX)
    en_tetes_http = {"User-Agent": "Mozilla/5.0 (compatible; ProspectionBot/1.0)"}

    async with httpx.AsyncClient(headers=en_tetes_http) as client_http:
        taches = [
            traiter_lien(semaphore, client_http, client_ia, titre, url)
            for titre, url in a_traiter
        ]
        resultats = []
        for i, tache_terminee in enumerate(asyncio.as_completed(taches), start=1):
            resultat = await tache_terminee
            print(f"[{i}/{len(a_traiter)}] {'OK' if resultat else 'ignoré'}")
            if resultat:
                resultats.append(resultat)

    if not resultats:
        print("Aucun résumé généré, resume.csv inchangé.")
        return

    id_suivant = prochain_id(FICHIER_CSV)
    fichier_existe_deja = FICHIER_CSV.exists() and FICHIER_CSV.stat().st_size > 0
    aujourd_hui = date.today().isoformat()

    with FICHIER_CSV.open("a", encoding="utf-8", newline="") as f:
        # QUOTE_ALL : chaque champ est entre guillemets, donc les virgules et retours à la
        # ligne dans un résumé ne peuvent jamais casser la structure des colonnes.
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES_CSV, quoting=csv.QUOTE_ALL)
        if not fichier_existe_deja:
            ecrivain.writeheader()
        for resultat in resultats:
            ecrivain.writerow(
                {
                    "id": id_suivant,
                    "date": aujourd_hui,
                    "lien": nettoyer_champ(resultat["lien"]),
                    "titre": nettoyer_champ(resultat["titre"]),
                    "resume": nettoyer_champ(resultat["resume"]),
                    "categorie": nettoyer_champ(resultat["categorie"]),
                }
            )
            id_suivant += 1

    print(f"{len(resultats)} nouvelles lignes ajoutées à {FICHIER_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
