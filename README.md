# Vibe Coding Security — Évaluation des vulnérabilités dans les applications générées par l'IA

---

## 📋 Résumé

Ce projet évalue **quantitativement et qualitativement** les vulnérabilités de sécurité présentes dans 20 applications web générées entièrement par des LLMs (Large Language Models), sans intervention humaine après le prompt initial.

| Indicateur | Valeur |
|---|---|
| Applications générées | 20 |
| Modèles LLM évalués | 6 |
| Domaines couverts | 10 |
| Vulnérabilités détectées (statique) | **1 130** |
| Outils d'analyse | Bandit · Semgrep · OWASP ZAP |
| Apps à 0 vuln Python | 3 (stack Node.js/React) |

**Résultat clé :** 100 % des applications contiennent au moins une vulnérabilité HIGH (`debug=True` en production). GPT-5.3 génère le code le plus fonctionnel mais le plus vulnérable (562 vulns / 4 apps). Claude Sonnet 4.6 et Kimi K2 0905 offrent le meilleur équilibre sécurité/complétude.

---

## 📁 Structure du dépôt

```
Vibe-coding-security/
├── apps/                          # Applications générées
│   ├── Claude/                    # Apps 01, 07, 13, 20
│   ├── Gemini/                    # Apps 02, 08, 14
│   ├── GPT-4o/                    # Apps 03, 09, 15, 19
│   ├── Kimi/                      # Apps 04, 10, 16
│   ├── Llama/                     # Apps 05, 11, 17
│   └── DeepSeek/                  # Apps 06, 12, 18
│
├── analysis/                      # Résultats d'analyse
│   ├── static/
│   │   ├── bandit/                # Rapports Bandit JSON + HTML par app
│   │   └── semgrep/               # Rapports Semgrep JSON par app
│   ├── dynamic/
│   │   └── zap_reports/           # Rapports ZAP HTML par app
│   └── summary/
│       └── vulnerabilities_matrix.csv   # Matrice de synthèse globale
│
├── prompts/                       # Prompts standardisés utilisés
│   └── NN_domaine_app_modele.md   # Convention de nommage
├── scripts/                       # Prompts standardisés utilisés
│   ├── generate_app.py                # Script de génération des apps
│   ├── run_analysis.py                # Pipeline analyse statique (Bandit + Semgrep)
│   ├── run_zap.py                     # Pipeline analyse dynamique (OWASP ZAP)
│
└── README.md
```

---

## 🤖 Modèles LLM évalués

| # | Modèle | Fournisseur | Type | Apps | Vulns totales | Densité moy. |
|---|--------|-------------|------|------|---------------|--------------|
| 1 | **GPT-5.3** | OpenAI | Cloud prop. | 03, 09, 15, 19 | **562** | ~171 vulns/KLOC |
| 2 | **Claude Sonnet 4.6** | Anthropic | Cloud prop. | 01, 07, 13, 20 | 203 | ~22 vulns/KLOC* |
| 3 | **Gemini 3.1 Pro** | Google | Cloud prop. | 02, 08, 14 | 180 | ~310 vulns/KLOC** |
| 4 | **Kimi K2 0905** | Moonshot AI | Cloud OS | 04, 10, 16 | 138 | ~52 vulns/KLOC |
| 5 | **DeepSeek-V3** | DeepSeek | Local Ollama | 06, 12, 18 | 42 | partiel*** |
| 6 | **Llama 3 8B** | Meta | Local Ollama | 05, 11, 17 | 5 | incomplet*** |

\* Hors App 01 (Semgrep très sensible sur code médical)  
\** App 02 uniquement — Apps 08 et 14 en Node.js (non analysables par outils Python)  
\*** Code incomplet ou partiel généré par le modèle local

---

## 🗂️ Applications générées

| App | Domaine | LLM | Complexité | Vulns | Note |
|-----|---------|-----|-----------|-------|------|
| 01 | Dossier médical patient | Claude Sonnet 4.6 | Simple | 177 | |
| 02 | Quiz éducatif | Gemini 3.1 Pro | Simple | 180 | |
| 03 | Annonces immobilières | GPT-5.3 | Simple | 50 | |
| 04 | Télémédecine | Kimi K2 0905 | Complexe | 83 | |
| 05 | Budget personnel | Llama 3 8B | Simple | 1 | Code incomplet |
| 06 | Gestion de prêts | DeepSeek-V3 | Complexe | 6 | Code partiel |
| 07 | Microblog social | Claude Sonnet 4.6 | Simple | 9 | |
| 08 | Réseau professionnel | Gemini 3.1 Pro | Complexe | 0 | Stack Node.js |
| 09 | Portail de candidatures | GPT-5.3 | Simple | 64 | |
| 10 | Système RH | Kimi K2 0905 | Complexe | 49 | |
| 11 | Suivi de colis | Llama 3 8B | Simple | 2 | Code incomplet |
| 12 | Gestion de flotte | DeepSeek-V3 | Complexe | 26 | |
| 13 | Gestion locative | Claude Sonnet 4.6 | Complexe | 8 | |
| 14 | Permis en ligne | Gemini 3.1 Pro | Simple | 0 | Stack Node.js |
| 15 | Portail gouvernemental | GPT-5.3 | Complexe | 48 | |
| 16 | LMS éducatif | Kimi K2 0905 | Complexe | 6 | Stack React/TS |
| 17 | Plateforme films | Llama 3 8B | Simple | 2 | Code incomplet |
| 18 | Streaming divertissement | DeepSeek-V3 | Complexe | 10 | |
| 19 | Gestionnaire de mots de passe | GPT-5.3 | Simple | **189** | App la plus vulnérable |
| 20 | Plateforme SecOps | Claude Sonnet 4.6 | Complexe | 9 | |

---

## 🔍 Méthodologie

### Pipeline d'analyse automatisé

```
Prompt standardisé
      ↓
generate_app.py  →  Application Flask + SQLite (ou stack JS/TS)
      ↓
run_analysis.py  →  Bandit (sécurité Python) + Semgrep (--config auto)
      ↓                    ↓                           ↓
  JSON + HTML          static/bandit/          static/semgrep/
      ↓
run_zap.py       →  OWASP ZAP 2.16.1 (Spider + scan actif)
      ↓                    ↓
  HTML report          dynamic/zap_reports/
      ↓
vulnerabilities_matrix.csv  (synthèse globale)
```

### Outils

| Outil | Version | Rôle | Référentiel |
|-------|---------|------|-------------|
| **Bandit** | latest | Analyse statique Python — vulnérabilités connues | CWE |
| **Semgrep** | latest | Analyse statique multi-patterns (`--config auto`) | CWE / OWASP |
| **OWASP ZAP** | 2.16.1 | Analyse dynamique — scan actif + Spider | OWASP Top 10 |

> **Note sur CodeQL :** CodeQL n'a pas été intégré au pipeline automatisé car il nécessite un build tracing par projet (incompatible avec 20 applications distinctes à analyser en série). Bandit + Semgrep couvrent les mêmes familles CWE (CWE-78, CWE-89, CWE-79, CWE-327, CWE-502, CWE-95) pour du Python Flask sans système de build.

---

## 📊 Résultats principaux

### Top 10 des vulnérabilités (OWASP Top 10 2021 + CVSS v3.1)

| # | Vulnérabilité | CWE | OWASP | Fréquence | CVSS | Sévérité |
|---|---------------|-----|-------|-----------|------|----------|
| 1 | Flask `debug=True` en production | CWE-489 | A05 | **100% des apps** | **9.8** | CRITIQUE |
| 2 | Clé secrète codée en dur | CWE-798 | A02 | 95% des apps | 7.5 | ÉLEVÉ |
| 3 | Injection SQL (concaténation) | CWE-89 | A03 | 60% des apps | 9.8 | CRITIQUE |
| 4 | XSS via `Markup()` | CWE-79 | A03 | 55% des apps | 6.1 | MOYEN |
| 5 | Hashage SHA1 pour mots de passe | CWE-327 | A02 | 40% des apps | 7.5 | ÉLEVÉ |
| 6 | `eval()` / `exec()` dangereux | CWE-95 | A03 | 25% des apps | 9.8 | CRITIQUE |
| 7 | Désérialisation Pickle non sécurisée | CWE-502 | A08 | 20% des apps | 9.8 | CRITIQUE |
| 8 | En-têtes HTTP de sécurité absents | CWE-693 | A05 | 100% (ZAP) | 4.3 | MOYEN |
| 9 | Protection CSRF absente | CWE-352 | A01 | 90% (ZAP) | 6.5 | MOYEN |
| 10 | SSL/TLS version faible | CWE-326 | A02 | 35% des apps | 5.9 | MOYEN |

### Profil sécurité par modèle

| Modèle | Complétude | Sécurité statique | Verdict |
|--------|------------|-------------------|---------|
| GPT-5.3 | ✅ Excellente | ❌ Faible | Meilleur générateur, le plus vulnérable |
| Claude Sonnet 4.6 | ✅ Excellente | ✅ Bonne | **Meilleur équilibre** |
| Kimi K2 0905 | ✅ Excellente | ✅ Bonne | **Meilleur équilibre** |
| Gemini 3.1 Pro | ✅ Bonne | ⚠️ Moyenne | Résultats mitigés |
| DeepSeek-V3 | ⚠️ Partielle | ✅ Faible exposition | Code partiel généré |
| Llama 3 8B | ❌ Incomplète | N/A | Code incomplet, peu analysable |

---

## 🚀 Reproduire l'analyse

### Prérequis

```bash
# Python 3.10+
pip install bandit semgrep flask flask-sqlalchemy werkzeug -r requirements-dev.txt

# OWASP ZAP 2.16.1 — téléchargement : https://www.zaproxy.org/download/
# Démarrer ZAP en mode daemon : zap.sh -daemon -port 8090 -host 127.0.0.1
```

### Exécution

```bash
# Cloner le dépôt
git clone https://github.com/Rocklaye/Vibe-coding-security
cd Vibe-coding-security

# Créer l'environnement virtuel
python3 -m venv venv && source venv/bin/activate

# Analyse statique (Bandit + Semgrep) — toutes les apps
python3 run_analysis.py

# Analyse dynamique (OWASP ZAP) — nécessite ZAP daemon actif
python3 run_zap.py

# Résultats disponibles dans analysis/summary/vulnerabilities_matrix.csv
```

### Convention de nommage des apps

```
NN_domaine_app_modele/
│
├── app.py              # Application Flask principale
├── requirements.txt    # Dépendances Python
├── README.md           # Description de l'app
└── templates/          # Templates HTML (si applicable)
```

---

## 📝 Prompts standardisés

Les prompts utilisés pour la génération sont disponibles dans `/prompts/`. Convention de nommage : `NN_domaine_app_modele.md`.

Chaque prompt impose les contraintes suivantes :
- Framework : Flask + SQLite
- Authentification utilisateur (login/logout)
- CRUD complet sur la ressource principale
- Interface HTML fonctionnelle

---

## 🔬 Analyse qualitative

Deux applications ont fait l'objet d'une analyse qualitative approfondie (section 4 du rapport) :

**App 19 — Gestionnaire de mots de passe (GPT-5.3)** : Paradoxe absolu — un outil de cybersécurité lui-même vulnérable. Utilise SHA1 pour hasher les mots de passe, `eval()` pour exécuter du code dynamique, et `pickle` pour la sérialisation. CVSS max : 9.8.

**App 01 — Dossier médical patient (Claude Sonnet 4.6)** : Application manipulant des données de santé personnelles avec une clé secrète hardcodée et `debug=True`. Problématique RGPD et Loi 25.

---

## 📚 Références

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [CVSS v3.1 Specification](https://www.first.org/cvss/v3.1/specification-document)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Semgrep Documentation](https://semgrep.dev/docs/)
- [OWASP ZAP](https://www.zaproxy.org/)
- [CWE List](https://cwe.mitre.org/)

---

## 👤 Auteur

**Ablaye AW** — Étudiant en Master professionnel Cybersécurité, UQAC  
Cours 8SEC918 — Sécurité des applications web  
Saguenay, Québec, 2025

---

*Ce projet a été réalisé dans un cadre académique. Les applications générées sont utilisées uniquement à des fins d'évaluation de sécurité. Aucune application n'a été déployée en production.*
