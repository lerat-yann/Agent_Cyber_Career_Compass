"""
Outils réels pour le Cyber Career Compass.

Sources de données :
- MITRE ATT&CK STIX/TAXII : https://github.com/mitre/cti (gratuit, sans clé)
- NIST NICE Framework     : données structurées statiques (standard public NIST SP 800-181)
- NIST NVD API v2.0       : https://nvd.nist.gov/ (gratuit, 5 req/30s sans clé)
"""

import json
import requests
from agents import function_tool

MITRE_CTI_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
MITRE_CACHE_FILE = "mitre_cache.json"  # Cache disque local
_mitre_cache = None  # Cache mémoire secondaire
REQUEST_TIMEOUT = 10

# ── Données NIST NICE Framework (SP 800-181 Rev 1) ──────────────────────────
# Source : https://niccs.cisa.gov/workforce-development/nice-framework
# Structurées ici pour éviter la dépendance réseau sur ces données statiques.

NICE_ROLES = {
    "soc_analyst": {
        "nice_id": "PR-CDA-001",
        "title": "Cyber Defense Analyst",
        "category": "Protect and Defend",
        "posture": "Défensif / Blue Team",
        "level": "Intermédiaire",
        "daily_missions": [
            "Surveiller les alertes SIEM et qualifier les incidents",
            "Analyser les logs réseau, système et applicatif",
            "Investiguer les comportements suspects (triage)",
            "Documenter et escalader les incidents confirmés",
            "Maintenir et tuner les règles de détection",
        ],
        "entry_profile": "Profil méthodique, analytique, à l'aise avec les outils de monitoring",
        "salary_range_fr": "32 000 – 48 000 €/an (junior à confirmé)",
        "demand": "Très forte — pénurie mondiale de profils SOC",
    },
    "pentester": {
        "nice_id": "PR-VAM-001",
        "title": "Vulnerability Assessment Analyst / Penetration Tester",
        "category": "Analyze",
        "posture": "Offensif / Red Team",
        "level": "Intermédiaire à avancé",
        "daily_missions": [
            "Planifier et exécuter des tests d'intrusion (web, réseau, infra)",
            "Identifier, exploiter et documenter les vulnérabilités",
            "Rédiger des rapports techniques et exécutifs",
            "Recommander des mesures correctives",
            "Effectuer du reverse engineering de base",
        ],
        "entry_profile": "Curieux, créatif, à l'aise avec Linux/scripting, goût du challenge technique",
        "salary_range_fr": "40 000 – 65 000 €/an",
        "demand": "Forte — marché en croissance, certification OSCP très valorisée",
    },
    "cloud_security_engineer": {
        "nice_id": "PR-INF-001",
        "title": "Cloud Security Engineer",
        "category": "Securely Provision",
        "posture": "Défensif / Ingénierie",
        "level": "Intermédiaire à avancé",
        "daily_missions": [
            "Sécuriser les architectures cloud (AWS/Azure/GCP)",
            "Implémenter l'IAM, le chiffrement, la segmentation réseau",
            "Auditer les configurations cloud (CIS Benchmarks)",
            "Intégrer la sécurité dans les pipelines CI/CD (DevSecOps)",
            "Répondre aux incidents cloud",
        ],
        "entry_profile": "Background DevOps ou SysAdmin avec appétence sécurité",
        "salary_range_fr": "50 000 – 75 000 €/an",
        "demand": "Très forte — migration cloud massive, profils rares",
    },
    "incident_responder": {
        "nice_id": "PR-CIR-001",
        "title": "Cyber Defense Incident Responder",
        "category": "Protect and Defend",
        "posture": "Défensif / DFIR",
        "level": "Intermédiaire à avancé",
        "daily_missions": [
            "Gérer le cycle de vie complet des incidents de sécurité",
            "Conduire l'analyse forensique (disque, mémoire, réseau)",
            "Contenir et éradiquer les menaces actives",
            "Coordonner avec les équipes IT et management",
            "Produire des post-mortems et leçons apprises",
        ],
        "entry_profile": "Solide background technique, sang-froid sous pression, rigueur documentaire",
        "salary_range_fr": "45 000 – 70 000 €/an",
        "demand": "Forte — ransomwares et APT alimentent la demande",
    },
    "threat_intelligence_analyst": {
        "nice_id": "AN-TWA-001",
        "title": "Threat/Warning Analyst",
        "category": "Analyze",
        "posture": "Analytique / Mixte",
        "level": "Intermédiaire",
        "daily_missions": [
            "Collecter et analyser des renseignements sur les menaces (CTI)",
            "Produire des rapports de threat intelligence",
            "Suivre les groupes APT et leurs TTPs (MITRE ATT&CK)",
            "Alimenter les équipes SOC et IR avec du contexte",
            "Surveiller le dark web et les sources OSINT",
        ],
        "entry_profile": "Profil analytique, capacité de synthèse, intérêt géopolitique/cybercriminalité",
        "salary_range_fr": "40 000 – 60 000 €/an",
        "demand": "Croissante — spécialité émergente très recherchée",
    },
    "grc_analyst": {
        "nice_id": "OV-MGT-001",
        "title": "Information Systems Security Manager / GRC Analyst",
        "category": "Oversee and Govern",
        "posture": "Gouvernance / Risque / Conformité",
        "level": "Intermédiaire (technique modéré)",
        "daily_missions": [
            "Évaluer et gérer les risques cybersécurité",
            "Assurer la conformité (ISO 27001, RGPD, NIS2, DORA)",
            "Rédiger et maintenir les politiques de sécurité",
            "Piloter les audits internes et externes",
            "Sensibiliser les collaborateurs",
        ],
        "entry_profile": "Profil organisé, communication aisée, appétence juridique/réglementaire",
        "salary_range_fr": "38 000 – 60 000 €/an",
        "demand": "Très forte — NIS2 et DORA créent une explosion de la demande en Europe",
    },
    "appsec_engineer": {
        "nice_id": "PR-SWD-001",
        "title": "Software Developer (Security Focus) / AppSec Engineer",
        "category": "Securely Provision",
        "posture": "Mixte (Dev + Sécurité)",
        "level": "Intermédiaire",
        "daily_missions": [
            "Conduire des revues de code sécurisé",
            "Réaliser des tests SAST/DAST sur les applications",
            "Intégrer la sécurité dans les cycles de développement (SDLC)",
            "Former les développeurs aux pratiques sécurisées",
            "Triage des vulnérabilités applicatives (CVE, OWASP)",
        ],
        "entry_profile": "Développeur web/backend reconverti sécurité, connaissance des langages courants",
        "salary_range_fr": "45 000 – 70 000 €/an",
        "demand": "Forte — shift-left security, DevSecOps en plein essor",
    },
    "security_engineer": {
        "nice_id": "PR-INF-002",
        "title": "Systems Security Engineer",
        "category": "Securely Provision",
        "posture": "Défensif / Architecture",
        "level": "Avancé",
        "daily_missions": [
            "Concevoir et déployer des architectures sécurisées",
            "Intégrer et opérer les outils de sécurité (EDR, SIEM, WAF, PAM)",
            "Conduire des évaluations de sécurité des systèmes",
            "Définir les standards et guidelines techniques",
            "Collaborer avec les équipes réseau et système",
        ],
        "entry_profile": "Solide background infrastructure/réseau avec expertise sécurité",
        "salary_range_fr": "48 000 – 75 000 €/an",
        "demand": "Forte — profil généraliste très apprécié en PME et ETI",
    },
}

SKILLS_BY_ROLE = {
    "soc_analyst": [
        {"skill": "Log Analysis", "importance": "Essentiel",
         "why": "Le cœur du métier : lire les journaux pour détecter les anomalies"},
        {"skill": "SIEM", "importance": "Essentiel",
         "why": "Outil quotidien (Splunk, Microsoft Sentinel, QRadar)"},
        {"skill": "Network Basics", "importance": "Essentiel",
         "why": "Comprendre TCP/IP, DNS, HTTP pour analyser le trafic"},
        {"skill": "Security Monitoring", "importance": "Essentiel",
         "why": "Surveiller en continu les alertes et indicateurs"},
        {"skill": "Incident Response", "importance": "Important",
         "why": "Qualifier et escalader les incidents confirmés"},
        {"skill": "Threat Intelligence", "importance": "Important",
         "why": "Contextualiser les alertes avec les TTPs connus"},
        {"skill": "Linux", "importance": "Important",
         "why": "Analyser les logs et artifacts sur systèmes Linux"},
        {"skill": "Malware Basics", "importance": "Complémentaire",
         "why": "Reconnaître les comportements malveillants courants"},
        {"skill": "Scripting (Python / Bash)", "importance": "Complémentaire",
         "why": "Automatiser l'analyse et le triage d'alertes"},
        {"skill": "Forensics", "importance": "Complémentaire",
         "why": "Approfondir l'investigation sur les incidents majeurs"},
    ],
    "pentester": [
        {"skill": "Web Security", "importance": "Essentiel",
         "why": "Identifier et exploiter les vulnérabilités web (OWASP Top 10)"},
        {"skill": "Linux", "importance": "Essentiel",
         "why": "Environnement principal des outils offensifs (Kali, Parrot)"},
        {"skill": "Network Basics", "importance": "Essentiel",
         "why": "Comprendre les protocoles pour les attaques réseau"},
        {"skill": "Scripting (Python / Bash)", "importance": "Essentiel",
         "why": "Automatiser les exploits et personnaliser les outils"},
        {"skill": "Vulnerability Scanning", "importance": "Important",
         "why": "Cartographier la surface d'attaque (Nmap, Nessus, Burp)"},
        {"skill": "Windows Security Basics", "importance": "Important",
         "why": "Active Directory est une cible fréquente en pentest interne"},
        {"skill": "Malware Basics", "importance": "Important",
         "why": "Comprendre les techniques de post-exploitation"},
        {"skill": "Forensics", "importance": "Complémentaire",
         "why": "Comprendre les traces laissées lors d'un test"},
        {"skill": "Cloud Basics", "importance": "Complémentaire",
         "why": "Pentests cloud de plus en plus demandés"},
        {"skill": "Secure Coding", "importance": "Complémentaire",
         "why": "Comprendre les failles depuis la perspective développeur"},
    ],
    "cloud_security_engineer": [
        {"skill": "Cloud Basics", "importance": "Essentiel",
         "why": "Maîtriser AWS/Azure/GCP et leurs services de sécurité natifs"},
        {"skill": "IAM (Identity and Access Management)", "importance": "Essentiel",
         "why": "Le périmètre cloud repose entièrement sur l'IAM"},
        {"skill": "Network Basics", "importance": "Essentiel",
         "why": "VPC, Security Groups, segmentation réseau cloud"},
        {"skill": "DevSecOps", "importance": "Essentiel",
         "why": "Intégrer la sécurité dans les pipelines CI/CD"},
        {"skill": "Container Security", "importance": "Important",
         "why": "Docker et Kubernetes sont omniprésents dans le cloud"},
        {"skill": "Scripting (Python / Bash)", "importance": "Important",
         "why": "Automatiser les audits et remédiation via IaC"},
        {"skill": "Security Architecture", "importance": "Important",
         "why": "Concevoir des architectures cloud Zero Trust"},
        {"skill": "Vulnerability Scanning", "importance": "Complémentaire",
         "why": "Scanner les ressources cloud mal configurées"},
        {"skill": "Incident Response", "importance": "Complémentaire",
         "why": "Gérer les incidents dans un contexte cloud"},
        {"skill": "Risk Management", "importance": "Complémentaire",
         "why": "Évaluer les risques liés aux services tiers et SaaS"},
    ],
    "incident_responder": [
        {"skill": "Incident Response", "importance": "Essentiel",
         "why": "Le cœur du métier : containment, éradication, recovery"},
        {"skill": "Forensics", "importance": "Essentiel",
         "why": "Analyser les preuves numériques (disque, mémoire, réseau)"},
        {"skill": "Log Analysis", "importance": "Essentiel",
         "why": "Reconstituer la timeline de l'attaque"},
        {"skill": "Malware Basics", "importance": "Essentiel",
         "why": "Comprendre le comportement du code malveillant analysé"},
        {"skill": "Network Basics", "importance": "Important",
         "why": "Analyser le trafic pour détecter les C2 et exfiltrations"},
        {"skill": "Windows Security Basics", "importance": "Important",
         "why": "La majorité des incidents ciblent les environnements Windows"},
        {"skill": "Threat Intelligence", "importance": "Important",
         "why": "Contextualiser l'incident avec les TTPs des groupes connus"},
        {"skill": "SIEM", "importance": "Important",
         "why": "Utiliser le SIEM pour la corrélation d'événements"},
        {"skill": "Scripting (Python / Bash)", "importance": "Complémentaire",
         "why": "Automatiser la collecte d'artifacts et l'analyse"},
        {"skill": "Cloud Basics", "importance": "Complémentaire",
         "why": "Incidents cloud de plus en plus fréquents"},
    ],
    "threat_intelligence_analyst": [
        {"skill": "Threat Intelligence", "importance": "Essentiel",
         "why": "Collecter, analyser et disséminer le renseignement sur les menaces"},
        {"skill": "Log Analysis", "importance": "Essentiel",
         "why": "Corréler les indicateurs de compromission (IoC)"},
        {"skill": "Malware Basics", "importance": "Essentiel",
         "why": "Analyser les TTPs et les familles de malwares"},
        {"skill": "SIEM", "importance": "Important",
         "why": "Alimenter le SIEM avec les IoC produits"},
        {"skill": "Network Basics", "importance": "Important",
         "why": "Comprendre les vecteurs d'attaque réseau"},
        {"skill": "Scripting (Python / Bash)", "importance": "Important",
         "why": "Automatiser la collecte OSINT et le traitement des feeds"},
        {"skill": "Forensics", "importance": "Complémentaire",
         "why": "Analyser des samples de malware et des artifacts"},
        {"skill": "Risk Management", "importance": "Complémentaire",
         "why": "Traduire le renseignement en évaluation de risque"},
        {"skill": "Security Monitoring", "importance": "Complémentaire",
         "why": "Comprendre le contexte opérationnel des équipes SOC"},
        {"skill": "Web Security", "importance": "Complémentaire",
         "why": "Suivre les campagnes ciblant les applications web"},
    ],
    "grc_analyst": [
        {"skill": "Risk Management", "importance": "Essentiel",
         "why": "Évaluer, traiter et suivre les risques cyber"},
        {"skill": "Security Architecture", "importance": "Important",
         "why": "Comprendre les architectures pour évaluer les risques"},
        {"skill": "IAM (Identity and Access Management)", "importance": "Important",
         "why": "Élément central de tout référentiel de conformité"},
        {"skill": "Log Analysis", "importance": "Important",
         "why": "Vérifier la traçabilité dans le cadre des audits"},
        {"skill": "Network Basics", "importance": "Complémentaire",
         "why": "Comprendre le périmètre technique lors des audits"},
        {"skill": "Cloud Basics", "importance": "Complémentaire",
         "why": "Les référentiels cloud (CSA, CIS) sont incontournables"},
        {"skill": "Scripting (Python / Bash)", "importance": "Complémentaire",
         "why": "Automatiser les revues de conformité"},
        {"skill": "Vulnerability Scanning", "importance": "Complémentaire",
         "why": "Intégrer les scans dans le processus de gestion des risques"},
        {"skill": "Incident Response", "importance": "Complémentaire",
         "why": "Décliner les procédures IR dans les politiques"},
        {"skill": "Security Monitoring", "importance": "Complémentaire",
         "why": "Lire les tableaux de bord de sécurité lors des comités"},
    ],
    "appsec_engineer": [
        {"skill": "Web Security", "importance": "Essentiel",
         "why": "OWASP Top 10 et vulnérabilités applicatives sont le quotidien"},
        {"skill": "Secure Coding", "importance": "Essentiel",
         "why": "Guider les développeurs vers les pratiques sécurisées"},
        {"skill": "Vulnerability Scanning", "importance": "Essentiel",
         "why": "SAST/DAST pour détecter les failles dans le code et l'app"},
        {"skill": "Scripting (Python / Bash)", "importance": "Important",
         "why": "Automatiser les scans et intégrer dans les pipelines"},
        {"skill": "DevSecOps", "importance": "Important",
         "why": "Shift-left : intégrer la sécurité dès le développement"},
        {"skill": "Network Basics", "importance": "Important",
         "why": "Comprendre les flux applicatifs et les expositions"},
        {"skill": "Linux", "importance": "Important",
         "why": "Les apps et pipelines CI/CD tournent majoritairement sous Linux"},
        {"skill": "Threat Intelligence", "importance": "Complémentaire",
         "why": "Suivre les CVE et vulnérabilités des dépendances"},
        {"skill": "Cloud Basics", "importance": "Complémentaire",
         "why": "Les apps sont de plus en plus déployées dans le cloud"},
        {"skill": "Container Security", "importance": "Complémentaire",
         "why": "Sécuriser les images Docker et les déploiements Kubernetes"},
    ],
    "security_engineer": [
        {"skill": "Security Architecture", "importance": "Essentiel",
         "why": "Concevoir des systèmes sécurisés end-to-end"},
        {"skill": "Network Basics", "importance": "Essentiel",
         "why": "Firewall, IDS/IPS, segmentation — base de l'ingénierie sécu"},
        {"skill": "IAM (Identity and Access Management)", "importance": "Essentiel",
         "why": "Déployer et opérer les solutions d'identité (SSO, MFA, PAM)"},
        {"skill": "SIEM", "importance": "Important",
         "why": "Déployer, intégrer et maintenir la stack SIEM"},
        {"skill": "Linux", "importance": "Important",
         "why": "La majorité des composants de sécurité tournent sous Linux"},
        {"skill": "Windows Security Basics", "importance": "Important",
         "why": "Active Directory, GPO, hardening Windows"},
        {"skill": "Cloud Basics", "importance": "Important",
         "why": "Les architectures hybrides sont la norme"},
        {"skill": "Scripting (Python / Bash)", "importance": "Important",
         "why": "Automatiser les déploiements et configurations"},
        {"skill": "Vulnerability Scanning", "importance": "Complémentaire",
         "why": "Identifier et corriger les expositions de l'infrastructure"},
        {"skill": "Container Security", "importance": "Complémentaire",
         "why": "Sécuriser les déploiements conteneurisés"},
    ],
}

LEARNING_RESOURCES = {
    "Log Analysis": [
        {"name": "Splunk Training (Free)", "url": "https://www.splunk.com/en_us/training/free-courses.html",
         "type": "Cours pratique", "price": "Gratuit", "level": "Débutant"},
        {"name": "Elastic SIEM Tutorial", "url": "https://www.elastic.co/guide/en/siem/guide/current/index.html",
         "type": "Documentation", "price": "Gratuit", "level": "Intermédiaire"},
    ],
    "SIEM": [
        {"name": "Splunk Fundamentals 1", "url": "https://www.splunk.com/en_us/training/free-courses/splunk-fundamentals-1.html",
         "type": "Cours structuré", "price": "Gratuit", "level": "Débutant"},
        {"name": "Microsoft Sentinel Learning Path", "url": "https://learn.microsoft.com/en-us/azure/sentinel/",
         "type": "Cours officiel", "price": "Gratuit", "level": "Intermédiaire"},
    ],
    "Network Basics": [
        {"name": "TryHackMe — Pre-Security Path", "url": "https://tryhackme.com/path/outline/presecurity",
         "type": "Lab pratique", "price": "Freemium", "level": "Débutant"},
        {"name": "Cisco Networking Basics", "url": "https://skillsforall.com/course/networking-basics",
         "type": "Cours structuré", "price": "Gratuit", "level": "Débutant"},
    ],
    "Web Security": [
        {"name": "PortSwigger Web Security Academy", "url": "https://portswigger.net/web-security",
         "type": "Lab pratique", "price": "Gratuit", "level": "Débutant à avancé"},
        {"name": "OWASP Top 10", "url": "https://owasp.org/www-project-top-ten/",
         "type": "Documentation", "price": "Gratuit", "level": "Débutant"},
    ],
    "Linux": [
        {"name": "OverTheWire: Bandit", "url": "https://overthewire.org/wargames/bandit/",
         "type": "Wargame pratique", "price": "Gratuit", "level": "Débutant"},
        {"name": "TryHackMe — Linux Fundamentals", "url": "https://tryhackme.com/module/linux-fundamentals",
         "type": "Lab pratique", "price": "Freemium", "level": "Débutant"},
    ],
    "Incident Response": [
        {"name": "SANS Incident Response Resources", "url": "https://www.sans.org/blog/incident-response/",
         "type": "Documentation", "price": "Gratuit", "level": "Intermédiaire"},
        {"name": "NIST SP 800-61 — Computer Security Incident Handling Guide",
         "url": "https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final",
         "type": "Documentation officielle", "price": "Gratuit", "level": "Intermédiaire"},
    ],
    "Forensics": [
        {"name": "Autopsy Digital Forensics", "url": "https://www.autopsy.com/",
         "type": "Outil + documentation", "price": "Gratuit", "level": "Intermédiaire"},
        {"name": "TryHackMe — Digital Forensics", "url": "https://tryhackme.com/module/digital-forensics-and-incident-response",
         "type": "Lab pratique", "price": "Freemium", "level": "Intermédiaire"},
    ],
    "Vulnerability Scanning": [
        {"name": "Nmap Documentation", "url": "https://nmap.org/book/toc.html",
         "type": "Documentation officielle", "price": "Gratuit", "level": "Débutant"},
        {"name": "Hack The Box — Starting Point", "url": "https://www.hackthebox.com/hacker/hacking-lab",
         "type": "Lab pratique", "price": "Freemium", "level": "Débutant"},
    ],
    "Scripting (Python / Bash)": [
        {"name": "Automate the Boring Stuff with Python", "url": "https://automatetheboringstuff.com/",
         "type": "Livre en ligne", "price": "Gratuit", "level": "Débutant"},
        {"name": "TryHackMe — Python Basics", "url": "https://tryhackme.com/room/pythonbasics",
         "type": "Lab pratique", "price": "Freemium", "level": "Débutant"},
    ],
    "Cloud Basics": [
        {"name": "AWS Cloud Practitioner Essentials", "url": "https://aws.amazon.com/training/learn-about/cloud-practitioner/",
         "type": "Cours officiel", "price": "Gratuit", "level": "Débutant"},
        {"name": "Google Cloud Skills Boost (Free tier)", "url": "https://www.cloudskillsboost.google/",
         "type": "Lab pratique", "price": "Freemium", "level": "Débutant"},
    ],
    "IAM (Identity and Access Management)": [
        {"name": "Microsoft Entra ID Documentation", "url": "https://learn.microsoft.com/en-us/entra/identity/",
         "type": "Documentation officielle", "price": "Gratuit", "level": "Intermédiaire"},
        {"name": "AWS IAM Tutorials", "url": "https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorials.html",
         "type": "Tutoriels officiels", "price": "Gratuit", "level": "Intermédiaire"},
    ],
    "Threat Intelligence": [
        {"name": "MITRE ATT&CK Navigator", "url": "https://mitre-attack.github.io/attack-navigator/",
         "type": "Outil interactif", "price": "Gratuit", "level": "Intermédiaire"},
        {"name": "OpenCTI Platform", "url": "https://www.opencti.io/",
         "type": "Plateforme open source", "price": "Gratuit", "level": "Avancé"},
    ],
    "Risk Management": [
        {"name": "NIST Cybersecurity Framework", "url": "https://www.nist.gov/cyberframework",
         "type": "Référentiel officiel", "price": "Gratuit", "level": "Intermédiaire"},
        {"name": "ISO 27001 Overview (ANSSI)", "url": "https://www.ssi.gouv.fr/entreprise/bonnes-pratiques/",
         "type": "Documentation", "price": "Gratuit", "level": "Intermédiaire"},
    ],
    "Secure Coding": [
        {"name": "OWASP Secure Coding Practices", "url": "https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/",
         "type": "Guide de référence", "price": "Gratuit", "level": "Intermédiaire"},
        {"name": "SANS CWE Top 25", "url": "https://cwe.mitre.org/top25/archive/2023/2023_top25_list.html",
         "type": "Documentation", "price": "Gratuit", "level": "Intermédiaire"},
    ],
    "DevSecOps": [
        {"name": "OWASP DevSecOps Guideline", "url": "https://owasp.org/www-project-devsecops-guideline/",
         "type": "Guide officiel", "price": "Gratuit", "level": "Intermédiaire"},
        {"name": "GitHub Actions Security Hardening", "url": "https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions",
         "type": "Documentation officielle", "price": "Gratuit", "level": "Intermédiaire"},
    ],
    "Container Security": [
        {"name": "Docker Security Best Practices", "url": "https://docs.docker.com/develop/security-best-practices/",
         "type": "Documentation officielle", "price": "Gratuit", "level": "Intermédiaire"},
        {"name": "CIS Kubernetes Benchmark", "url": "https://www.cisecurity.org/benchmark/kubernetes",
         "type": "Référentiel", "price": "Gratuit", "level": "Avancé"},
    ],
    "Security Architecture": [
        {"name": "NIST Zero Trust Architecture SP 800-207", "url": "https://csrc.nist.gov/publications/detail/sp/800-207/final",
         "type": "Publication officielle", "price": "Gratuit", "level": "Avancé"},
        {"name": "SABSA Framework Overview", "url": "https://sabsa.org/sabsa-executive-summary/",
         "type": "Framework", "price": "Gratuit", "level": "Avancé"},
    ],
    "Security Monitoring": [
        {"name": "Security Onion Documentation", "url": "https://docs.securityonion.net/",
         "type": "Documentation plateforme", "price": "Gratuit", "level": "Intermédiaire"},
        {"name": "MITRE D3FEND", "url": "https://d3fend.mitre.org/",
         "type": "Référentiel défensif", "price": "Gratuit", "level": "Intermédiaire"},
    ],
    "Malware Basics": [
        {"name": "ANY.RUN Interactive Sandbox", "url": "https://any.run/",
         "type": "Sandbox en ligne", "price": "Freemium", "level": "Intermédiaire"},
        {"name": "MalwareBazaar (Abuse.ch)", "url": "https://bazaar.abuse.ch/",
         "type": "Base de données samples", "price": "Gratuit", "level": "Intermédiaire"},
    ],
    "Windows Security Basics": [
        {"name": "Microsoft Security Documentation", "url": "https://learn.microsoft.com/en-us/security/",
         "type": "Documentation officielle", "price": "Gratuit", "level": "Débutant"},
        {"name": "TryHackMe — Windows Fundamentals", "url": "https://tryhackme.com/module/windows-fundamentals",
         "type": "Lab pratique", "price": "Freemium", "level": "Débutant"},
    ],
}


# ── Outils MITRE ATT&CK (API REST réelle) ───────────────────────────────────

@function_tool
def get_mitre_techniques_for_role(role_keyword: str) -> str:
    """
    Interroge l'API MITRE ATT&CK pour récupérer les techniques réelles
    associées à un métier ou un domaine cyber.
    Source : https://attack.mitre.org/api/ (gratuit, sans clé API)
    """
    # Mapping métier → tactiques MITRE ATT&CK les plus pertinentes
    role_tactics_map = {
        "soc": ["TA0001", "TA0002", "TA0003", "TA0005", "TA0011"],
        "pentester": ["TA0001", "TA0002", "TA0003", "TA0004", "TA0006", "TA0007", "TA0008", "TA0009"],
        "threat intelligence": ["TA0001", "TA0002", "TA0040", "TA0009", "TA0011"],
        "incident": ["TA0040", "TA0010", "TA0011", "TA0005"],
        "cloud": ["TA0001", "TA0003", "TA0006", "TA0007", "TA0010"],
        "appsec": ["TA0001", "TA0002", "TA0009", "TA0040"],
        "grc": [],
        "security engineer": ["TA0001", "TA0003", "TA0005", "TA0006"],
    }

    # Trouver le mapping le plus pertinent
    matched_tactics = []
    role_lower = role_keyword.lower()
    for key, tactics in role_tactics_map.items():
        if key in role_lower:
            matched_tactics = tactics
            break
    if not matched_tactics:
        matched_tactics = ["TA0001", "TA0002", "TA0003"]

    try:
        techniques = _load_mitre_techniques()
        if not techniques:
            return json.dumps({"fallback": _get_mitre_fallback(role_keyword)}, ensure_ascii=False)

        # Mots-clés tactiques par rôle pour filtrer
        tactic_keywords = {
            "soc": ["defense-evasion", "discovery", "lateral-movement", "command-and-control", "exfiltration"],
            "pentest": ["initial-access", "execution", "privilege-escalation", "discovery", "lateral-movement"],
            "cloud": ["initial-access", "privilege-escalation", "defense-evasion", "exfiltration"],
            "incident": ["persistence", "defense-evasion", "discovery", "lateral-movement", "exfiltration"],
            "threat": ["initial-access", "execution", "persistence", "command-and-control"],
            "grc": ["initial-access", "persistence", "exfiltration"],
            "appsec": ["initial-access", "execution", "privilege-escalation"],
        }
        role_lower = role_keyword.lower()
        matched_kw = []
        for key, kws in tactic_keywords.items():
            if key in role_lower:
                matched_kw = kws
                break
        if not matched_kw:
            matched_kw = ["initial-access", "execution", "discovery"]

        relevant = []
        for tech in techniques:
            kill_chain = tech.get("kill_chain_phases", [])
            tech_phases = [p.get("phase_name", "") for p in kill_chain]
            if any(kw in tech_phases for kw in matched_kw):
                ext_refs = tech.get("external_references", [])
                tech_id = next((r.get("external_id", "") for r in ext_refs if r.get("source_name") == "mitre-attack"), "")
                tech_url = next((r.get("url", "") for r in ext_refs if r.get("source_name") == "mitre-attack"), "")
                desc = tech.get("description", "")
                relevant.append({
                    "id": tech_id,
                    "name": tech.get("name", ""),
                    "description_short": desc[:200] if desc else "",
                    "tactics": tech_phases,
                    "url": tech_url,
                })

        relevant = relevant[:10]
        return json.dumps({
            "source": "MITRE ATT&CK Enterprise Matrix (données réelles live)",
            "role_queried": role_keyword,
            "techniques_count": len(relevant),
            "techniques": relevant,
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Erreur MITRE : {str(e)}",
                           "fallback": _get_mitre_fallback(role_keyword)}, ensure_ascii=False)


@function_tool
def get_mitre_groups_and_software(search_term: str) -> str:
    """
    Récupère les groupes d'attaquants (APT) et logiciels malveillants réels
    depuis la base MITRE ATT&CK. Utile pour le Threat Intelligence.
    Source : https://attack.mitre.org/api/ (gratuit, sans clé API)
    """
    try:
        data = _load_mitre_raw()
        if not data:
            return json.dumps({"error": "Données MITRE non disponibles"}, ensure_ascii=False)

        objects = data.get("objects", [])
        search_lower = search_term.lower()
        results = {"source": "MITRE ATT&CK Enterprise Matrix (données réelles live)", "groups": [], "software": []}

        for obj in objects:
            if obj.get("type") == "intrusion-set":
                name = obj.get("name", "").lower()
                desc = (obj.get("description", "") or "").lower()
                aliases = [a.lower() for a in obj.get("aliases", [])]
                if search_lower in name or search_lower in desc or any(search_lower in a for a in aliases) or search_lower in ["apt", "all", "threat", "groupe"]:
                    ext_refs = obj.get("external_references", [])
                    group_id = next((r.get("external_id", "") for r in ext_refs if r.get("source_name") == "mitre-attack"), "")
                    group_url = next((r.get("url", "") for r in ext_refs if r.get("source_name") == "mitre-attack"), "")
                    results["groups"].append({
                        "name": obj.get("name", ""),
                        "id": group_id,
                        "aliases": obj.get("aliases", [])[:3],
                        "description": obj.get("description", "")[:250] if obj.get("description") else "",
                        "url": group_url,
                    })

        results["groups"] = results["groups"][:8]
        return json.dumps(results, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Erreur MITRE groupes : {str(e)}"}, ensure_ascii=False)


@function_tool
def get_mitre_cve_context(cve_id: str) -> str:
    """
    Recherche le contexte MITRE d'un CVE ou d'une vulnérabilité connue.
    Requête vers l'API NVD (NIST National Vulnerability Database) - gratuit.
    Source : https://nvd.nist.gov/developers/vulnerabilities (gratuit, 5 req/30s sans clé)
    """
    try:
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {"cveId": cve_id.upper()} if cve_id.upper().startswith("CVE-") else {"keywordSearch": cve_id}
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

        if response.status_code != 200:
            return json.dumps({"error": f"API NVD non disponible (HTTP {response.status_code})"})

        data = response.json()
        vulns = data.get("vulnerabilities", [])

        if not vulns:
            return json.dumps({"message": f"Aucun CVE trouvé pour '{cve_id}'"})

        results = []
        for v in vulns[:3]:
            cve = v.get("cve", {})
            descriptions = cve.get("descriptions", [])
            desc_en = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")
            metrics = cve.get("metrics", {})
            cvss_data = (metrics.get("cvssMetricV31", [{}]) or
                         metrics.get("cvssMetricV30", [{}]) or
                         metrics.get("cvssMetricV2", [{}]))
            score = cvss_data[0].get("cvssData", {}).get("baseScore", "N/A") if cvss_data else "N/A"

            results.append({
                "id": cve.get("id", ""),
                "description": desc_en[:300],
                "cvss_score": score,
                "severity": cvss_data[0].get("cvssData", {}).get("baseSeverity", "N/A") if cvss_data else "N/A",
                "url": f"https://nvd.nist.gov/vuln/detail/{cve.get('id', '')}",
                "source": "NIST NVD (données réelles)",
            })

        return json.dumps({"cves": results}, ensure_ascii=False)

    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "Impossible de contacter l'API NVD (vérifier la connexion internet)"})
    except Exception as e:
        return json.dumps({"error": f"Erreur API NVD : {str(e)}"})


# ── Outils données structurées NICE Framework ────────────────────────────────

@function_tool
def get_role_details(role_name: str) -> str:
    """
    Retourne les détails complets d'un métier cyber basés sur le NIST NICE Framework.
    Données : NIST SP 800-181 Rev 1 (standard public officiel).
    """
    role_lower = role_name.lower().replace(" ", "_").replace("-", "_")

    # Matching flexible des noms de rôles
    role_key = None
    for key in NICE_ROLES:
        if key in role_lower or role_lower in key:
            role_key = key
            break
    if not role_key:
        mappings = {
            "soc": "soc_analyst", "analyste": "soc_analyst",
            "pentest": "pentester", "offensif": "pentester",
            "cloud": "cloud_security_engineer",
            "incident": "incident_responder", "dfir": "incident_responder",
            "threat": "threat_intelligence_analyst", "intel": "threat_intelligence_analyst",
            "grc": "grc_analyst", "conformité": "grc_analyst", "risque": "grc_analyst",
            "appsec": "appsec_engineer", "application": "appsec_engineer",
            "développeur": "appsec_engineer", "dev": "appsec_engineer",
            "security engineer": "security_engineer", "ingénieur": "security_engineer",
        }
        for keyword, mapped_key in mappings.items():
            if keyword in role_lower:
                role_key = mapped_key
                break

    if not role_key:
        available = list(NICE_ROLES.keys())
        return json.dumps({"error": f"Rôle '{role_name}' non trouvé",
                           "available_roles": available}, ensure_ascii=False)

    role_data = NICE_ROLES[role_key]
    return json.dumps({
        "role_id": role_key,
        "nice_id": role_data["nice_id"],
        "title": role_data["title"],
        "category": role_data["category"],
        "posture": role_data["posture"],
        "level": role_data["level"],
        "daily_missions": role_data["daily_missions"],
        "entry_profile": role_data["entry_profile"],
        "salary_range_fr": role_data["salary_range_fr"],
        "market_demand": role_data["demand"],
        "source": "NIST NICE Framework SP 800-181 Rev 1",
    }, ensure_ascii=False)


@function_tool
def get_skills_for_role(role_name: str) -> str:
    """
    Retourne les compétences techniques nécessaires pour un métier cyber,
    classées par niveau d'importance (Essentiel / Important / Complémentaire).
    Basé sur le NIST NICE Framework et les standards industrie.
    """
    role_lower = role_name.lower().replace(" ", "_").replace("-", "_")

    role_key = None
    mappings = {
        "soc": "soc_analyst", "analyste soc": "soc_analyst",
        "pentest": "pentester",
        "cloud": "cloud_security_engineer",
        "incident": "incident_responder", "dfir": "incident_responder",
        "threat": "threat_intelligence_analyst", "intel": "threat_intelligence_analyst",
        "grc": "grc_analyst", "conformité": "grc_analyst",
        "appsec": "appsec_engineer", "application": "appsec_engineer",
        "dev": "appsec_engineer", "développeur": "appsec_engineer",
        "security engineer": "security_engineer", "ingénieur sécurité": "security_engineer",
    }
    for key in list(SKILLS_BY_ROLE.keys()) + list(mappings.keys()):
        clean_key = mappings.get(key, key)
        if clean_key in SKILLS_BY_ROLE and (key in role_lower or role_lower in key):
            role_key = clean_key
            break

    if not role_key:
        for key in SKILLS_BY_ROLE:
            if key in role_lower or role_lower in key:
                role_key = key
                break

    if not role_key:
        return json.dumps({"error": f"Rôle '{role_name}' non trouvé",
                           "available_roles": list(SKILLS_BY_ROLE.keys())}, ensure_ascii=False)

    skills = SKILLS_BY_ROLE[role_key]
    essential = [s for s in skills if s["importance"] == "Essentiel"]
    important = [s for s in skills if s["importance"] == "Important"]
    complementary = [s for s in skills if s["importance"] == "Complémentaire"]

    return json.dumps({
        "role": role_name,
        "total_skills": len(skills),
        "essential": essential,
        "important": important,
        "complementary": complementary,
        "source": "NIST NICE Framework + standards industrie",
    }, ensure_ascii=False)


@function_tool
def get_learning_resources(skill_name: str, budget: str = "gratuit") -> str:
    """
    Retourne des ressources d'apprentissage réelles pour une compétence cyber.
    Toutes les ressources sont gratuites ou freemium — sources officielles vérifiées.
    """
    # Matching flexible
    resource_key = None
    skill_lower = skill_name.lower()
    for key in LEARNING_RESOURCES:
        if key.lower() in skill_lower or skill_lower in key.lower():
            resource_key = key
            break

    if not resource_key:
        # Retourner les ressources générales TryHackMe / HTB
        return json.dumps({
            "skill": skill_name,
            "resources": [
                {"name": "TryHackMe — Plateforme complète", "url": "https://tryhackme.com",
                 "type": "Plateforme d'apprentissage", "price": "Freemium"},
                {"name": "Hack The Box Academy", "url": "https://academy.hackthebox.com",
                 "type": "Plateforme pratique", "price": "Freemium"},
                {"name": "ANSSI — Guide des bonnes pratiques", "url": "https://www.ssi.gouv.fr/uploads/2017/01/guide_bonnes_pratiques_hygiene_informatique_anssi.pdf",
                 "type": "Guide officiel", "price": "Gratuit"},
            ],
            "note": "Ressources générales — compétence non trouvée dans la base",
        }, ensure_ascii=False)

    resources = LEARNING_RESOURCES[resource_key]
    if budget.lower() in ["gratuit", "free", "0"] :
        resources = [r for r in resources if r["price"] in ["Gratuit", "Freemium"]]

    return json.dumps({
        "skill": skill_name,
        "resources": resources,
        "source": "Ressources officielles et plateformes validées",
    }, ensure_ascii=False)


@function_tool
def compare_roles(role1: str, role2: str) -> str:
    """
    Compare deux métiers cyber côte à côte : posture, niveau, missions, salaires.
    Utile pour aider l'utilisateur à choisir entre deux orientations.
    """
    r1 = json.loads(get_role_details(role1))
    r2 = json.loads(get_role_details(role2))

    if "error" in r1 or "error" in r2:
        return json.dumps({"error": "Un des deux rôles n'a pas été trouvé",
                           "detail": {"role1": r1, "role2": r2}}, ensure_ascii=False)

    return json.dumps({
        "comparison": {
            "role1": {"name": r1["title"], "posture": r1["posture"],
                      "level": r1["level"], "salary": r1["salary_range_fr"],
                      "demand": r1["market_demand"],
                      "top_missions": r1["daily_missions"][:3]},
            "role2": {"name": r2["title"], "posture": r2["posture"],
                      "level": r2["level"], "salary": r2["salary_range_fr"],
                      "demand": r2["market_demand"],
                      "top_missions": r2["daily_missions"][:3]},
        },
        "source": "NIST NICE Framework SP 800-181 Rev 1",
    }, ensure_ascii=False)


@function_tool
def get_all_roles_overview() -> str:
    """
    Retourne une vue d'ensemble de tous les métiers cyber disponibles
    avec leur posture et niveau. Utile pour le matching initial.
    """
    overview = []
    for key, role in NICE_ROLES.items():
        overview.append({
            "role_id": key,
            "title": role["title"],
            "posture": role["posture"],
            "level": role["level"],
            "demand": role["demand"],
            "nice_id": role["nice_id"],
        })
    return json.dumps({
        "roles": overview,
        "total": len(overview),
        "source": "NIST NICE Framework SP 800-181 Rev 1",
    }, ensure_ascii=False)



@function_tool
def get_mitre_latest_techniques(limit: int = 10) -> str:
    """
    Récupère les techniques MITRE ATT&CK les plus récentes depuis l'API officielle.
    Utile pour répondre aux questions générales sur MITRE ATT&CK et ses mises à jour.
    Source : https://attack.mitre.org/api/ (gratuit, sans clé)
    """
    try:
        techniques = _load_mitre_techniques()
        if not techniques:
            return json.dumps({"error": "Données MITRE non disponibles",
                               "reference": "https://attack.mitre.org/resources/updates/"}, ensure_ascii=False)

        # Trier par date de modification
        dated = []
        for t in techniques:
            modified = t.get("modified", "") or t.get("created", "")
            dated.append((modified, t))
        dated.sort(key=lambda x: x[0], reverse=True)

        recent = []
        for _, t in dated[:limit]:
            ext_refs = t.get("external_references", [])
            tech_id = next((r.get("external_id", "") for r in ext_refs if r.get("source_name") == "mitre-attack"), "")
            tech_url = next((r.get("url", "") for r in ext_refs if r.get("source_name") == "mitre-attack"), "")
            phases = [p.get("phase_name", "") for p in t.get("kill_chain_phases", [])]
            desc = t.get("description", "")
            recent.append({
                "id": tech_id,
                "name": t.get("name", ""),
                "modified": t.get("modified", "")[:10] if t.get("modified") else "",
                "created": t.get("created", "")[:10] if t.get("created") else "",
                "tactics": phases,
                "description": desc[:200] if desc else "",
                "url": tech_url,
            })

        return json.dumps({
            "source": "MITRE ATT&CK Enterprise Matrix (données réelles live — GitHub mitre/cti)",
            "total_techniques_in_matrix": len(techniques),
            "most_recent_techniques": recent,
            "reference": "https://attack.mitre.org/resources/updates/",
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Erreur : {str(e)}"}, ensure_ascii=False)

# ── Helpers internes ─────────────────────────────────────────────────────────

def _load_mitre_raw() -> dict:
    """
    Charge le fichier STIX MITRE ATT&CK.
    Priorité : cache mémoire → cache disque → téléchargement GitHub.
    Le cache disque évite de re-télécharger 45 Mo à chaque session.
    """
    global _mitre_cache
    import os, time

    # 1. Cache mémoire (même processus)
    if _mitre_cache is not None:
        return _mitre_cache

    # 2. Cache disque (fichier local, valide 7 jours)
    if os.path.exists(MITRE_CACHE_FILE):
        age_days = (time.time() - os.path.getmtime(MITRE_CACHE_FILE)) / 86400
        if age_days < 7:
            try:
                with open(MITRE_CACHE_FILE, "r", encoding="utf-8") as f:
                    _mitre_cache = json.load(f)
                    return _mitre_cache
            except Exception:
                pass

    # 3. Téléchargement depuis GitHub
    try:
        response = requests.get(MITRE_CTI_URL, timeout=90)
        if response.status_code == 200:
            _mitre_cache = response.json()
            # Sauvegarder sur disque pour les prochains appels
            try:
                with open(MITRE_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(_mitre_cache, f)
            except Exception:
                pass
            return _mitre_cache
    except Exception:
        pass
    return {}


def _load_mitre_techniques() -> list:
    """Retourne uniquement les objets de type attack-pattern (techniques)."""
    data = _load_mitre_raw()
    if not data:
        return []
    return [
        obj for obj in data.get("objects", [])
        if obj.get("type") == "attack-pattern"
        and not obj.get("x_mitre_deprecated", False)
        and not obj.get("revoked", False)
    ]


def _get_mitre_fallback(role_keyword: str) -> dict:
    """Données de secours si l'API MITRE est indisponible."""
    fallbacks = {
        "soc": {
            "key_techniques": ["T1078 Valid Accounts", "T1059 Command and Scripting Interpreter",
                                "T1566 Phishing", "T1055 Process Injection"],
            "key_tactics": ["Initial Access", "Execution", "Defense Evasion", "Command and Control"],
            "reference": "https://attack.mitre.org/matrices/enterprise/",
        },
        "pentest": {
            "key_techniques": ["T1190 Exploit Public-Facing Application", "T1059 Command and Scripting Interpreter",
                                "T1548 Abuse Elevation Control Mechanism", "T1083 File and Directory Discovery"],
            "key_tactics": ["Initial Access", "Execution", "Privilege Escalation", "Discovery"],
            "reference": "https://attack.mitre.org/matrices/enterprise/",
        },
    }
    for key, data in fallbacks.items():
        if key in role_keyword.lower():
            return data
    return {
        "key_techniques": ["T1078 Valid Accounts", "T1566 Phishing", "T1486 Data Encrypted for Impact"],
        "key_tactics": ["Initial Access", "Execution", "Impact"],
        "reference": "https://attack.mitre.org/",
        "note": "Données statiques de secours — API MITRE indisponible",
    }
