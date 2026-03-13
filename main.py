"""
Cyber Career Compass — Interface CLI
Lancement : python main.py
"""

import asyncio
from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from manager import manager

BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║             Cyber Career Compass                              ║
║   Orientation · Métiers · Compétences · Roadmap              ║
╚═══════════════════════════════════════════════════════════════╝
Posez votre question en français (ou 'quit' pour quitter)

Exemples :
  > Je suis développeur web, comment me reconvertir en cybersécurité ?
  > Quelle différence entre SOC analyst et Pentester ?
  > Je veux devenir Cloud Security Engineer, par où commencer ?
  > C'est quoi MITRE ATT&CK concrètement ?
  > Donne-moi un plan complet pour devenir pentester depuis zéro
"""

REFUSED_MESSAGE = (
    "Je suis le Cyber Career Compass — spécialisé dans l'orientation "
    "vers les métiers de la cybersécurité.\n"
    "Je ne peux traiter que des demandes liées à :\n"
    "  • L'orientation et les métiers cyber\n"
    "  • Les compétences à acquérir\n"
    "  • Les parcours d'apprentissage\n"
    "  • Les ressources pédagogiques\n"
    "  • Les concepts cyber à but éducatif\n\n"
    "Les demandes d'exploitation opérationnelle de systèmes sont hors périmètre."
)


async def chat(query: str) -> str:
    try:
        result = await Runner.run(manager, input=query, max_turns=20)
        return result.final_output
    except InputGuardrailTripwireTriggered:
        return REFUSED_MESSAGE
    except Exception as e:
        return f"Erreur inattendue : {type(e).__name__}: {e}"


def main():
    print(BANNER)
    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBonne continuation dans votre parcours cyber !")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Bonne continuation dans votre parcours cyber !")
            break

        print("\nAnalyse en cours...\n")
        response = asyncio.run(chat(query))
        print(response)


if __name__ == "__main__":
    main()
