"""
Configuration du Cyber Career Compass.
Double provider : Groq (prioritaire, meilleur tool-calling) + OpenRouter (fallback).

Les deux clés peuvent coexister dans .env :
  GROQ_API_KEY=gsk_...
  OPENROUTER_API_KEY=sk-or-...

Groq est utilisé en premier (kimi-k2 = meilleur tool-calling gratuit).
Si Groq rate-limit (429), app.py relance automatiquement avec OpenRouter.
"""

import os
from dotenv import load_dotenv
from agents import OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled

load_dotenv()

# ── Récupération des clés (compatible .env + Streamlit secrets) ──────────────
try:
    import streamlit as st
    _secrets_get = lambda key: st.secrets.get(key, None)
except Exception:
    _secrets_get = lambda key: None

GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or _secrets_get("GROQ_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or _secrets_get("OPENROUTER_API_KEY")

# ── Variable d'environnement pour forcer un provider ─────────────────────────
# Utilisée par app.py pour basculer sur OpenRouter après un 429 Groq
FORCE_PROVIDER = os.environ.get("FORCE_PROVIDER", "").lower()

# ── Sélection du provider ────────────────────────────────────────────────────
if FORCE_PROVIDER == "openrouter" and OPENROUTER_API_KEY:
    PROVIDER = "openrouter"
elif GROQ_API_KEY and FORCE_PROVIDER != "openrouter":
    PROVIDER = "groq"
elif OPENROUTER_API_KEY:
    PROVIDER = "openrouter"
else:
    raise ValueError(
        "Aucune clé API trouvée.\n"
        "Ajoutez dans votre .env :\n"
        "  GROQ_API_KEY=gsk_...          (prioritaire — meilleur tool-calling)\n"
        "  OPENROUTER_API_KEY=sk-or-...  (fallback — modèles gratuits)\n\n"
        "Idéalement, mettez LES DEUX pour le fallback automatique."
    )

# ── Configuration selon le provider ──────────────────────────────────────────
if PROVIDER == "groq":
    API_KEY = GROQ_API_KEY
    BASE_URL = "https://api.groq.com/openai/v1"
    MODEL_MAIN = "moonshotai/kimi-k2-instruct"
    MODEL_FAST = "llama-3.1-8b-instant"
    # Indique si un fallback est possible
    HAS_FALLBACK = bool(OPENROUTER_API_KEY)
else:
    API_KEY = OPENROUTER_API_KEY
    BASE_URL = "https://openrouter.ai/api/v1"
    MODEL_MAIN = "openrouter/free"
    MODEL_FAST = "openrouter/free"
    HAS_FALLBACK = False  # Déjà sur le fallback

print(f"[Config] Provider : {PROVIDER} | Modèle : {MODEL_MAIN}"
      f"{' (fallback OpenRouter disponible)' if HAS_FALLBACK else ''}")

# ── Désactiver le tracing ────────────────────────────────────────────────────
set_tracing_disabled(True)

# ── Client API ───────────────────────────────────────────────────────────────
_extra_headers = {}
if PROVIDER == "openrouter":
    _extra_headers = {
        "HTTP-Referer": "https://cyber-career-compass.streamlit.app",
        "X-Title": "Cyber Career Compass",
    }

_client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    default_headers=_extra_headers,
)

# ── Modèles exportés (noms inchangés pour compatibilité) ────────────────────
groq_model = OpenAIChatCompletionsModel(
    model=MODEL_MAIN,
    openai_client=_client,
)

groq_model_fast = OpenAIChatCompletionsModel(
    model=MODEL_FAST,
    openai_client=_client,
)
