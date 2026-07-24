"""
Script interactif : pilote un navigateur Chromium en temps réel via des instructions
en langage naturel, grâce à browser-use (+ Playwright en dessous) et un LLM OpenAI.

Le navigateur est ouvert UNE SEULE FOIS au démarrage et reste ouvert entre chaque
commande. Il ne se ferme que lorsque l'utilisateur tape "quit" ou "exit".

Deux comportements particuliers sont implémentés :

1. Informations manquantes : l'agent ne doit jamais inventer une donnée qu'il ne
   connaît pas (mot de passe, code, choix personnel...). Il dispose d'une action
   "demander_information_manquante" qui interrompt son exécution, pose la question
   dans le terminal et attend la réponse tapée par l'utilisateur avant de continuer.
   Les valeurs sensibles (est_sensible=True) ne sont jamais renvoyées en clair au
   modèle : elles sont stockées dans agent.sensitive_data et référencées via un
   placeholder <secret>...</secret>, conformément au mécanisme natif de browser-use.

2. Interruption en cours de tâche : pendant qu'une instruction s'exécute, taper
   "stop" (ou "pause"/"annule"/"arrete") dans le terminal interrompt proprement la
   tâche en cours (le navigateur et le contexte de l'agent restent intacts) et
   redonne la main pour taper une nouvelle instruction, qui continue la même
   conversation grâce à agent.add_new_task(...).
"""

import asyncio
import functools
import http.server
import os
import re
import sys
import tempfile
import threading

from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatOpenAI, Tools
from browser_use.agent.views import ActionResult

# Commandes qui déclenchent l'arrêt propre du script (ferment le navigateur)
COMMANDES_ARRET = {"quit", "exit"}

# Mots-clés qui interrompent uniquement la tâche en cours, sans fermer le navigateur
MOTS_INTERRUPTION_TACHE = {"stop", "pause", "annule", "arrete", "arrête"}

# Repère les URLs "file:///D:/..." (Windows) dans une instruction en texte libre
MOTIF_URL_FICHIER_LOCAL = re.compile(r"file:///([A-Za-z]):/([^\s\"'<>]*)")

CONSIGNE_INFO_MANQUANTE = """
RÈGLE ABSOLUE CONCERNANT LES INFORMATIONS MANQUANTES :
Tu ne dois JAMAIS inventer, deviner ou halluciner une information que tu ne connais pas
(mot de passe, code de vérification, numéro, choix personnel, adresse, etc.).
Si une information nécessaire à la tâche ne t'a pas été fournie dans la consigne, tu DOIS
impérativement appeler l'action "demander_information_manquante" avec une question claire
et précise, puis attendre la réponse avant de continuer. Ne termine jamais une tâche par un
échec silencieux ou une valeur inventée : demande toujours à l'utilisateur humain.
Pour tout mot de passe, code secret ou donnée confidentielle, appelle cette action avec
est_sensible=True : la valeur te sera alors fournie sous la forme d'un placeholder
<secret>nom</secret> à utiliser tel quel dans le champ concerné, sans jamais l'écrire en clair.
""".strip()


class ServeurFichiersLocaux:
    """
    browser-use bloque en dur toute navigation vers une URL file:// (aucune
    option de configuration ne permet de l'autoriser : voir SecurityWatchdog,
    qui rejette toute URL sans "hostname", ce qui est toujours le cas pour
    file:///D:/...). Pour contourner ce blocage sans jamais avoir à modifier
    le prompt, on sert chaque lecteur référencé via un petit serveur HTTP
    local (127.0.0.1 uniquement) et on réécrit automatiquement les URLs
    file:///X:/... en http://127.0.0.1:PORT/... avant de transmettre
    l'instruction à l'Agent.
    """

    def __init__(self) -> None:
        self._serveurs_par_lecteur: dict[str, int] = {}
        self._verrou = threading.Lock()

    def _port_pour_lecteur(self, lettre_lecteur: str) -> int:
        lettre_lecteur = lettre_lecteur.upper()
        with self._verrou:
            if lettre_lecteur in self._serveurs_par_lecteur:
                return self._serveurs_par_lecteur[lettre_lecteur]

            racine = f"{lettre_lecteur}:\\"
            gestionnaire = functools.partial(
                http.server.SimpleHTTPRequestHandler, directory=racine
            )
            # port=0 -> le système choisit un port libre automatiquement
            httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gestionnaire)
            port = httpd.server_address[1]

            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()

            self._serveurs_par_lecteur[lettre_lecteur] = port
            print(f"Serveur local démarré pour le lecteur {lettre_lecteur}: -> http://127.0.0.1:{port}/")
            return port

    def convertir_instruction(self, instruction: str) -> str:
        """Remplace toute URL file:///X:/... trouvée dans l'instruction par son équivalent http local."""

        def remplacer(correspondance: re.Match) -> str:
            lettre_lecteur, chemin_relatif = correspondance.group(1), correspondance.group(2)
            port = self._port_pour_lecteur(lettre_lecteur)
            return f"http://127.0.0.1:{port}/{chemin_relatif}"

        return MOTIF_URL_FICHIER_LOCAL.sub(remplacer, instruction)


def charger_cle_api() -> str:
    """Charge la clé API OpenAI depuis le fichier .env et la valide."""
    load_dotenv()  # Charge les variables du fichier .env dans l'environnement

    cle_api = os.getenv("OPENAI_API_KEY")
    if not cle_api or not cle_api.strip():
        print("Erreur : la variable OPENAI_API_KEY est absente ou vide dans le fichier .env.")
        print("Copiez .env.example vers .env et renseignez votre clé (format sk-...).")
        sys.exit(1)

    return cle_api.strip()


class EtatInteractif:
    """
    Coordonne les entrées clavier entre trois consommateurs potentiels :
    - la boucle principale qui attend la prochaine instruction quand l'agent est inactif,
    - la surveillance du mot-clé d'interruption pendant qu'une tâche s'exécute,
    - l'action "demander_information_manquante" qui attend une réponse précise.

    Un seul thread lit stdin (input() est bloquant), toutes les lignes passent par une
    unique asyncio.Queue puis sont redistribuées ici selon le contexte courant : il n'y a
    donc jamais deux consommateurs qui se disputent la même ligne tapée par l'utilisateur.
    """

    def __init__(self) -> None:
        self.lignes_brutes: asyncio.Queue[str | None] = asyncio.Queue()
        self.instructions: asyncio.Queue[str | None] = asyncio.Queue()
        self.agent: Agent | None = None
        self.agent_en_cours = False
        self.fermeture_demandee = False
        self.reponse_attendue: asyncio.Future[str] | None = None
        self.compteur_secrets = 0

    def demarrer_lecteur_stdin(self) -> None:
        boucle = asyncio.get_running_loop()

        def lire_stdin_en_boucle() -> None:
            while True:
                try:
                    ligne = input()
                except EOFError:
                    boucle.call_soon_threadsafe(self.lignes_brutes.put_nowait, None)
                    return
                boucle.call_soon_threadsafe(self.lignes_brutes.put_nowait, ligne)

        threading.Thread(target=lire_stdin_en_boucle, daemon=True).start()

    async def distribuer_lignes(self) -> None:
        """Tâche de fond : route chaque ligne tapée vers le bon consommateur selon le contexte."""
        while True:
            ligne = await self.lignes_brutes.get()

            if ligne is None:
                # Entrée standard fermée : on débloque tout le monde proprement
                if self.reponse_attendue and not self.reponse_attendue.done():
                    self.reponse_attendue.set_result("")
                self.fermeture_demandee = True
                if self.agent:
                    self.agent.stop()
                await self.instructions.put(None)
                return

            if self.reponse_attendue is not None and not self.reponse_attendue.done():
                # Une action "demander_information_manquante" attend précisément cette ligne
                self.reponse_attendue.set_result(ligne)
                continue

            mot = ligne.strip().lower()

            if self.agent_en_cours:
                if mot in MOTS_INTERRUPTION_TACHE or mot in COMMANDES_ARRET:
                    if mot in COMMANDES_ARRET:
                        self.fermeture_demandee = True
                    print(
                        "\n⏹ Arrêt demandé : la tâche en cours va s'interrompre à la fin de "
                        "l'étape actuelle (le navigateur reste ouvert)..."
                    )
                    if self.agent:
                        self.agent.stop()
                else:
                    print(
                        f"\n(Instruction ignorée pendant l'exécution en cours : « {ligne} ». "
                        "Retapez-la une fois la tâche arrêtée ou terminée.)"
                    )
                continue

            # Agent inactif : c'est la prochaine instruction à exécuter
            await self.instructions.put(ligne)

    async def demander_a_utilisateur(self, invite: str) -> str:
        print(invite, end="", flush=True)
        self.reponse_attendue = asyncio.get_running_loop().create_future()
        try:
            reponse = await self.reponse_attendue
        finally:
            self.reponse_attendue = None
        return reponse


def creer_outils(etat: EtatInteractif) -> Tools:
    outils = Tools()

    @outils.action(
        "Pose une question à l'utilisateur humain dans le terminal lorsqu'une information "
        "nécessaire à la tâche est manquante et ne peut pas être devinée (mot de passe, code de "
        "vérification, choix personnel, numéro, etc.). Attend la réponse avant de continuer. "
        "Mets est_sensible=True pour tout mot de passe ou donnée confidentielle : la valeur ne "
        "sera alors jamais affichée en clair, tu recevras uniquement un placeholder <secret>...</secret> "
        "à utiliser dans le champ concerné."
    )
    async def demander_information_manquante(question: str, est_sensible: bool = False) -> ActionResult:
        print(f"\n❓ L'agent a besoin d'une information pour continuer :\n   {question}")
        reponse = await etat.demander_a_utilisateur("   Votre réponse : ")

        if est_sensible and etat.agent is not None:
            etat.compteur_secrets += 1
            cle = f"info_utilisateur_{etat.compteur_secrets}"
            if etat.agent.sensitive_data is None:
                etat.agent.sensitive_data = {}
            etat.agent.sensitive_data[cle] = reponse
            return ActionResult(
                extracted_content=(
                    f"Valeur sensible fournie par l'utilisateur, disponible via le placeholder "
                    f"<secret>{cle}</secret>. Utilise ce tag tel quel dans le champ concerné, "
                    f"n'écris jamais la valeur en clair."
                ),
                long_term_memory=(
                    f"L'utilisateur a fourni une valeur sensible pour « {question} », "
                    f"accessible via <secret>{cle}</secret>."
                ),
            )

        return ActionResult(
            extracted_content=reponse,
            long_term_memory=f"L'utilisateur a répondu à la question « {question} » : {reponse}",
        )

    return outils


async def main() -> None:
    print("=== Démarrage du contrôleur de navigateur browser-use ===")

    # 1. Chargement de la clé API OpenAI depuis .env
    cle_api = charger_cle_api()
    os.environ["OPENAI_API_KEY"] = cle_api  # S'assure que la lib l'utilise bien

    # 2. Initialisation du LLM (réutilisé pour chaque commande)
    llm = ChatOpenAI(model="gpt-4o-mini")

    # 3. Création d'un dossier de profil temporaire et vide.
    dossier_profil = tempfile.mkdtemp(prefix="browser_use_profile_")

    # 4. Lancement du navigateur Chromium visible, session unique et persistante
    navigateur = Browser(
        headless=False,
        user_data_dir=dossier_profil,
        keep_alive=True,
    )
    await navigateur.start()

    print("Navigateur Chromium lancé et prêt.")
    print("Tapez une instruction en langage naturel, ou 'quit'/'exit' pour quitter.")
    print("Pendant l'exécution d'une tâche, tapez 'stop' pour l'interrompre sans fermer le navigateur.\n")

    # 4bis. Serveur(s) HTTP local(aux) pour contourner le blocage file:// de browser-use
    serveur_fichiers = ServeurFichiersLocaux()

    # 4ter. Coordination clavier + outil "demander_information_manquante"
    etat = EtatInteractif()
    etat.demarrer_lecteur_stdin()
    tache_distribution = asyncio.create_task(etat.distribuer_lignes())
    outils = creer_outils(etat)

    try:
        while True:
            print(">> ", end="", flush=True)
            instruction = await etat.instructions.get()

            if instruction is None:
                print("\nEntrée standard fermée, arrêt du script.")
                break

            instruction = instruction.strip()
            if not instruction:
                continue

            if instruction.lower() in COMMANDES_ARRET:
                print("Fermeture du navigateur et arrêt du script...")
                break

            tache = serveur_fichiers.convertir_instruction(instruction)
            if tache != instruction:
                print(f"Chemin local détecté, exposé temporairement en local : {tache}")

            print(f"Exécution de l'instruction : {instruction}")
            try:
                if etat.agent is None:
                    etat.agent = Agent(
                        task=tache,
                        llm=llm,
                        browser=navigateur,
                        tools=outils,
                        extend_system_message=CONSIGNE_INFO_MANQUANTE,
                        sensitive_data={},
                    )
                else:
                    etat.agent.add_new_task(tache)

                etat.agent_en_cours = True
                try:
                    resultat = await etat.agent.run()
                finally:
                    etat.agent_en_cours = False

                print("Résultat de l'action :")
                print(resultat)
            except Exception as erreur:
                # Une instruction ratée ne doit pas interrompre la boucle principale
                print(f"Erreur lors de l'exécution de l'instruction : {erreur}")

            if etat.fermeture_demandee:
                print("Fermeture du navigateur et arrêt du script...")
                break

            print()  # Ligne vide pour la lisibilité avant la prochaine commande

    finally:
        tache_distribution.cancel()
        # 8. Fermeture propre du navigateur, quelle que soit la façon dont on sort de la boucle
        await navigateur.close()
        print("Navigateur fermé. Script terminé.")


if __name__ == "__main__":
    asyncio.run(main())
