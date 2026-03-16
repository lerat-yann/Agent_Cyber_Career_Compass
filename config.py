"""
Configuration du Cyber Career Compass — V6.
Double provider : Groq (prioritaire, meilleur tool-calling) + OpenRouter (fallback).

V6 : Registre d'agents + switch à chaud (plus de importlib.reload).
  - register_agent(agent) : enregistre un agent dans le registre
  - switch_to_fallback()  : bascule TOUS les agents sur OpenRouter
  - switch_to_groq()      : rebascule sur Groq

Les deux clés peuvent coexister dans .env :
  GROQ_API_KEY=gsk_...
  OPENROUTER_API_KEY=sk-or-...
"""

import os
from dotenv import load_dotenv
from agents import OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled

load_dotenv()

# ── Récupération des clés (compatible .env + Streamlit secrets) ──────────────
try:
    import streamlit as st
    def _secrets_get(key):
        try:
            return st.secrets.get(key, None)
        except Exception:
            return None
except Exception:
    _secrets_get = lambda key: None

GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or _secrets_get("GROQ_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or _secrets_get("OPENROUTER_API_KEY")

# ── Désactiver le tracing ────────────────────────────────────────────────────
set_tracing_disabled(True)

# ══════════════════════════════════════════════════════════════════════════════
# CLIENTS — les deux sont créés au démarrage (si les clés existent)
# ══════════════════════════════════════════════════════════════════════════════

_groq_client = None
_openrouter_client = None

if GROQ_API_KEY:
    _groq_client = AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
    )

if OPENROUTER_API_KEY:
    _openrouter_client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": "https://cyber-career-compass.streamlit.app",
            "X-Title": "Cyber Career Compass",
        },
    )

# Vérifier qu'au moins un provider est disponible
if not _groq_client and not _openrouter_client:
    raise ValueError(
        "Aucune clé API trouvée.\n"
        "Ajoutez dans votre .env :\n"
        "  GROQ_API_KEY=gsk_...          (prioritaire — meilleur tool-calling)\n"
        "  OPENROUTER_API_KEY=sk-or-...  (fallback — modèles gratuits)\n\n"
        "Idéalement, mettez LES DEUX pour le fallback automatique."
    )

# ══════════════════════════════════════════════════════════════════════════════
# MODÈLES — un jeu par provider
# ══════════════════════════════════════════════════════════════════════════════

_groq_model_main = None
_groq_model_fast = None
_openrouter_model_main = None
_openrouter_model_fast = None

if _groq_client:
    _groq_model_main = OpenAIChatCompletionsModel(
        model="moonshotai/kimi-k2-instruct",
        openai_client=_groq_client,
    )
    _groq_model_fast = OpenAIChatCompletionsModel(
        model="llama-3.1-8b-instant",
        openai_client=_groq_client,
    )

if _openrouter_client:
    _openrouter_model_main = OpenAIChatCompletionsModel(
        model="openrouter/free",
        openai_client=_openrouter_client,
    )
    _openrouter_model_fast = OpenAIChatCompletionsModel(
        model="openrouter/free",
        openai_client=_openrouter_client,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PROVIDER ACTIF + MODÈLES EXPORTÉS
# ══════════════════════════════════════════════════════════════════════════════

# Provider initial : Groq si disponible, sinon OpenRouter
if _groq_client:
    PROVIDER = "groq"
    groq_model = _groq_model_main
    groq_model_fast = _groq_model_fast
else:
    PROVIDER = "openrouter"
    groq_model = _openrouter_model_main
    groq_model_fast = _openrouter_model_fast

HAS_FALLBACK = bool(_groq_client and _openrouter_client)

print(f"[Config V6] Provider : {PROVIDER} | Modèle : {groq_model.model}"
      f"{' (fallback OpenRouter disponible)' if HAS_FALLBACK else ''}")

# ══════════════════════════════════════════════════════════════════════════════
# REGISTRE D'AGENTS — switch à chaud sans reload
# ══════════════════════════════════════════════════════════════════════════════

_registered_agents = []


def register_agent(agent):
    """Enregistre un agent pour que switch_to_fallback/switch_to_groq puisse
    mettre à jour son .model automatiquement.
    Retourne l'agent (permet d'écrire : agent = register_agent(Agent(...)))."""
    _registered_agents.append(agent)
    return agent


def switch_to_fallback():
    """Bascule TOUS les agents enregistrés sur OpenRouter.
    Retourne True si le switch a réussi, False si pas de fallback disponible."""
    global PROVIDER, groq_model, groq_model_fast

    if not _openrouter_client:
        print("[Config V6] Pas de fallback OpenRouter disponible")
        return False

    PROVIDER = "openrouter"
    groq_model = _openrouter_model_main
    groq_model_fast = _openrouter_model_fast

    for agent in _registered_agents:
        # Les agents "main" utilisent groq_model, le classifieur utilise groq_model_fast
        # On bascule tout sur OpenRouter main par défaut
        agent.model = _openrouter_model_main

    print(f"[Config V6] Switch → OpenRouter | {len(_registered_agents)} agents mis à jour")
    return True


def switch_to_groq():
    """Rebascule TOUS les agents enregistrés sur Groq.
    Retourne True si le switch a réussi, False si Groq non disponible."""
    global PROVIDER, groq_model, groq_model_fast

    if not _groq_client:
        print("[Config V6] Pas de client Groq disponible")
        return False

    PROVIDER = "groq"
    groq_model = _groq_model_main
    groq_model_fast = _groq_model_fast

    for agent in _registered_agents:
        agent.model = _groq_model_main

    print(f"[Config V6] Switch → Groq | {len(_registered_agents)} agents mis à jour")
    return True
