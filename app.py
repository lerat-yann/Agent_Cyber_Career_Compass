"""
Cyber Career Compass — Interface Streamlit V5
Lancement : streamlit run app.py

V5 : Système de profilage (sidebar) pour personnaliser les recommandations.
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


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Profil utilisateur (V5)
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("👤 Mon profil")
    st.caption("Optionnel — permet de personnaliser les recommandations")

    if "profil" not in st.session_state:
        st.session_state.profil = {
            "niveau": "Non renseigné",
            "temps": "Non renseigné",
            "budget": "Non renseigné",
            "anglais": "Non renseigné",
        }

    with st.expander("🎯 Renseigner mon profil", expanded=False):
        niveau = st.selectbox(
            "Niveau technique actuel",
            [
                "Non renseigné",
                "Débutant complet (jamais ouvert un terminal)",
                "Bases IT (je sais utiliser un PC, un peu de réseau)",
                "Technicien IT (admin sys, support, helpdesk)",
                "Développeur (web, backend, mobile)",
                "DevOps / SysAdmin expérimenté",
                "Déjà en cybersécurité (reconversion interne)",
            ],
            index=0,
            key="select_niveau",
        )

        temps = st.selectbox(
            "Temps disponible par semaine",
            [
                "Non renseigné",
                "Moins de 3h (apprentissage léger)",
                "3 à 5h (rythme régulier)",
                "5 à 10h (rythme soutenu)",
                "10h+ (formation intensive / reconversion)",
            ],
            index=0,
            key="select_temps",
        )

        budget = st.selectbox(
            "Budget formation",
            [
                "Non renseigné",
                "Gratuit uniquement (0€)",
                "Petit budget (< 50€/mois)",
                "Budget moyen (50-200€/mois ou CPF)",
                "Budget confortable (certifications payantes OK)",
            ],
            index=0,
            key="select_budget",
        )

        anglais = st.selectbox(
            "Niveau d'anglais",
            [
                "Non renseigné",
                "Pas du tout (ressources FR uniquement)",
                "Lecture basique (je me débrouille avec un traducteur)",
                "Confortable en lecture (docs techniques OK)",
                "Bilingue / courant",
            ],
            index=0,
            key="select_anglais",
        )

        if st.button("💾 Enregistrer mon profil", use_container_width=True):
            st.session_state.profil = {
                "niveau": niveau,
                "temps": temps,
                "budget": budget,
                "anglais": anglais,
            }
            st.success("Profil enregistré !")

    # Résumé compact du profil actif
    profil = st.session_state.profil
    profil_actif = any(v != "Non renseigné" for v in profil.values())

    if profil_actif:
        st.markdown("**Profil actif :**")
        for key, emoji in [("niveau", "📊"), ("temps", "⏱️"), ("budget", "💰"), ("anglais", "🌍")]:
            if profil[key] != "Non renseigné":
                court = profil[key].split("(")[0].strip()
                st.caption(f"{emoji} {court}")

        if st.button("🗑️ Réinitialiser le profil", use_container_width=True):
            st.session_state.profil = {
                "niveau": "Non renseigné",
                "temps": "Non renseigné",
                "budget": "Non renseigné",
                "anglais": "Non renseigné",
            }
            st.rerun()
    else:
        st.caption("Aucun profil renseigné — réponses génériques")

    st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DU MANAGER
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def load_manager(provider_override=None):
    """Charge le manager avec le provider spécifié."""
    if provider_override:
        os.environ["FORCE_PROVIDER"] = provider_override
    elif "FORCE_PROVIDER" in os.environ:
        del os.environ["FORCE_PROVIDER"]

    import config
    importlib.reload(config)
    import agent_learning_coach
    importlib.reload(agent_learning_coach)
    import cyber_agents
    importlib.reload(cyber_agents)
    import manager as manager_module
    importlib.reload(manager_module)

    return manager_module.manager


if "active_provider" not in st.session_state:
    st.session_state.active_provider = None

manager = load_manager(st.session_state.active_provider)

from config import PROVIDER, HAS_FALLBACK
provider_label = "🟢 Groq (kimi-k2)" if PROVIDER == "groq" else "🟡 OpenRouter (free)"
fallback_label = " · Fallback disponible" if HAS_FALLBACK else ""
st.caption(f"Provider : {provider_label}{fallback_label}")


# ══════════════════════════════════════════════════════════════════════════════
# ENRICHISSEMENT DE LA QUERY AVEC LE PROFIL
# ══════════════════════════════════════════════════════════════════════════════

def _enrichir_query(query: str, profil: dict) -> str:
    """Ajoute le contexte du profil utilisateur à la question.
    Ne modifie rien si aucun profil n'est renseigné."""
    parties = []
    if profil.get("niveau", "Non renseigné") != "Non renseigné":
        parties.append(f"Mon niveau technique : {profil['niveau']}")
    if profil.get("temps", "Non renseigné") != "Non renseigné":
        parties.append(f"Temps disponible : {profil['temps']}")
    if profil.get("budget", "Non renseigné") != "Non renseigné":
        parties.append(f"Budget : {profil['budget']}")
    if profil.get("anglais", "Non renseigné") != "Non renseigné":
        parties.append(f"Niveau d'anglais : {profil['anglais']}")

    if not parties:
        return query

    contexte = "\n".join(f"- {p}" for p in parties)
    return (
        f"{query}\n\n"
        f"[PROFIL DE L'UTILISATEUR — adapte ta réponse en conséquence :\n"
        f"{contexte}\n"
        f"Priorise les ressources adaptées à ce profil : "
        f"niveau, budget, langue, et rythme d'apprentissage.]"
    )


# ══════════════════════════════════════════════════════════════════════════════
# EXEMPLES DE QUESTIONS
# ══════════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════════
# HISTORIQUE + CHAT
# ══════════════════════════════════════════════════════════════════════════════

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

input_value = st.session_state.pop("pending_query", None)

user_input = st.chat_input(
    "Ex : Je suis développeur, comment me reconvertir en cyber ?"
) or input_value

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Enrichir avec le profil (invisible pour l'utilisateur)
    query_enrichie = _enrichir_query(user_input, st.session_state.profil)

    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours — consultation des agents spécialisés..."):
            try:
                result = asyncio.run(
                    Runner.run(manager, input=query_enrichie, max_turns=20)
                )
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

                # Détection élargie : 429, 403, rate limit, permission denied
                is_rate_limit = (
                    "429" in error_str
                    or "403" in error_str
                    or "rate_limit" in error_str.lower()
                    or "RateLimitError" in error_type
                    or "PermissionDeniedError" in error_type
                    or "Access denied" in error_str
                )

                if is_rate_limit and HAS_FALLBACK and PROVIDER == "groq":
                    st.session_state.active_provider = "openrouter"
                    st.warning(
                        "⚡ Limite Groq atteinte — basculement sur OpenRouter. "
                        "Relancez votre question."
                    )
                    load_manager.clear()
                    st.rerun()
                elif is_rate_limit:
                    response = (
                        "⚠️ **Limite de requêtes atteinte**\n\n"
                        "Le provider actuel est temporairement saturé. "
                        "Réessayez dans quelques minutes."
                    )
                else:
                    response = f"⚠️ Erreur : {error_type}: {e}"

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Bouton retour Groq
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    if PROVIDER == "openrouter" and st.session_state.active_provider == "openrouter":
        if st.button("🔄 Réessayer avec Groq (kimi-k2)", use_container_width=True):
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
