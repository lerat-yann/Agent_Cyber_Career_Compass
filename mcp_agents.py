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
    """Extrait uniquement les étapes/phases du parcours depuis le plan complet.
    Réduit le contenu de ~8000 à ~1500 caractères pour rester sous 10k tokens Groq.
    L'utilisateur voit toujours le plan complet — cette extraction est uniquement
    pour l'agent Calendar qui n'a besoin que des étapes."""
    lines = contenu.split("\n")
    parcours_lines = []
    in_parcours = False

    for line in lines:
        lower = line.lower().strip()
        # Détecter les sections parcours/planning/phases/mois
        if any(kw in lower for kw in [
            "parcours guidé", "parcours", "planning",
            "phase 1", "phase 2", "phase 3",
            "mois 1", "mois 2", "mois 3", "mois 4", "mois 5",
            "mois 6", "mois 7", "mois 8", "mois 9", "mois 10",
            "étape 1", "étape 2", "étape 3",
        ]):
            in_parcours = True
        if in_parcours:
            parcours_lines.append(line)
        # Stopper à la fin du parcours
        if in_parcours and any(kw in lower for kw in [
            "budget", "marché réel", "conseil concret", "💰", "📊",
        ]):
            break

    if parcours_lines:
        return "\n".join(parcours_lines)

    # Fallback : si pas de section parcours trouvée, résumer les lignes clés
    key_lines = [l for l in lines if any(kw in l.lower() for kw in [
        "phase", "mois", "étape", "→", "certification", "linux", "web",
        "pratique", "ctf", "réseau", "pentest",
    ])]
    if key_lines:
        return "\n".join(key_lines[:20])

    # Dernier recours
    return contenu[:2000]


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

            agent_calendar = Agent(
                name="Agent Google Calendar MCP",
                instructions=(
                    f"Nous sommes le {__import__('datetime').date.today().strftime('%d/%m/%Y')}.\n"
                    "Crée des événements Google Calendar pour chaque étape du parcours.\n"
                    "Événements all-day, premier dans 7 jours à partir d'aujourd'hui.\n"
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
