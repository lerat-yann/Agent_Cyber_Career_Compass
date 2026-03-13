from agents import Agent, Runner, GuardrailFunctionOutput, input_guardrail
from config import groq_model_fast

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
    # Contexte général
    "cyber", "infosec", "sécurité", "réseau", "linux", "python",
]

# Mots-clés qui signalent une demande offensive opérationnelle à bloquer
OFFENSIVE_KEYWORDS = [
    "exploiter", "attaquer", "contourner", "backdoor", "rootkit",
    "keylogger", "botnet", "ddos", "deface", "injection sql sur",
    "bypass", "crack", "bruteforce", "hack un site", "pirater",
    "comment accéder", "voler des données", "exfiltrer",
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
    Couche 3 : LLM classifieur pour les cas ambigus.

    Conforme à SYS_07_GUARDRAIL.md
    """
    input_str = str(input)

    # Couche 1 — Blocage immédiat si demande offensive opérationnelle
    if _is_obviously_offensive(input_str):
        return GuardrailFunctionOutput(
            output_info={"classification": "offensif_operationnel", "layer": 1},
            tripwire_triggered=True,
        )

    # Couche 2 — Passage immédiat si mots-clés orientation/cyber évidents
    if _is_obviously_cyber_career(input_str):
        return GuardrailFunctionOutput(
            output_info={"classification": "orientation_cyber (keywords)", "layer": 2},
            tripwire_triggered=False,
        )

    # Couche 3 — LLM pour les cas ambigus
    classifier = Agent(
        name="Classifieur Cyber Career",
        instructions=(
            "Tu détermines si une requête concerne l'orientation professionnelle en cybersécurité, "
            "l'apprentissage des métiers cyber, la compréhension des rôles, compétences ou ressources "
            "pédagogiques en sécurité informatique.\n"
            "IMPORTANT : Une question générale sur la sécurité, le réseau, ou le code "
            "dans un contexte d'apprentissage est AUTORISÉE.\n"
            "Une demande d'exploitation réelle d'un système est REFUSÉE.\n"
            "Réponds UNIQUEMENT par 'orientation_cyber' ou 'hors_sujet'. Rien d'autre."
        ),
        model=groq_model_fast,
    )

    result = await Runner.run(classifier, input=input_str, max_turns=1)
    classification = result.final_output.strip().lower()
    is_cyber_career = "orientation_cyber" in classification

    return GuardrailFunctionOutput(
        output_info={"classification": classification, "layer": 3},
        tripwire_triggered=not is_cyber_career,
    )
