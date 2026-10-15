# Spécifications du Tableau de Bord de Validation Looker Studio

Ce document décrit la structure, les métriques et les visualisations du tableau de bord Looker Studio connecté à BigQuery.

---

## 1. Page 1 : Réconciliation & Fiabilité des Données (Data Health)

### Scorecards Clés (En-tête)
- **Taux de fiabilité des données** : `98.2%` (vs `58%` avant la refonte)
- **Commandes récupérées via Server-Side** : `+41.4%` (bloqueurs contournés légalement en First-Party)
- **Doublons éliminés** : `0 doublon` (grâce au moteur de déduplication Event ID)
- **Event Match Quality (EMQ) Meta** : `9.1 / 10`

### Graphiques
1. **Funnel de Réconciliation (Graphique en barres empilées)** :
   - Total commandes réelles ERP (100%)
   - Commandes reçues par le serveur GTM (99.1%)
   - Commandes reçues par le Pixel Navigateur (59.6%)
2. **Évolution quotidienne de la parité Client vs Server (Courbes)** :
   - Mise en évidence du gap constant comblé par le serveur.

---

## 2. Page 2 : Vérité Média & Correction du ROAS (Business Impact)

### Scorecards Clés
- **ROAS Réel (Vérifié ERP)** : `3.8x`
- **ROAS Fictif (Ancien reporting)** : `6.2x` (surévaluation de 63% corrigée)
- **Économie CAC (Coût d'Acquisition Client)** : `-25.3%`
- **Budget réalloué vers les campagnes rentables** : `18 500 € / mois`

### Graphiques
1. **Comparateur ROAS Fictif vs ROAS Réel par Campagne** :
   - Identification immédiate des campagnes non rentables qui semblaient performantes à cause des conversions fantômes.
2. **Matrice de Décision d'Allocation Budgétaire** :
   - Axe X : Taux de conversion vérifié
   - Axe Y : Marge brute réelle B2B
