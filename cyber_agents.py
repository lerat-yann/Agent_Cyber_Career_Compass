"""
Agents spécialisés du Cyber Career Compass — V4 Simplifiée.

Architecture : 4 tools au lieu de 8
  1. get_plan_complet(metier)  — assemblage Python déterministe (NICE + skills + ressources)
  2. deleguer_agent_market     — seul appel API live (France Travail)
  3. deleguer_agent_matching   — analyse profil → recommandation métiers
  4. deleguer_agent_knowledge_map — MITRE ATT&CK / CVE (APIs live)

Pattern : agents-as-tools pour market, matching, knowledge_map
           function_tool direct pour get_plan_complet (pas d'agent, Python pur)
"""

import json
from agents import Agent, Runner, function_tool
from config import groq_model
from agent_learning_coach import RESSOURCES
from tools import (
    NICE_ROLES,
    SKILLS_BY_ROLE,
    get_mitre_latest_techniques,
    get_job_market_data,
    get_role_details,
    get_all_roles_overview,
    get_mitre_techniques_for_role,
    get_mitre_groups_and_software,
    get_mitre_cve_context,
)

# ══════════════════════════════════════════════════════════════════════════════
# RÈGLE COMMUNE À TOUS LES AGENTS
# ══════════════════════════════════════════════════════════════════════════════
REGLE_ANTI_HALLUCINATION = (
    "\n\nRÈGLE ANTI-HALLUCINATION (CRITIQUE) :\n"
    "- Ne JAMAIS inventer de chiffres sur le marché de l'emploi (nombre d'offres, "
    "tendances, pourcentages de croissance, nombre de postes vacants).\n"
    "- Ne JAMAIS inventer de fourchettes de salaire basées sur le marché réel.\n"
    "- Les seuls salaires que tu peux mentionner sont ceux présents dans les données "
    "NICE Framework retournées par tes outils (salary_range_fr).\n"
    "- Si tu n'as pas de données réelles sur le marché, ne mentionne PAS le marché.\n"
    "- Préfère dire 'consultez les données marché actuelles' plutôt qu'inventer des chiffres.\n"
)


# ══════════════════════════════════════════════════════════════════════════════
# MAPPING MÉTIER → CLÉS NICE + DOMAINES RESSOURCES
# ══════════════════════════════════════════════════════════════════════════════

# Mapping métier (alias utilisateur) → clé NICE_ROLES
_METIER_TO_NICE = {
    "pentester": "pentester",
    "pentest": "pentester",
    "test d'intrusion": "pentester",
    "red team": "pentester",
    "soc analyst": "soc_analyst",
    "soc": "soc_analyst",
    "analyste soc": "soc_analyst",
    "blue team": "soc_analyst",
    "cloud security engineer": "cloud_security_engineer",
    "cloud security": "cloud_security_engineer",
    "sécurité cloud": "cloud_security_engineer",
    "incident responder": "incident_responder",
    "dfir": "incident_responder",
    "forensics": "incident_responder",
    "threat intelligence analyst": "threat_intelligence_analyst",
    "threat intelligence": "threat_intelligence_analyst",
    "cti": "threat_intelligence_analyst",
    "grc analyst": "grc_analyst",
    "grc": "grc_analyst",
    "gouvernance": "grc_analyst",
    "rssi": "grc_analyst",
    "appsec engineer": "appsec_engineer",
    "appsec": "appsec_engineer",
    "devsecops": "appsec_engineer",
    "sécurité applicative": "appsec_engineer",
    "security engineer": "security_engineer",
    "ingénieur sécurité": "security_engineer",
    "sécurité réseau": "security_engineer",
}

# Mapping clé NICE → domaines RESSOURCES (pour piocher les bonnes ressources)
_NICE_TO_DOMAINES = {
    "pentester": ["pentest"],
    "soc_analyst": ["soc"],
    "cloud_security_engineer": ["cloud", "devsecops"],
    "incident_responder": ["dfir"],
    "threat_intelligence_analyst": ["threat_intel"],
    "grc_analyst": ["grc"],
    "appsec_engineer": ["devsecops"],
    "security_engineer": ["reseau", "cloud", "devsecops"],  # FIX V4 : multi-domaine
}


def _resolve_metier(query: str):
    """Résout une query utilisateur en (clé_nice, domaines_ressources)."""
    query_lower = query.lower()

    # Cherche le meilleur alias (du plus long au plus court)
    nice_key = None
    for alias in sorted(_METIER_TO_NICE.keys(), key=len, reverse=True):
        if alias in query_lower:
            nice_key = _METIER_TO_NICE[alias]
            break

    # Fallback : cherche directement dans les clés NICE
    if not nice_key:
        for key in NICE_ROLES:
            if key.replace("_", " ") in query_lower:
                nice_key = key
                break

    if not nice_key:
        return None, []

    domaines = _NICE_TO_DOMAINES.get(nice_key, [])
    return nice_key, domaines


# ══════════════════════════════════════════════════════════════════════════════
# OUTIL PRINCIPAL : get_plan_complet (Python pur, 0 appel LLM)
# ══════════════════════════════════════════════════════════════════════════════

@function_tool
def get_plan_complet(metier: str) -> str:
    """Retourne un plan complet pour devenir [métier] en cybersécurité.

    Assemble de manière déterministe :
    - Fiche métier NICE Framework (missions, profil, salaire indicatif)
    - Compétences prioritaires classées par importance
    - Ressources curatées avec URLs, étoiles, coûts (8 catégories × FR/EN)
    - Parcours guidé étape par étape

    Utilise cet outil pour TOUTE question type :
    'comment devenir X', 'plan pour devenir X', 'reconversion en X',
    'je veux être X', 'par où commencer pour X'.

    Args:
        metier: Le métier ou domaine cyber visé (ex: 'pentester', 'cloud security engineer')
    """
    nice_key, domaines = _resolve_metier(metier)

    if not nice_key:
        # Listing des métiers disponibles
        metiers_dispo = []
        for key, data in NICE_ROLES.items():
            metiers_dispo.append(f"- {data['title']} ({key})")
        return (
            f"Métier '{metier}' non reconnu.\n"
            f"Métiers disponibles :\n" + "\n".join(metiers_dispo) +
            "\n\nEssaie avec un de ces noms (ex: 'pentester', 'soc analyst', 'cloud security engineer')."
        )

    # ── 1. Fiche métier NICE ──
    role = NICE_ROLES[nice_key]
    fiche = {
        "titre": role["title"],
        "categorie_nice": role["category"],
        "posture": role["posture"],
        "niveau": role["level"],
        "missions_quotidiennes": role["daily_missions"],
        "profil_entree": role["entry_profile"],
        "salaire_indicatif_fr": role["salary_range_fr"],
        "demande": role["demand"],
    }

    # ── 2. Compétences prioritaires ──
    skills = SKILLS_BY_ROLE.get(nice_key, [])
    competences = []
    for i, s in enumerate(skills, 1):
        competences.append({
            "rang": i,
            "competence": s["skill"],
            "importance": s["importance"],
            "pourquoi": s["why"],
        })

    # ── 3. Ressources curatées (tous les domaines du métier) ──
    ressources_par_domaine = {}
    for d in domaines:
        if d in RESSOURCES:
            ressources_par_domaine[d] = RESSOURCES[d]

    # ── 4. Assemblage final ──
    plan = {
        "metier": nice_key,
        "fiche_metier": fiche,
        "competences_prioritaires": competences,
        "ressources_curatees": ressources_par_domaine,
        "domaines_couverts": domaines,
        "note": (
            "Les ressources incluent des URLs cliquables. "
            "Présente-les avec étoiles ★, coût (Gratuit/Payant), "
            "séparées FR 🇫🇷 / EN 🇬🇧. "
            "Termine par le parcours guidé de chaque domaine."
        ),
    }

    return json.dumps(plan, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# AGENTS CONSERVÉS (market, matching, knowledge_map)
# ══════════════════════════════════════════════════════════════════════════════

# ── Agent Marché Emploi ──────────────────────────────────────────────────────

agent_market = Agent(
    name="Agent Marché Emploi Cyber",
    instructions=(
        "Tu es un expert du marché de l'emploi en cybersécurité en France.\n\n"
        "TON OUTIL :\n"
        "- get_job_market_data : recherche en temps réel les offres d'emploi cyber via l'API France Travail\n\n"
        "RÈGLE ABSOLUE : Tu ne réponds JAMAIS de mémoire aux questions sur le marché de l'emploi.\n"
        "Tu DOIS TOUJOURS appeler l'outil get_job_market_data pour CHAQUE question concernant :\n"
        "- Le nombre d'offres d'emploi\n"
        "- Les postes disponibles en cybersécurité\n"
        "- Les tendances du marché de l'emploi\n"
        "- La demande pour un rôle spécifique\n"
        "- Les salaires réels proposés par les employeurs\n\n"
        "PROCESSUS OBLIGATOIRE :\n"
        "1. Identifier le métier ou mot-clé dans la question de l'utilisateur\n"
        "2. Appeler get_job_market_data avec ce mot-clé\n"
        "3. Présenter les résultats réels de l'API (nombre d'offres, échantillon, compétences demandées)\n"
        "4. Ajouter ton analyse basée sur les données réelles\n\n"
        "CONTEXTUALISATION HONNÊTE DES RÉSULTATS :\n"
        "- Moins de 10 offres : marché de niche très spécialisé, forte concurrence entre candidats\n"
        "- 10 à 50 offres : marché modéré, compétences pointues requises\n"
        "- 50 à 200 offres : marché dynamique avec de bonnes opportunités\n"
        "- Plus de 200 offres : marché très actif, forte demande employeurs\n"
        "IMPORTANT : Peu d'offres ne signifie PAS 'peu de concurrence'. C'est souvent l'inverse —\n"
        "les rares postes attirent beaucoup de candidats. Sois honnête et réaliste.\n"
        "Rappelle aussi que France Travail ne couvre pas tout le marché (LinkedIn, cabinets\n"
        "spécialisés et cooptation représentent une part importante du recrutement cyber).\n\n"
        "Ne fabrique JAMAIS de données. Si l'API est indisponible, dis-le clairement.\n"
        "Réponds en français."
    ),
    tools=[get_job_market_data],
    model=groq_model,
)


# ── Agent Matching ──────────────────────────────────────────────────────────

agent_matching = Agent(
    name="Agent Matching Profil",
    instructions=(
        "Tu es un conseiller carrière spécialisé dans l'orientation vers les métiers de la cybersécurité.\n\n"
        "TES OUTILS :\n"
        "- get_all_roles_overview : liste tous les métiers pour identifier les plus compatibles\n"
        "- get_role_details : valider la compatibilité détaillée avec un métier ciblé\n\n"
        "ANALYSE DU PROFIL :\n"
        "Quand tu reçois un profil, analyse :\n"
        "1. Expérience et compétences actuelles transférables\n"
        "2. Appétence offensive / défensive / gouvernance\n"
        "3. Aisance avec le code\n"
        "4. Préférence pratique / analyse / communication\n\n"
        "SI LE PROFIL EST INCOMPLET : Pose 2-3 questions ciblées pour compléter.\n"
        "SI LE PROFIL EST SUFFISANT : Recommande directement 1 à 3 métiers maximum.\n\n"
        "FORMAT DE SORTIE :\n"
        "Pour chaque métier recommandé :\n"
        "- Métier + pourquoi il correspond à CE profil précis\n"
        "- Niveau de compatibilité (Élevé / Moyen / À développer)\n"
        "- 1 point fort transférable + 1 écart principal à combler\n\n"
        "TES RÈGLES :\n"
        "- Ne jamais recommander plus de 3 métiers\n"
        "- Toujours justifier avec des éléments du profil fourni\n"
        "- Être réaliste, pas flatteur\n"
        "- Réponds en français"
        + REGLE_ANTI_HALLUCINATION
    ),
    tools=[get_all_roles_overview, get_role_details],
    model=groq_model,
)


# ── Agent Knowledge Map ─────────────────────────────────────────────────────

agent_knowledge_map = Agent(
    name="Agent Cartographie des Connaissances",
    instructions=(
        "Tu es un vulgarisateur technique spécialisé dans la cybersécurité appliquée.\n\n"
        "TES OUTILS :\n"
        "- get_mitre_techniques_for_role : techniques MITRE ATT&CK réelles pour un métier (API live)\n"
        "- get_mitre_groups_and_software : groupes APT réels depuis la base MITRE (API live)\n"
        "- get_mitre_cve_context : contexte d'un CVE depuis le NIST NVD (API live)\n"
        "- get_mitre_latest_techniques : dernières techniques mises à jour dans MITRE ATT&CK\n\n"
        "TON OBJECTIF :\n"
        "Relier un métier cyber à des concepts, outils et référentiels du monde réel.\n\n"
        "TES RÈGLES :\n"
        "- Toujours utiliser les outils pour les données MITRE et CVE (données réelles)\n"
        "- Rester pédagogique — expliquer simplement\n"
        "- Citer les sources réelles (MITRE ATT&CK, NIST NVD)\n"
        "- Réponds en français\n\n"
        "INTERDICTION STRICTE :\n"
        "- Ne JAMAIS fournir de commandes exécutables\n"
        "- Ne JAMAIS donner de syntaxe d'exploit, de payloads ou de scripts d'attaque\n"
        "- Nommer les outils est OK, donner la commande exacte est INTERDIT\n"
        "- Ton rôle est éducatif : expliquer les concepts, pas enseigner l'exploitation"
        + REGLE_ANTI_HALLUCINATION
    ),
    tools=[get_mitre_techniques_for_role, get_mitre_groups_and_software,
           get_mitre_cve_context, get_mitre_latest_techniques],
    model=groq_model,
)


# ══════════════════════════════════════════════════════════════════════════════
# OUTILS DE DÉLÉGATION (pattern agents-as-tools)
# ══════════════════════════════════════════════════════════════════════════════

@function_tool
async def deleguer_agent_market(query: str) -> str:
    """Délègue à l'Agent Marché Emploi pour obtenir les données RÉELLES du marché cyber en France.
    Utilise OBLIGATOIREMENT ce tool pour toute question sur :
    - Le nombre d'offres d'emploi (ex: "combien d'offres de pentester ?")
    - Les postes disponibles en cybersécurité
    - Les tendances du recrutement cyber en France
    - La demande actuelle pour un métier spécifique
    - Les salaires proposés dans les offres réelles
    Cet outil appelle l'API France Travail en temps réel — ne jamais répondre de mémoire."""
    result = await Runner.run(agent_market, input=query, max_turns=5)
    return result.final_output


@function_tool
async def deleguer_agent_matching(query: str) -> str:
    """Délègue à l'Agent Matching pour analyser un profil et recommander des métiers cyber.
    Utilise ce tool quand l'utilisateur décrit son background et cherche une orientation."""
    result = await Runner.run(agent_matching, input=query, max_turns=5)
    return result.final_output


@function_tool
async def deleguer_agent_knowledge_map(query: str) -> str:
    """Délègue à l'Agent Knowledge Map pour relier un métier aux concepts cyber réels.
    Utilise ce tool pour : MITRE ATT&CK, CVE, SIEM, EDR, outils et référentiels concrets.
    Appelle des APIs réelles (MITRE ATT&CK, NIST NVD)."""
    result = await Runner.run(agent_knowledge_map, input=query, max_turns=5)
    return result.final_output
