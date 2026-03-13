# Cyber Career Compass

Un assistant d'orientation vers les métiers de la cybersécurité, basé sur une architecture multi-agents avec des **données réelles** (MITRE ATT&CK, NIST NVD, NIST NICE Framework).

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

L'agent **refuse toute demande d'exploitation opérationnelle** grâce à un système de guardrails.

---

## Architecture

### Vue d'ensemble

```
User Input (CLI ou Streamlit)
    ↓
[Guardrail SYS_07] → Rejette si hors-sujet ou offensif
    ↓
[Manager SYS_00] → Orchestrateur principal
    ├→ [Agent Matching SYS_03]       → get_all_roles_overview, get_role_details
    ├→ [Agent Rôles SYS_01]          → get_role_details, compare_roles
    ├→ [Agent Compétences SYS_02]    → get_skills_for_role, get_learning_resources
    ├→ [Agent Learning Path SYS_04]  → get_skills_for_role, get_learning_resources
    ├→ [Agent Ressources SYS_05]     → get_learning_resources
    └→ [Agent Knowledge Map SYS_06]  → MITRE ATT&CK API, NIST NVD API
    ↓
Réponse synthétisée
```

### Pattern : Agents-as-Tools

Identique au projet voyage de référence. Chaque agent spécialisé est wrappé comme un outil de délégation que le manager peut appeler. Le manager orchestre et synthétise.

### Les agents

| Agent | Fichier | Outils | Source données |
|-------|---------|--------|----------------|
| Manager SYS_00 | `manager.py` | 6 outils de délégation | — |
| Agent Rôles SYS_01 | `cyber_agents.py` | `get_role_details`, `compare_roles`, `get_all_roles_overview` | NIST NICE Framework |
| Agent Compétences SYS_02 | `cyber_agents.py` | `get_skills_for_role`, `get_learning_resources` | NIST NICE Framework |
| Agent Matching SYS_03 | `cyber_agents.py` | `get_all_roles_overview`, `get_role_details` | NIST NICE Framework |
| Agent Learning Path SYS_04 | `cyber_agents.py` | `get_skills_for_role`, `get_learning_resources` | NIST NICE Framework |
| Agent Ressources SYS_05 | `cyber_agents.py` | `get_learning_resources` | Sources officielles |
| Agent Knowledge Map SYS_06 | `cyber_agents.py` | `get_mitre_techniques_for_role`, `get_mitre_groups_and_software`, `get_mitre_cve_context` | **MITRE ATT&CK API + NIST NVD API** |
| Guardrail SYS_07 | `guardrails.py` | LLM classifieur | — |

### Les outils (`tools.py`)

| Outil | Source | Type de données |
|-------|--------|-----------------|
| `get_role_details` | NIST NICE Framework SP 800-181 | Statique structuré |
| `get_skills_for_role` | NIST NICE Framework + industrie | Statique structuré |
| `get_learning_resources` | Sources officielles vérifiées | Statique structuré |
| `compare_roles` | NIST NICE Framework | Calcul local |
| `get_all_roles_overview` | NIST NICE Framework | Statique structuré |
| `get_mitre_techniques_for_role` | **MITRE ATT&CK REST API** | **Données réelles live** |
| `get_mitre_groups_and_software` | **MITRE ATT&CK REST API** | **Données réelles live** |
| `get_mitre_cve_context` | **NIST NVD API v2.0** | **Données réelles live** |

### Guardrails (`guardrails.py`)

Validation en 3 couches :

1. **Couche offensive (blocage immédiat)** — mots-clés d'exploitation opérationnelle → rejet sans appel API
2. **Couche cyber/orientation (passage immédiat)** — mots-clés orientation/cyber → accepté sans appel API
3. **Couche LLM (cas ambigus)** — classifieur `llama-3.1-8b-instant`

---

## Sources de données réelles

### MITRE ATT&CK REST API
- **URL** : `https://attack.mitre.org/api/`
- **Authentification** : Aucune (totalement publique)
- **Limite** : Aucune limite officielle
- **Données** : Techniques, tactiques, groupes APT, logiciels malveillants
- **Documentation** : https://attack.mitre.org/resources/attack-data-and-tools/

### NIST NVD API v2.0
- **URL** : `https://services.nvd.nist.gov/rest/json/cves/2.0`
- **Authentification** : Sans clé (5 req/30s) | Avec clé gratuite (50 req/30s)
- **Clé gratuite** : https://nvd.nist.gov/developers/request-an-api-key
- **Données** : CVE, scores CVSS, descriptions de vulnérabilités

### NIST NICE Framework (SP 800-181 Rev 1)
- **Source** : https://niccs.cisa.gov/workforce-development/nice-framework
- **Type** : Données structurées statiques (standard public officiel)
- **Données** : Rôles, compétences, catégories de travail

---

## Différences avec le projet voyage

| Aspect | Projet Voyage | Cyber Career Compass |
|--------|---------------|----------------------|
| APIs réelles | `get_weather` (Open-Meteo) | `get_mitre_*` (MITRE ATT&CK) + `get_mitre_cve_context` (NIST NVD) |
| Données simulées | Vols, hôtels | Aucune — tout est réel ou structuré |
| Guardrail | 2 couches | 3 couches (+ détection offensive) |
| Nombre d'agents | 3 | 6 |
| Fallback API | Non | Oui (données statiques si API indisponible) |

---

## Installation et lancement

### Prérequis

- Python 3.10+
- Une clé API Groq (gratuite sur [console.groq.com](https://console.groq.com))

### Installation

```bash
cd cyber_compass
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### Configuration

Créer un fichier `.env` :

```bash
GROQ_API_KEY=votre_clé_groq
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
cyber_compass/
├── config.py           # Initialisation modèles Groq (llama-4-scout + llama-3.1-8b)
├── guardrails.py       # Validation 3 couches (offensif / orientation / LLM)
├── tools.py            # Outils : MITRE ATT&CK API + NIST NVD API + NIST NICE Framework
├── cyber_agents.py     # 6 agents spécialisés + outils de délégation
├── manager.py          # Orchestrateur SYS_00
├── main.py             # Interface CLI
├── app.py              # Interface Web Streamlit
├── requirements.txt    # Dépendances Python
└── .env                # Variables d'environnement (non versionné)
```

---

## Règles de l'agent

1. **Domaine restreint** — Orientation cyber uniquement. Exploitation opérationnelle refusée.
2. **Maximum 3 métiers recommandés** — Pour rester actionnable.
3. **Données réelles** — MITRE ATT&CK et NIST NVD sont appelées en live. Fallback statique si indisponibles.
4. **Délégation obligatoire** — Le manager ne répond jamais directement sur les données métier.
5. **Ressources gratuites en priorité** — Adapté à un contexte de démonstration et débutants.
6. **Langue française** — Instructions, réponses et exemples en français.
