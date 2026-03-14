# =============================================================================
# AGENT LEARNING COACH — Cyber Career Compass
# Fichier : agent_learning_coach.py
# Rôle    : Propose un parcours d'apprentissage personnalisé avec ressources
#           curatées (vidéos, labs, certifications, blogs, podcasts,
#           communautés, CTF, newsletters) pour 9 domaines cyber.
#           Séparation FR / EN, notation par étoiles, coût, parcours guidé.
# =============================================================================

from config import groq_model

# =============================================================================
# BASE DE RESSOURCES CURATÉES — 9 domaines × 8 catégories × FR + EN
# =============================================================================

RESSOURCES = {

    # -------------------------------------------------------------------------
    "pentest": {
        "label": "Pentest / Red Team",
        "youtube": {
            "fr": [
                {"nom": "Hafnium", "etoiles": 5, "desc": "Vulgarisation pentest & CTF, très pédagogique pour débutants"},
                {"nom": "Processus Verbal", "etoiles": 5, "desc": "Writeups CTF & techniques offensives expliquées en français"},
                {"nom": "MrTuxRoot", "etoiles": 4, "desc": "Pentest web, Linux, exploitation — niveau intermédiaire"},
                {"nom": "Khaos Farbauti", "etoiles": 4, "desc": "Sécurité offensive, OSINT, social engineering"},
            ],
            "en": [
                {"nom": "IppSec", "etoiles": 5, "desc": "Référence absolue HTB walkthroughs, techniques avancées"},
                {"nom": "John Hammond", "etoiles": 5, "desc": "CTF, malware, pentest — excellent pour tous niveaux"},
                {"nom": "TCM Security", "etoiles": 5, "desc": "Pentest pratique, cours complets gratuits sur YouTube"},
                {"nom": "LiveOverflow", "etoiles": 4, "desc": "Binary exploitation, web hacking — niveau avancé"},
                {"nom": "HackerSploit", "etoiles": 4, "desc": "Pentest Kali Linux, Metasploit — bon pour débutants"},
            ],
        },
        "labs": {
            "fr": [
                {"nom": "Root-Me", "etoiles": 5, "cout": "Gratuit", "desc": "Plateforme française de référence, 500+ challenges"},
                {"nom": "NewbieContest", "etoiles": 4, "cout": "Gratuit", "desc": "Wargames en français, idéal grands débutants"},
            ],
            "en": [
                {"nom": "TryHackMe", "etoiles": 5, "cout": "Gratuit+", "desc": "Parcours guidés idéal débutants. Premium vaut la peine"},
                {"nom": "HackTheBox", "etoiles": 5, "cout": "Payant", "desc": "Machines réalistes, niveau intermédiaire+. VIP recommandé"},
                {"nom": "PentesterLab", "etoiles": 4, "cout": "Payant", "desc": "Focus web, très structuré. Pro vaut la peine"},
                {"nom": "VulnHub", "etoiles": 4, "cout": "Gratuit", "desc": "VMs téléchargeables, pratique hors ligne"},
            ],
        },
        "certifications": {
            "fr": [
                {"nom": "PASSI (ANSSI)", "etoiles": 4, "cout": "Payant", "desc": "Qualification française pour prestataires pentest"},
            ],
            "en": [
                {"nom": "OSCP (OffSec)", "etoiles": 5, "cout": "Payant", "desc": "La certification pentest la plus reconnue mondialement"},
                {"nom": "eJPT (eLearnSecurity)", "etoiles": 4, "cout": "Payant", "desc": "Entrée en matière abordable avant l'OSCP"},
                {"nom": "CEH (EC-Council)", "etoiles": 4, "cout": "Payant", "desc": "Reconnue en entreprise, plus théorique que l'OSCP"},
                {"nom": "CompTIA PenTest+", "etoiles": 3, "cout": "Payant", "desc": "Bonne base théorique, moins valorisée que l'OSCP"},
            ],
        },
        "blogs_docs": {
            "fr": [
                {"nom": "Le Hack Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Articles techniques approfondis en français"},
                {"nom": "Pixis Security", "etoiles": 4, "cout": "Gratuit", "desc": "Writeups et techniques offensives en français"},
                {"nom": "ANSSI — guides PASSI", "etoiles": 4, "cout": "Gratuit", "desc": "Méthodologie officielle française pour les tests d'intrusion"},
            ],
            "en": [
                {"nom": "PortSwigger Web Academy", "etoiles": 5, "cout": "Gratuit", "desc": "Référence absolue sécurité web, labs interactifs gratuits"},
                {"nom": "HackTricks", "etoiles": 5, "cout": "Gratuit", "desc": "Bible du pentester, checklists et techniques exhaustives"},
                {"nom": "PayloadsAllTheThings", "etoiles": 4, "cout": "Gratuit", "desc": "Repo GitHub de référence pour les payloads offensifs"},
                {"nom": "OWASP Testing Guide", "etoiles": 4, "cout": "Gratuit", "desc": "Méthodologie complète pour les tests web"},
            ],
        },
        "podcasts": {
            "fr": [
                {"nom": "Darknet Podcast", "etoiles": 4, "desc": "Actualités et techniques cyber en français"},
                {"nom": "NoLimitSecu", "etoiles": 4, "desc": "Podcast généraliste cyber français très reconnu"},
            ],
            "en": [
                {"nom": "Darknet Diaries", "etoiles": 5, "desc": "Histoires vraies de hacks, excellent storytelling"},
                {"nom": "Hacking Humans (SANS)", "etoiles": 4, "desc": "Social engineering et ingénierie sociale"},
                {"nom": "Risky Business", "etoiles": 4, "desc": "Actualités sécurité offensives hebdomadaires"},
            ],
        },
        "communautes": {
            "fr": [
                {"nom": "Discord HackademINT", "etoiles": 5, "desc": "Grande communauté FR pentest & CTF, très active"},
                {"nom": "Forum Zeste de Savoir", "etoiles": 4, "desc": "Entraide technique en français, section sécurité"},
            ],
            "en": [
                {"nom": "Discord TryHackMe", "etoiles": 5, "desc": "Communauté officielle, très active, bonne entraide débutants"},
                {"nom": "Reddit r/netsec", "etoiles": 4, "desc": "Actualités et discussions techniques offensives"},
                {"nom": "Reddit r/hacking", "etoiles": 4, "desc": "Communauté généraliste, bon pour débuter"},
            ],
        },
        "ctf": {
            "fr": [
                {"nom": "FCSC (ANSSI)", "etoiles": 5, "cout": "Gratuit", "desc": "France Cybersecurity Challenge — CTF national officiel"},
                {"nom": "Hack.lu CTF", "etoiles": 4, "cout": "Gratuit", "desc": "CTF international organisé partiellement par la communauté FR"},
            ],
            "en": [
                {"nom": "CTFtime.org", "etoiles": 5, "cout": "Gratuit", "desc": "Calendrier mondial des CTF, référence pour trouver les compétitions"},
                {"nom": "picoCTF", "etoiles": 5, "cout": "Gratuit", "desc": "CTF permanent Carnegie Mellon, idéal débutants, progressif"},
                {"nom": "pwn.college", "etoiles": 4, "cout": "Gratuit", "desc": "Focus binary exploitation, très structuré — niveau intermédiaire+"},
            ],
        },
        "newsletters": {
            "fr": [
                {"nom": "CERT-FR Bulletins", "etoiles": 4, "cout": "Gratuit", "desc": "Bulletins officiels ANSSI sur les vulnérabilités actives"},
                {"nom": "Korben.info", "etoiles": 4, "cout": "Gratuit", "desc": "Actu sécurité & outils, vulgarisé, bon pour la veille"},
            ],
            "en": [
                {"nom": "tl;dr sec (Clint Gibler)", "etoiles": 5, "cout": "Gratuit", "desc": "Newsletter hebdo très dense, ressources offensives/défensives"},
                {"nom": "Krebs on Security", "etoiles": 4, "cout": "Gratuit", "desc": "Blog/newsletter de référence sur les menaces réelles"},
                {"nom": "The Hacker News", "etoiles": 4, "cout": "Gratuit", "desc": "Actualités vulnérabilités et exploits quotidiens"},
            ],
        },
        "parcours": [
            "1. Bases Linux & réseaux (TryHackMe — Pre-Security Path)",
            "2. Introduction au pentest (TryHackMe — Jr Penetration Tester Path)",
            "3. Pratique web (PortSwigger Web Academy — labs gratuits)",
            "4. Machines réalistes (HackTheBox — machines Easy/Medium)",
            "5. CTF pour consolider (picoCTF puis Root-Me)",
            "6. Certification (eJPT puis OSCP selon objectif professionnel)",
        ],
    },

    # -------------------------------------------------------------------------
    "soc": {
        "label": "SOC / Blue Team",
        "youtube": {
            "fr": [
                {"nom": "NoLimitSecu", "etoiles": 5, "desc": "Référence FR, épisodes sur la détection, SIEM, threat hunting"},
                {"nom": "Cyber Rangers", "etoiles": 4, "desc": "SOC, Blue Team, réponse à incident expliqués en français"},
                {"nom": "Sécurité Info", "etoiles": 4, "desc": "Actualités et techniques défensives vulgarisées"},
            ],
            "en": [
                {"nom": "John Hammond", "etoiles": 5, "desc": "Malware analysis, forensics, blue team — excellent tous niveaux"},
                {"nom": "SANS Cyber Defense", "etoiles": 5, "desc": "Chaîne officielle SANS, webinars threat hunting & SIEM"},
                {"nom": "Gerald Auger (SimplyCyber)", "etoiles": 4, "desc": "SOC analyst career path, outils défensifs pratiques"},
                {"nom": "13Cubed", "etoiles": 4, "desc": "Forensics Windows & memory analysis, très technique"},
            ],
        },
        "labs": {
            "fr": [
                {"nom": "Root-Me — Blue Team", "etoiles": 4, "cout": "Gratuit", "desc": "Section forensics et analyse de logs sur Root-Me"},
                {"nom": "ANSSI — Wargames FCSC", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges forensics officiels lors du FCSC"},
            ],
            "en": [
                {"nom": "TryHackMe — SOC Path", "etoiles": 5, "cout": "Gratuit+", "desc": "Parcours SOC Level 1 & 2 guidés, idéal pour débuter"},
                {"nom": "LetsDefend", "etoiles": 5, "cout": "Payant", "desc": "Simulation SOC réaliste avec alertes, logs et SIEM — très recommandé"},
                {"nom": "BlueTeamLabs Online", "etoiles": 4, "cout": "Gratuit+", "desc": "Investigations forensics et réponse à incident pratiques"},
                {"nom": "CyberDefenders", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges Blue Team réalistes, forensics & threat hunting"},
            ],
        },
        "certifications": {
            "fr": [
                {"nom": "PDIS (ANSSI)", "etoiles": 4, "cout": "Payant", "desc": "Prestataires de Détection d'Incidents — qualification nationale française"},
            ],
            "en": [
                {"nom": "CompTIA Security+", "etoiles": 5, "cout": "Payant", "desc": "Certification d'entrée reconnue mondialement, bonne base SOC"},
                {"nom": "Splunk Core Certified", "etoiles": 5, "cout": "Payant", "desc": "SIEM le plus demandé en entreprise, certification très valorisée"},
                {"nom": "BTL1 (Security Blue Team)", "etoiles": 4, "cout": "Payant", "desc": "Blue Team Level 1 — pratique et abordable, excellent rapport qualité/prix"},
                {"nom": "CySA+ (CompTIA)", "etoiles": 4, "cout": "Payant", "desc": "Cybersecurity Analyst, niveau intermédiaire SOC"},
            ],
        },
        "blogs_docs": {
            "fr": [
                {"nom": "CERT-FR", "etoiles": 5, "cout": "Gratuit", "desc": "Alertes et bulletins officiels ANSSI — lecture obligatoire analyste SOC"},
                {"nom": "Sekoia.io Blog", "etoiles": 4, "cout": "Gratuit", "desc": "Threat intelligence et analyses d'incidents par une entreprise FR"},
            ],
            "en": [
                {"nom": "MITRE ATT&CK", "etoiles": 5, "cout": "Gratuit", "desc": "Référence mondiale des TTPs adversaires — base de tout SOC"},
                {"nom": "Elastic SIEM Docs", "etoiles": 5, "cout": "Gratuit", "desc": "Documentation technique SIEM open source très utilisée"},
                {"nom": "Sigma Rules (GitHub)", "etoiles": 4, "cout": "Gratuit", "desc": "Règles de détection standardisées, référence pour les analystes"},
                {"nom": "VirusTotal Blog", "etoiles": 4, "cout": "Gratuit", "desc": "Analyses de malwares et techniques de détection"},
            ],
        },
        "podcasts": {
            "fr": [
                {"nom": "NoLimitSecu", "etoiles": 5, "desc": "Podcast FR de référence, épisodes dédiés SOC & CSIRT"},
                {"nom": "La Quadrature du Net", "etoiles": 4, "desc": "Angle défensif, droits numériques et surveillance"},
            ],
            "en": [
                {"nom": "Darknet Diaries", "etoiles": 5, "desc": "Cas réels d'incidents et réponses — excellent pour comprendre les menaces"},
                {"nom": "SANS Internet Stormcast", "etoiles": 4, "desc": "Briefing quotidien 5 min sur les menaces du jour — indispensable"},
                {"nom": "Blueprint (Detection)", "etoiles": 4, "desc": "Focus threat detection et engineering de règles SIEM"},
            ],
        },
        "communautes": {
            "fr": [
                {"nom": "Discord ZATAZ", "etoiles": 5, "desc": "Communauté FR cybersécurité défensive très active"},
                {"nom": "Slack RSSI.fr", "etoiles": 4, "desc": "Réseau professionnel des RSSI et analystes sécurité français"},
            ],
            "en": [
                {"nom": "Discord Cyber Defenders", "etoiles": 5, "desc": "Communauté Blue Team internationale, entraide sur les challenges"},
                {"nom": "Reddit r/blueteamsec", "etoiles": 4, "desc": "Articles et discussions techniques défensives de qualité"},
                {"nom": "Slack MispProject", "etoiles": 4, "desc": "Communauté autour du partage de threat intelligence"},
            ],
        },
        "ctf": {
            "fr": [
                {"nom": "FCSC — catégorie Forensics", "etoiles": 5, "cout": "Gratuit", "desc": "Challenges forensics de très haute qualité, organisés par l'ANSSI"},
            ],
            "en": [
                {"nom": "CyberDefenders", "etoiles": 5, "cout": "Gratuit", "desc": "Investigations Blue Team complètes avec pcap, logs, mémoire"},
                {"nom": "DFIR.training", "etoiles": 5, "cout": "Gratuit", "desc": "Ressources et challenges forensics & réponse à incident"},
                {"nom": "Boss of the SOC (Splunk)", "etoiles": 4, "cout": "Gratuit", "desc": "Compétition SOC avec Splunk, très réaliste"},
            ],
        },
        "newsletters": {
            "fr": [
                {"nom": "CERT-FR Alertes", "etoiles": 5, "cout": "Gratuit", "desc": "Notifications immédiates sur les vulnérabilités critiques exploitées"},
                {"nom": "Threatpost FR", "etoiles": 4, "cout": "Gratuit", "desc": "Actualités menaces et incidents en français"},
            ],
            "en": [
                {"nom": "tl;dr sec", "etoiles": 5, "cout": "Gratuit", "desc": "Newsletter hebdo dense, focus détection et outils défensifs"},
                {"nom": "SANS NewsBites", "etoiles": 5, "cout": "Gratuit", "desc": "Résumé bi-hebdomadaire des incidents et vulnérabilités critiques"},
                {"nom": "Risky Business Newsletter", "etoiles": 4, "cout": "Gratuit", "desc": "Analyse hebdo des menaces et actualités sécurité"},
            ],
        },
        "parcours": [
            "1. Bases réseaux & systèmes (TryHackMe — Pre-Security Path)",
            "2. Fondamentaux SOC (TryHackMe — SOC Level 1 Path)",
            "3. SIEM en pratique (LetsDefend — alertes simulées)",
            "4. Threat Intelligence (MITRE ATT&CK + CyberDefenders challenges)",
            "5. Forensics (BlueTeamLabs Online + DFIR.training)",
            "6. Certification (CompTIA Security+ puis BTL1 ou Splunk Core)",
        ],
    },

    # -------------------------------------------------------------------------
    "cloud": {
        "label": "Cloud Security",
        "youtube": {
            "fr": [
                {"nom": "Xavki", "etoiles": 5, "desc": "DevOps & Cloud en français, excellente pédagogie Kubernetes/AWS"},
                {"nom": "Ambient IT", "etoiles": 4, "desc": "Formations cloud AWS/Azure en français, niveau débutant à intermédiaire"},
                {"nom": "Cocadmin", "etoiles": 4, "desc": "Sécurité cloud et infrastructure as code expliqués en français"},
            ],
            "en": [
                {"nom": "Cloud Security Podcast", "etoiles": 5, "desc": "Référence cloud security, interviews d'experts AWS/GCP/Azure"},
                {"nom": "fwd:cloudsec", "etoiles": 5, "desc": "Conférences et talks cloud security avancés"},
                {"nom": "NetworkChuck", "etoiles": 4, "desc": "Cloud, réseaux, sécurité — très accessible pour débuter"},
                {"nom": "TechWorld with Nana", "etoiles": 4, "desc": "DevOps & Kubernetes — indispensable pour comprendre l'environnement cloud"},
            ],
        },
        "labs": {
            "fr": [
                {"nom": "AWS Free Tier", "etoiles": 5, "cout": "Gratuit", "desc": "Environnement réel AWS gratuit 12 mois — indispensable pour pratiquer"},
            ],
            "en": [
                {"nom": "CloudGoat (Rhino Security)", "etoiles": 5, "cout": "Gratuit", "desc": "Environnement AWS volontairement vulnérable, très réaliste"},
                {"nom": "TryHackMe — Cloud Path", "etoiles": 5, "cout": "Gratuit+", "desc": "Parcours cloud security guidé, idéal débutants"},
                {"nom": "HackTheBox — Cloud", "etoiles": 4, "cout": "Payant", "desc": "Machines cloud réalistes, niveau intermédiaire+"},
                {"nom": "flaws.cloud / flaws2.cloud", "etoiles": 5, "cout": "Gratuit", "desc": "Challenges AWS vulnérables créés par Scott Piper — référence absolue"},
            ],
        },
        "certifications": {
            "fr": [
                {"nom": "AWS Solutions Architect Associate", "etoiles": 5, "cout": "Payant", "desc": "Certification AWS la plus demandée en entreprise — très valorisée"},
            ],
            "en": [
                {"nom": "AWS Security Specialty", "etoiles": 5, "cout": "Payant", "desc": "La certification cloud security AWS la plus reconnue"},
                {"nom": "Google Professional Cloud Security", "etoiles": 4, "cout": "Payant", "desc": "Équivalent GCP, très demandé dans les grandes entreprises"},
                {"nom": "CCSP (ISC2)", "etoiles": 4, "cout": "Payant", "desc": "Certification cloud security généraliste, reconnue mondialement"},
                {"nom": "AZ-500 (Microsoft Azure)", "etoiles": 4, "cout": "Payant", "desc": "Certification sécurité Azure, incontournable pour l'écosystème Microsoft"},
            ],
        },
        "blogs_docs": {
            "fr": [
                {"nom": "ANSSI — Guide Cloud", "etoiles": 5, "cout": "Gratuit", "desc": "Recommandations officielles ANSSI pour la sécurisation du cloud"},
                {"nom": "Le Cloud Sécurisé (CNIL)", "etoiles": 4, "cout": "Gratuit", "desc": "Guides CNIL sur la conformité et sécurité cloud"},
            ],
            "en": [
                {"nom": "AWS Security Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Blog officiel AWS sécurité — meilleures pratiques et nouveautés"},
                {"nom": "Hacking the Cloud", "etoiles": 5, "cout": "Gratuit", "desc": "Techniques offensives cloud, référence pour les pentesters cloud"},
                {"nom": "OWASP Cloud Security", "etoiles": 4, "cout": "Gratuit", "desc": "Guide OWASP spécifique aux menaces cloud"},
                {"nom": "CloudSecDocs", "etoiles": 4, "cout": "Gratuit", "desc": "Checklists et guides de hardening cloud par provider"},
            ],
        },
        "podcasts": {
            "fr": [
                {"nom": "Electro Monkeys", "etoiles": 4, "desc": "DevOps & Cloud en français, épisodes sur la sécurité Kubernetes"},
            ],
            "en": [
                {"nom": "Cloud Security Podcast (Google)", "etoiles": 5, "desc": "Interviews d'experts cloud security — référence du domaine"},
                {"nom": "Screaming in the Cloud", "etoiles": 4, "desc": "Actualités et pratiques cloud security, ton accessible"},
                {"nom": "AWS Podcast", "etoiles": 4, "desc": "Nouveautés AWS dont les fonctionnalités sécurité"},
            ],
        },
        "communautes": {
            "fr": [
                {"nom": "Cloud Nord (Slack FR)", "etoiles": 4, "desc": "Communauté francophone cloud & DevOps, section sécurité"},
            ],
            "en": [
                {"nom": "Cloud Security Forum (Slack)", "etoiles": 5, "desc": "Communauté internationale cloud security très active"},
                {"nom": "Reddit r/cloudsecurity", "etoiles": 4, "desc": "Discussions pratiques et retours d'expérience cloud security"},
                {"nom": "Discord fwd:cloudsec", "etoiles": 4, "desc": "Communauté des professionnels cloud security"},
            ],
        },
        "ctf": {
            "fr": [
                {"nom": "FCSC — catégorie Cloud", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges cloud lors du CTF national ANSSI"},
            ],
            "en": [
                {"nom": "flaws.cloud", "etoiles": 5, "cout": "Gratuit", "desc": "6 niveaux de challenges AWS — le meilleur CTF cloud gratuit"},
                {"nom": "flaws2.cloud", "etoiles": 5, "cout": "Gratuit", "desc": "Suite de flaws.cloud avec perspectives attaquant et défenseur"},
                {"nom": "CloudGoat scenarios", "etoiles": 4, "cout": "Gratuit", "desc": "Scénarios d'attaque AWS réalistes à déployer soi-même"},
            ],
        },
        "newsletters": {
            "fr": [
                {"nom": "ANSSI Veille Cloud", "etoiles": 4, "cout": "Gratuit", "desc": "Alertes et recommandations cloud de l'ANSSI"},
            ],
            "en": [
                {"nom": "tl;dr sec", "etoiles": 5, "cout": "Gratuit", "desc": "Section cloud security très fournie chaque semaine"},
                {"nom": "CloudSecList", "etoiles": 5, "cout": "Gratuit", "desc": "Newsletter dédiée cloud security — très ciblée et pertinente"},
                {"nom": "Last Week in AWS", "etoiles": 4, "cout": "Gratuit", "desc": "Résumé hebdo des nouveautés AWS dont les updates sécurité"},
            ],
        },
        "parcours": [
            "1. Bases cloud (AWS Free Tier + TryHackMe Cloud Path)",
            "2. Comprendre les menaces (flaws.cloud niveaux 1-6)",
            "3. Techniques offensives cloud (CloudGoat + Hacking the Cloud)",
            "4. Hardening & conformité (AWS Security Blog + CloudSecDocs)",
            "5. Certification (AWS Solutions Architect Associate puis AWS Security Specialty)",
        ],
    },

    # -------------------------------------------------------------------------
    "grc": {
        "label": "GRC / Conformité",
        "youtube": {
            "fr": [
                {"nom": "RSSI TV", "etoiles": 5, "desc": "Chaîne dédiée aux RSSI francophones, gouvernance et conformité"},
                {"nom": "Sécurité Info", "etoiles": 4, "desc": "GRC, RGPD et conformité expliqués en français"},
                {"nom": "Technique du Droit", "etoiles": 4, "desc": "Droit du numérique et conformité cyber — très utile pour la GRC"},
            ],
            "en": [
                {"nom": "Gerald Auger (SimplyCyber)", "etoiles": 5, "desc": "GRC career path, CISO mindset, excellente pédagogie"},
                {"nom": "ISACA", "etoiles": 4, "desc": "Chaîne officielle ISACA, gouvernance et audit IT"},
                {"nom": "Cybersecurity Guide", "etoiles": 4, "desc": "Frameworks GRC (NIST, ISO 27001) expliqués accessiblement"},
            ],
        },
        "labs": {
            "fr": [
                {"nom": "CNIL — Bac à sable RGPD", "etoiles": 5, "cout": "Gratuit", "desc": "Outils pratiques CNIL pour mettre en conformité RGPD"},
            ],
            "en": [
                {"nom": "TryHackMe — GRC Path", "etoiles": 4, "cout": "Gratuit+", "desc": "Introduction à la gouvernance et conformité cyber"},
                {"nom": "NIST Cybersecurity Framework", "etoiles": 5, "cout": "Gratuit", "desc": "Framework de référence US, exercices pratiques d'implémentation"},
            ],
        },
        "certifications": {
            "fr": [
                {"nom": "CISA (ISACA) — version FR", "etoiles": 5, "cout": "Payant", "desc": "Audit des systèmes d'information — certification d'or pour la GRC"},
                {"nom": "Lead Implementer ISO 27001", "etoiles": 5, "cout": "Payant", "desc": "Certification de référence pour implémenter un SMSI en entreprise"},
            ],
            "en": [
                {"nom": "CISSP (ISC2)", "etoiles": 5, "cout": "Payant", "desc": "La certification sécurité la plus reconnue mondialement pour les managers"},
                {"nom": "CISM (ISACA)", "etoiles": 5, "cout": "Payant", "desc": "Information Security Manager — très valorisée pour devenir RSSI"},
                {"nom": "CompTIA Security+", "etoiles": 4, "cout": "Payant", "desc": "Bonne base GRC, reconnue mondialement, accessible"},
            ],
        },
        "blogs_docs": {
            "fr": [
                {"nom": "ANSSI — Guides et référentiels", "etoiles": 5, "cout": "Gratuit", "desc": "RGS, PGSSI-S, guides sectoriels — référence nationale"},
                {"nom": "CNIL — Documentation", "etoiles": 5, "cout": "Gratuit", "desc": "Guides pratiques RGPD, analyses d'impact, registres"},
                {"nom": "Club EBIOS", "etoiles": 4, "cout": "Gratuit", "desc": "Ressources sur la méthode d'analyse de risque EBIOS Risk Manager"},
            ],
            "en": [
                {"nom": "NIST SP 800 series", "etoiles": 5, "cout": "Gratuit", "desc": "Publications spéciales NIST — référence mondiale pour les contrôles"},
                {"nom": "ISO 27001 Guide (IT Governance)", "etoiles": 4, "cout": "Gratuit", "desc": "Guide d'implémentation ISO 27001 accessible"},
                {"nom": "ISACA Knowledge Center", "etoiles": 4, "cout": "Gratuit", "desc": "Articles et ressources sur la gouvernance IT"},
            ],
        },
        "podcasts": {
            "fr": [
                {"nom": "NoLimitSecu — épisodes GRC", "etoiles": 5, "desc": "Épisodes dédiés RSSI, gouvernance et réglementation"},
                {"nom": "Cyber & You", "etoiles": 4, "desc": "Podcast sur les métiers cyber dont le RSSI et la GRC"},
            ],
            "en": [
                {"nom": "CISO Series Podcast", "etoiles": 5, "desc": "Discussions entre CISO sur la gouvernance et la stratégie sécurité"},
                {"nom": "Compliance & Risk Podcast", "etoiles": 4, "desc": "Focus conformité réglementaire et gestion des risques"},
                {"nom": "Security Weekly (Management)", "etoiles": 4, "desc": "Épisodes management dédiés GRC et stratégie"},
            ],
        },
        "communautes": {
            "fr": [
                {"nom": "CESIN (Club des RSSI)", "etoiles": 5, "desc": "Association des RSSI français — réseau professionnel de référence"},
                {"nom": "CLUSIF", "etoiles": 4, "desc": "Club de la Sécurité de l'Information Français, publications et événements"},
            ],
            "en": [
                {"nom": "ISACA Community", "etoiles": 5, "desc": "Réseau mondial des professionnels GRC et audit IT"},
                {"nom": "Reddit r/cybersecurity (GRC threads)", "etoiles": 4, "desc": "Discussions GRC, retours d'expérience CISO"},
                {"nom": "LinkedIn — CISO Community", "etoiles": 4, "desc": "Réseau professionnel incontournable pour les profils GRC"},
            ],
        },
        "ctf": {
            "fr": [
                {"nom": "ENISA Tabletop Exercises", "etoiles": 4, "cout": "Gratuit", "desc": "Exercices de simulation de crise cyber — format GRC"},
            ],
            "en": [
                {"nom": "NIST Tabletop Exercises", "etoiles": 5, "cout": "Gratuit", "desc": "Scénarios de gestion de crise et réponse à incident"},
                {"nom": "Cybereason Tabletop", "etoiles": 4, "cout": "Gratuit", "desc": "Exercices décisionnels pour CISO et équipes de direction"},
            ],
        },
        "newsletters": {
            "fr": [
                {"nom": "ANSSI — Lettre de la sécurité", "etoiles": 5, "cout": "Gratuit", "desc": "Publications officielles ANSSI sur la réglementation et les incidents"},
                {"nom": "CNIL Newsletter", "etoiles": 4, "cout": "Gratuit", "desc": "Actualités RGPD, délibérations et nouvelles obligations"},
            ],
            "en": [
                {"nom": "ISACA Now Newsletter", "etoiles": 5, "cout": "Gratuit", "desc": "Actualités gouvernance, audit et conformité"},
                {"nom": "Compliance Week", "etoiles": 4, "cout": "Gratuit", "desc": "Newsletter spécialisée conformité réglementaire"},
            ],
        },
        "parcours": [
            "1. Comprendre les frameworks (NIST CSF + ISO 27001 Guide gratuit)",
            "2. Analyse de risque (EBIOS Risk Manager — méthode ANSSI)",
            "3. RGPD pratique (CNIL outils + registre de traitement)",
            "4. Gouvernance IT (ISACA Knowledge Center + CISA study materials)",
            "5. Certification (CompTIA Security+ puis CISM ou CISSP selon expérience)",
        ],
    },

    # -------------------------------------------------------------------------
    "crypto": {
        "label": "Cryptographie",
        "youtube": {
            "fr": [
                {"nom": "Science Étonnante", "etoiles": 5, "desc": "Vulgarisation mathématiques et cryptographie, excellent pour les bases"},
                {"nom": "Passe-Science", "etoiles": 4, "desc": "Mathématiques appliquées à la crypto — très pédagogique"},
                {"nom": "ANSSI — Conférences", "etoiles": 4, "desc": "Conférences techniques sur la cryptographie appliquée à la cybersécurité"},
            ],
            "en": [
                {"nom": "Christof Paar (Crypto lectures)", "etoiles": 5, "desc": "Cours universitaire complet sur la cryptographie — référence académique"},
                {"nom": "computerphile", "etoiles": 5, "desc": "Explications visuelles de la crypto (RSA, AES, courbes elliptiques)"},
                {"nom": "Dan Boneh (Stanford)", "etoiles": 5, "desc": "Cours Coursera crypto disponibles sur YouTube — niveau universitaire"},
            ],
        },
        "labs": {
            "fr": [
                {"nom": "Root-Me — Cryptanalyse", "etoiles": 5, "cout": "Gratuit", "desc": "Section cryptanalyse avec challenges progressifs en français"},
            ],
            "en": [
                {"nom": "Cryptopals Challenges", "etoiles": 5, "cout": "Gratuit", "desc": "52 challenges de cryptanalyse pratique — référence absolue du domaine"},
                {"nom": "CryptoHack", "etoiles": 5, "cout": "Gratuit", "desc": "Plateforme interactive d'apprentissage crypto par la pratique"},
                {"nom": "MysteryTwister C3", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges cryptanalyse de niveaux variés"},
            ],
        },
        "certifications": {
            "fr": [
                {"nom": "Master Cryptis (Limoges)", "etoiles": 5, "cout": "Payant", "desc": "Formation universitaire française en cryptographie appliquée"},
            ],
            "en": [
                {"nom": "Coursera — Cryptography I & II (Stanford)", "etoiles": 5, "cout": "Gratuit+", "desc": "Le cours de référence mondial en cryptographie par Dan Boneh"},
                {"nom": "SANS SEC575 — Crypto", "etoiles": 4, "cout": "Payant", "desc": "Module cryptographie appliquée à la sécurité des systèmes"},
            ],
        },
        "blogs_docs": {
            "fr": [
                {"nom": "ANSSI — RGS Cryptographie", "etoiles": 5, "cout": "Gratuit", "desc": "Recommandations officielles françaises sur les algorithmes cryptographiques"},
                {"nom": "Cryptologie.fr", "etoiles": 4, "cout": "Gratuit", "desc": "Ressources pédagogiques sur la cryptographie en français"},
            ],
            "en": [
                {"nom": "A Graduate Course in Applied Cryptography", "etoiles": 5, "cout": "Gratuit", "desc": "Livre complet de Boneh & Shoup, disponible gratuitement en ligne"},
                {"nom": "NIST Cryptographic Standards", "etoiles": 5, "cout": "Gratuit", "desc": "Standards officiels (AES, SHA, post-quantique) — lecture de référence"},
                {"nom": "Crypto101 (lvh.io)", "etoiles": 4, "cout": "Gratuit", "desc": "Introduction pratique à la cryptographie, gratuit en ligne"},
            ],
        },
        "podcasts": {
            "fr": [
                {"nom": "NoLimitSecu — épisodes crypto", "etoiles": 4, "desc": "Épisodes dédiés cryptographie et PKI"},
            ],
            "en": [
                {"nom": "Security Now (Steve Gibson)", "etoiles": 5, "desc": "Épisodes approfondis sur TLS, PKI et algorithmes crypto"},
                {"nom": "Risky Business — crypto episodes", "etoiles": 4, "desc": "Actualités cryptographie post-quantique et vulnérabilités"},
            ],
        },
        "communautes": {
            "fr": [
                {"nom": "Forum Crypto-FR", "etoiles": 4, "desc": "Communauté francophone de cryptographie et cryptanalyse"},
            ],
            "en": [
                {"nom": "CryptoHack Discord", "etoiles": 5, "desc": "Communauté active de cryptanalyse, entraide sur les challenges"},
                {"nom": "Reddit r/cryptography", "etoiles": 4, "desc": "Discussions techniques et académiques sur la cryptographie"},
                {"nom": "IACR (International Assoc. for Cryptologic Research)", "etoiles": 5, "desc": "Recherche académique crypto — publications et conférences"},
            ],
        },
        "ctf": {
            "fr": [
                {"nom": "FCSC — catégorie Crypto", "etoiles": 5, "cout": "Gratuit", "desc": "Challenges cryptanalyse de très haute qualité, ANSSI"},
            ],
            "en": [
                {"nom": "Cryptopals", "etoiles": 5, "cout": "Gratuit", "desc": "52 challenges progressifs — le meilleur parcours de cryptanalyse pratique"},
                {"nom": "CryptoHack Challenges", "etoiles": 5, "cout": "Gratuit", "desc": "Challenges interactifs couvrant RSA, AES, courbes elliptiques"},
                {"nom": "CTFtime — Crypto category", "etoiles": 4, "cout": "Gratuit", "desc": "Archives de challenges crypto des meilleurs CTF internationaux"},
            ],
        },
        "newsletters": {
            "fr": [
                {"nom": "ANSSI — publications crypto", "etoiles": 4, "cout": "Gratuit", "desc": "Alertes sur les vulnérabilités cryptographiques et mises à jour RGS"},
            ],
            "en": [
                {"nom": "IACR ePrint digest", "etoiles": 5, "cout": "Gratuit", "desc": "Nouvelles publications académiques en cryptographie"},
                {"nom": "This Week in Cryptography", "etoiles": 4, "cout": "Gratuit", "desc": "Résumé hebdo des actualités et vulnérabilités cryptographiques"},
            ],
        },
        "parcours": [
            "1. Bases mathématiques (Science Étonnante + Passe-Science YouTube)",
            "2. Cryptographie appliquée (Coursera Cryptography I par Dan Boneh — gratuit)",
            "3. Pratique (Crypto101 + CryptoHack premiers challenges)",
            "4. Cryptanalyse (Cryptopals challenges 1 à 20)",
            "5. Niveau avancé (FCSC crypto + CryptoHack avancé + lecture IACR)",
        ],
    },

    # -------------------------------------------------------------------------
    "dfir": {
        "label": "Forensics / DFIR",
        "youtube": {
            "fr": [
                {"nom": "ANSSI — Conférences DFIR", "etoiles": 5, "desc": "Conférences techniques sur la réponse à incident et forensics"},
                {"nom": "Forensics France", "etoiles": 4, "desc": "Chaîne dédiée au forensics numérique en français"},
            ],
            "en": [
                {"nom": "13Cubed", "etoiles": 5, "desc": "Forensics Windows, memory analysis — référence absolue du domaine"},
                {"nom": "John Hammond", "etoiles": 5, "desc": "Malware analysis, forensics CTF — excellent pour tous niveaux"},
                {"nom": "SANS DFIR Summit", "etoiles": 5, "desc": "Talks des meilleurs experts DFIR mondiaux, disponibles gratuitement"},
                {"nom": "OALabs", "etoiles": 4, "desc": "Malware reverse engineering et analyse mémoire — niveau avancé"},
            ],
        },
        "labs": {
            "fr": [
                {"nom": "Root-Me — Forensics", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges forensics progressifs en français"},
                {"nom": "FCSC — Forensics", "etoiles": 5, "cout": "Gratuit", "desc": "Challenges DFIR de haute qualité organisés par l'ANSSI"},
            ],
            "en": [
                {"nom": "BlueTeamLabs Online", "etoiles": 5, "cout": "Gratuit+", "desc": "Investigations forensics complètes avec artefacts réels"},
                {"nom": "CyberDefenders", "etoiles": 5, "cout": "Gratuit", "desc": "Labs DFIR avec pcap, images disque, mémoire — très réalistes"},
                {"nom": "DFIR.training", "etoiles": 5, "cout": "Gratuit", "desc": "Ressources et exercices forensics tous niveaux"},
                {"nom": "MemLabs (GitHub)", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges forensics mémoire avec Volatility"},
            ],
        },
        "certifications": {
            "fr": [
                {"nom": "PRIS (ANSSI)", "etoiles": 5, "cout": "Payant", "desc": "Prestataires de Réponse aux Incidents de Sécurité — qualification nationale"},
            ],
            "en": [
                {"nom": "GCFE (SANS/GIAC)", "etoiles": 5, "cout": "Payant", "desc": "GIAC Certified Forensic Examiner — référence mondiale DFIR"},
                {"nom": "GCFA (SANS/GIAC)", "etoiles": 5, "cout": "Payant", "desc": "GIAC Certified Forensic Analyst — niveau avancé, très valorisé"},
                {"nom": "GNFA (SANS/GIAC)", "etoiles": 4, "cout": "Payant", "desc": "Network Forensic Analyst — spécialisation réseau"},
                {"nom": "EnCE (OpenText)", "etoiles": 4, "cout": "Payant", "desc": "EnCase Certified Examiner — reconnu dans les enquêtes judiciaires"},
            ],
        },
        "blogs_docs": {
            "fr": [
                {"nom": "ANSSI — Guides DFIR", "etoiles": 5, "cout": "Gratuit", "desc": "Guides officiels de réponse à incident et forensics"},
                {"nom": "Forensik-blog.fr", "etoiles": 4, "cout": "Gratuit", "desc": "Blog technique forensics en français, artefacts Windows"},
            ],
            "en": [
                {"nom": "SANS DFIR Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Articles techniques DFIR par les meilleurs experts mondiaux"},
                {"nom": "Volatility Docs", "etoiles": 5, "cout": "Gratuit", "desc": "Documentation officielle du framework forensics mémoire de référence"},
                {"nom": "AboutDFIR.com", "etoiles": 5, "cout": "Gratuit", "desc": "Ressources et outils DFIR exhaustifs, bien organisés"},
                {"nom": "Forensics Wiki", "etoiles": 4, "cout": "Gratuit", "desc": "Encyclopédie des artefacts forensics et techniques d'analyse"},
            ],
        },
        "podcasts": {
            "fr": [
                {"nom": "NoLimitSecu — DFIR", "etoiles": 4, "desc": "Épisodes dédiés réponse à incident et investigation numérique"},
            ],
            "en": [
                {"nom": "SANS Internet Stormcast", "etoiles": 5, "desc": "Briefing quotidien incluant les incidents et IOC du jour"},
                {"nom": "Digital Forensics Survival Podcast", "etoiles": 5, "desc": "Podcast dédié DFIR, techniques et outils — référence du domaine"},
                {"nom": "Forensic Focus Podcast", "etoiles": 4, "desc": "Interviews de praticiens DFIR et actualités du domaine"},
            ],
        },
        "communautes": {
            "fr": [
                {"nom": "Discord DFIR.fr", "etoiles": 4, "desc": "Communauté francophone DFIR et réponse à incident"},
            ],
            "en": [
                {"nom": "DFIR.training Community", "etoiles": 5, "desc": "Communauté DFIR internationale, partage de ressources et d'outils"},
                {"nom": "Discord CyberDefenders", "etoiles": 5, "desc": "Entraide sur les investigations forensics et les challenges"},
                {"nom": "Reddit r/computerforensics", "etoiles": 4, "desc": "Questions techniques et retours d'expérience DFIR"},
            ],
        },
        "ctf": {
            "fr": [
                {"nom": "FCSC — Forensics", "etoiles": 5, "cout": "Gratuit", "desc": "Les meilleurs challenges forensics en français, niveau ANSSI"},
            ],
            "en": [
                {"nom": "CyberDefenders", "etoiles": 5, "cout": "Gratuit", "desc": "Investigations complètes avec disques, mémoire, pcap"},
                {"nom": "BlueTeamLabs DFIR challenges", "etoiles": 5, "cout": "Gratuit+", "desc": "Scénarios réalistes de réponse à incident"},
                {"nom": "MemLabs", "etoiles": 4, "cout": "Gratuit", "desc": "6 labs memory forensics avec Volatility, progressifs"},
            ],
        },
        "newsletters": {
            "fr": [
                {"nom": "CERT-FR — Rapports d'incidents", "etoiles": 5, "cout": "Gratuit", "desc": "Rapports d'analyse d'incidents réels publiés par l'ANSSI"},
            ],
            "en": [
                {"nom": "SANS DFIR Newsletter", "etoiles": 5, "cout": "Gratuit", "desc": "Actualités forensics et outils DFIR hebdomadaires"},
                {"nom": "This Week in 4n6", "etoiles": 5, "cout": "Gratuit", "desc": "Résumé hebdo des publications, outils et writeups DFIR"},
                {"nom": "Forensic Focus Newsletter", "etoiles": 4, "cout": "Gratuit", "desc": "Actualités du domaine forensics numérique"},
            ],
        },
        "parcours": [
            "1. Bases OS (artefacts Windows/Linux — SANS posters gratuits)",
            "2. Forensics fichiers (CyberDefenders — challenges Beginner)",
            "3. Memory forensics (MemLabs + Volatility docs)",
            "4. Network forensics (BlueTeamLabs + analyse pcap Wireshark)",
            "5. Incident response complet (DFIR.training + scénarios CyberDefenders)",
            "6. Certification (GCFE puis GCFA selon niveau d'expérience)",
        ],
    },

    # -------------------------------------------------------------------------
    "threat_intel": {
        "label": "Threat Intelligence",
        "youtube": {
            "fr": [
                {"nom": "ANSSI — Conférences CTI", "etoiles": 5, "desc": "Conférences sur la Cyber Threat Intelligence par l'ANSSI"},
                {"nom": "Sekoia.io YouTube", "etoiles": 4, "desc": "Webinars CTI par une entreprise française spécialisée"},
            ],
            "en": [
                {"nom": "SANS CTI Summit", "etoiles": 5, "desc": "Summit annuel dédié à la threat intelligence — talks d'experts"},
                {"nom": "Katie Nickels (MITRE)", "etoiles": 5, "desc": "Talks sur ATT&CK et threat intelligence appliquée"},
                {"nom": "CrowdStrike YouTube", "etoiles": 4, "desc": "Analyses de groupes APT et techniques CTI"},
            ],
        },
        "labs": {
            "fr": [
                {"nom": "MISP (instance de test)", "etoiles": 5, "cout": "Gratuit", "desc": "Plateforme open source de partage de threat intelligence — déployer localement"},
            ],
            "en": [
                {"nom": "TryHackMe — CTI Path", "etoiles": 4, "cout": "Gratuit+", "desc": "Introduction guidée à la threat intelligence"},
                {"nom": "OpenCTI (instance de test)", "etoiles": 5, "cout": "Gratuit", "desc": "Plateforme CTI open source très utilisée en entreprise"},
                {"nom": "MITRE ATT&CK Navigator", "etoiles": 5, "cout": "Gratuit", "desc": "Outil officiel MITRE pour cartographier les TTPs — indispensable"},
            ],
        },
        "certifications": {
            "fr": [
                {"nom": "CERT-FR — Formations CTI", "etoiles": 4, "cout": "Payant", "desc": "Formations officielles sur la CTI dispensées par l'ANSSI"},
            ],
            "en": [
                {"nom": "SANS FOR578 (GCTI)", "etoiles": 5, "cout": "Payant", "desc": "Cyber Threat Intelligence — la formation de référence mondiale"},
                {"nom": "Recorded Future University", "etoiles": 4, "cout": "Gratuit", "desc": "Formations CTI gratuites par Recorded Future"},
                {"nom": "MITRE ATT&CK Defender (MAD)", "etoiles": 4, "cout": "Gratuit", "desc": "Certification gratuite MITRE sur l'utilisation d'ATT&CK"},
            ],
        },
        "blogs_docs": {
            "fr": [
                {"nom": "Sekoia.io Threat Intelligence Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Rapports CTI de qualité sur les APT ciblant l'Europe"},
                {"nom": "ANSSI — Rapports CTI", "etoiles": 5, "cout": "Gratuit", "desc": "Rapports d'analyse de menaces publiés par l'ANSSI"},
            ],
            "en": [
                {"nom": "MITRE ATT&CK", "etoiles": 5, "cout": "Gratuit", "desc": "Base de données TTPs adversaires — référence mondiale CTI"},
                {"nom": "Mandiant Threat Intelligence Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Rapports APT et analyses de campagnes malveillantes"},
                {"nom": "The DFIR Report", "etoiles": 5, "cout": "Gratuit", "desc": "Rapports d'incidents détaillés avec TTPs mappés ATT&CK"},
                {"nom": "Recorded Future Blog", "etoiles": 4, "cout": "Gratuit", "desc": "Analyses de menaces et tendances CTI"},
            ],
        },
        "podcasts": {
            "fr": [
                {"nom": "NoLimitSecu — CTI", "etoiles": 4, "desc": "Épisodes dédiés threat intelligence et renseignement cyber"},
            ],
            "en": [
                {"nom": "SANS CTI Summit Recordings", "etoiles": 5, "desc": "Archives des présentations du summit CTI — très dense"},
                {"nom": "Threat Intelligence Podcast (Recorded Future)", "etoiles": 5, "desc": "Interviews d'analystes CTI et actualités des menaces"},
                {"nom": "Risky Business", "etoiles": 4, "desc": "Actualités menaces avec perspective CTI hebdomadaire"},
            ],
        },
        "communautes": {
            "fr": [
                {"nom": "FIRST.org — membres FR", "etoiles": 4, "desc": "Forum international des équipes de réponse à incident, présence française"},
            ],
            "en": [
                {"nom": "MISP Community", "etoiles": 5, "desc": "Communauté mondiale de partage de threat intelligence"},
                {"nom": "CTI League", "etoiles": 4, "desc": "Communauté de professionnels CTI partageant des IOC"},
                {"nom": "Reddit r/threatintelligence", "etoiles": 4, "desc": "Discussions sur les techniques et outils CTI"},
            ],
        },
        "ctf": {
            "fr": [
                {"nom": "FCSC — Threat Intel challenges", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges d'attribution et d'analyse de menaces"},
            ],
            "en": [
                {"nom": "MITRE ATT&CK Evaluations", "etoiles": 5, "cout": "Gratuit", "desc": "Scénarios d'évaluation basés sur des APT réels"},
                {"nom": "CyberDefenders — CTI labs", "etoiles": 4, "cout": "Gratuit", "desc": "Labs d'investigation avec perspective threat intelligence"},
            ],
        },
        "newsletters": {
            "fr": [
                {"nom": "ANSSI — Rapports de menaces", "etoiles": 5, "cout": "Gratuit", "desc": "Publications CTI officielles sur les menaces ciblant la France"},
                {"nom": "Sekoia.io Newsletter CTI", "etoiles": 4, "cout": "Gratuit", "desc": "Veille mensuelle sur les APT et campagnes actives"},
            ],
            "en": [
                {"nom": "The DFIR Report Newsletter", "etoiles": 5, "cout": "Gratuit", "desc": "Rapports hebdo d'incidents réels avec analyse CTI complète"},
                {"nom": "Mandiant Threat Intelligence", "etoiles": 5, "cout": "Gratuit", "desc": "Alertes et rapports sur les nouvelles campagnes APT"},
                {"nom": "Intel471 Cybercrime Newsletter", "etoiles": 4, "cout": "Gratuit", "desc": "Focus cybercriminalité et groupes ransomware"},
            ],
        },
        "parcours": [
            "1. Comprendre ATT&CK (MITRE ATT&CK Navigator + MAD certification gratuite)",
            "2. Fondamentaux CTI (TryHackMe CTI Path + Recorded Future University)",
            "3. Outils CTI (déployer MISP local + OpenCTI)",
            "4. Analyse de rapports (The DFIR Report + Mandiant blog — lire 10 rapports)",
            "5. Production de renseignement (créer ses propres rapports CTI sur des incidents publics)",
            "6. Certification (SANS FOR578 / GCTI pour les professionnels)",
        ],
    },

    # -------------------------------------------------------------------------
    "reseau": {
        "label": "Sécurité réseau",
        "youtube": {
            "fr": [
                {"nom": "Grafikart", "etoiles": 4, "desc": "Réseaux et protocoles expliqués en français, bon pour les bases"},
                {"nom": "IT-Connect", "etoiles": 5, "desc": "Tutoriels réseau Windows/Linux en français, très complets"},
                {"nom": "Khaos Farbauti", "etoiles": 4, "desc": "Sécurité réseau et sniffing expliqués en français"},
            ],
            "en": [
                {"nom": "Professor Messer", "etoiles": 5, "desc": "Network+ et Security+ — référence pour les bases réseau/sécurité"},
                {"nom": "NetworkChuck", "etoiles": 5, "desc": "Réseaux, Cisco, sécurité — très accessible et motivant"},
                {"nom": "David Bombal", "etoiles": 4, "desc": "Cisco, GNS3, ethical hacking réseau — niveau intermédiaire"},
                {"nom": "Practical Networking", "etoiles": 4, "desc": "Protocoles réseau expliqués visuellement, excellent pour débuter"},
            ],
        },
        "labs": {
            "fr": [
                {"nom": "Root-Me — Réseau", "etoiles": 5, "cout": "Gratuit", "desc": "Challenges réseau et sniffing en français, très complets"},
            ],
            "en": [
                {"nom": "TryHackMe — Network Security", "etoiles": 5, "cout": "Gratuit+", "desc": "Parcours sécurité réseau guidé, idéal débutants"},
                {"nom": "PacketLife (Wireshark labs)", "etoiles": 4, "cout": "Gratuit", "desc": "Captures pcap réelles à analyser avec Wireshark"},
                {"nom": "GNS3 (simulateur réseau)", "etoiles": 5, "cout": "Gratuit", "desc": "Simulateur réseau open source — créer des labs complets"},
                {"nom": "HackTheBox — réseau", "etoiles": 4, "cout": "Payant", "desc": "Challenges et machines avec composantes réseau avancées"},
            ],
        },
        "certifications": {
            "fr": [
                {"nom": "Cisco CCNA (version FR)", "etoiles": 5, "cout": "Payant", "desc": "Base incontournable pour tout professionnel réseau/sécurité"},
            ],
            "en": [
                {"nom": "CompTIA Network+", "etoiles": 5, "cout": "Payant", "desc": "Certification réseau vendor-neutral, excellente base"},
                {"nom": "CompTIA Security+", "etoiles": 5, "cout": "Payant", "desc": "Inclut une large partie sécurité réseau, très reconnue"},
                {"nom": "Cisco CyberOps Associate", "etoiles": 4, "cout": "Payant", "desc": "Sécurité réseau opérationnelle orientée SOC"},
                {"nom": "Juniper JNCIS-SEC", "etoiles": 3, "cout": "Payant", "desc": "Sécurité Juniper Networks, utile dans certains secteurs"},
            ],
        },
        "blogs_docs": {
            "fr": [
                {"nom": "IT-Connect Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Tutoriels réseau et sécurité en français, très bien documentés"},
                {"nom": "ANSSI — Guides réseau", "etoiles": 5, "cout": "Gratuit", "desc": "Recommandations officielles sécurisation des infrastructures réseau"},
            ],
            "en": [
                {"nom": "Cisco Security Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Analyses de menaces réseau et nouvelles vulnérabilités"},
                {"nom": "SANS Network Security", "etoiles": 5, "cout": "Gratuit", "desc": "Whitepapers et guides techniques sécurité réseau"},
                {"nom": "Wireshark Docs", "etoiles": 4, "cout": "Gratuit", "desc": "Documentation officielle Wireshark — outil incontournable"},
            ],
        },
        "podcasts": {
            "fr": [
                {"nom": "NoLimitSecu — réseau", "etoiles": 4, "desc": "Épisodes sécurité réseau et infrastructure"},
            ],
            "en": [
                {"nom": "Packet Pushers", "etoiles": 5, "desc": "Podcast réseau de référence, épisodes sécurité très techniques"},
                {"nom": "Risky Business", "etoiles": 4, "desc": "Actualités vulnérabilités réseau et attaques infrastructure"},
                {"nom": "Security Now", "etoiles": 4, "desc": "Protocoles réseau et sécurité expliqués en profondeur"},
            ],
        },
        "communautes": {
            "fr": [
                {"nom": "Forum IT-Connect", "etoiles": 5, "desc": "Communauté francophone réseau & sécurité très active"},
                {"nom": "Cisco Learning Network FR", "etoiles": 4, "desc": "Communauté Cisco avec ressources en français"},
            ],
            "en": [
                {"nom": "Reddit r/networking", "etoiles": 5, "desc": "Communauté réseau très active, bonne entraide"},
                {"nom": "Reddit r/netsec", "etoiles": 4, "desc": "Sécurité réseau, vulnérabilités et actualités techniques"},
                {"nom": "Cisco Learning Network", "etoiles": 4, "desc": "Communauté officielle Cisco, ressources et forums"},
            ],
        },
        "ctf": {
            "fr": [
                {"nom": "Root-Me — Réseau", "etoiles": 5, "cout": "Gratuit", "desc": "Section réseau avec pcap, protocoles, man-in-the-middle"},
            ],
            "en": [
                {"nom": "PicoCTF — Networking", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges réseau accessibles aux débutants"},
                {"nom": "PacketLife Challenges", "etoiles": 4, "cout": "Gratuit", "desc": "Analyses de captures réseau réelles"},
                {"nom": "CTFtime — Network category", "etoiles": 4, "cout": "Gratuit", "desc": "Archives challenges réseau des meilleurs CTF"},
            ],
        },
        "newsletters": {
            "fr": [
                {"nom": "CERT-FR — Alertes réseau", "etoiles": 5, "cout": "Gratuit", "desc": "Alertes sur les vulnérabilités d'équipements réseau critiques"},
            ],
            "en": [
                {"nom": "Packet Pushers Newsletter", "etoiles": 5, "cout": "Gratuit", "desc": "Actualités réseau et sécurité infrastructure hebdomadaires"},
                {"nom": "tl;dr sec", "etoiles": 4, "cout": "Gratuit", "desc": "Section infrastructure et réseau dans la newsletter hebdo"},
            ],
        },
        "parcours": [
            "1. Modèle OSI & protocoles (Practical Networking YouTube + Professor Messer)",
            "2. Pratique Wireshark (PacketLife captures + TryHackMe Network Security)",
            "3. Simulation réseau (GNS3 — créer un lab avec routeurs et firewall)",
            "4. Challenges réseau (Root-Me section réseau)",
            "5. Certification (CompTIA Network+ puis Security+ ou Cisco CCNA)",
        ],
    },

    # -------------------------------------------------------------------------
    "devsecops": {
        "label": "DevSecOps",
        "youtube": {
            "fr": [
                {"nom": "Xavki", "etoiles": 5, "desc": "Docker, Kubernetes, CI/CD en français — base indispensable pour DevSecOps"},
                {"nom": "Cocadmin", "etoiles": 4, "desc": "Infrastructure as code et sécurité DevOps en français"},
                {"nom": "Ambient IT", "etoiles": 4, "desc": "Formations DevOps et sécurité cloud en français"},
            ],
            "en": [
                {"nom": "TechWorld with Nana", "etoiles": 5, "desc": "DevOps complet — Docker, K8s, CI/CD — excellent pour les bases"},
                {"nom": "Defcon/BlackHat — DevSecOps talks", "etoiles": 5, "desc": "Talks sur la sécurité des pipelines CI/CD et supply chain"},
                {"nom": "OWASP DevSlop", "etoiles": 4, "desc": "Sécurité applicative et pratiques DevSecOps"},
                {"nom": "Computerphile — AppSec", "etoiles": 4, "desc": "Vulnérabilités applicatives expliquées clairement"},
            ],
        },
        "labs": {
            "fr": [
                {"nom": "Root-Me — Web & AppSec", "etoiles": 5, "cout": "Gratuit", "desc": "Challenges sécurité applicative en français"},
            ],
            "en": [
                {"nom": "PortSwigger Web Academy", "etoiles": 5, "cout": "Gratuit", "desc": "Référence absolue sécurité web — labs interactifs gratuits"},
                {"nom": "TryHackMe — DevSecOps Path", "etoiles": 5, "cout": "Gratuit+", "desc": "Parcours DevSecOps complet incluant CI/CD et containers"},
                {"nom": "OWASP WebGoat", "etoiles": 4, "cout": "Gratuit", "desc": "Application web volontairement vulnérable pour s'entraîner"},
                {"nom": "Kubernetes Goat", "etoiles": 4, "cout": "Gratuit", "desc": "Cluster Kubernetes volontairement vulnérable"},
            ],
        },
        "certifications": {
            "fr": [
                {"nom": "CNCF Kubernetes Security (CKS)", "etoiles": 5, "cout": "Payant", "desc": "Certified Kubernetes Security Specialist — référence pour la sécurité K8s"},
            ],
            "en": [
                {"nom": "GWEB (SANS/GIAC)", "etoiles": 5, "cout": "Payant", "desc": "GIAC Web Application Penetration Tester — référence AppSec"},
                {"nom": "AWS DevOps Engineer", "etoiles": 4, "cout": "Payant", "desc": "Certification DevOps AWS incluant les pratiques de sécurité"},
                {"nom": "CSSLP (ISC2)", "etoiles": 4, "cout": "Payant", "desc": "Certified Secure Software Lifecycle Professional"},
                {"nom": "CompTIA Security+", "etoiles": 4, "cout": "Payant", "desc": "Bonne base sécurité applicative reconnue"},
            ],
        },
        "blogs_docs": {
            "fr": [
                {"nom": "ANSSI — Guides développement sécurisé", "etoiles": 5, "cout": "Gratuit", "desc": "Recommandations officielles pour le développement sécurisé"},
                {"nom": "OWASP France", "etoiles": 5, "cout": "Gratuit", "desc": "Ressources OWASP en français, Top 10 et guides pratiques"},
            ],
            "en": [
                {"nom": "OWASP Top 10", "etoiles": 5, "cout": "Gratuit", "desc": "Les 10 vulnérabilités web les plus critiques — lecture obligatoire"},
                {"nom": "Google Project Zero Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Recherche en sécurité applicative de très haut niveau"},
                {"nom": "Snyk Blog", "etoiles": 4, "cout": "Gratuit", "desc": "Sécurité des dépendances et supply chain logicielle"},
                {"nom": "Trail of Bits Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Audit de sécurité et recherche appliquée — niveau très avancé"},
            ],
        },
        "podcasts": {
            "fr": [
                {"nom": "Electro Monkeys", "etoiles": 4, "desc": "DevOps & Kubernetes en français, épisodes sécurité"},
            ],
            "en": [
                {"nom": "DevSecOps Podcast (SANS)", "etoiles": 5, "desc": "Pratiques DevSecOps, outils et retours d'expérience"},
                {"nom": "Security Now — AppSec episodes", "etoiles": 4, "desc": "Épisodes dédiés à la sécurité applicative et web"},
                {"nom": "Application Security Weekly", "etoiles": 4, "desc": "Actualités et techniques AppSec hebdomadaires"},
            ],
        },
        "communautes": {
            "fr": [
                {"nom": "OWASP France Chapter", "etoiles": 5, "desc": "Chapitre français OWASP — meetups et ressources locales"},
                {"nom": "DevSecOps France (LinkedIn)", "etoiles": 4, "desc": "Groupe LinkedIn francophone DevSecOps actif"},
            ],
            "en": [
                {"nom": "OWASP Slack", "etoiles": 5, "desc": "Communauté mondiale AppSec, nombreux channels spécialisés"},
                {"nom": "Reddit r/devsecops", "etoiles": 4, "desc": "Discussions pratiques DevSecOps, outils et retours d'expérience"},
                {"nom": "DevSecOps Community (Discord)", "etoiles": 4, "desc": "Communauté internationale DevSecOps active"},
            ],
        },
        "ctf": {
            "fr": [
                {"nom": "Root-Me — Web Serveur", "etoiles": 5, "cout": "Gratuit", "desc": "Challenges injection, XSS, CSRF — excellents pour AppSec"},
            ],
            "en": [
                {"nom": "PortSwigger Web Academy Labs", "etoiles": 5, "cout": "Gratuit", "desc": "Labs interactifs sur toutes les vulnérabilités web — incontournable"},
                {"nom": "OWASP WebGoat", "etoiles": 4, "cout": "Gratuit", "desc": "Application d'entraînement aux vulnérabilités OWASP"},
                {"nom": "HackTheBox — Web challenges", "etoiles": 4, "cout": "Payant", "desc": "Challenges web réalistes de niveau intermédiaire à avancé"},
            ],
        },
        "newsletters": {
            "fr": [
                {"nom": "ANSSI — Développement sécurisé", "etoiles": 4, "cout": "Gratuit", "desc": "Publications sur les vulnérabilités applicatives et bonnes pratiques"},
            ],
            "en": [
                {"nom": "tl;dr sec — AppSec section", "etoiles": 5, "cout": "Gratuit", "desc": "Section DevSecOps et AppSec très fournie chaque semaine"},
                {"nom": "Snyk Newsletter", "etoiles": 4, "cout": "Gratuit", "desc": "Vulnérabilités dans les dépendances open source"},
                {"nom": "OWASP Newsletter", "etoiles": 4, "cout": "Gratuit", "desc": "Actualités sécurité applicative et nouveaux projets OWASP"},
            ],
        },
        "parcours": [
            "1. Bases DevOps (TechWorld with Nana — Docker & K8s + Xavki FR)",
            "2. Vulnérabilités web (OWASP Top 10 + PortSwigger Web Academy)",
            "3. Sécurité des pipelines CI/CD (TryHackMe DevSecOps Path)",
            "4. Sécurité des containers (Kubernetes Goat + CKS study materials)",
            "5. Pratique avancée (HackTheBox Web + Root-Me Web Serveur)",
            "6. Certification (CKS pour Kubernetes ou GWEB pour AppSec)",
        ],
    },

    # -------------------------------------------------------------------------
    "osint": {
        "label": "OSINT",
        "youtube": {
            "fr": [
                {"nom": "Khaos Farbauti", "etoiles": 5, "desc": "OSINT, investigations et social engineering en français — référence FR"},
                {"nom": "Wonderfall", "etoiles": 4, "desc": "OSINT pratique et vie privée en français"},
                {"nom": "Geotrouvetout", "etoiles": 4, "desc": "Géolocalisation et investigation OSINT en français"},
            ],
            "en": [
                {"nom": "Bendobrown (The OSINT Curious Project)", "etoiles": 5, "desc": "Référence mondiale OSINT, techniques et outils pratiques"},
                {"nom": "IntelTechniques (Michael Bazzell)", "etoiles": 5, "desc": "OSINT avancé, vie privée — le plus complet du domaine"},
                {"nom": "TraceLabs", "etoiles": 4, "desc": "OSINT humanitaire pour retrouver des personnes disparues"},
                {"nom": "Sector035", "etoiles": 4, "desc": "Tutoriels OSINT hebdomadaires, outils et techniques"},
            ],
        },
        "labs": {
            "fr": [
                {"nom": "Root-Me — OSINT", "etoiles": 5, "cout": "Gratuit", "desc": "Challenges OSINT en français, investigation et géolocalisation"},
                {"nom": "OSINT-FR challenges", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges OSINT francophones variés"},
            ],
            "en": [
                {"nom": "TryHackMe — OSINT Path", "etoiles": 4, "cout": "Gratuit+", "desc": "Introduction guidée aux techniques OSINT"},
                {"nom": "GeoGuessr (pratique géoloc)", "etoiles": 4, "cout": "Gratuit+", "desc": "Excellent pour développer les réflexes de géolocalisation"},
                {"nom": "Sourcing Games", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges OSINT orientés recherche de personnes et entreprises"},
                {"nom": "TraceLabs CTF", "etoiles": 5, "cout": "Gratuit", "desc": "CTF OSINT humanitaire — trouver de vraies personnes disparues"},
            ],
        },
        "certifications": {
            "fr": [
                {"nom": "Certification OSINT (INHESJ)", "etoiles": 4, "cout": "Payant", "desc": "Formation OSINT par l'Institut National des Hautes Études de Sécurité"},
            ],
            "en": [
                {"nom": "SANS SEC487 (GOSI)", "etoiles": 5, "cout": "Payant", "desc": "Open-Source Intelligence Gathering — certification de référence"},
                {"nom": "IntelTechniques Online Training", "etoiles": 5, "cout": "Payant", "desc": "Formation complète OSINT par Michael Bazzell — très pratique"},
                {"nom": "OSINT Curious Certification", "etoiles": 4, "cout": "Payant", "desc": "Certification pratique orientée investigations réelles"},
            ],
        },
        "blogs_docs": {
            "fr": [
                {"nom": "OSINT-FR Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Blog francophone de référence sur l'OSINT et les investigations"},
                {"nom": "Khaos Farbauti Blog", "etoiles": 4, "cout": "Gratuit", "desc": "Articles OSINT et social engineering en français"},
            ],
            "en": [
                {"nom": "Bellingcat Guides", "etoiles": 5, "cout": "Gratuit", "desc": "Guides d'investigation OSINT par le média de référence mondiale"},
                {"nom": "IntelTechniques.com", "etoiles": 5, "cout": "Gratuit", "desc": "Outils et ressources OSINT de Michael Bazzell — exhaustif"},
                {"nom": "OSINT Curious Blog", "etoiles": 5, "cout": "Gratuit", "desc": "Articles et writeups OSINT hebdomadaires de très haute qualité"},
                {"nom": "Week in OSINT (Sector035)", "etoiles": 4, "cout": "Gratuit", "desc": "Résumé hebdo des outils et techniques OSINT"},
            ],
        },
        "podcasts": {
            "fr": [
                {"nom": "Khaos Farbauti Podcast", "etoiles": 4, "desc": "OSINT et investigations numériques en français"},
            ],
            "en": [
                {"nom": "Privacy, Security & OSINT (Michael Bazzell)", "etoiles": 5, "desc": "Le podcast OSINT de référence mondiale — incontournable"},
                {"nom": "The OSINT Curious Project Podcast", "etoiles": 5, "desc": "Techniques OSINT pratiques et retours d'expérience"},
                {"nom": "Bellingcat Podcast", "etoiles": 4, "desc": "Investigations OSINT journalistiques réelles"},
            ],
        },
        "communautes": {
            "fr": [
                {"nom": "Discord OSINT-FR", "etoiles": 5, "desc": "Communauté francophone OSINT très active, entraide et challenges"},
                {"nom": "Telegram OSINT France", "etoiles": 4, "desc": "Groupe Telegram francophone de partage de ressources OSINT"},
            ],
            "en": [
                {"nom": "Discord OSINT Curious", "etoiles": 5, "desc": "Communauté internationale OSINT — la plus active du domaine"},
                {"nom": "Reddit r/OSINT", "etoiles": 4, "desc": "Discussions techniques et demandes d'aide OSINT"},
                {"nom": "TraceLabs Community", "etoiles": 4, "desc": "Communauté OSINT humanitaire, CTF et formation"},
            ],
        },
        "ctf": {
            "fr": [
                {"nom": "Root-Me — OSINT", "etoiles": 5, "cout": "Gratuit", "desc": "Section OSINT complète avec géolocalisation et investigation"},
                {"nom": "FCSC — OSINT", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges OSINT lors du CTF national ANSSI"},
            ],
            "en": [
                {"nom": "TraceLabs CTF", "etoiles": 5, "cout": "Gratuit", "desc": "CTF OSINT humanitaire — cas réels de personnes disparues"},
                {"nom": "Bellingcat OSINT Challenges", "etoiles": 5, "cout": "Gratuit", "desc": "Challenges de géolocalisation et vérification de faits"},
                {"nom": "GeoHints Challenges", "etoiles": 4, "cout": "Gratuit", "desc": "Challenges de géolocalisation progressifs"},
            ],
        },
        "newsletters": {
            "fr": [
                {"nom": "OSINT-FR Newsletter", "etoiles": 5, "cout": "Gratuit", "desc": "Résumé hebdo des outils et actualités OSINT en français"},
            ],
            "en": [
                {"nom": "Week in OSINT (Sector035)", "etoiles": 5, "cout": "Gratuit", "desc": "La newsletter OSINT hebdo de référence — outils et techniques"},
                {"nom": "Bellingcat Newsletter", "etoiles": 4, "cout": "Gratuit", "desc": "Investigations et nouvelles techniques OSINT journalistiques"},
                {"nom": "IntelTechniques Newsletter", "etoiles": 4, "cout": "Gratuit", "desc": "Mises à jour des outils OSINT par Michael Bazzell"},
            ],
        },
        "parcours": [
            "1. Bases et état d'esprit (OSINT Curious YouTube + Bellingcat Guides)",
            "2. Outils fondamentaux (IntelTechniques.com + Google Dorks)",
            "3. Pratique géolocalisation (GeoGuessr + Bellingcat challenges)",
            "4. Investigations complètes (Root-Me OSINT + Sourcing Games)",
            "5. CTF OSINT (TraceLabs CTF — cas réels motivants)",
            "6. Niveau avancé (SANS SEC487 ou IntelTechniques Online Training)",
        ],
    },
}

# =============================================================================
# OUTIL : accès aux ressources curatées par domaine
# =============================================================================

import json
from agents import Agent, Runner, function_tool


@function_tool
def get_ressources_domaine(domaine: str) -> str:
    """Retourne les ressources curatées pour un domaine cyber spécifique.

    Domaines disponibles : pentest, soc, cloud, grc, crypto, dfir,
    threat_intel, reseau, devsecops, osint.

    Retourne : YouTube, labs, certifications, blogs, podcasts,
    communautés, CTF, newsletters + parcours guidé.
    Ressources séparées FR / EN, avec étoiles et coût.

    Args:
        domaine: Le domaine cyber (ex: 'pentest', 'soc', 'cloud')
    """
    domaine_lower = domaine.lower().strip()

    # Mapping des alias courants
    alias = {
        "pentesting": "pentest", "red team": "pentest", "redteam": "pentest",
        "test d'intrusion": "pentest", "test intrusion": "pentest",
        "blue team": "soc", "blueteam": "soc", "soc analyst": "soc",
        "analyste soc": "soc", "défensif": "soc",
        "cloud security": "cloud", "sécurité cloud": "cloud", "aws": "cloud",
        "azure": "cloud", "gcp": "cloud",
        "gouvernance": "grc", "conformité": "grc", "compliance": "grc",
        "risque": "grc", "rssi": "grc", "iso 27001": "grc", "rgpd": "grc",
        "cryptographie": "crypto", "chiffrement": "crypto",
        "forensics": "dfir", "forensic": "dfir", "incident response": "dfir",
        "réponse à incident": "dfir", "investigation numérique": "dfir",
        "threat intelligence": "threat_intel", "cti": "threat_intel",
        "renseignement": "threat_intel", "threat hunting": "threat_intel",
        "réseau": "reseau", "network": "reseau", "sécurité réseau": "reseau",
        "network security": "reseau", "firewall": "reseau",
        "devsecops": "devsecops", "appsec": "devsecops",
        "sécurité applicative": "devsecops", "sdlc": "devsecops",
        "osint": "osint", "investigation": "osint", "open source intelligence": "osint",
    }

    # Résolution du domaine
    if domaine_lower in RESSOURCES:
        cle = domaine_lower
    elif domaine_lower in alias:
        cle = alias[domaine_lower]
    else:
        # Recherche partielle
        cle = None
        for key in RESSOURCES:
            if key in domaine_lower or domaine_lower in key:
                cle = key
                break
        if not cle:
            return json.dumps({
                "error": f"Domaine '{domaine}' non trouvé.",
                "domaines_disponibles": list(RESSOURCES.keys()),
                "conseil": "Reformule avec un des domaines disponibles.",
            }, ensure_ascii=False)

    data = RESSOURCES[cle]
    return json.dumps(data, ensure_ascii=False, indent=2)


@function_tool
def list_domaines_disponibles() -> str:
    """Liste tous les domaines cyber disponibles dans la base de ressources curatées.
    Appelle cet outil en premier pour savoir quels domaines sont couverts."""
    domaines = []
    for cle, data in RESSOURCES.items():
        domaines.append({"cle": cle, "label": data.get("label", cle)})
    return json.dumps(domaines, ensure_ascii=False)


# =============================================================================
# INSTRUCTIONS SYSTÈME DE L'AGENT
# =============================================================================

LEARNING_COACH_INSTRUCTIONS = """
Tu es l'agent Learning Coach de Cyber Career Compass (SYS_09).

TON RÔLE : Proposer des ressources d'apprentissage personnalisées et un parcours
guidé pour aider l'utilisateur à se former dans un domaine de la cybersécurité.

FONCTIONNEMENT HYBRIDE :
Tu recevras souvent des DONNÉES CURATÉES directement dans le message (format JSON).
Ces données sont ta BASE DE RÉFÉRENCE — des ressources vérifiées, notées, avec coûts.
Tu dois TOUJOURS les utiliser comme socle de ta réponse.

Si tu ne reçois PAS de données curatées dans le message, utilise tes outils :
- list_domaines_disponibles : liste les domaines couverts
- get_ressources_domaine : retourne les ressources curatées pour un domaine

DOMAINES COUVERTS :
pentest, soc, cloud, grc, crypto, dfir, threat_intel, reseau, devsecops, osint

COMMENT RÉPONDRE :

1. UTILISER LES DONNÉES CURATÉES comme socle (les 8 catégories)
2. ADAPTER au niveau de l'utilisateur :
   - Débutant → focus sur les gratuits et les ★★★★★, parcours progressif
   - Intermédiaire → mix gratuit/payant, certifications utiles
   - Avancé → ressources pointues, certifications avancées
3. PRÉSENTER dans cet ordre, séparées FR 🇫🇷 / EN 🇬🇧 :
   1. Chaînes YouTube (démarrer facilement)
   2. Labs pratiques (mettre les mains dedans)
   3. Blogs & docs (approfondir)
   4. CTF & challenges (valider les acquis)
   5. Communautés (ne pas apprendre seul)
   6. Podcasts (veille passive)
   7. Newsletters (rester à jour)
   8. Certifications (valider officiellement — en dernier)
4. INDIQUER pour chaque ressource : nom, étoiles ★, Gratuit/Payant, description courte
5. TERMINER par le parcours guidé (clé "parcours" dans les données)
   avec la mention "Ce parcours est une suggestion, pas une obligation."

TES LIBERTÉS :
- Tu peux hiérarchiser et mettre en avant les meilleures ressources selon le niveau
- Tu peux ajouter des conseils personnalisés sur l'ordre d'apprentissage
- Tu peux enrichir avec des précisions sur comment utiliser les ressources
- Tu peux adapter le parcours guidé au contexte de l'utilisateur

TES LIMITES :
- Ne recommande JAMAIS une ressource payante sans mentionner l'alternative gratuite
- Encourage toujours à commencer par le gratuit avant d'investir
- Ne JAMAIS inventer de chiffres sur le marché de l'emploi
- Les données curatées sont ton socle — ne les ignore pas, ne les remplace pas
  par des connaissances génériques
- Réponds en français, ton bienveillant et concret
"""


# =============================================================================
# CRÉATION DE L'AGENT
# =============================================================================

agent_learning_coach = Agent(
    name="Agent Learning Coach",
    instructions=LEARNING_COACH_INSTRUCTIONS,
    tools=[get_ressources_domaine, list_domaines_disponibles],
    model=groq_model,
)
