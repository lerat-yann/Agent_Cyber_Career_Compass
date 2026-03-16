"""
Cyber Career Compass — Interface Streamlit V7
Lancement : streamlit run app.py

V7 : Intégration MCP (Gmail + Google Calendar via Composio).
     Boutons "Envoyer par mail" et "Planifier dans Calendar" sous la réponse.
V6 : Switch à chaud Groq → OpenRouter via config.switch_to_fallback().
"""

import asyncio
import streamlit as st
import config
from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from manager import manager
from mcp_agents import (
    envoyer_par_mail,
    planifier_calendrier,
    MCP_GMAIL_AVAILABLE,
    MCP_CALENDAR_AVAILABLE,
)

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
# SIDEBAR — Profil utilisateur
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
# AFFICHAGE PROVIDER ACTIF
# ══════════════════════════════════════════════════════════════════════════════

provider_label = "🟢 Groq (kimi-k2)" if config.PROVIDER == "groq" else "🟡 OpenRouter (free)"
fallback_label = " · Fallback disponible" if config.HAS_FALLBACK else ""
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

                if is_rate_limit and config.HAS_FALLBACK and config.PROVIDER == "groq":
                    # V6 : switch à chaud — pas de reload, mutation in-place
                    switched = config.switch_to_fallback()
                    if switched:
                        st.warning(
                            "⚡ Limite Groq atteinte — basculement sur OpenRouter. "
                            "Relancez votre question."
                        )
                        st.rerun()
                    else:
                        response = (
                            "⚠️ **Limite de requêtes atteinte**\n\n"
                            "Impossible de basculer sur le provider de secours. "
                            "Réessayez dans quelques minutes."
                        )
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

        # Sauvegarder la dernière réponse pour les boutons MCP
        if not response.startswith("⚠️") and not response.startswith("🔒"):
            st.session_state.last_response = response


# ══════════════════════════════════════════════════════════════════════════════
# BOUTONS MCP : Mail + Calendar (V7)
# Affichés EN DEHORS du bloc if user_input pour persister après rerun
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.get("last_response"):
    mcp_cols = st.columns(2)

    with mcp_cols[0]:
        if MCP_GMAIL_AVAILABLE:
            if st.button("📧 Envoyer par mail", key="btn_mail", use_container_width=True):
                st.session_state.show_mail_form = True

    with mcp_cols[1]:
        if MCP_CALENDAR_AVAILABLE:
            if st.button("📅 Planifier dans Calendar", key="btn_calendar", use_container_width=True):
                st.session_state.show_calendar_confirm = True

    # ── Formulaire mail ──
    if st.session_state.get("show_mail_form"):
        with st.form("mail_form"):
            email_dest = st.text_input("Adresse email du destinataire")
            submitted = st.form_submit_button("Envoyer")
            if submitted and email_dest:
                with st.spinner("📧 Envoi en cours via Gmail MCP..."):
                    result_mail = envoyer_par_mail(
                        destinataire=email_dest,
                        sujet="Votre plan Cyber Career Compass",
                        contenu=st.session_state.last_response,
                    )
                st.markdown(result_mail)
                st.session_state.show_mail_form = False

    # ── Confirmation Calendar ──
    if st.session_state.get("show_calendar_confirm"):
        st.info("📅 Cela va créer des événements dans votre Google Calendar pour chaque étape du parcours.")
        col_ok, col_cancel = st.columns(2)
        with col_ok:
            if st.button("✅ Confirmer", key="cal_confirm"):
                with st.spinner("📅 Planification en cours via Google Calendar MCP..."):
                    result_cal = planifier_calendrier(
                        contenu_plan=st.session_state.last_response,
                    )
                st.markdown(result_cal)
                st.session_state.show_calendar_confirm = False
        with col_cancel:
            if st.button("❌ Annuler", key="cal_cancel"):
                st.session_state.show_calendar_confirm = False


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Bouton retour Groq
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    if config.PROVIDER == "openrouter" and config.HAS_FALLBACK:
        if st.button("🔄 Réessayer avec Groq (kimi-k2)", use_container_width=True):
            config.switch_to_groq()
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
