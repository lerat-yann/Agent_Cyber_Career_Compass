#!/usr/bin/env python3
"""
🔧 Diagnostic France Travail — Étape par étape
================================================
Ce script teste toute la chaîne de l'API France Travail
et vous dit exactement où ça coince.

Usage :
    python test_france_travail.py

Prérequis :
    - Fichier .env avec FRANCE_TRAVAIL_CLIENT_ID et FRANCE_TRAVAIL_CLIENT_SECRET
    - pip install requests python-dotenv
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

FT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
FT_OFFRES_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

def main():
    print("=" * 60)
    print("🔧 DIAGNOSTIC API FRANCE TRAVAIL")
    print("=" * 60)

    # ── ÉTAPE 1 : Vérifier les credentials dans .env ─────────
    print("\n📋 ÉTAPE 1 — Credentials .env")
    client_id = os.environ.get("FRANCE_TRAVAIL_CLIENT_ID", "")
    client_secret = os.environ.get("FRANCE_TRAVAIL_CLIENT_SECRET", "")

    if not client_id:
        print("   ❌ FRANCE_TRAVAIL_CLIENT_ID est VIDE ou absent du .env")
        print("   → Allez sur https://francetravail.io/data/api/offres-emploi")
        print("   → Créez une application et copiez le Client ID dans votre .env")
        sys.exit(1)
    else:
        print(f"   ✅ Client ID trouvé : {client_id[:8]}...{client_id[-4:]}")

    if not client_secret:
        print("   ❌ FRANCE_TRAVAIL_CLIENT_SECRET est VIDE ou absent du .env")
        sys.exit(1)
    else:
        print(f"   ✅ Client Secret trouvé : {client_secret[:4]}...{client_secret[-4:]}")

    # ── ÉTAPE 2 : Obtenir un token OAuth2 ─────────────────────
    print("\n🔑 ÉTAPE 2 — Token OAuth2")
    try:
        resp = requests.post(
            FT_TOKEN_URL,
            params={"realm": "/partenaire"},
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "api_offresdemploiv2 o2dsoffre",
            },
            timeout=15,
        )
        print(f"   HTTP Status : {resp.status_code}")

        if resp.status_code == 200:
            token_data = resp.json()
            token = token_data.get("access_token", "")
            expires_in = token_data.get("expires_in", 0)
            print(f"   ✅ Token obtenu ! (expire dans {expires_in}s)")
            print(f"   Token : {token[:20]}...")
        elif resp.status_code == 401:
            print("   ❌ ERREUR 401 — Credentials invalides !")
            print("   → Vos credentials ont probablement expiré ou sont incorrects")
            print("   → Allez sur https://francetravail.io/data/api pour les régénérer")
            print(f"   Réponse : {resp.text[:300]}")
            sys.exit(1)
        elif resp.status_code == 403:
            print("   ❌ ERREUR 403 — Accès refusé")
            print("   → Votre application n'a peut-être pas les bons scopes")
            print("   → Vérifiez que 'api_offresdemploiv2' est activé sur votre app")
            print(f"   Réponse : {resp.text[:300]}")
            sys.exit(1)
        else:
            print(f"   ❌ ERREUR inattendue : {resp.status_code}")
            print(f"   Réponse : {resp.text[:300]}")
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("   ❌ ERREUR DE CONNEXION — Impossible de joindre le serveur")
        print("   → Vérifiez votre connexion internet")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("   ❌ TIMEOUT — Le serveur ne répond pas")
        sys.exit(1)

    # ── ÉTAPE 3 : Requête offres d'emploi ─────────────────────
    print("\n🔍 ÉTAPE 3 — Recherche d'offres (mot-clé : 'cybersecurite')")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        # Test 1 : recherche large SANS filtre domaine
        params_large = {
            "motsCles": "cybersecurite",
            "range": "0-4",
        }
        resp1 = requests.get(FT_OFFRES_URL, headers=headers, params=params_large, timeout=15)
        print(f"\n   Test A (sans filtre domaine) — HTTP {resp1.status_code}")

        if resp1.status_code == 200:
            data1 = resp1.json()
            total1 = resp1.headers.get("Content-Range", "").split("/")[-1] if "Content-Range" in resp1.headers else len(data1.get("resultats", []))
            offres1 = data1.get("resultats", [])
            print(f"   ✅ {total1} offres trouvées !")
            if offres1:
                print(f"   Exemple : {offres1[0].get('intitule', 'N/A')} — {offres1[0].get('lieuTravail', {}).get('libelle', 'N/A')}")
        elif resp1.status_code == 204:
            print("   ⚠️  0 offres (HTTP 204 No Content)")
        elif resp1.status_code == 401:
            print("   ❌ Token rejeté (401) — le token est peut-être déjà expiré")
            print(f"   Réponse : {resp1.text[:300]}")
        else:
            print(f"   ❌ Erreur : {resp1.text[:300]}")

        # Test 2 : avec filtre domaine=M (comme dans votre code actuel)
        params_domaine = {
            "motsCles": "cybersecurite",
            "domaine": "M",
            "range": "0-4",
        }
        resp2 = requests.get(FT_OFFRES_URL, headers=headers, params=params_domaine, timeout=15)
        print(f"\n   Test B (avec domaine='M') — HTTP {resp2.status_code}")

        if resp2.status_code == 200:
            data2 = resp2.json()
            total2 = resp2.headers.get("Content-Range", "").split("/")[-1] if "Content-Range" in resp2.headers else len(data2.get("resultats", []))
            print(f"   ✅ {total2} offres trouvées avec filtre domaine")
        elif resp2.status_code == 204:
            print("   ⚠️  0 offres avec domaine='M' — CE FILTRE PEUT ÊTRE LE PROBLÈME !")
            print("   → Le filtre domaine='M' exclut peut-être les offres cyber")
        else:
            print(f"   ❌ Erreur : {resp2.text[:300]}")

        # Test 3 : recherche 'pentester' (le cas qui échoue)
        params_pentester = {
            "motsCles": "cybersecurite test intrusion",
            "range": "0-4",
        }
        resp3 = requests.get(FT_OFFRES_URL, headers=headers, params=params_pentester, timeout=15)
        print(f"\n   Test C (pentester sans domaine) — HTTP {resp3.status_code}")

        if resp3.status_code == 200:
            data3 = resp3.json()
            total3 = resp3.headers.get("Content-Range", "").split("/")[-1] if "Content-Range" in resp3.headers else len(data3.get("resultats", []))
            offres3 = data3.get("resultats", [])
            print(f"   ✅ {total3} offres pentester trouvées !")
            if offres3:
                for o in offres3[:3]:
                    print(f"      • {o.get('intitule', 'N/A')} — {o.get('entreprise', {}).get('nom', 'N/A')} ({o.get('lieuTravail', {}).get('libelle', 'N/A')})")
        elif resp3.status_code == 204:
            print("   ⚠️  0 offres pentester")
        else:
            print(f"   ❌ Erreur : {resp3.text[:300]}")

    except Exception as e:
        print(f"   ❌ Exception : {e}")

    # ── RÉSUMÉ ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print("""
Si ÉTAPE 1 ❌ → Ajoutez les credentials dans .env
Si ÉTAPE 2 ❌ → Régénérez vos credentials sur francetravail.io
Si Test A ✅ mais Test B ⚠️  → Le filtre domaine='M' est le problème
   → Solution : retirer le paramètre 'domaine' de tools.py
Si tout ✅ → L'API fonctionne, le problème est dans le câblage agent
    """)


if __name__ == "__main__":
    main()
