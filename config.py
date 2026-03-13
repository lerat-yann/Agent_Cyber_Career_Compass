import os
import streamlit as st
from dotenv import load_dotenv
from agents import OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY manquante. Créez un fichier .env avec GROQ_API_KEY=votre-clé\n"
        "Clé gratuite sur : https://console.groq.com"
    )

set_tracing_disabled(True)

groq_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
)

# Modèle principal — agents spécialisés + manager
groq_model = OpenAIChatCompletionsModel(
    model="moonshotai/kimi-k2-instruct",
    openai_client=groq_client,
)

# Modèle léger — guardrail classifieur uniquement (quota séparé)
groq_model_fast = OpenAIChatCompletionsModel(
    model="llama-3.1-8b-instant",
    openai_client=groq_client,
)
