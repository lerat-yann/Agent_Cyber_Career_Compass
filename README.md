# 🛡️ Cyber Career Compass

Un assistant d'orientation vers les métiers de la cybersécurité, basé sur une architecture **multi-agents** avec des **données réelles** (MITRE ATT&CK, NIST NVD, NIST NICE Framework, France Travail).

> **[🚀 Démo live sur Streamlit Cloud](https://agent-cyber-career-compass.streamlit.app/)**

---

## Ce que fait cet agent

L'agent aide les utilisateurs à planifier leur carrière en cybersécurité en coordonnant plusieurs agents spécialisés. Il peut :

- Analyser un profil et recommander des métiers cyber compatibles
- Expliquer et comparer les métiers (SOC, Pentest, Cloud Security, GRC, AppSec…)
- Identifier les compétences nécessaires par métier
- Construire une roadmap 30 / 60 / 90 jours personnalisée
- Recommander des ressources d'apprentissage réelles (gratuites ou freemium)
- Récupérer les techniques MITRE ATT&CK réelles liées à un métier (API live)
- Rechercher le contexte d'un CVE via le NIST NVD (API live)
- Fournir les données **réelles** du marché de l'emploi cyber en France (API France Travail live)

L'agent **refuse toute demande d'exploitation opérationnelle** grâce à un système de guardrails à 3 couches.

---

## Architecture

### Vue d'ensemble

```
User Input (CLI ou Streamlit)
    ↓
[Guardrail SYS_07] → Rejette si hors-sujet ou offensif (3 couches)
    ↓
[Manager SYS_00] → Orchestrateur intelligent (routage dynamique)
    ├→ [Agent Matching SYS_03]       → get_all_roles_overview, get_role_details
    ├→ [Agent Rôles SYS_01]          → get_role_details, compare_roles
    ├→ [Agent Compétences SYS_02]    → get_skills_for_role, get_learning_resources
    ├→ [Agent Learning Path SYS_04]  → get_skills_for_role, get_learning_resources
    ├→ [Agent Ressources SYS_05]     → get_learning_resources
    ├→ [Agent Knowledge Map SYS_06]  → MITRE ATT&CK API, NIST NVD API
    └→ [Agent Marché SYS_08]         → France Travail API (offres emploi live)
    ↓
Réponse synthétisée
```

### Pattern : Agents-as-Tools avec orchestration intelligente

Chaque agent spécialisé est wrappé comme un outil de délégation que le manager peut appeler. Le manager **décide dynamiquement** quels agents appeler et dans quel ordre selon la question posée — il n'y a pas de séquence fixe. Le manager synthétise les réponses de tous les agents appelés.

### Les agents

| Agent | Fichier | Outils | Source données |
| --- | --- | --- | --- |
| Manager SYS_00 | `manager.py` | 7 outils de délégation | — |
| Agent Rôles SYS_01 | `cyber_agents.py` | `get_role_details`, `compare_roles`, `get_all_roles_overview` | NIST NICE Framework |
| Agent Compétences SYS_02 | `cyber_agents.py` | `get_skills_for_role`, `get_learning_resources` | NIST NICE Framework |
| Agent Matching SYS_03 | `cyber_agents.py` | `get_all_roles_overview`, `get_role_details` | NIST NICE Framework |
| Agent Learning Path SYS_04 | `cyber_agents.py` | `get_skills_for_role`, `get_learning_resources` | NIST NICE Framework |
| Agent Ressources SYS_05 | `cyber_agents.py` | `get_learning_resources` | Sources officielles |
| Agent Knowledge Map SYS_06 | `cyber_agents.py` | `get_mitre_techniques_for_role`, `get_mitre_groups_and_software`, `get_mitre_cve_context`, `get_mitre_latest_techniques` | **MITRE ATT&CK + NIST NVD** |
| Agent Marché SYS_08 | `cyber_agents.py` | `get_job_market_data` | **France Travail API v2** |
| Guardrail SYS_07 | `guardrails.py` | LLM classifieur | — |

### Les outils (`tools.py`)

| Outil | Source | Type de données |
| --- | --- | --- |
| `get_role_details` | NIST NICE Framework SP 800-181 | Statique structuré |
| `get_skills_for_role` | NIST NICE Framework + industrie | Statique structuré |
| `get_learning_resources` | Sources officielles vérifiées | Statique structuré |
| `compare_roles` | NIST NICE Framework | Calcul local |
| `get_all_roles_overview` | NIST NICE Framework | Statique structuré |
| `get_mitre_techniques_for_role` | **MITRE ATT&CK REST API** | **Données réelles live** |
| `get_mitre_groups_and_software` | **MITRE ATT&CK REST API** | **Données réelles live** |
| `get_mitre_cve_context` | **NIST NVD API v2.0** | **Données réelles live** |
| `get_mitre_latest_techniques` | **MITRE ATT&CK REST API** | **Données réelles live** |
| `get_job_market_data` | **France Travail API v2** | **Données réelles live** |

### Guardrails (`guardrails.py`)

Validation en 3 couches :

1. **Couche offensive (blocage immédiat)** — mots-clés d'exploitation opérationnelle → rejet sans appel API
2. **Couche cyber/orientation (passage immédiat)** — mots-clés orientation/cyber/CVE → accepté sans appel API
3. **Couche LLM (cas ambigus)** — classifieur `llama-3.1-8b-instant` avec exemples explicites

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
- **Clé gratuite** : https://nvd.nist.gov/developers/request-an-api-key
- **Données** : CVE, scores CVSS, descriptions de vulnérabilités

### NIST NICE Framework (SP 800-181 Rev 1)

- **Source** : https://niccs.cisa.gov/workforce-development/nice-framework
- **Type** : Données structurées statiques (standard public officiel)
- **Données** : 8 rôles, compétences, catégories de travail

### France Travail API v2 (Offres d'emploi)

- **URL** : `https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search`
- **Authentification** : OAuth2 (Client ID + Secret, gratuit)
- **Inscription** : https://francetravail.io/data/api/offres-emploi
- **Données** : Offres d'emploi cyber en temps réel (nombre, salaires, compétences demandées, localisation)

---

## Installation et lancement

### Prérequis

- Python 3.10+
- Une clé API Groq (gratuite sur [console.groq.com](https://console.groq.com))
- Des credentials France Travail (gratuits sur [francetravail.io](https://francetravail.io/data/api/offres-emploi))

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
GROQ_API_KEY=votre_clé_groq

# France Travail (offres emploi live)
FRANCE_TRAVAIL_CLIENT_ID=votre_client_id
FRANCE_TRAVAIL_CLIENT_SECRET=votre_client_secret

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
├── config.py           # Initialisation modèles Groq
├── guardrails.py       # Validation 3 couches (offensif / orientation / LLM)
├── tools.py            # 10 outils : MITRE + NIST NVD + NICE Framework + France Travail
├── cyber_agents.py     # 7 agents spécialisés + outils de délégation
├── manager.py          # Orchestrateur intelligent (routage dynamique)
├── main.py             # Interface CLI
├── app.py              # Interface Web Streamlit
├── requirements.txt    # Dépendances Python
├── .env.example        # Template variables d'environnement
└── .env                # Variables d'environnement (non versionné)
```

---

## Stack technique

| Composant | Technologie |
| --- | --- |
| Framework agents | `openai-agents` (OpenAI Agents SDK) |
| Provider LLM | Groq API |
| Modèle principal | `moonshotai/kimi-k2-instruct` (tool-calling) |
| Modèle guardrail | `llama-3.1-8b-instant` (classification rapide) |
| Interface web | Streamlit |
| APIs externes | MITRE ATT&CK, NIST NVD, France Travail |

---

## Exemples de questions

| Question | Agents mobilisés |
| --- | --- |
| "Combien d'offres de pentester en France ?" | Market |
| "C'est quoi le métier de SOC analyst ?" | Roles |
| "SOC analyst vs incident responder ?" | Roles |
| "Je suis dev Python, quel métier cyber ?" | Matching + Roles |
| "Plan complet pour devenir pentester" | Roles + Skills + Learning Path + Resources + Market + Knowledge Map |
| "Quelles techniques MITRE ATT&CK récentes ?" | Knowledge Map |
| "Contexte du CVE-2024-3400 ?" | Knowledge Map |
| "Comment exploiter une faille SQL ?" | ❌ Bloqué par guardrail |

---

## Règles de l'agent

1. **Domaine restreint** — Orientation cyber uniquement. Exploitation opérationnelle refusée.
2. **Maximum 3 métiers recommandés** — Pour rester actionnable.
3. **Données réelles** — MITRE ATT&CK, NIST NVD et France Travail sont appelés en live.
4. **Orchestration intelligente** — Le manager décide dynamiquement quels agents appeler.
5. **Anti-hallucination marché** — Aucun chiffre d'offres sans appel API France Travail.
6. **Ressources gratuites en priorité** — Adapté aux débutants et à la démonstration.
7. **Langue française** — Instructions, réponses et exemples en français.
