"""
Agents MCP du Cyber Career Compass — V7.5.

Intègre Gmail et Google Calendar via Composio MCP (Streamable HTTP).
Utilise tool_filter pour n'exposer que les tools nécessaires (1-2 par serveur)
au lieu des 22 par défaut. Cela réduit les tokens de ~5000 à ~500,
permettant d'envoyer le contenu intégral sous la limite Groq 10k.
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


# ── Tool filters ─────────────────────────────────────────────────────────────
# On ne garde que les tools strictement nécessaires pour réduire les tokens.
# Les noms exacts seront découverts au premier run — on filtre par mots-clés.

def _gmail_tool_filter(context, tool):
    """Ne garde que les tools d'envoi de mail."""
    name = tool.name.lower()
    return any(kw in name for kw in ["send", "create_draft", "create_email"])


def _calendar_tool_filter(context, tool):
    """Ne garde que le tool de création d'événement."""
    name = tool.name.lower()
    return "create_event" in name or "create_a_event" in name or "insert_event" in name


def _extract_parcours(contenu: str) -> str:
    """Extrait uniquement les étapes du parcours depuis le plan complet.
    Max 6 lignes pour rester sous 10k tokens Groq avec le schéma du tool."""
    lines = contenu.split("\n")
    
    # Stratégie 1 : lignes avec → (format "1. Bases Linux → TryHackMe")
    arrow_lines = [l.strip() for l in lines if "→" in l and l.strip()]
    if len(arrow_lines) >= 3:
        return "\n".join(arrow_lines[:6])
    
    # Stratégie 2 : lignes contenant "Mois" ou "Phase"
    phase_lines = [l.strip() for l in lines 
                   if any(kw in l.lower() for kw in ["mois ", "phase "])
                   and l.strip()]
    if len(phase_lines) >= 2:
        return "\n".join(phase_lines[:6])
    
    # Stratégie 3 : lignes numérotées
    import re
    numbered = [l.strip() for l in lines if re.match(r'^\d+[\.\)]\s', l.strip())]
    if len(numbered) >= 3:
        return "\n".join(numbered[:6])
    
    # Dernier recours
    return contenu[:800]


# ══════════════════════════════════════════════════════════════════════════════
# FONCTION : Envoyer un plan par mail via Gmail MCP
# ══════════════════════════════════════════════════════════════════════════════

async def _envoyer_mail_mcp(destinataire: str, sujet: str, contenu: str) -> str:
    """Connecte le serveur MCP Gmail, crée un agent, envoie le mail."""
    if not MCP_GMAIL_AVAILABLE:
        return "❌ Gmail MCP non configuré. Ajoutez COMPOSIO_MCP_GMAIL_URL et COMPOSIO_API_KEY dans les secrets."

    try:
        async with MCPServerStreamableHttp(
            name="Gmail Composio",
            params={
                "url": COMPOSIO_MCP_GMAIL_URL,
                "headers": {"x-api-key": COMPOSIO_API_KEY},
            },
            cache_tools_list=True,
            tool_filter=_gmail_tool_filter,
        ) as gmail_server:

            agent_gmail = Agent(
                name="Agent Gmail MCP",
                instructions="Envoie l'email demandé via Gmail. Confirme en français.",
                mcp_servers=[gmail_server],
                model=config.groq_model,
            )

            task = (
                f"Envoie un email à {destinataire} "
                f"avec le sujet '{sujet}' "
                f"et ce contenu :\n\n{contenu}"
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

    # Extraire uniquement les étapes/phases du parcours pour rester sous 10k tokens.
    # L'agent Calendar n'a besoin que des étapes, pas des ressources ni du marché.
    parcours = _extract_parcours(contenu_plan)

    try:
        async with MCPServerStreamableHttp(
            name="Google Calendar Composio",
            params={
                "url": COMPOSIO_MCP_CALENDAR_URL,
                "headers": {"x-api-key": COMPOSIO_API_KEY},
            },
            cache_tools_list=True,
            tool_filter=_calendar_tool_filter,
        ) as calendar_server:

            from datetime import date, timedelta
            today = date.today()
            start = today + timedelta(days=7)

            agent_calendar = Agent(
                name="Agent Google Calendar MCP",
                instructions="Crée les événements demandés. Confirme en français.",
                mcp_servers=[calendar_server],
                model=config.groq_model,
            )

            task = (
                f"Date d'aujourd'hui : {today.strftime('%Y-%m-%d')}.\n"
                f"Crée UN événement all-day par étape, en commençant le {start.strftime('%Y-%m-%d')}.\n"
                f"Espace chaque événement de 7 jours (semaine suivante).\n"
                f"Titre : 'Cyber Compass — [nom étape]'.\n\n"
                f"Étapes :\n{parcours}"
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
