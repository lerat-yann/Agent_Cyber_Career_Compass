"""
Agents MCP du Cyber Career Compass — V7.1.

Intègre Gmail et Google Calendar via Composio MCP (Streamable HTTP).
Composio utilise le transport Streamable HTTP (pas SSE).
Requiert le header x-api-key avec la clé API Composio.

Deux fonctions exposées pour app.py :
  - envoyer_par_mail(destinataire, contenu) → envoie le plan par Gmail
  - planifier_calendrier(contenu) → crée les événements dans Google Calendar
"""

import os
import asyncio
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStreamableHttp
from config import groq_model, register_agent

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


# ══════════════════════════════════════════════════════════════════════════════
# FONCTION : Envoyer un plan par mail via Gmail MCP
# ══════════════════════════════════════════════════════════════════════════════

async def _envoyer_mail_mcp(destinataire: str, sujet: str, contenu: str) -> str:
    """Connecte le serveur MCP Gmail, crée un agent, envoie le mail."""
    if not MCP_GMAIL_AVAILABLE:
        return "❌ Gmail MCP non configuré. Ajoutez COMPOSIO_MCP_GMAIL_URL et COMPOSIO_API_KEY dans les secrets."

    # Tronquer le contenu pour rester sous la limite tokens Groq (10k TPM)
    # On garde max ~3000 caractères pour laisser de la place au prompt + tools
    contenu_tronque = contenu[:3000]
    if len(contenu) > 3000:
        contenu_tronque += "\n\n[... plan complet tronqué pour l'envoi — consultez l'app pour la version complète]"

    try:
        async with MCPServerStreamableHttp(
            name="Gmail Composio",
            params={
                "url": COMPOSIO_MCP_GMAIL_URL,
                "headers": {"x-api-key": COMPOSIO_API_KEY},
            },
            cache_tools_list=True,
        ) as gmail_server:

            agent_gmail = Agent(
                name="Agent Gmail MCP",
                instructions=(
                    "Tu es un agent spécialisé dans l'envoi d'emails via Gmail.\n"
                    "Quand on te demande d'envoyer un mail, utilise les outils Gmail disponibles.\n"
                    "Envoie le mail tel quel, sans modifier le contenu.\n"
                    "Confirme l'envoi avec l'adresse du destinataire.\n"
                    "Réponds en français."
                ),
                mcp_servers=[gmail_server],
                model=groq_model,
            )

            task = (
                f"Envoie un email à {destinataire} "
                f"avec le sujet '{sujet}' "
                f"et le contenu suivant :\n\n{contenu_tronque}"
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

    # Tronquer le plan pour rester sous la limite tokens Groq
    # On garde le parcours guidé (les étapes clés) — max ~3000 caractères
    contenu_tronque = contenu_plan[:3000]

    try:
        async with MCPServerStreamableHttp(
            name="Google Calendar Composio",
            params={
                "url": COMPOSIO_MCP_CALENDAR_URL,
                "headers": {"x-api-key": COMPOSIO_API_KEY},
            },
            cache_tools_list=True,
        ) as calendar_server:

            agent_calendar = Agent(
                name="Agent Google Calendar MCP",
                instructions=(
                    "Tu es un agent spécialisé dans la planification Google Calendar.\n"
                    "À partir d'un plan d'apprentissage cybersécurité, crée des événements "
                    "dans Google Calendar.\n\n"
                    "RÈGLES :\n"
                    "- Crée UN événement par phase/étape du parcours\n"
                    "- Chaque événement dure une journée entière (all-day event)\n"
                    "- Espace les événements selon le rythme indiqué dans le plan\n"
                    "- Le premier événement commence dans 7 jours à partir d'aujourd'hui\n"
                    "- Titre de l'événement : 'Cyber Compass — [nom de l'étape]'\n"
                    "- Description : détails de l'étape + ressources mentionnées\n"
                    "- Confirme la création de chaque événement\n"
                    "- Réponds en français"
                ),
                mcp_servers=[calendar_server],
                model=groq_model,
            )

            task = (
                "À partir du plan d'apprentissage suivant, crée des événements "
                "dans Google Calendar pour chaque phase du parcours :\n\n"
                f"{contenu_tronque}"
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
