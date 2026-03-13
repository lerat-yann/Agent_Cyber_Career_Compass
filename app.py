"""
Cyber Career Compass — Interface Streamlit
Lancement : streamlit run app.py
"""

import asyncio
import streamlit as st
from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from manager import manager

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

    # Appel de l'agent
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
                response = f"⚠️ Erreur : {type(e).__name__}: {e}"

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

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
