"""
gtm_ss_proxy_server.py
First-Party Server-Side Tagging Gateway (simulating GTM Server-Side proxy).
- Receives events via first-party endpoint (e.g. data.company-b2b.com)
- Sets and preserves HTTP-Only cookies to bypass Safari ITP expiration
- Masks IP addresses for GDPR compliance
- Coordinates event dispatch to GA4, Meta CAPI, and Google Ads
- Includes an interactive Web UI at "/" for live testing and demonstration
"""

import time
import hashlib
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

try:
    from .cookie_consent_handler import ConsentHandler
except ImportError:
    from cookie_consent_handler import ConsentHandler

app = FastAPI(
    title="GTM Server-Side First-Party Proxy",
    version="1.0.0",
    description="First-party server container proxying tracking signals with GDPR compliance."
)

class EventItem(BaseModel):
    item_id: str
    item_name: str
    price: float
    quantity: int = 1

class TrackingEvent(BaseModel):
    event_name: str
    event_id: str = Field(..., description="Unique event ID for cross-channel deduplication")
    timestamp: Optional[int] = None
    value: Optional[float] = None
    currency: Optional[str] = "EUR"
    user_data: Optional[Dict[str, Any]] = None
    custom_parameters: Optional[Dict[str, Any]] = None
    items: Optional[List[EventItem]] = None
    consent: Optional[Dict[str, str]] = None

def anonymize_ip(ip: str) -> str:
    """Mask the last octet of IPv4 or last 80 bits of IPv6 for GDPR compliance."""
    if not ip:
        return "0.0.0.0"
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
    return "2001:db8::"

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "gtm-ss-proxy",
        "first_party_domain": "data.company-b2b.com",
        "timestamp": int(time.time()),
        "endpoints": {
            "root_ui": "/",
            "swagger_docs": "/docs",
            "redoc": "/redoc",
            "collect_endpoint": "POST /collect"
        }
    }

@app.post("/collect")
async def collect_event(event: TrackingEvent, request: Request, response: Response):
    client_ip = request.client.host if request.client else "127.0.0.1"
    masked_ip = anonymize_ip(client_ip)
    user_agent = request.headers.get("user-agent", "")

    # Manage Consent
    consent_mgr = ConsentHandler(event.consent)
    sanitized_event = consent_mgr.sanitize_payload_for_consent(event.model_dump())

    # First-Party HTTP-Only cookie management to resist Safari ITP
    fbp_cookie = request.cookies.get("_fbp")
    is_new_cookie = False
    if not fbp_cookie:
        is_new_cookie = True
        fbp_cookie = f"fb.1.{int(time.time()*1000)}.{hashlib.md5(client_ip.encode()).hexdigest()[:8]}"
        response.set_cookie(
            key="_fbp",
            value=fbp_cookie,
            max_age=365*24*3600, # 1 year lifetime (server-side HTTP-Only)
            httponly=True,
            secure=True,
            samesite="lax"
        )

    # Compute PII hash preview if email present
    email_hashed = None
    raw_email = (event.user_data or {}).get("email")
    if raw_email and consent_mgr.is_ads_allowed():
        email_hashed = hashlib.sha256(raw_email.strip().lower().encode("utf-8")).hexdigest()

    return {
        "status": "accepted",
        "event_id": event.event_id,
        "event_name": event.event_name,
        "value": event.value,
        "currency": event.currency,
        "anonymized_ip": masked_ip,
        "first_party_cookie": {
            "_fbp": fbp_cookie,
            "created_now": is_new_cookie,
            "http_only": True,
            "itp_safe_duration": "365 days"
        },
        "consent_mode": {
            "analytics_allowed": consent_mgr.is_analytics_allowed(),
            "ads_allowed": consent_mgr.is_ads_allowed(),
            "pii_sanitized_for_gdpr": not consent_mgr.is_ads_allowed()
        },
        "dispatched_to": {
            "meta_capi": {
                "status": "forwarded",
                "sha256_email": email_hashed,
                "event_id": event.event_id
            },
            "google_ads_enhanced": {
                "status": "forwarded",
                "hashed_identifiers": True if email_hashed else False
            },
            "ga4_measurement_protocol": {
                "status": "dispatched",
                "transaction_id": event.event_id
            }
        }
    }

@app.get("/", response_class=HTMLResponse)
def root_ui():
    return """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GTM Server-Side First-Party Gateway — Live Console</title>
    <style>
        :root {
            --bg: #0b0f19;
            --surface: #131b2e;
            --surface-border: #1e293b;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.15);
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text-main);
            font-family: var(--font-family);
            line-height: 1.6;
            padding: 2rem 1rem;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
        }
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--surface-border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }
        .badge-live {
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        .badge-live::before {
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--success);
            box-shadow: 0 0 10px var(--success);
        }
        .nav-links a {
            color: var(--accent);
            text-decoration: none;
            margin-left: 1rem;
            font-weight: 500;
            font-size: 0.95rem;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            border: 1px solid rgba(56, 189, 248, 0.2);
            transition: all 0.2s;
        }
        .nav-links a:hover {
            background: var(--accent-glow);
            border-color: var(--accent);
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1.2fr;
            gap: 1.5rem;
        }
        @media (max-width: 850px) {
            .grid { grid-template-columns: 1fr; }
        }
        .card {
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        .card h2 {
            font-size: 1.2rem;
            margin-bottom: 1rem;
            color: var(--accent);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        label {
            display: block;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.3rem;
            font-weight: 500;
        }
        input, select {
            width: 100%;
            padding: 0.65rem 0.85rem;
            background: #0f172a;
            border: 1px solid var(--surface-border);
            border-radius: 6px;
            color: var(--text-main);
            font-family: inherit;
            margin-bottom: 1rem;
            font-size: 0.95rem;
        }
        input:focus, select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 2px var(--accent-glow);
        }
        .consent-group {
            background: rgba(15, 23, 42, 0.6);
            border: 1px dashed var(--surface-border);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1.2rem;
        }
        .consent-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
        }
        .consent-row:last-child { margin-bottom: 0; }
        .toggle-btn {
            background: #1e293b;
            color: var(--text-muted);
            border: 1px solid #334155;
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .toggle-btn.active-granted {
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
            border-color: var(--success);
        }
        .btn-submit {
            width: 100%;
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: white;
            border: none;
            padding: 0.85rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s, box-shadow 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        .btn-submit:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        }
        .btn-submit:active { transform: translateY(0); }
        pre {
            background: #080c14;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 1rem;
            font-family: var(--font-mono);
            font-size: 0.82rem;
            overflow-x: auto;
            max-height: 520px;
            color: #38bdf8;
        }
        .metric-pill {
            display: inline-block;
            background: rgba(56, 189, 248, 0.1);
            color: #38bdf8;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.75rem;
            margin-right: 0.4rem;
            margin-bottom: 0.5rem;
            border: 1px solid rgba(56, 189, 248, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🎯 GTM Server-Side Gateway</h1>
                <p style="color: var(--text-muted); font-size: 0.9rem;">
                    Console de test First-Party · Meta CAPI · Google Ads · RGPD Consent Mode v2
                </p>
            </div>
            <div>
                <span class="badge-live">Port 8080 · En Ligne</span>
                <nav class="nav-links" style="display: inline-block;">
                    <a href="/docs" target="_blank">📖 Swagger Docs</a>
                    <a href="/health" target="_blank">💚 Health Check</a>
                </nav>
            </div>
        </header>

        <div style="margin-bottom: 1.5rem;">
            <span class="metric-pill">🛡️ Bypass Adblockers First-Party</span>
            <span class="metric-pill">🍪 Cookies HTTP-Only (1 an)</span>
            <span class="metric-pill">🔐 Hachage SHA-256 PII</span>
            <span class="metric-pill">⚖️ Google Consent Mode v2</span>
            <span class="metric-pill">⚡ Déduplication Event ID</span>
        </div>

        <div class="grid">
            <!-- Formulaire de Test -->
            <div class="card">
                <h2>🧪 Simulateur d'Événement</h2>
                <form id="trackingForm">
                    <label for="eventName">Type d'événement</label>
                    <select id="eventName">
                        <option value="purchase">purchase (Commande confirmée)</option>
                        <option value="generate_lead">generate_lead (Demande de devis / RFQ)</option>
                        <option value="add_to_cart">add_to_cart (Ajout panier B2B)</option>
                        <option value="begin_checkout">begin_checkout (Étape paiement)</option>
                    </select>

                    <label for="orderValue">Montant de la transaction (€ HT)</label>
                    <input type="number" id="orderValue" value="1450.00" step="50">

                    <label for="userEmail">Email client professionnel</label>
                    <input type="email" id="userEmail" value="directeur.achats@pro-groupe.fr">

                    <label for="userPhone">Téléphone</label>
                    <input type="text" id="userPhone" value="+33140506070">

                    <div class="consent-group">
                        <label style="color: var(--text-main); margin-bottom: 0.6rem;">🔒 Consent Mode v2 (RGPD)</label>
                        <div class="consent-row">
                            <span>analytics_storage (Mesure GA4)</span>
                            <button type="button" class="toggle-btn active-granted" id="btn-analytics" onclick="toggleConsent('analytics')">granted</button>
                        </div>
                        <div class="consent-row">
                            <span>ad_storage (Cookies Pub / CAPI)</span>
                            <button type="button" class="toggle-btn active-granted" id="btn-ads" onclick="toggleConsent('ads')">granted</button>
                        </div>
                        <div class="consent-row">
                            <span>ad_user_data (Transmission PII)</span>
                            <button type="button" class="toggle-btn active-granted" id="btn-userdata" onclick="toggleConsent('userdata')">granted</button>
                        </div>
                    </div>

                    <button type="submit" class="btn-submit">
                        <span>🚀 Envoyer le Hit Serveur</span>
                    </button>
                </form>
            </div>

            <!-- Console de Sortie -->
            <div class="card">
                <h2>📡 Réponse du Serveur & Traitement</h2>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;" id="responseMeta">
                    En attente d'un événement...
                </div>
                <pre id="outputLog">// Cliquez sur "Envoyer le Hit Serveur" pour tester l'endpoint POST /collect
// Le résultat affichera :
// - L'adresse IP anonymisée (RGPD)
// - Le cookie First-Party HTTP-Only _fbp généré
// - Le hachage SHA-256 des données client (si consenti)
// - Le dispatching vers Meta CAPI, Google Ads et GA4</pre>
            </div>
        </div>
    </div>

    <script>
        const consentState = {
            analytics: 'granted',
            ads: 'granted',
            userdata: 'granted'
        };

        function toggleConsent(type) {
            consentState[type] = consentState[type] === 'granted' ? 'denied' : 'granted';
            const btn = document.getElementById('btn-' + type);
            btn.textContent = consentState[type];
            if (consentState[type] === 'granted') {
                btn.className = 'toggle-btn active-granted';
            } else {
                btn.className = 'toggle-btn';
            }
        }

        document.getElementById('trackingForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const outputLog = document.getElementById('outputLog');
            const responseMeta = document.getElementById('responseMeta');

            const eventId = 'TX-' + Date.now();
            const payload = {
                event_name: document.getElementById('eventName').value,
                event_id: eventId,
                timestamp: Math.floor(Date.now() / 1000),
                value: parseFloat(document.getElementById('orderValue').value),
                currency: 'EUR',
                user_data: {
                    email: document.getElementById('userEmail').value,
                    phone: document.getElementById('userPhone').value,
                    client_id: 'cid_' + Math.floor(Math.random() * 1000000)
                },
                consent: {
                    analytics_storage: consentState.analytics,
                    ad_storage: consentState.ads,
                    ad_user_data: consentState.userdata,
                    ad_personalization: consentState.ads
                }
            };

            responseMeta.textContent = 'Envoi vers POST /collect...';
            try {
                const res = await fetch('/collect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                responseMeta.innerHTML = `<span style="color: #10b981;">✓ HTTP ${res.status} Accepted</span> · Traité en ${res.headers.get('date') || 'temps réel'}`;
                outputLog.textContent = JSON.stringify(data, null, 2);
            } catch (err) {
                responseMeta.innerHTML = `<span style="color: #ef4444;">✗ Erreur : ${err.message}</span>`;
                outputLog.textContent = err.stack || err;
            }
        });
    </script>
</body>
</html>
"""
