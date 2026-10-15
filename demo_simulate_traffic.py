"""
demo_simulate_traffic.py
Generates simulated B2B e-commerce transactions and sends them to the local
GTM Server-Side Gateway (http://localhost:8080/collect).
Demonstrates:
- Consent Mode v2 impact on PII sanitization
- First-Party HTTP-Only cookie receipt
- Event ID deduplication and multi-channel dispatch
"""

import time
import json
import random
import urllib.request

BASE_URL = "http://localhost:8080"

SAMPLE_B2B_COMPANIES = [
    {"email": "contact@logistique-pro.fr", "phone": "+33140506070", "value": 2850.0},
    {"email": "achats@industrie-nord.com", "phone": "+33320102030", "value": 4120.0},
    {"email": "direction@tech-systems.io", "phone": "+33561708090", "value": 1390.0},
    {"email": "atelier@mecanique-precision.fr", "phone": "+33472001122", "value": 890.0},
]

def check_health():
    print("1. Verification de l'etat du serveur (/health)...")
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=3) as resp:
            data = json.loads(resp.read().decode())
            print(f"   [OK] Statut: {data['status']} | Service: {data['service']}\n")
    except Exception as e:
        print(f"   [ERREUR] Le serveur n'est pas accessible sur {BASE_URL}: {e}")
        return False
    return True

def send_simulated_event(event_name: str, client_data: dict, consent_granted: bool = True):
    event_id = f"TX-B2B-{int(time.time()*1000)}-{random.randint(100, 999)}"
    
    consent = {
        "analytics_storage": "granted",
        "ad_storage": "granted" if consent_granted else "denied",
        "ad_user_data": "granted" if consent_granted else "denied",
        "ad_personalization": "granted" if consent_granted else "denied"
    }

    payload = {
        "event_name": event_name,
        "event_id": event_id,
        "timestamp": int(time.time()),
        "value": client_data["value"],
        "currency": "EUR",
        "user_data": {
            "email": client_data["email"],
            "phone": client_data["phone"],
            "client_id": f"ga4_cid_{random.randint(10000, 99999)}"
        },
        "consent": consent
    }

    req = urllib.request.Request(
        f"{BASE_URL}/collect",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    with urllib.request.urlopen(req, timeout=3) as resp:
        res_data = json.loads(resp.read().decode())
        consent_label = "Opt-in Ads (Granted)" if consent_granted else "Refus Ads (Denied - RGPD)"
        print(f"-> Envoi '{event_name}' ({client_data['value']} EUR) | {consent_label}")
        print(f"   Event ID       : {res_data['event_id']}")
        print(f"   IP Anonymisee  : {res_data['anonymized_ip']}")
        print(f"   Cookie _fbp    : {res_data['first_party_cookie']['_fbp']}")
        sha = res_data['dispatched_to']['meta_capi']['sha256_email']
        print(f"   SHA-256 Meta   : {sha[:16]}... (securise)" if sha else "   SHA-256 Meta   : [PURGE - Non consenti RGPD]")
        print("-" * 65)

def main():
    print("=" * 65)
    print("SIMULATEUR DE TRAFIC - GTM SERVER-SIDE B2B TRACKING")
    print("=" * 65)

    if not check_health():
        return

    print("2. Envoi de transactions simulees avec Consent Mode v2...")
    for i, company in enumerate(SAMPLE_B2B_COMPANIES):
        # Alterne entre consentement accepte et refuse pour tester la conformite RGPD
        granted = (i % 2 == 0)
        send_simulated_event("purchase", company, consent_granted=granted)
        time.sleep(0.5)

    print("\n[SUCCES] Toutes les transactions ont ete traitees par la passerelle First-Party !")
    print("Rendez-vous sur http://localhost:8080/ pour la console visuelle interactive.")
    print("Documentation API disponible sur http://localhost:8080/docs")

if __name__ == "__main__":
    main()
