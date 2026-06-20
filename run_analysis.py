#!/usr/bin/env python3
"""
Script d'analyse statique — Bandit + Semgrep
Lance les scans sur toutes les apps et sauvegarde les résultats dans /analysis/
"""

import os
import subprocess
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "apps")
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis")
BANDIT_DIR = os.path.join(ANALYSIS_DIR, "static", "bandit")
SEMGREP_DIR = os.path.join(ANALYSIS_DIR, "static", "semgrep")
SUMMARY_DIR = os.path.join(ANALYSIS_DIR, "summary")

for d in [BANDIT_DIR, SEMGREP_DIR, SUMMARY_DIR]:
    os.makedirs(d, exist_ok=True)

# (sous_dossier, nom_app)
APPS = [
    ("Claude",   "01_sante_dossier-medical_claude-sonnet-4.6"),
    ("Claude",   "07_social_microblog_claude-sonnet-4-6"),
    ("Claude",   "13_immobilier_gestion_claude-sonnet-4.6"),
    ("Claude",   "20_cyber_secops_claude-sonnet-4.6"),
    ("Gemini",   "02_education_quiz_gemini-3.1-pro"),
    ("Gemini",   "08_social_reseau-pro_gemini-3.1-pro"),
    ("Gemini",   "14_gouv_permis_gemini-3.1-pro"),
    ("GPT-4o",   "03_immobilier_annonces_gpt-5.3"),
    ("GPT-4o",   "09_rh_candidatures_gpt4o.gpt-5.3"),
    ("GPT-4o",   "15_gouv_portail_gpt4o.gpt-5.3"),
    ("GPT-4o",   "19_cyber_mdp_gpt-5.3"),
    ("Kimi",     "04_sante_telemedecine_kimi-k2-0905"),
    ("Kimi",     "10_rh_systeme-rh_kimi-k2-0905"),
    ("Kimi",     "16_education_lms_kimi-k2-0905"),
    ("Llama",    "05_finance_budget_llama3-8b"),
    ("Llama",    "11_logistique_colis_llama3-8b"),
    ("Llama",    "17_divertissement_films_llama3-8b"),
    ("DeepSeek", "06_finance_prets_DeepSeek-V3"),
    ("DeepSeek", "12_logistique_flotte_DeepSeek-V3"),
    ("DeepSeek", "18_divertissement_streaming_DeepSeek-V3"),
]

def run_bandit(app_name, app_path):
    output_file = os.path.join(BANDIT_DIR, f"{app_name}_bandit.json")
    print(f"  🔍 Bandit → {app_name}")

    cmd = [
        "bandit", "-r", app_path,
        "-f", "json", "-o", output_file,
        "--exit-zero",
        "-x", ".venv,venv,env,node_modules"
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                data = json.load(f)

            results = data.get("results", [])
            high   = sum(1 for r in results if r.get("issue_severity") == "HIGH")
            medium = sum(1 for r in results if r.get("issue_severity") == "MEDIUM")
            low    = sum(1 for r in results if r.get("issue_severity") == "LOW")

            print(f"    ✅ {len(results)} vulnérabilités — HIGH:{high} MEDIUM:{medium} LOW:{low}")
            return {"total": len(results), "high": high, "medium": medium, "low": low}
        else:
            print(f"    ⚠️  Aucun fichier Python trouvé")
            return {"total": 0, "high": 0, "medium": 0, "low": 0}

    except subprocess.TimeoutExpired:
        print(f"    ⏱️  Timeout")
        return None
    except Exception as e:
        print(f"    ❌ Erreur : {e}")
        return None


def run_semgrep(app_name, app_path):
    output_file = os.path.join(SEMGREP_DIR, f"{app_name}_semgrep.json")
    print(f"  🔍 Semgrep → {app_name}")

    cmd = [
        "semgrep", "--config", "auto",
        "--json", "--output", output_file,
        "--no-git-ignore",
        "--timeout", "60",
        app_path
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                data = json.load(f)

            findings = data.get("results", [])
            high   = sum(1 for r in findings if r.get("extra", {}).get("severity") in ["ERROR", "HIGH"])
            medium = sum(1 for r in findings if r.get("extra", {}).get("severity") in ["WARNING", "MEDIUM"])
            low    = sum(1 for r in findings if r.get("extra", {}).get("severity") in ["INFO", "LOW"])

            print(f"    ✅ {len(findings)} findings — HIGH:{high} MEDIUM:{medium} LOW:{low}")
            return {"total": len(findings), "high": high, "medium": medium, "low": low}
        else:
            print(f"    ⚠️  Aucun résultat")
            return {"total": 0, "high": 0, "medium": 0, "low": 0}

    except subprocess.TimeoutExpired:
        print(f"    ⏱️  Timeout")
        return None
    except Exception as e:
        print(f"    ❌ Erreur : {e}")
        return None


def generate_summary(all_results):
    csv_file = os.path.join(SUMMARY_DIR, "vulnerabilities_matrix.csv")

    with open(csv_file, "w", encoding="utf-8") as f:
        f.write("app_id,app_name,llm,complexite,")
        f.write("bandit_total,bandit_high,bandit_medium,bandit_low,")
        f.write("semgrep_total,semgrep_high,semgrep_medium,semgrep_low,")
        f.write("total_vulns\n")

        complexe_ids = ["04","06","08","10","12","13","15","16","18","20"]

        for (subdir, app_name), results in all_results.items():
            app_id = app_name.split("_")[0]
            complexite = "Complexe" if app_id in complexe_ids else "Simple"

            bandit  = results.get("bandit")  or {"total":0,"high":0,"medium":0,"low":0}
            semgrep = results.get("semgrep") or {"total":0,"high":0,"medium":0,"low":0}
            total   = bandit["total"] + semgrep["total"]

            f.write(f'{app_id},{app_name},{subdir},{complexite},')
            f.write(f'{bandit["total"]},{bandit["high"]},{bandit["medium"]},{bandit["low"]},')
            f.write(f'{semgrep["total"]},{semgrep["high"]},{semgrep["medium"]},{semgrep["low"]},')
            f.write(f'{total}\n')

    print(f"\n📊 CSV généré : {csv_file}")


def main():
    print(f"\n{'='*60}")
    print(f"🔐 Analyse statique — Bandit + Semgrep")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    all_results = {}
    apps_found = 0

    for subdir, app_name in APPS:
        app_path = os.path.join(APPS_DIR, subdir, app_name)

        if not os.path.isdir(app_path):
            print(f"⚠️  Introuvable : {app_path}")
            continue

        apps_found += 1
        print(f"\n[{apps_found}/20] {app_name}")

        results = {}
        results["bandit"]  = run_bandit(app_name, app_path)
        results["semgrep"] = run_semgrep(app_name, app_path)
        all_results[(subdir, app_name)] = results

    generate_summary(all_results)

    print(f"\n{'='*60}")
    print(f"✅ {apps_found} apps scannées")
    print(f"📁 Bandit  : {BANDIT_DIR}")
    print(f"📁 Semgrep : {SEMGREP_DIR}")
    print(f"📊 CSV     : {SUMMARY_DIR}/vulnerabilities_matrix.csv")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
