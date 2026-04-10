# 🛡️ Cyber Career Compass

Un assistant d'orientation vers les métiers de la cybersécurité, basé sur une architecture **multi-agents** avec des **données réelles** (MITRE ATT&CK, NIST NVD, NIST NICE Framework, France Travail) et une **intégration MCP** (Gmail + Google Calendar via Composio).

> **[🚀 Démo live sur Streamlit Cloud](https://agent-cyber-career-compass.streamlit.app/)**

---

## Ce que fait cet agent

L'agent aide les utilisateurs à planifier leur carrière en cybersécurité en coordonnant plusieurs agents spécialisés. Il peut :

- Analyser un profil et recommander des métiers cyber compatibles
- Expliquer et comparer les métiers (SOC, Pentest, Cloud Security, GRC, AppSec…)
- Identifier les compétences nécessaires par métier
- Construire un plan d'apprentissage personnalisé avec ressources curatées
- Recommander des ressources d'apprentissage réelles (gratuites ou freemium) avec URLs, étoiles ★ et coûts
- Récupérer les techniques MITRE ATT&CK réelles liées à un métier (API live)
- Rechercher le contexte d'un CVE via le NIST NVD (API live)
- Fournir les données **réelles** du marché de l'emploi cyber en France (API France Travail live)
- **📧 Envoyer le plan complet par email** via Gmail MCP (Composio)
- **📅 Planifier le parcours dans Google Calendar** via Google Calendar MCP (Composio)

L'agent **refuse toute demande d'exploitation opérationnelle** grâce à un système de guardrails à 3 couches.

---

## Architecture

### Vue d'ensemble

```
User Input (Streamlit)
    ↓
[Guardrail 3 couches] → Rejette si hors-sujet ou offensif
    ↓
[Manager — Orchestrateur] → Routage dynamique vers les agents spécialisés
    ├→ [get_plan_complet]             → Fiche NICE + compétences + ressources curatées (Python pur)
    ├→ [Agent Marché Emploi]          → Données emploi live (API France Travail)
    ├→ [Agent Matching Profil]        → Analyse profil → recommandation métiers
    └→ [Agent Knowledge Map]          → MITRE ATT&CK, CVE (APIs live)
    ↓
Réponse synthétisée affichée dans le chat
    ↓
[Boutons MCP]
    ├→ 📧 [Agent Gmail MCP]           → Envoie le plan par mail (Composio MCP)
    └→ 📅 [Agent Google Calendar MCP] → Planifie le parcours dans Calendar (Composio MCP)
```

### Pattern : Agents-as-Tools avec orchestration intelligente

Chaque agent spécialisé est wrappé comme un outil de délégation que le manager peut appeler. Le manager **décide dynamiquement** quels agents appeler et dans quel ordre selon la question posée — il n'y a pas de séquence fixe. Le manager synthétise les réponses de tous les agents appelés.

---

## Les agents (7 au total)

### Agents principaux (orchestration cyber)

| # | Agent | Fichier | Rôle | Outils utilisés |
|---|-------|---------|------|-----------------|
| 1 | **Manager — Orchestrateur** | `manager.py` | Reçoit la question, décide quels agents appeler, synthétise la réponse finale | 4 outils de délégation |
| 2 | **Agent Marché Emploi** | `cyber_agents.py` | Recherche en temps réel les offres d'emploi cyber via l'API France Travail | `get_job_market_data` |
| 3 | **Agent Matching Profil** | `cyber_agents.py` | Analyse le profil utilisateur et recommande 1 à 3 métiers cyber compatibles | `get_all_roles_overview`, `get_role_details` |
| 4 | **Agent Knowledge Map** | `cyber_agents.py` | Relie un métier aux concepts cyber réels (MITRE ATT&CK, CVE, groupes APT) | `get_mitre_techniques_for_role`, `get_mitre_groups_and_software`, `get_mitre_cve_context`, `get_mitre_latest_techniques` |
| 5 | **Agent Learning Coach** | `agent_learning_coach.py` | Base de ressources curatées (10 domaines × 8 catégories × FR/EN) | `get_ressources_domaine`, `list_domaines_disponibles` |

### Agents MCP (intégrations externes via Composio)

| # | Agent | Fichier | Rôle | Protocole |
|---|-------|---------|------|-----------|
| 6 | **Agent Gmail MCP** | `mcp_agents.py` | Envoie le plan d'apprentissage complet par email via Gmail | MCP Streamable HTTP (Composio) |
| 7 | **Agent Google Calendar MCP** | `mcp_agents.py` | Crée des événements dans Google Calendar pour chaque phase du parcours | MCP Streamable HTTP (Composio) |

### Agent auxiliaire

| Agent | Fichier | Rôle |
|-------|---------|------|
| **Classifieur Guardrail** | `guardrails.py` | Agent éphémère (couche 3) qui classifie les requêtes ambigues comme "orientation_cyber" ou "hors_sujet" |

---

## Outils et fonctions

### Outil principal : `get_plan_complet` (Python pur, 0 appel LLM)

Assemble de manière **déterministe** pour chaque métier :
- Fiche métier NICE Framework (missions, profil, salaire indicatif)
- Compétences prioritaires classées par importance
- Ressources curatées avec URLs, étoiles ★, coûts (8 catégories × FR/EN)
- Parcours guidé étape par étape

### Outils API live (`tools.py`)

| Outil | Source | Type |
|-------|--------|------|
| `get_mitre_techniques_for_role` | MITRE ATT&CK REST API | Données réelles live |
| `get_mitre_groups_and_software` | MITRE ATT&CK REST API | Données réelles live |
| `get_mitre_cve_context` | NIST NVD API v2.0 | Données réelles live |
| `get_mitre_latest_techniques` | MITRE ATT&CK REST API | Données réelles live |
| `get_job_market_data` | France Travail API v2 | Données réelles live |
| `get_role_details` | NIST NICE Framework SP 800-181 | Statique structuré |
| `get_all_roles_overview` | NIST NICE Framework | Statique structuré |

### Intégration MCP (`mcp_agents.py`)

| Fonction | Serveur MCP | Transport | Optimisations |
|----------|-------------|-----------|---------------|
| `envoyer_par_mail` | Gmail via Composio | Streamable HTTP | Tool filter (1 tool exposé sur 22) |
| `planifier_calendrier` | Google Calendar via Composio | Streamable HTTP | Tool filter (1 tool sur 22) + extraction parcours + dates calculées en Python |

**Optimisations MCP pour respecter la limite Groq 10k tokens :**
- **Tool filtering** : seuls les tools nécessaires sont exposés au LLM (1-2 sur 22), réduisant les tokens de schéma de ~5000 à ~500
- **Extraction intelligente du parcours** : pour Calendar, seules les étapes sont extraites (3 stratégies : lignes avec →, lignes "Mois/Phase", lignes numérotées)
- **Dates calculées en Python** : les dates des événements Calendar sont calculées avec `datetime` en respectant la durée de chaque phase, pas par le LLM

### ⚠️ Limitation Google Calendar (version actuelle)

**Le bouton 📧 Gmail fonctionne pour tous les utilisateurs** — le mail est envoyé depuis le compte de l'application vers n'importe quelle adresse email.

**Le bouton 📅 Google Calendar ne fonctionne que pour le compte du développeur.** Les événements sont créés dans le calendrier Google lié au compte Composio de l'application. Un utilisateur externe ne verra pas les événements dans son propre calendrier.

**Pourquoi ?** L'URL MCP Composio est liée à un seul compte Google via OAuth. Pour que chaque utilisateur puisse utiliser son propre calendrier, il faudrait un flux d'authentification individuel.

**Roadmap V8 — Google Calendar multi-utilisateurs :**
- Ajouter un bouton "Connecter mon Google Calendar" dans la sidebar
- Implémenter un flux OAuth 2.0 Google par utilisateur (redirection → autorisation → callback)
- Stocker le token OAuth de chaque utilisateur dans sa session Streamlit (`st.session_state`)
- Passer le token utilisateur au serveur MCP Composio (via le paramètre `user_id` de l'URL ou via les Connected Accounts Composio)
- Alternative : héberger un serveur MCP Google Calendar custom qui accepte un token par requête

---

## Guardrails (`guardrails.py`)

Validation en 3 couches :

1. **Couche offensive (blocage immédiat)** — mots-clés d'exploitation opérationnelle → rejet sans appel API
2. **Couche cyber/orientation (passage immédiat)** — mots-clés orientation/cyber/CVE → accepté sans appel API
3. **Couche LLM (cas ambigus)** — classifieur `llama-3.1-8b-instant` avec fail-safe (si le LLM échoue → blocage par défaut)

---

## Système de fallback (V6)

L'application utilise un **double provider** avec basculement automatique :

- **Provider principal** : Groq (Kimi K2) — meilleur tool-calling gratuit
- **Provider fallback** : OpenRouter (modèles gratuits) — activé si Groq rate-limit (429)

Le basculement se fait **à chaud** via un registre d'agents (`register_agent`) — tous les agents sont mutés in-place sans redémarrage. Un bouton "Réessayer avec Groq" permet de revenir au provider principal.

---

## Profilage utilisateur (V5)

La sidebar Streamlit permet de renseigner un profil optionnel :
- Niveau technique (débutant → expert)
- Temps disponible par semaine
- Budget formation
- Niveau d'anglais

Le profil est injecté dans la requête pour personnaliser les recommandations (ressources adaptées au niveau, budget, langue).

---

## Sources de données réelles

### MITRE ATT&CK (via GitHub STIX)

- **Source** : `https://github.com/mitre/cti` (fichier STIX JSON)
- **Authentification** : Aucune (totalement publique)
- **Cache** : Fichier local `mitre_cache.json` (valide 7 jours)
- **Données** : 691+ techniques, tactiques, groupes APT, logiciels malveillants

### NIST NVD API v2.0

- **URL** : `https://services.nvd.nist.gov/rest/json/cves/2.0`
- **Authentification** : Sans clé (5 req/30s) | Avec clé gratuite (50 req/30s)
- **Données** : CVE, scores CVSS, descriptions de vulnérabilités

### NIST NICE Framework (SP 800-181 Rev 1)

- **Source** : https://niccs.cisa.gov/workforce-development/nice-framework
- **Type** : Données structurées statiques (standard public officiel)
- **Données** : 8 rôles cyber, compétences, catégories de travail

### France Travail API v2 (Offres d'emploi)

- **URL** : `https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search`
- **Authentification** : OAuth2 (Client ID + Secret, gratuit)
- **Données** : Offres d'emploi cyber en temps réel

### Composio MCP (Gmail + Google Calendar)

- **Transport** : Streamable HTTP (pas SSE)
- **Authentification** : x-api-key header + OAuth2 Google
- **Gmail** : Envoi d'emails avec le plan complet
- **Google Calendar** : Création d'événements all-day avec dates calculées dynamiquement

---

## Installation et lancement

### Prérequis

- Python 3.10+
- Une clé API Groq (gratuite sur [console.groq.com](https://console.groq.com))
- Une clé API OpenRouter (gratuite sur [openrouter.ai](https://openrouter.ai)) — pour le fallback
- Des credentials France Travail (gratuits sur [francetravail.io](https://francetravail.io/data/api/offres-emploi))
- Un compte Composio (gratuit sur [composio.dev](https://composio.dev)) — pour Gmail + Calendar MCP

### Installation

```bash
git clone https://github.com/lerat-yann/Agent_Cyber_Career_Compass.git
cd Agent_Cyber_Career_Compass
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### Configuration

Créer un fichier `.env` :

```env
# Provider principal (Groq — meilleur tool-calling gratuit)
GROQ_API_KEY=gsk_...

# Provider fallback (OpenRouter — modèles gratuits)
OPENROUTER_API_KEY=sk-or-...

# France Travail (offres emploi live)
FRANCE_TRAVAIL_CLIENT_ID=votre_client_id
FRANCE_TRAVAIL_CLIENT_SECRET=votre_client_secret

# MCP Composio (Gmail + Google Calendar)
COMPOSIO_API_KEY=votre_clé_composio
COMPOSIO_MCP_GMAIL_URL=https://backend.composio.dev/v3/mcp/votre_id_gmail
COMPOSIO_MCP_CALENDAR_URL=https://backend.composio.dev/v3/mcp/votre_id_calendar

# Optionnel : clé NVD pour plus de quota CVE
# NVD_API_KEY=votre_clé_nvd
```

### Lancement

**Interface CLI :**

```bash
python main.py
```

**Interface Web (Streamlit) :**

```bash
streamlit run app.py
```

---

## Structure des fichiers

```
Agent_Cyber_Career_Compass/
├── config.py                  # Double provider Groq/OpenRouter + registre agents + switch à chaud
├── guardrails.py              # Validation 3 couches (offensif / orientation / LLM)
├── tools.py                   # Outils : MITRE ATT&CK + NIST NVD + NICE Framework + France Travail
├── cyber_agents.py            # 3 agents spécialisés + get_plan_complet + outils de délégation
├── agent_learning_coach.py    # Base de ressources curatées (10 domaines × 8 catégories × FR/EN)
├── mcp_agents.py              # Agents MCP : Gmail + Google Calendar via Composio
├── manager.py                 # Orchestrateur intelligent (routage dynamique)
├── main.py                    # Interface CLI
├── app.py                     # Interface Web Streamlit (profilage + chat + boutons MCP)
├── requirements.txt           # Dépendances Python
└── .env                       # Variables d'environnement (non versionné)
```

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Framework agents | `openai-agents` (OpenAI Agents SDK) |
| Protocole MCP | `MCPServerStreamableHttp` (Streamable HTTP) |
| Provider MCP | Composio (Gmail + Google Calendar) |
| Provider LLM principal | Groq API (Kimi K2) |
| Provider LLM fallback | OpenRouter (modèles gratuits) |
| Modèle principal | `moonshotai/kimi-k2-instruct` (tool-calling) |
| Modèle guardrail | `llama-3.1-8b-instant` (classification rapide) |
| Interface web | Streamlit |
| APIs externes | MITRE ATT&CK, NIST NVD, France Travail, Composio MCP |

---

## Exemples de questions

| Question | Agents mobilisés |
|----------|-----------------|
| "Combien d'offres de pentester en France ?" | Market |
| "C'est quoi le métier de SOC analyst ?" | get_plan_complet |
| "SOC analyst vs incident responder ?" | get_plan_complet (×2) |
| "Je suis dev Python, quel métier cyber ?" | Matching |
| "Plan complet pour devenir pentester" | get_plan_complet + Market |
| "Quelles techniques MITRE ATT&CK récentes ?" | Knowledge Map |
| "Contexte du CVE-2024-3400 ?" | Knowledge Map |
| "Comment exploiter une faille SQL ?" | ❌ Bloqué par guardrail |
| *(clic bouton 📧)* | Agent Gmail MCP |
| *(clic bouton 📅)* | Agent Google Calendar MCP |

---

## Règles de l'agent

1. **Domaine restreint** — Orientation cyber uniquement. Exploitation opérationnelle refusée.
2. **Maximum 3 métiers recommandés** — Pour rester actionnable.
3. **Données réelles** — MITRE ATT&CK, NIST NVD et France Travail sont appelés en live.
4. **Orchestration intelligente** — Le manager décide dynamiquement quels agents appeler.
5. **Anti-hallucination marché** — Aucun chiffre d'offres sans appel API France Travail.
6. **Ressources curatées** — URLs vérifiées, étoiles ★, coûts, séparation FR 🇫🇷 / EN 🇬🇧.
7. **Langue française** — Instructions, réponses et exemples en français.
8. **Fallback automatique** — Groq → OpenRouter si rate-limit, transparent pour l'utilisateur.
9. **MCP intégré** — Gmail et Google Calendar via Composio avec tool filtering et dates calculées en Python.

---

## Historique des versions

| Version | Description |
|---------|-------------|
| V4 | Simplification architecture : 4 tools au lieu de 8, `get_plan_complet` déterministe |
| V5 | Profilage utilisateur (sidebar Streamlit), résultats personnalisés |
| V5.1 | Guardrails renforcés (mots-clés offensifs élargis, fail-safe LLM) |
| V6 | Fallback à chaud Groq → OpenRouter via registre d'agents (plus de `importlib.reload`) |
| V7 | Intégration MCP : Gmail + Google Calendar via Composio (Streamable HTTP) |
| V7.5 | Tool filtering MCP (1 tool exposé sur 22), fin des hallucinations Calendar |
| V7.10 | Dates Calendar calculées en Python avec durées réelles par phase |
