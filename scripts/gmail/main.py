import importlib.util
import os
import base64
import json
import time
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

print("=== SCRIPT DÉMARRÉ ===")

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
env_path = "D:/Documents/Advanced-Python/ODDS/scripts/env.py"
spec = importlib.util.spec_from_file_location("env", env_path)
env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(env)
globals().update({k: v for k, v in vars(env).items() if not k.startswith('__')})

print("loadind good")
print(f"__name__ = {__name__}")  # doit afficher __main__

# ── Labels IDs à récupérer dynamiquement ──────────────────────────────────────

def get_or_create_label(service, name):
    """Retourne l'ID d'un label existant ou le crée."""
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for l in labels:
        if l['name'].lower() == name.lower():
            return l['id']
    # Créer si inexistant
    created = service.users().labels().create(
        userId='me',
        body={'name': name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
    ).execute()
    print(f"  🏷️  Label '{name}' créé.")
    return created['id']

# ── Gmail ──────────────────────────────────────────────────────────────────────

def get_gmail_service():
    creds = None
    if os.path.exists('D:/Documents/Advanced-Python/ODDS/scripts/gmail/token.json'):
        creds = Credentials.from_authorized_user_file('D:/Documents/Advanced-Python/ODDS/scripts/gmail/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'D:/Documents/Advanced-Python/ODDS/scripts/gmail/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('D:/Documents/Advanced-Python/ODDS/scripts/gmail/token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_emails(service, max_results=50):
    results = service.users().messages().list(
        userId='me',
        maxResults=max_results,
        q='is:unread'          # ← seul changement
    ).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = txt['payload']
        headers = payload['headers']
        subject   = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender    = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        label_ids = txt.get('labelIds', [])

        body = ''
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
        elif 'body' in payload:
            data = payload['body'].get('data', '')
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

        emails.append({
            'id': msg['id'],
            'subject': subject,
            'from': sender,
            'body': body[:600],
            'labels': label_ids
        })
    return emails


def apply_labels(service, msg_id, add_label_ids=[], remove_label_ids=[]):
    service.users().messages().modify(
        userId='me',
        id=msg_id,
        body={'addLabelIds': add_label_ids, 'removeLabelIds': remove_label_ids}
    ).execute()

# ── GPT ────────────────────────────────────────────────────────────────────────
GPT_PROMPT = """Tu es un assistant qui analyse des emails reçus par quelqu'un avec ce profil :
- Ingénieur cloud/DevOps en recherche d'emploi en France
- Président d'une association (projets éducatifs, Afrique, développement)
- Gérant d'une SASU (projets tech, subventions, appels à projets)
- Personne avec une vie sociale normale : amis, anciens profs, recruteurs LinkedIn, contacts perso

Retourne UNIQUEMENT un JSON valide avec ces champs:
{
  "utile": true ou false,
  "categorie": "promo" | "alerte" | "securite" | "recrutement" | "appel_projet" | "social" | "administratif" | "autre",
  "offre_pertinente": true ou false,
  "projet_pertinent": true ou false,
  "resume": "1-2 phrases max en français"
}

Règles strictes:

- "utile": false UNIQUEMENT si c'est clairement une pub, newsletter commerciale, spam ou alerte Google sans contenu réel
- "utile": true dans tous les autres cas, notamment :
  → email d'un ami, collègue, ancien prof, contact perso ou professionnel
  → recruteur qui contacte directement (LinkedIn, email direct)
  → facture, reçu, confirmation de commande, abonnement payant
  → document administratif, juridique, fiscal, bancaire, assurance
  → email de justice, huissier, administration, impôts, CAF, URSSAF, etc.
  → alerte de sécurité (compte piraté, 2FA, mot de passe)
  → tout email qui sort de l'ordinaire ou qui peut avoir des conséquences

- "categorie":
  → "social" : email d'une personne réelle (ami, contact, recruteur direct, ancien prof)
  → "administratif" : facture, banque, assurance, justice, impôts, admin, abonnement
  → "recrutement" : offre d'emploi, chasseur de tête, job alert
  → "appel_projet" : AAP, subvention, appel à candidatures
  → "securite" : alerte sécurité, connexion suspecte, 2FA
  → "alerte" : Google Alert ou notification automatique
  → "promo" : pub, soldes, newsletter marketing
  → "autre" : tout ce qui ne rentre pas ailleurs

- "offre_pertinente": true SEULEMENT si c'est une offre d'emploi réelle pour profil cloud/DevOps/SRE/infra/Linux/Ansible/GitLab/Kubernetes
  → false si offre en Inde ou hors France/Europe sans mention remote
  → true si bien présentée même hors France, préciser la localisation dans resume

- "projet_pertinent": true si c'est un VRAI appel à projets avec possibilité de candidater :
  → subventions, financements, AAP éducation/Afrique/tech/social/développement
  → appels de fondations, collectivités, institutions publiques, ONG
  → false si alerte Google vide ou sans contenu exploitable

- "resume": résume l'essentiel en 1-2 phrases, précise pays/région pour offres d'emploi, et l'expéditeur si c'est un contact humain

Email à analyser:
"""



def classify_email(subject, sender, body):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": OPENAI_KEY
    }
    contenu = f"De: {sender}\nSujet: {subject}\nBody: {body[:500]}"
    data = {
        "model": "gpt-3.5-turbo-1106",
        "messages": [
            {"role": "system", "content": "Tu retournes uniquement du JSON valide, sans markdown."},
            {"role": "user", "content": GPT_PROMPT + contenu}
        ],
        "temperature": 0.2
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        content = r.json()['choices'][0]['message']['content'].strip()
        if '```' in content:
            content = content.split('```')[1].replace('json', '').strip()
        return json.loads(content)
    except Exception as e:
        print(f"  [GPT Error] {e}")
        return {"utile": True, "categorie": "autre", "offre_pertinente": False, "resume": "Erreur GPT - conservé par sécurité"}

# ── MAIN ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    service = get_gmail_service()

    # Récupérer/créer les labels
    print("🏷️  Chargement des labels...")
    LABEL_GPT      = get_or_create_label(service, "GPT")
    LABEL_A_SUIVRE = get_or_create_label(service, "A Suivre")

    print(f"\n📬 Récupération des 50 derniers emails...")
    emails = get_emails(service, max_results=50)

    # Trier: PRIMARY en premier
    def priority(e):
        labels = e['labels']
        if 'CATEGORY_PROMOTIONS' in labels or 'CATEGORY_UPDATES' in labels:
            return 1
        return 0

    emails.sort(key=priority)

    to_archive = []
    kept       = []
    offres_top = []

    print(f"\n🔍 Analyse GPT de {len(emails)} emails...\n")

    for i, email in enumerate(emails):
        #print(f"[{i+1}/{len(emails)}] {email['subject'][:65]}")
        result = classify_email(email['subject'], email['from'], email['body'])
        email['gpt'] = result

        offre_tag = ""
        if result.get('offre_pertinente'):
            offre_tag += " 🎯 OFFRE"
        if result.get('projet_pertinent'):
            offre_tag += " 🚀 PROJET"

        icon = "✅" if result['utile'] else "🗑️ "
        #print(f"  {icon} {result['categorie'].upper()}{offre_tag}")
        #print(f"     📝 {result['resume']}")

        if result.get('offre_pertinente') or result.get('projet_pertinent'):
            offres_top.append(email)

        if not result['utile']:
            to_archive.append(email)
        else:
            kept.append(email)

    # ── Résumé ────────────────────────────────────────────────────────────────
    #print(f"\n{'='*65}")

    if offres_top:
        #print(f"\n🎯 OFFRES / PROJETS PERTINENTS ({len(offres_top)}) → seront labelisés 'A Suivre' :")
        for e in offres_top:
            tag = "🎯 OFFRE" if e['gpt'].get('offre_pertinente') else "🚀 PROJET"
            print(f"  {tag} {e['from'][:40]}")
            print(f"     {e['subject'][:60]}")
            print(f"     📝 {e['gpt']['resume']}")

    print(f"\n📌 EMAILS UTILES CONSERVÉS ({len(kept)}) :")
    for e in kept:
        tag = ""
        if e['gpt'].get('offre_pertinente'):
            tag = " 🎯"
        if e['gpt'].get('projet_pertinent'):
            tag = " 🚀"
        print(f"  ✅{tag} {e['subject'][:55]}")
        print(f"      └─ {e['gpt']['resume']}")

    print(f"\n🗑️  EMAILS À ARCHIVER ({len(to_archive)}) :")
    for e in to_archive:
        print(f"  ❌ [{e['gpt']['categorie']}] {e['subject'][:55]}")
        print(f"      └─ {e['gpt']['resume']}")

    # ── Archivage email par email ─────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"🗑️  TRAITEMENT EMAIL PAR EMAIL ({len(to_archive)} à archiver)\n")

    for e in to_archive:
        print(f"\n📧 De     : {e['from'][:60]}")
        print(f"   Sujet  : {e['subject'][:60]}")
        print(f"   Catég  : {e['gpt']['categorie'].upper()}")
        print(f"   Résumé : {e['gpt']['resume']}")

        action = input("   ❓ (a)rchiver / (g)arder / (q)uitter : ").strip().lower()

        if action == 'a':
            apply_labels(service, e['id'],
                         add_label_ids=[LABEL_GPT],
                         remove_label_ids=['INBOX'])
            print("   ✅ Archivé + label GPT")
        elif action == 'q':
            print("   ⏹️  Script arrêté.")
            break
        else:
            print("   📌 Gardé dans inbox.")

    # ── Offres/projets → A Suivre ─────────────────────────────────────────────
    if offres_top:
        print(f"\n🎯 Application du label 'A Suivre' sur {len(offres_top)} offres/projets...")
        confirm2 = input("❓ Confirmer ? (o/n) : ").strip().lower()
        if confirm2 == 'o':
            for e in offres_top:
                apply_labels(service, e['id'],
                             add_label_ids=[LABEL_GPT, LABEL_A_SUIVRE])
                print(f"  🎯 [A Suivre] {e['subject'][:55]}")

    print(f"\n✅ Terminé !")
