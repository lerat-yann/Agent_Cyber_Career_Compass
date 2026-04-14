"""
Guardrails du Cyber Career Compass — V8.

V8 : Compatible mémoire conversationnelle — quand l'input est un historique
     (liste de messages), le guardrail extrait le dernier message user pour
     les couches 1-2 (mots-clés) et vérifie aussi le contexte complet.
     La couche 3 (LLM) reçoit le contexte conversationnel pour juger.
V6 : Le classifieur couche 3 utilise config.groq_model_fast via import module
     (pas `from config import groq_model_fast` qui fige la référence).
     Ainsi, switch_to_fallback() met à jour le modèle du classifieur aussi.
"""

import config
from agents import Agent, Runner, GuardrailFunctionOutput, input_guardrail
from config import register_agent

# Mots-clés qui signalent clairement une intention d'orientation / apprentissage cyber
CYBER_CAREER_KEYWORDS = [
    # Métiers
    "soc", "pentester", "pentest", "red team", "blue team", "dfir",
    "threat intelligence", "grc", "appsec", "devSecOps", "ciso",
    "analyste", "analyst", "ingénieur sécurité", "security engineer",
    "incident responder", "cloud security",
    # Apprentissage / orientation
    "métier", "carrière", "orientation", "reconversion", "formation",
    "compétence", "apprendre", "certifi", "tryhackme", "hackthebox",
    "roadmap", "parcours", "plan", "débutant", "junior", "transition",
    "cours", "ressource", "tutoriel", "level", "niveau",
    # Domaine cyber
    "cybersécurité", "cybersecurity", "sécurité informatique",
    "hacking", "vulnérabilité", "exploit", "owasp", "mitre",
    "siem", "iam", "forensic", "malware", "phishing", "ransomware",
    "pentest", "audit", "test d'intrusion",
    # Référentiels et bases de données (questions éducatives légitimes)
    "cve-", "cve ", "nvd", "cvss", "nist", "att&ck", "stix",
    "taxii", "apt", "technique t1", "groupe apt",
    # Contexte général
    "cyber", "infosec", "sécurité", "réseau", "linux", "python",
]

# Mots-clés qui signalent une demande offensive opérationnelle à bloquer
OFFENSIVE_KEYWORDS = [
    "exploiter", "attaquer", "contourner", "backdoor", "rootkit",
    "keylogger", "botnet", "ddos", "deface", "injection sql sur",
    "bypass", "crack", "bruteforce", "hack un site", "pirater",
    "comment accéder", "voler des données", "exfiltrer",
    # V5 — ajouts pour couvrir les demandes d'attaques spécifiques
    "attaque xss", "attaque sql", "attaque csrf", "attaque rce",
    "faire une xss", "faire une injection", "faire un ddos",
    "code pour attaquer", "code pour hacker", "code pour pirater",
    "script d'attaque", "payload pour", "exploit pour",
    "donne moi le code", "donne-moi le code",
    "comment hacker", "comment pirater", "comment cracker",
]


def _is_obviously_cyber_career(text: str) -> bool:
    """Retourne True si le texte contient des mots-clés évidents d'orientation cyber."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in CYBER_CAREER_KEYWORDS)


def _is_obviously_offensive(text: str) -> bool:
    """Retourne True si le texte semble être une demande offensive opérationnelle."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in OFFENSIVE_KEYWORDS)


@input_guardrail
async def cyber_career_guardrail(ctx, agent, input):
    """
    Bloque les demandes hors du périmètre orientation / apprentissage cyber.

    Couche 1 : mots-clés offensifs → blocage immédiat.
    Couche 2 : mots-clés orientation/cyber → passage immédiat.
    Couche 3 : LLM classifieur pour les cas ambigus (fail-safe : blocage si erreur).

    Conforme à SYS_07_GUARDRAIL.md

    V8 : Compatible mémoire conversationnelle — quand l'input est une liste
         de messages (historique), on extrait le dernier message utilisateur
         pour les couches 1-2 (mots-clés) et on passe le contexte complet
         à la couche 3 (LLM classifieur).
    """
    # V8 : extraire le dernier message utilisateur si l'input est un historique
    if isinstance(input, list):
        # Chercher le dernier message "user" dans la liste
        last_user_msg = ""
        for msg in reversed(input):
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        input_str = last_user_msg
        # Contexte complet pour la couche 3 (LLM) — inclut l'historique
        input_str_full = " ".join(
            msg.get("content", "") for msg in input
            if isinstance(msg, dict)
        )
    else:
        input_str = str(input)
        input_str_full = input_str

    # Couche 1 — Blocage immédiat si demande offensive opérationnelle
    if _is_obviously_offensive(input_str):
        return GuardrailFunctionOutput(
            output_info={"classification": "offensif_operationnel", "layer": 1},
            tripwire_triggered=True,
        )

    # Couche 2 — Passage immédiat si mots-clés orientation/cyber évidents
    # V8 : on vérifie aussi l'historique complet — un message court comme
    #       "Et côté salaire ?" est légitime si la conversation porte sur le cyber
    if _is_obviously_cyber_career(input_str) or _is_obviously_cyber_career(input_str_full):
        return GuardrailFunctionOutput(
            output_info={"classification": "orientation_cyber (keywords)", "layer": 2},
            tripwire_triggered=False,
        )

    # Couche 3 — LLM pour les cas ambigus (avec fail-safe)
    try:
        # V6 : on utilise config.groq_model_fast (accès dynamique via le module)
        # Pas de register_agent ici car le classifieur est éphémère (recréé à chaque appel)
        classifier = Agent(
            name="Classifieur Cyber Career",
            instructions=(
                "Tu détermines si une requête concerne l'orientation professionnelle en cybersécurité, "
                "l'apprentissage des métiers cyber, la compréhension des rôles, compétences ou ressources "
                "pédagogiques en sécurité informatique.\n\n"
                "AUTORISÉ (réponds 'orientation_cyber') :\n"
                "- Questions sur les métiers, compétences, formations, certifications\n"
                "- Questions sur les concepts cyber (MITRE ATT&CK, CVE, CVSS, APT, OWASP...)\n"
                "- Demander le contexte ou l'explication d'un CVE spécifique (ex: CVE-2024-3400)\n"
                "- Questions générales sur la sécurité, le réseau, ou le code dans un contexte d'apprentissage\n"
                "- Questions sur le marché de l'emploi en cybersécurité\n\n"
                "REFUSÉ (réponds 'hors_sujet') :\n"
                "- Demande d'exploitation réelle d'un système ou d'un site\n"
                "- Questions totalement hors domaine cyber (cuisine, sport, etc.)\n"
                "- Demandes de code malveillant, payloads, scripts d'attaque\n\n"
                "Réponds UNIQUEMENT par 'orientation_cyber' ou 'hors_sujet'. Rien d'autre."
            ),
            model=config.groq_model_fast,
        )

        # V8 : on passe le contexte complet au classifieur pour qu'il juge
        # la requête dans son contexte conversationnel
        classifier_input = (
            f"Contexte de la conversation :\n{input_str_full}\n\n"
            f"Dernière requête à classifier :\n{input_str}"
        ) if input_str_full != input_str else input_str

        result = await Runner.run(classifier, input=classifier_input, max_turns=1)
        classification = result.final_output.strip().lower()

        # Vérification stricte : la réponse doit contenir exactement un des deux termes
        if "orientation_cyber" in classification:
            is_cyber_career = True
        elif "hors_sujet" in classification:
            is_cyber_career = False
        else:
            # Réponse inattendue du LLM → blocage par sécurité
            is_cyber_career = False

        return GuardrailFunctionOutput(
            output_info={"classification": classification, "layer": 3},
            tripwire_triggered=not is_cyber_career,
        )

    except Exception:
        # Si le LLM classifieur échoue (rate limit, timeout, etc.)
        # → Blocage par sécurité (fail-safe)
        return GuardrailFunctionOutput(
            output_info={"classification": "erreur_llm_failsafe", "layer": 3},
            tripwire_triggered=True,
        )
