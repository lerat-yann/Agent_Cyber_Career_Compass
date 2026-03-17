"""
Agents MCP du Cyber Career Compass — V7.4.

Intègre Gmail et Google Calendar via Composio MCP (Streamable HTTP).

Les agents MCP utilisent Groq (Kimi K2) car c'est le seul modèle gratuit
avec un tool-calling fiable. Pour rester sous la limite 10k tokens de Groq,
on minimise les instructions et on envoie le contenu de façon compacte.

Deux fonctions exposées pour app.py :
  - envoyer_par_mail(destinataire, contenu) → envoie le plan par Gmail
  - planifier_calendrier(contenu) → crée les événements dans Google Calendar
"""

import os
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp
import config

# ── URLs MCP + clé API depuis les secrets ────────────────────────────────────

try:
    import streamlit as st
    def _secrets_get(key):
        try:
            return st.secrets.get(key, None)
        except Exception:
            return None
except Exception:
    _secrets_get = lambda key: None

COMPOSIO_MCP_GMAIL_URL = os.environ.get("COMPOSIO_MCP_GMAIL_URL") or _secrets_get("COMPOSIO_MCP_GMAIL_URL")
COMPOSIO_MCP_CALENDAR_URL = os.environ.get("COMPOSIO_MCP_CALENDAR_URL") or _secrets_get("COMPOSIO_MCP_CALENDAR_URL")
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY") or _secrets_get("COMPOSIO_API_KEY")

MCP_GMAIL_AVAILABLE = bool(COMPOSIO_MCP_GMAIL_URL and COMPOSIO_API_KEY)
MCP_CALENDAR_AVAILABLE = bool(COMPOSIO_MCP_CALENDAR_URL and COMPOSIO_API_KEY)

print(f"[MCP] Gmail: {'✅ configuré' if MCP_GMAIL_AVAILABLE else '❌ non configuré'}")
print(f"[MCP] Calendar: {'✅ configuré' if MCP_CALENDAR_AVAILABLE else '❌ non configuré'}")
if not COMPOSIO_API_KEY:
    print("[MCP] ⚠️ COMPOSIO_API_KEY manquante — les MCP ne fonctionneront pas")


def _extract_parcours(contenu: str) -> str:
    """Extrait uniquement la section parcours/étapes du plan complet.
    Cela réduit drastiquement la taille envoyée au LLM Calendar
    tout en gardant les informations utiles pour créer les événements."""
    lines = contenu.split("\n")
    parcours_lines = []
    in_parcours = False

    for line in lines:
        lower = line.lower().strip()
        # Détecter le début d'une section parcours/planning
        if any(kw in lower for kw in ["parcours", "mois 1", "mois 2", "phase 1", "phase 2",
                                        "étape 1", "étape 2", "planning", "calendrier",
                                        "semaine 1", "semaine 2"]):
            in_parcours = True
        # Détecter les sections qu'on veut garder aussi
        if any(kw in lower for kw in ["compétences à maîtriser", "fiche métier"]):
            # Garder le titre du métier
            if "fiche métier" in lower or "plan complet" in lower:
                parcours_lines.append(line)
        if in_parcours:
            parcours_lines.append(line)
        # Stopper si on atteint une section non pertinente après le parcours
        if in_parcours and any(kw in lower for kw in ["budget", "marché réel", "conseil concret"]):
            break

    if parcours_lines:
        return "\n".join(parcours_lines)

    # Fallback : si pas de section parcours détectée, prendre les 2000 premiers caractères
    return contenu[:2000]


# ══════════════════════════════════════════════════════════════════════════════
# FONCTION : Envoyer un plan par mail via Gmail MCP
# ══════════════════════════════════════════════════════════════════════════════

async def _envoyer_mail_mcp(destinataire: str, sujet: str, contenu: str) -> str:
    """Connecte le serveur MCP Gmail, crée un agent, envoie le mail."""
    if not MCP_GMAIL_AVAILABLE:
        return "❌ Gmail MCP non configuré. Ajoutez COMPOSIO_MCP_GMAIL_URL et COMPOSIO_API_KEY dans les secrets."

    # Limiter le contenu du mail à ~6000 caractères pour rester sous 10k tokens
    # (instructions + tool schema + contenu doivent tenir dans 10k)
    contenu_mail = contenu[:6000]
    if len(contenu) > 6000:
        contenu_mail += "\n\n---\nPlan complet disponible sur Cyber Career Compass."

    try:
        async with MCPServerStreamableHttp(
            name="Gmail Composio",
            params={
                "url": COMPOSIO_MCP_GMAIL_URL,
                "headers": {"x-api-key": COMPOSIO_API_KEY},
            },
            cache_tools_list=True,
        ) as gmail_server:

            # Instructions ultra-courtes pour économiser des tokens
            agent_gmail = Agent(
                name="Agent Gmail MCP",
                instructions="Envoie l'email demandé via Gmail. Confirme en français.",
                mcp_servers=[gmail_server],
                model=config.groq_model,
            )

            task = (
                f"Envoie un email à {destinataire} "
                f"avec le sujet '{sujet}' "
                f"et ce contenu :\n\n{contenu_mail}"
            )

            result = await Runner.run(agent_gmail, input=task, max_turns=5)
            return result.final_output

    except Exception as e:
        return f"❌ Erreur envoi mail : {type(e).__name__}: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# FONCTION : Planifier un parcours dans Google Calendar via MCP
# ══════════════════════════════════════════════════════════════════════════════

async def _planifier_calendrier_mcp(contenu_plan: str) -> str:
    """Connecte le serveur MCP Calendar, crée un agent, planifie les événements."""
    if not MCP_CALENDAR_AVAILABLE:
        return "❌ Google Calendar MCP non configuré. Ajoutez COMPOSIO_MCP_CALENDAR_URL et COMPOSIO_API_KEY dans les secrets."

    # Extraire uniquement le parcours (étapes/mois) pour rester sous 10k tokens
    parcours = _extract_parcours(contenu_plan)

    try:
        async with MCPServerStreamableHttp(
            name="Google Calendar Composio",
            params={
                "url": COMPOSIO_MCP_CALENDAR_URL,
                "headers": {"x-api-key": COMPOSIO_API_KEY},
            },
            cache_tools_list=True,
        ) as calendar_server:

            # Instructions compactes
            agent_calendar = Agent(
                name="Agent Google Calendar MCP",
                instructions=(
                    "Crée des événements Google Calendar pour chaque étape du parcours.\n"
                    "Événements all-day, premier dans 7 jours.\n"
                    "Titre : 'Cyber Compass — [étape]'.\n"
                    "Confirme en français."
                ),
                mcp_servers=[calendar_server],
                model=config.groq_model,
            )

            task = (
                "Crée des événements Calendar pour ce parcours :\n\n"
                f"{parcours}"
            )

            result = await Runner.run(agent_calendar, input=task, max_turns=10)
            return result.final_output

    except Exception as e:
        return f"❌ Erreur planification calendrier : {type(e).__name__}: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# FONCTIONS SYNCHRONES pour app.py (wrappers asyncio)
# ══════════════════════════════════════════════════════════════════════════════

def envoyer_par_mail(destinataire: str, sujet: str, contenu: str) -> str:
    """Wrapper synchrone pour l'envoi de mail MCP. Utilisé par app.py."""
    return asyncio.run(_envoyer_mail_mcp(destinataire, sujet, contenu))


def planifier_calendrier(contenu_plan: str) -> str:
    """Wrapper synchrone pour la planification Calendar MCP. Utilisé par app.py."""
    return asyncio.run(_planifier_calendrier_mcp(contenu_plan))
