#!/usr/bin/env python3
"""
Script d'analyse dynamique — OWASP ZAP v2
Avec les ports corrects pour chaque app
"""

import os
import sys
import time
import subprocess
import requests
from zapv2 import ZAPv2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "apps")
ZAP_DIR  = os.path.join(BASE_DIR, "analysis", "dynamic", "zap_reports")
SUMMARY_DIR = os.path.join(BASE_DIR, "analysis", "summary")
os.makedirs(ZAP_DIR, exist_ok=True)

ZAP_PORT    = 8090
ZAP_ADDRESS = f"http://localhost:{ZAP_PORT}"

# (sous_dossier, nom_app, fichier_principal, port, stack)
APPS = [
    ("Claude",   "01_sante_dossier-medical_claude-sonnet-4.6",       "app.py",   5000, "flask"),
    ("Claude",   "07_social_microblog_claude-sonnet-4-6",             "app.py",   8080, "flask"),
    ("Claude",   "13_immobilier_gestion_claude-sonnet-4.6",           "app.py",   8081, "flask"),
    ("Claude",   "20_cyber_secops_claude-sonnet-4.6",                 "app.py",   8082, "flask"),
    ("Gemini",   "02_education_quiz_gemini-3.1-pro",                  "app.py",   5000, "flask"),
    ("Gemini",   "08_social_reseau-pro_gemini-3.1-pro",               "app.js",   3000, "node"),
    ("Gemini",   "14_gouv_permis_gemini-3.1-pro",                     "app.js",   3000, "node"),
    ("GPT-4o",   "03_immobilier_annonces_gpt-5.3",                    "app.py",   5000, "flask"),
    ("GPT-4o",   "09_rh_candidatures_gpt4o.gpt-5.3",                  "app.py",   5000, "flask"),
    ("GPT-4o",   "15_gouv_portail_gpt4o.gpt-5.3",                     "app.py",   5000, "flask"),
    ("GPT-4o",   "19_cyber_mdp_gpt-5.3",                              "app.py",   5000, "flask"),
    ("Kimi",     "04_sante_telemedecine_kimi-k2-0905",                "app.py",   5000, "flask"),
    ("Kimi",     "10_rh_systeme-rh_kimi-k2-0905",                     "app.py",   5000, "flask"),
    ("Kimi",     "16_education_lms_kimi-k2-0905",                     None,       3000, "react"),
    ("Llama",    "05_finance_budget_llama3-8b",                       "app.py",   5000, "flask"),
    ("Llama",    "11_logistique_colis_llama3-8b",                     "app.py",   5000, "flask"),
    ("Llama",    "17_divertissement_films_llama3-8b",                 "app.py",   5000, "flask"),
    ("DeepSeek", "06_finance_prets_DeepSeek-V3",                      "app.py",   5000, "flask"),
    ("DeepSeek", "12_logistique_flotte_DeepSeek-V3",                  "app.py",   5000, "flask"),
    ("DeepSeek", "18_divertissement_streaming_DeepSeek-V3",           "app.py",   5000, "flask"),
]

def wait_for_app(url, timeout=30):
    print(f"    ⏳ Attente app sur {url}...")
    for i in range(timeout):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code < 500:
                print(f"    ✅ App prête ({i+1}s)")
                return True
        except:
            pass
        time.sleep(1)
    print(f"    ❌ App non démarrée après {timeout}s")
    return False

def wait_for_zap(timeout=30):
    for i in range(timeout):
        try:
            r = requests.get(f"{ZAP_ADDRESS}/JSON/core/view/version/", timeout=2)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def find_entry(app_path, entry_file):
    if entry_file is None:
        return None
    direct = os.path.join(app_path, entry_file)
    if os.path.exists(direct):
        return direct
    for root, dirs, files in os.walk(app_path):
        dirs[:] = [d for d in dirs if d not in ['venv','env','node_modules','__pycache__']]
        if entry_file in files:
            return os.path.join(root, entry_file)
    return None

def launch_app(entry_path, entry_dir, stack):
    """Lance l'app selon la stack."""
    if stack == "flask":
        venv_python = os.path.join(BASE_DIR, "venv", "bin", "python3")
        return subprocess.Popen(
            [venv_python, entry_path],
            cwd=entry_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    elif stack == "node":
        return subprocess.Popen(
            ["node", entry_path],
            cwd=entry_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    elif stack == "react":
        return subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=entry_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    return None

def scan_app(zap, url):
    # Vider la session
    zap.core.new_session(overwrite=True)
    time.sleep(1)

    # Spider
    print(f"    🕷️  Spider...")
    scan_id = zap.spider.scan(url)
    time.sleep(2)
    count = 0
    while int(zap.spider.status(scan_id)) < 100:
        print(f"    🕷️  {zap.spider.status(scan_id)}%", end='\r')
        time.sleep(2)
        count += 1
        if count > 60:
            break
    print(f"    ✅ Spider terminé")

    # Scan actif
    print(f"    ⚡ Scan actif...")
    scan_id = zap.ascan.scan(url)
    time.sleep(2)
    count = 0
    while int(zap.ascan.status(scan_id)) < 100:
        print(f"    ⚡ {zap.ascan.status(scan_id)}%", end='\r')
        time.sleep(3)
        count += 1
        if count > 200:
            print(f"\n    ⚠️  Timeout")
            break
    print(f"    ✅ Scan actif terminé")

    alerts = zap.core.alerts(baseurl=url)
    high   = sum(1 for a in alerts if a.get('risk') == 'High')
    medium = sum(1 for a in alerts if a.get('risk') == 'Medium')
    low    = sum(1 for a in alerts if a.get('risk') == 'Low')
    info   = sum(1 for a in alerts if a.get('risk') == 'Informational')
    print(f"    📊 {len(alerts)} alertes — HIGH:{high} MEDIUM:{medium} LOW:{low} INFO:{info}")
    return {"total": len(alerts), "high": high, "medium": medium, "low": low, "info": info}

def main():
    print(f"\n{'='*60}")
    print(f"🔐 Analyse dynamique — OWASP ZAP v2")
    print(f"{'='*60}\n")

    if not wait_for_zap(30):
        print("❌ ZAP non disponible — lance d'abord :")
        print("/usr/local/bin/zap.sh -daemon -port 8090 -config api.disablekey=true &")
        sys.exit(1)

    zap = ZAPv2(proxies={'http': ZAP_ADDRESS, 'https': ZAP_ADDRESS})
    results = {}

    for subdir, app_name, entry_file, port, stack in APPS:
        print(f"\n{'─'*50}")
        print(f"📱 [{stack.upper()}:{port}] {app_name}")

        app_url  = f"http://localhost:{port}"
        app_path = os.path.join(APPS_DIR, subdir, app_name)

        if not os.path.isdir(app_path):
            print(f"  ⚠️  Dossier introuvable")
            continue

        # Apps React/Vite — skip (pas de lancement auto)
        if stack == "react":
            print(f"  ⏭️  Stack React/Vite — scan manuel requis")
            continue

        entry_path = find_entry(app_path, entry_file)
        if not entry_path:
            print(f"  ⚠️  {entry_file} introuvable")
            continue

        entry_dir = os.path.dirname(entry_path)

        # Lancer l'app
        print(f"  🚀 Lancement ({stack})...")
        proc = launch_app(entry_path, entry_dir, stack)
        if not proc:
            print(f"  ❌ Impossible de lancer l'app")
            continue

        if not wait_for_app(app_url, timeout=30):
            proc.terminate()
            continue

        try:
            scan_results = scan_app(zap, app_url)
            results[app_name] = scan_results

            # Rapport HTML
            report_path = os.path.join(ZAP_DIR, f"{app_name}_zap.html")
            report = zap.core.htmlreport()
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"    📄 Rapport : {report_path}")

        except Exception as e:
            print(f"  ❌ Erreur : {e}")
            results[app_name] = None
        finally:
            proc.terminate()
            proc.wait()
            print(f"  🛑 App arrêtée")
            time.sleep(3)

    # CSV résumé
    csv_file = os.path.join(SUMMARY_DIR, "zap_results.csv")
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("app_name,zap_total,zap_high,zap_medium,zap_low,zap_info\n")
        for app_name, r in results.items():
            if r:
                f.write(f"{app_name},{r['total']},{r['high']},{r['medium']},{r['low']},{r['info']}\n")
            else:
                f.write(f"{app_name},0,0,0,0,0\n")

    print(f"\n{'='*60}")
    print(f"✅ Terminé — {len(results)} apps scannées")
    print(f"📁 Rapports : {ZAP_DIR}")
    print(f"📊 CSV      : {csv_file}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
