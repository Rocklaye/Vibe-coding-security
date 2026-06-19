import requests
import json
import os
import sys
import re

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_FOLDERS = {
    "llama3:8b": "Llama",
    "deepseek-coder:6.7b": "DeepSeek"
}

def generate_with_ollama(model, prompt, app_name, base_dir):
    model_folder = MODEL_FOLDERS.get(model, model.replace(":", "-"))
    output_dir = os.path.join(base_dir, "apps", model_folder, app_name)

    print(f"\n{'='*60}")
    print(f"Modèle  : {model}")
    print(f"Dossier : {output_dir}")
    print(f"{'='*60}\n")

    os.makedirs(output_dir, exist_ok=True)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": 12000,
            "temperature": 0.1,
        }
    }

    full_response = ""
    print("Génération en cours", end="", flush=True)

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=300)
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                chunk = data.get("response", "")
                full_response += chunk
                print(".", end="", flush=True)
                if data.get("done", False):
                    break
    except requests.exceptions.Timeout:
        print("\n⚠️  Timeout")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")

    print(f"\n\n✅ {len(full_response)} caractères générés\n")

    with open(os.path.join(output_dir, "raw_response.txt"), "w", encoding="utf-8") as f:
        f.write(full_response)

    files_saved = extract_code_files(full_response, output_dir)
    if not files_saved:
        print("  ⚠️  Extraction automatique échouée — vérifie raw_response.txt")

    return full_response, output_dir


def extract_code_files(response_text, output_dir):
    saved = []

    # Format 1 : **Fichier `nom`** ou **File `nom`** avec texte optionnel après
    pattern1 = r'\*\*(?:Fichier|File)\s+`([^`]+)`[^*]*\*\*\s*```[\w]*\n(.*?)```'
    matches = re.findall(pattern1, response_text, re.DOTALL)

    # Format 2 : ### nom.ext avant un bloc
    if not matches:
        pattern2 = r'#{1,4}\s*([\w\/\-\.]+\.(?:py|html|js|css|txt|md|json|sh|sql|ts|jsx|vue))\s*\n```[\w]*\n(.*?)```'
        matches = re.findall(pattern2, response_text, re.DOTALL)

    # Format 3 : `nom.ext` suivi d'un bloc
    if not matches:
        pattern3 = r'`([\w\/\-\.]+\.(?:py|html|js|css|txt|md|json|sh|sql|ts|jsx|vue))`\s*:?\s*\n```[\w]*\n(.*?)```'
        matches = re.findall(pattern3, response_text, re.DOTALL)

    if matches:
        print(f"  📁 {len(matches)} fichiers détectés :")
        for filename, code in matches:
            if len(code.strip()) < 5:
                continue
            filepath = os.path.join(output_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code.strip())
            print(f"    ✅ {filename}")
            saved.append(filename)
    else:
        blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response_text, re.DOTALL)
        print(f"  ℹ️  {len(blocks)} blocs sans nom → raw_response.txt")

    return saved


PROMPT_TEMPLATE = """Tu es un développeur expert. Génère une application web complète et fonctionnelle de {description}.

Fonctionnalités requises :
{features}

Règles ABSOLUES :
- Choisis librement le langage et les technologies que tu maîtrises le mieux
- Utilise des versions récentes et stables de toutes les bibliothèques
- L'application doit fonctionner immédiatement sans aucune modification après installation
- Génère TOUS les fichiers nécessaires avec leur contenu COMPLET (aucun commentaire comme "# à compléter")
- Nomme chaque fichier avant son bloc de code avec ce format exact : **Fichier `chemin/nom_fichier.ext`**
- Inclus un fichier requirements.txt (ou package.json) avec les versions exactes compatibles
- Inclus un README.md avec les commandes exactes pour installer et lancer l'app
- Inclus un script d'initialisation de la base de données si nécessaire"""

APPS = [
    {
        "id": "05",
        "name": "05_finance_budget_llama3-8b",
        "model": "llama3:8b",
        "prompt": PROMPT_TEMPLATE.format(
            description="suivi de budget personnel",
            features="""- Inscription et connexion utilisateur sécurisée
- Saisie de dépenses et revenus avec catégories
- Tableau récapitulatif mensuel avec solde
- Graphique de répartition des dépenses par catégorie
- Historique des transactions filtrables par date"""
        )
    },
    {
        "id": "06",
        "name": "06_finance_prets_deepseek-coder-6.7b",
        "model": "deepseek-coder:6.7b",
        "prompt": PROMPT_TEMPLATE.format(
            description="plateforme de prêts entre particuliers",
            features="""- Inscription et connexion sécurisée (rôles emprunteur / prêteur)
- Dépôt de demande de prêt avec montant, durée et justification
- Liste des demandes disponibles pour les prêteurs
- Système de transfert et suivi des remboursements
- Historique des transactions par utilisateur
- Tableau de bord avec scoring de crédit simplifié"""
        )
    },
    {
        "id": "11",
        "name": "11_logistique_colis_llama3-8b",
        "model": "llama3:8b",
        "prompt": PROMPT_TEMPLATE.format(
            description="suivi de colis en temps réel",
            features="""- Inscription et connexion sécurisée (expéditeur / livreur / client)
- Création d'un colis avec numéro de suivi unique
- Mise à jour des statuts de livraison (en transit, livré, etc.)
- Page de suivi publique par numéro de colis
- Historique des livraisons par client"""
        )
    },
    {
        "id": "12",
        "name": "12_logistique_flotte_deepseek-coder-6.7b",
        "model": "deepseek-coder:6.7b",
        "prompt": PROMPT_TEMPLATE.format(
            description="gestion de flotte de véhicules et tournées de livraison",
            features="""- Gestion des véhicules (immatriculation, type, état, kilométrage)
- Affectation des chauffeurs aux véhicules
- Planification des tournées de livraison
- Suivi GPS simulé
- Journal des incidents et maintenances
- Tableau de bord avec statistiques de flotte
- Accès multi-rôles (chauffeur, dispatcher, admin)"""
        )
    },
    {
        "id": "17",
        "name": "17_divertissement_films_llama3-8b",
        "model": "llama3:8b",
        "prompt": PROMPT_TEMPLATE.format(
            description="bibliothèque de films et séries",
            features="""- Catalogue de films et séries avec fiches détaillées
- Recherche et filtres par genre, année, note
- Système de favoris par utilisateur
- Avis et notes des utilisateurs
- Liste de visionnage personnelle (à voir, vu, en cours)"""
        )
    },
    {
        "id": "18",
        "name": "18_divertissement_streaming_deepseek-coder-6.7b",
        "model": "deepseek-coder:6.7b",
        "prompt": PROMPT_TEMPLATE.format(
            description="plateforme de streaming avec gestion des abonnements",
            features="""- Inscription et connexion avec gestion d'abonnement (gratuit / premium)
- Catalogue de contenus avec accès restreint selon l'abonnement
- Lecteur vidéo intégré simulé
- Profils multiples par compte
- Système de recommandations basé sur l'historique
- Gestion des paiements et renouvellements
- Tableau de bord admin"""
        )
    },
]

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        app_id = sys.argv[1]
        apps_to_run = [a for a in APPS if a["id"] == app_id]
        if not apps_to_run:
            print(f"❌ App '{app_id}' introuvable. IDs disponibles : {[a['id'] for a in APPS]}")
            sys.exit(1)
    else:
        apps_to_run = APPS

    print(f"\n🚀 Génération de {len(apps_to_run)} app(s)\n")

    for app in apps_to_run:
        response, out_dir = generate_with_ollama(
            app["model"], app["prompt"], app["name"], base_dir
        )
        print(f"\n✅ App {app['id']} → {out_dir}\n")
        print("-" * 60)

    print("\n🎉 Terminé !")
