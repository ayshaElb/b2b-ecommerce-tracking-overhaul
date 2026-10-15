# Rapport d'Audit & Cartographie des Défaillances de Tracking

**Client** : E-Commerce B2B (Équipements & Solutions professionnelles)  
**Périmètre** : Google Analytics 4 (Client-side), Google Tag Manager Web, Meta Pixel, Google Ads Conversion Tracking  
**Auditeur** : AyshaE Studio — Web Analytics & Data Engineering  

---

## 1. Synthèse Exécutive

L'audit technique a mis en évidence une **défaillance structurelle** du tracking client :

| Constat critique | Impact technique | Impact Business direct |
|---|---|---|
| **40% des événements d'achat manquants** | Bloqueurs de publicité (uBlock, Brave, Safari ITP) bloquant `google-analytics.com` et `connect.facebook.net` | Biais sévère d'attribution, leads qualifiés non comptabilisés |
| **+60% de conversions Ads fictives** | Absence de déduplication et déclenchement répété de la balise au rechargement de la page de confirmation | ROAS artificiellement gonflé (faux signaux envoyés aux algorithmes d'enchères Smart Bidding) |
| **Durée de vie cookie limitée à 24h** | Mesures ITP Apple réduisant la validité des cookies `_fbc`, `_fbp`, `_ga` | Impossibilité d'attribuer les cycles d'achat B2B longs (30-60 jours) |
| **Décisions média biaisées** | Campagnes rentables coupées par erreur, surinvestissement sur des segments sous-performants | Coût d'acquisition client (CAC) 25% trop élevé |

---

## 2. Recommandations & Architecture Cible

1. **Migration vers GTM Server-Side (GCP Cloud Run)** :
   - Routage de tous les hits analytiques via un sous-domaine First-Party (`data.notre-domaine.com`).
   - Rétablissement des cookies First-Party HTTP-Only avec durée de vie maximale (1 an).

2. **Connexion aux APIs de Conversion Serveur-à-Serveur** :
   - **Meta Conversions API (CAPI)** : Envoi redondant Client + Server avec déduplication stricte via `event_id`.
   - **Google Ads Enhanced Conversions** : Transmission des données de conversion enrichies (email hashé SHA-256).

3. **Dashboard de réconciliation temps réel (Looker Studio)** :
   - Monitoring continu de l'Event Match Quality (EMQ).
   - Alignement 1:1 entre le chiffre d'affaires mesuré et le chiffre d'affaires ERP facturé.
