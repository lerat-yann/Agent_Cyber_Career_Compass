"""
Cyber Career Compass — Interface Streamlit
Lancement : streamlit run app.py

Fallback automatique : Groq (kimi-k2) → OpenRouter (free) en cas de rate-limit.
"""

import asyncio
import os
import importlib
import streamlit as st
from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered

# ── Configuration de la page ──
st.set_page_config(
    page_title="Cyber Career Compass",
    page_icon="🔐",
    layout="centered",
)

st.title("🔐 Cyber Career Compass")
st.caption(
    "Orientation · Métiers · Compétences · Roadmap — "
    "Données réelles : NIST NICE Framework · MITRE ATT&CK · NIST NVD"
)


# ── Chargement du manager (avec gestion du fallback) ──
@st.cache_resource
def load_manager(provider_override=None):
    """Charge le manager avec le provider spécifié.
    Si provider_override='openrouter', force le fallback."""
    if provider_override:
        os.environ["FORCE_PROVIDER"] = provider_override
    elif "FORCE_PROVIDER" in os.environ:
        del os.environ["FORCE_PROVIDER"]

    # Recharger les modules pour prendre en compte le nouveau provider
    import config
    importlib.reload(config)
    import agent_learning_coach
    importlib.reload(agent_learning_coach)
    import cyber_agents
    importlib.reload(cyber_agents)
    import manager as manager_module
    importlib.reload(manager_module)

    return manager_module.manager


# Initialiser le provider actif
if "active_provider" not in st.session_state:
    st.session_state.active_provider = None  # Auto-detect

manager = load_manager(st.session_state.active_provider)

# Afficher le provider actif
from config import PROVIDER, HAS_FALLBACK
provider_label = "🟢 Groq (kimi-k2)" if PROVIDER == "groq" else "🟡 OpenRouter (free)"
fallback_label = " · Fallback disponible" if HAS_FALLBACK else ""
st.caption(f"Provider : {provider_label}{fallback_label}")


# ── Exemples de questions ──
with st.expander("💡 Exemples de questions", expanded=False):
    examples = [
        "Je suis développeur web, comment me reconvertir en cybersécurité ?",
        "Quelle différence entre SOC analyst et Pentester ?",
        "Je veux devenir Cloud Security Engineer, par où commencer ?",
        "Donne-moi un plan complet pour devenir pentester depuis zéro",
        "C'est quoi MITRE ATT&CK concrètement ?",
        "Quelles compétences pour un GRC analyst ?",
        "Je suis admin système avec 3 ans d'expérience, quel métier cyber me correspond ?",
    ]
    for ex in examples:
        if st.button(f"→ {ex}", key=ex, use_container_width=True):
            st.session_state.pending_query = ex

# ── Historique de conversation ──
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Affichage de l'historique ──
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Gestion des questions via boutons exemples ──
input_value = st.session_state.pop("pending_query", None)

# ── Input utilisateur ──
user_input = st.chat_input(
    "Ex : Je suis développeur, comment me reconvertir en cyber ?"
) or input_value

if user_input:
    # Afficher la question
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Appel de l'agent avec gestion du fallback
    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours — consultation des agents spécialisés..."):
            try:
                result = asyncio.run(Runner.run(manager, input=user_input, max_turns=20))
                response = result.final_output

            except InputGuardrailTripwireTriggered:
                response = (
                    "🔒 **Demande hors périmètre**\n\n"
                    "Je suis spécialisé dans l'**orientation vers les métiers cyber** et "
                    "l'**apprentissage de la cybersécurité**.\n\n"
                    "Je ne traite pas les demandes d'exploitation opérationnelle de systèmes.\n\n"
                    "**Ce que je peux faire :**\n"
                    "- Vous orienter vers les métiers cyber adaptés à votre profil\n"
                    "- Vous donner un plan d'apprentissage concret\n"
                    "- Vous expliquer les concepts cyber à but éducatif\n"
                    "- Vous recommander des ressources gratuites\n"
                )

            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__

                # Détection rate-limit (429) → fallback automatique
                if ("429" in error_str or "rate_limit" in error_str.lower()
                        or "RateLimitError" in error_type):
                    if HAS_FALLBACK and PROVIDER == "groq":
                        # Basculer sur OpenRouter
                        st.session_state.active_provider = "openrouter"
                        st.warning(
                            "⚡ Limite Groq atteinte — basculement automatique sur OpenRouter. "
                            "Relancez votre question."
                        )
                        load_manager.clear()  # Vider le cache pour recharger
                        st.rerun()
                    else:
                        response = (
                            "⚠️ **Limite de requêtes atteinte**\n\n"
                            "Le provider actuel est temporairement saturé. "
                            "Réessayez dans quelques minutes."
                        )
                else:
                    response = f"⚠️ Erreur : {error_type}: {e}"

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# ── Bouton pour revenir sur Groq (si on est en fallback) ──
if PROVIDER == "openrouter" and st.session_state.active_provider == "openrouter":
    if st.sidebar.button("🔄 Réessayer avec Groq (kimi-k2)"):
        st.session_state.active_provider = None
        load_manager.clear()
        st.rerun()

# ── Footer ──
st.divider()
st.caption(
    "Sources : [NIST NICE Framework](https://niccs.cisa.gov/workforce-development/nice-framework) · "
    "[MITRE ATT&CK](https://attack.mitre.org/) · "
    "[NIST NVD](https://nvd.nist.gov/) · "
    "[PortSwigger](https://portswigger.net/web-security) · "
    "[TryHackMe](https://tryhackme.com) · "
    "[ANSSI](https://www.ssi.gouv.fr/)"
)
