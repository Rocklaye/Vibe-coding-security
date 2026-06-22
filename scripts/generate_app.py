import requests
import json
import os
import sys
import re


## Script de génération d'applications avec Ollama


OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = """You are an expert Python/Flask developer. 
Your ONLY job is to write complete, working code files.
NEVER explain, NEVER give advice, NEVER describe steps.
ONLY output code files in this exact format:

### filename.py
```python
[complete file content]
```

### templates/index.html
```html
[complete file content]
```

Continue until ALL files are written. No explanations before or after."""

def generate_with_ollama(model, prompt, output_dir):
    print(f"\n{'='*60}")
    print(f"Modèle  : {model}")
    print(f"Dossier : {output_dir}")
    print(f"{'='*60}\n")

    os.makedirs(output_dir, exist_ok=True)

    # Combine system prompt + user prompt pour les modèles locaux
    full_prompt = f"{SYSTEM_PROMPT}\n\nTASK: {prompt}\n\nStart immediately with ### app.py"

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": True,
        "options": {
            "num_predict": 12000,
            "temperature": 0.1,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        }
    }

    full_response = ""
    print("Génération en cours", end="", flush=True)

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=600)
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                chunk = data.get("response", "")
                full_response += chunk
                print(".", end="", flush=True)
                if data.get("done", False):
                    break
    except requests.exceptions.Timeout:
        print("\n⚠️  Timeout — modèle trop lent")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")

    print(f"\n\n✅ {len(full_response)} caractères générés\n")

    # Sauvegarder la réponse brute
    with open(os.path.join(output_dir, "raw_response.txt"), "w", encoding="utf-8") as f:
        f.write(full_response)
    print(f"📄 raw_response.txt sauvegardé")

    # Extraire les fichiers
    extract_code_files(full_response, output_dir)
    return full_response


def extract_code_files(response_text, output_dir):
    saved = []

    # Pattern principal : ### filename.ext suivi d'un bloc ```
    pattern = r'###\s+([\w/\-\.]+\.(?:py|html|js|css|txt|md|json|cfg|sh|sql))\s*\n```[\w]*\n(.*?)```'
    matches = re.findall(pattern, response_text, re.DOTALL)

    # Pattern secondaire : **filename.ext** ou `filename.ext`
    if not matches:
        pattern2 = r'(?:\*\*|`)([\w/\-\.]+\.(?:py|html|js|css|txt|md|json|cfg|sh|sql))(?:\*\*|`)\s*\n```[\w]*\n(.*?)```'
        matches = re.findall(pattern2, response_text, re.DOTALL)

    # Pattern tertiaire : juste le nom avant ```
    if not matches:
        pattern3 = r'([\w/\-\.]+\.(?:py|html|js|css|txt|md|json|cfg|sh|sql))\s*\n```[\w]*\n(.*?)```'
        matches = re.findall(pattern3, response_text, re.DOTALL)

    # Dédupliquer
    seen = set()
    unique = []
    for name, code in matches:
        if name not in seen and len(code.strip()) > 20:
            seen.add(name)
            unique.append((name, code))

    if unique:
        print(f"\n📁 {len(unique)} fichiers extraits :")
        for filename, code in unique:
            filepath = os.path.join(output_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code.strip())
            lines = len(code.strip().split('\n'))
            print(f"  ✅ {filename} ({lines} lignes)")
            saved.append(filename)
    else:
        # Fallback : blocs numérotés
        blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response_text, re.DOTALL)
        blocks = [b for b in blocks if len(b.strip()) > 20]
        print(f"\n⚠️  Noms de fichiers non détectés — {len(blocks)} blocs extraits :")
        for i, block in enumerate(blocks):
            if 'from flask' in block or 'import flask' in block.lower() or 'app.route' in block:
                fname = f"app_{i+1}.py"
            elif '<!DOCTYPE' in block or '<html' in block:
                fname = f"template_{i+1}.html"
            elif 'function' in block or 'const ' in block:
                fname = f"script_{i+1}.js"
            else:
                fname = f"block_{i+1}.txt"
            filepath = os.path.join(output_dir, fname)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(block.strip())
            print(f"  📄 {fname} ({len(block.strip().split(chr(10)))} lignes)")
            saved.append(fname)

    return saved


# ─── APPS LOCALES ──────────────────────────────────────────────────────────────

APPS = [
    {
        "id": "05",
        "name": "05_finance_budget_llama3-8b",
        "model": "llama3:8b",
        "prompt": """Create a complete budget tracking web application with Flask and SQLite.

Files needed: app.py, models.py, templates/base.html, templates/login.html, templates/register.html, templates/dashboard.html, templates/add_transaction.html, static/style.css, requirements.txt, README.md

Features:
- User registration and login with password hashing
- Add income/expense transactions with categories and dates
- Monthly summary with total income, expenses, balance
- Transaction history with date filter
- Expense breakdown by category

Use Flask, SQLAlchemy, werkzeug.security for password hashing. SQLite database."""
    },
    {
        "id": "06",
        "name": "06_finance_prets_deepseek-coder-6.7b",
        "model": "deepseek-coder:6.7b",
        "prompt": """Create a complete peer-to-peer lending web application with Flask and SQLite.

Files needed: app.py, models.py, templates/base.html, templates/login.html, templates/register.html, templates/dashboard.html, templates/loans.html, templates/loan_detail.html, static/style.css, requirements.txt, README.md

Features:
- User registration and login (borrower/lender roles)
- Submit loan requests with amount, duration, justification
- List available loan requests for lenders
- Accept loan and track repayments
- Transaction history per user
- Simple credit score on dashboard

Use Flask, SQLAlchemy, werkzeug.security. SQLite database."""
    },
    {
        "id": "11",
        "name": "11_logistique_colis_llama3-8b",
        "model": "llama3:8b",
        "prompt": """Create a complete parcel tracking web application with Flask and SQLite.

Files needed: app.py, models.py, templates/base.html, templates/login.html, templates/register.html, templates/dashboard.html, templates/create_parcel.html, templates/track.html, static/style.css, requirements.txt, README.md

Features:
- User registration and login (sender/courier/client roles)
- Create parcel with unique tracking number
- Update delivery status (pending, in transit, delivered)
- Public tracking page by tracking number
- Delivery history per client

Use Flask, SQLAlchemy, werkzeug.security. SQLite database."""
    },
    {
        "id": "12",
        "name": "12_logistique_flotte_deepseek-coder-6.7b",
        "model": "deepseek-coder:6.7b",
        "prompt": """Create a complete fleet management web application with Flask and SQLite.

Files needed: app.py, models.py, templates/base.html, templates/login.html, templates/dashboard.html, templates/vehicles.html, templates/drivers.html, templates/routes.html, templates/incidents.html, static/style.css, requirements.txt, README.md

Features:
- Multi-role login (driver, dispatcher, admin)
- Vehicle management (plate, type, status, mileage)
- Driver assignment to vehicles
- Route/delivery planning
- Incident and maintenance log
- Fleet statistics dashboard

Use Flask, SQLAlchemy, werkzeug.security. SQLite database."""
    },
    {
        "id": "17",
        "name": "17_divertissement_films_llama3-8b",
        "model": "llama3:8b",
        "prompt": """Create a complete movie and series library web application with Flask and SQLite.

Files needed: app.py, models.py, templates/base.html, templates/login.html, templates/register.html, templates/catalog.html, templates/movie_detail.html, templates/profile.html, templates/watchlist.html, static/style.css, requirements.txt, README.md

Features:
- User registration and login
- Movie/series catalog with title, genre, year, rating
- Search and filter by genre, year, rating
- Add to favorites
- User reviews and ratings
- Personal watchlist (to watch, watching, watched)

Use Flask, SQLAlchemy, werkzeug.security. SQLite database."""
    },
    {
        "id": "18",
        "name": "18_divertissement_streaming_deepseek-coder-6.7b",
        "model": "deepseek-coder:6.7b",
        "prompt": """Create a complete streaming platform web application with Flask and SQLite.

Files needed: app.py, models.py, templates/base.html, templates/login.html, templates/register.html, templates/catalog.html, templates/player.html, templates/subscription.html, templates/admin.html, static/style.css, requirements.txt, README.md

Features:
- User registration and login with subscription tiers (free/premium)
- Content catalog with access control based on subscription
- Simulated video player page
- Multiple profiles per account
- Watch history and recommendations
- Subscription and payment management
- Admin dashboard for content and subscriber management

Use Flask, SQLAlchemy, werkzeug.security. SQLite database."""
    },
]


if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps")

    if len(sys.argv) > 1:
        app_id = sys.argv[1]
        apps_to_run = [a for a in APPS if a["id"] == app_id]
        if not apps_to_run:
            print(f"❌ App '{app_id}' introuvable. IDs : {[a['id'] for a in APPS]}")
            sys.exit(1)
    else:
        apps_to_run = APPS

    print(f"\n🚀 Génération de {len(apps_to_run)} app(s) avec Ollama\n")

    for app in apps_to_run:
        output_dir = os.path.join(base_dir, app["name"])
        generate_with_ollama(app["model"], app["prompt"], output_dir)
        print(f"\n✅ App {app['id']} → {output_dir}\n")
        print("-" * 60)

    print("\n🎉 Génération terminée !")
