# Fundamental AI Engine — cahier des charges pour Codex

**Nature :** projet Python FinTech d'intelligence fondamentale, d'abord prototype exploitable, puis API et moteur ML.  
**Stratégie :** Codex réalise la majorité de l'implémentation ; l'utilisateur vérifie, comprend et arbitre.  
**Contrainte de temps :** cible ambitieuse de **8 semaines** pour une démonstration de bout en bout, pas pour une maîtrise exhaustive de tous les domaines ni une garantie de rentabilité financière.  
**Source de vérité sur l'implémentation :** **le dépôt ouvert dans Codex**. Les extraits ci-dessous reflètent le dernier état discuté, mais peuvent avoir changé.

## 1. Vision produit et périmètre

Le moteur doit collecter des informations financières, éviter les doublons, analyser les événements avec un LLM, valider et historiser les sorties, puis fournir des alertes et une API. Un second volet exploitera l'historique (événements + marché) pour entraîner un modèle ML spécialisé sur l'effet des événements sur les prix.

### Actifs cibles et cas d'usage
- Actifs visés initialement : **BTCUSDT** et **XAUUSD**, mais les résultats doivent pouvoir porter explicitement sur plusieurs actifs ou sur `unknown` si le lien n'est pas justifié.
- Types d'entrées : nouvelles financières, annonces macroéconomiques, événements d'entreprise ou de marché ; sources à ajouter seulement si leur valeur est claire.
- Sorties : événements normalisés, analyses structurées, score ou signal indicatif, horizon, informations de provenance ; alertes Telegram pertinentes.
- **Hors périmètre MVP : trading automatique, clôture de position, promesse de rendement, système de haute fréquence.**
- Distinguer impérativement l'heure de publication, l'heure d'observation/collecte et l'heure de l'analyse pour éviter toute fuite future dans le ML.

## 2. État du code déjà vu pendant les séances

Les chemins exacts sont à vérifier dans le dépôt. Environnement local signalé : Windows, VS Code, `.venv`, répertoire `D:\desktop\fundamental-AI-Engine`.

### `main.py`
- Utilise `python-dotenv` avec `load_dotenv()` et `os.getenv("OPENROUTER_API_KEY")`.
- Client `OpenAI(base_url="https://openrouter.ai/api/v1", api_key=...)`.
- Modèle initial : `openrouter/free` (peut ne pas avoir de comportement stable ; configurer le modèle et ne pas le figer dans la logique métier).
- Fonction `call_llm(prompt)` qui effectue l'appel OpenRouter et renvoie le contenu texte.
- Fonction `analyze_news(news)` qui construit un prompt, appelle le LLM jusqu'à 3 fois, parse avec `json.loads`, puis valide avec Pydantic.
- Classe Pydantic `NewsAnalysis` avec champs :
  - `asset: str`
  - `direction: float` avec bornes -1 à 1
  - `importance: float` avec bornes 0 à 1
  - `confidence: float` avec bornes 0 à 1
  - `horizon_hours: int` strictement positif
- `NewsAnalysis.model_validate(data)` a été introduit à la place de `NewsAnalysis(**data)` pour transformer une sortie JSON de type `list` en `ValidationError` gérable.
- Dernière orchestration discutée : récupérer les actualités, sélectionner des articles, appeler l'analyse sur `article["headline"]`. **Vérifier le code réel ; le pipeline intégré n'a pas été certifié comme opérationnel de bout en bout.**
- Attention aux effets de bord à l'import : Finnhub ou LLM ne doivent pas être appelés au niveau module.

### `news_api.py`
- Fonction `fetch_news()` avec `requests.get("https://finnhub.io/api/v1/news", params={"category":"general", "token":os.getenv("FINNHUB_API_KEY")}, timeout=15)`.
- `load_dotenv()` nécessaire avant la lecture de la variable si l'environnement ne la fournit pas directement.
- Retour `response.json()` ; un test utilisateur a bien reçu une liste de dictionnaires d'actualités.
- Clés observées dans les articles : `id`, `headline`, `summary`, `source`, `category`, `datetime`, `related`, `url`, `image`.
- L'endpoint « general » fournit des actualités pas toujours pertinentes pour BTCUSDT/XAUUSD. Implémenter filtrage robuste et respect de la fraîcheur des news avant de dépenser des appels LLM.
- Contrôler `response.raise_for_status()` et le schéma JSON ; les erreurs API peuvent être des dictionnaires plutôt que des listes.

### `processor.py`
Classe en mémoire (dernière version connue) :

```python
class NewsProcessor:
    def __init__(self):
        self.seen_ids = set()

    def add_news(self, news_id):
        if news_id in self.seen_ids:
            return False
        self.seen_ids.add(news_id)
        return True

    def has_seen(self, news_id):
        return news_id in self.seen_ids
```

Cette déduplication ne survit pas au redémarrage. **Ne pas utiliser uniquement ce `set` comme preuve de traitement durable.** Si la classe doit être conservée, clarifier le rôle de cache en RAM vs BDD.

### `database.py` (travail en cours)
- `sqlite3.connect("news.db")`.
- Table de test : `CREATE TABLE IF NOT EXISTS processed_news (id INTEGER PRIMARY KEY)` ; une version utilisateur contenait une faute `INTERGER`, vérifier la structure déjà créée.
- Les tests d'insertion utilisaient `INSERT OR IGNORE INTO processed_news (id) VALUES (?)`, suivis de `commit()`.
- `cursor.rowcount` vaut 1 pour insertion et 0 pour ID ignoré.
- L'utilisateur a déjà rencontré une erreur en utilisant un curseur sur une connexion fermée.
- Le fichier a connu des imports `from main import *`, `from processor import *` et des appels HTTP au niveau global : **à nettoyer après audit**, sans casser la suite.
- Au dernier point, les fonctions `is_processed(news_id)` et `mark_processed(news_id)` **étaient planifiées, non confirmées comme réalisées**.

### Tests
- `test_processor.py` : tests de doublons et de séparation entre deux instances `NewsProcessor`.
- `test_analysis.py` : tests avec `pytest`, `Mock` et `monkeypatch` pour trois tentatives invalides et une tentative invalide suivie d'une valide.
- Les tests ont été signalés comme fonctionnels précédemment. Les relancer, inspecter leurs assertions, corriger sans effacer les exigences existantes.

## 3. Architecture cible (logique, non pas structure imposée de fichiers)

```text
Finnhub / nouvelles sources
          |
          v
 Validation HTTP + normalisation des articles
          |
          v
 Filtre d'actifs + pertinence + fraîcheur
          |
          v
 SQLite (puis PostgreSQL) : état et déduplication persistants
          |
          v
 Analyse LLM structurée + validation Pydantic
          |
          v
 Transaction BDD : article + analyse + métadonnées + état
          |
          +---> Règles de signal / seuils de qualité ---> Telegram
          |
          +---> API REST FastAPI / interrogation historique
          |
          +---> Dataset historique enrichi de prix ---> ML/backtesting
```

Ne pas multiplier les modules, classes ni dépendances sans gain fonctionnel concret.

### Flux attendu pour un article
1. Obtenir la liste via Finnhub ; gérer les exceptions et le schéma d'entrée.
2. Vérifier fraîcheur/pertinence, et si l'article est déjà traité dans **la BDD**.
3. Si nouveau et pertinent, produire une analyse LLM.
4. Valider la réponse selon un schéma explicite et exploitable ; retry uniquement pour les erreurs transitoires/réparables, journaliser autrement.
5. Enregistrer dans une transaction article, analyse, versions, timestamps et état. En cas d'échec, ne pas mettre `processed=true` ; conserver une possibilité de réessai.
6. Évaluer les règles d'alerte, envoyer une notification si nécessaire et conserver l'état d'envoi pour éviter les doublons.
7. Exposer les résultats avec FastAPI lorsque la base est fiable.

### Modèle de données proposé (à adapter après inspection)
- `articles`: `source`, `source_article_id`, `headline`, `summary`, `url`, `published_at_utc`, `fetched_at_utc`, état de traitement ; unicité de `(source, source_article_id)`.
- `analyses`: `id`, FK article, `model_id`, `prompt_version`, `analyzed_at_utc`, `asset`, `direction`, `importance`, `confidence`, `horizon_hours`, `raw_response` si utile et sécurisé, `status`, `error` ; historiser les versions quand cela sert l'évaluation.
- `alerts`: FK analyse, canal, tentative, statut, `sent_at_utc`, clé d'idempotence.
- `market_prices` (phase ML): `asset`, `timestamp_utc`, `open`, `high`, `low`, `close`, `volume`, `source`, granularité et contrôles de cohérence.
- Ne pas enregistrer de secrets ni de données personnelles non nécessaires.

## 4. Exigences de fiabilité MVP

### Déduplication et gestion des échecs
- Conserver l'identité d'une actualité indépendamment des redémarrages.
- `INSERT OR IGNORE` seul n'est pas suffisant pour décider du statut « analysé » si l'insertion précède le traitement. Éviter de confondre *article connu* et *article analysé avec succès*.
- Protéger les écritures contre double traitement si plusieurs workers tournent un jour en parallèle, sans surconstruire un système distribué au MVP.
- Réessayer les erreurs de réseau et les réponses JSON invalides avec bornes et logs ; ne pas provoquer des boucles infinies ni des coûts API excessifs.

### Qualité LLM
- Prompt donnant un schéma strict ; parser et valider toujours côté Python.
- Déterminer ce qu'il faut faire quand une actualité ne concerne pas les actifs cibles : ignorer/indiquer non pertinent plutôt que forcer un score.
- `confidence` du LLM = valeur subjective fournie par le modèle, **pas** probabilité prédictive calibrée.
- Ne pas prétendre qu'un score finance est un edge : mesurer la réalité sur des données historiques hors échantillon.
- Ajouter progressivement un petit dataset d'évaluation annoté, reproductible, avec cas limites.

### Sécurité / opérations
- Configuration en `.env` / variables d'environnement. Ne pas committer les tokens ; vérifier `.gitignore`.
- `timeout`, erreurs HTTP, limites de taux, journaux exploitables sans fuite de secrets.
- Tests unitaires et d'intégration sans appels payants/réseau par défaut.
- `Docker` et CI seulement après une chaîne locale stable.
- Aucune automatisation d'ordres financiers dans le MVP.

## 5. Feuille de route de livraison en 8 semaines (cible, adaptable)

**S1 — Pipeline + SQLite :** audit du repo, finalisation de l'orchestration, BDD robuste, modèle de données minimal, déduplication persistante, sauvegarde des analyses, tests.

**S2 — Data Engineering :** SQL/PostgreSQL, ingestion structurée, qualité des données, horodatages et premiers prix historiques ; privilégier besoin réel plutôt qu'ETL générique.

**S3 — AI Engineering :** tool calling, RAG/embeddings uniquement sur un cas utile (recherche de contexte historique), évaluation systématique LLM.

**S4 — Agents + API :** décision explicite sur la nécessité d'un agent/LangGraph, FastAPI, endpoints de consultation et documentation.

**S5 — Production :** Telegram, scheduling, Docker, VPS/cloud si disponible, CI, logs et supervision.

**S6 — ML :** dataset articles/événements/prix, labels, baselines avec scikit-learn, première évaluation chronologique.

**S7 — Quant ML :** backtests walk-forward, biais et frais, calibration, robustesse et comparaison aux baselines ; réutiliser les recherches quant antérieures si accessibles dans le dépôt, ne pas les supposer présentes.

**S8 — Démo :** connecter les prédictions ML à l'API ou aux alertes si les métriques le justifient ; tests end-to-end, documentation, cas de démonstration et état honnête du produit.

**Arbitrage temps :** si nécessaire, réduire la complexité de RAG/agents/ML avancé plutôt que livrer un pipeline non fiable. Livrer un **MVP visible en 1–2 semaines** est plus important que cocher toutes les technologies.

## 6. Première mission à donner à Codex (exécutable immédiatement)

> Ouvre le dépôt présent dans ton workspace. **Commence par un audit sans modification** : arborescence, fichier de dépendances, git status, classes/fonctions existantes, appels réseau à l'import, tests et fonctionnement de `database.py`. Compare l'état réel avec `PROJECT_BRIEF.md` et liste les écarts. Ne présume pas que les fonctionnalités décrites sont déjà codées. Ensuite, propose un plan de modifications minimal pour livrer une chaîne **Finnhub → analyse LLM Pydantic → SQLite (articles + analyses, sans doublons, reprise après échec)**. Indique les fichiers à toucher, les tests à ajouter et les critères d'acceptation. **Attends ma validation du plan avant de modifier les fichiers.** Ne lis pas ni n'affiche le contenu des clés de `.env`.

### Critères d'acceptation de la première livraison
- Lancement manuel du pipeline depuis un point d'entrée explicite.
- Aucune requête HTTP ou LLM déclenchée par le simple import d'un module.
- Un article nouveau et pertinent peut être analysé et persisté avec son ID et ses métadonnées.
- Un article déjà analysé n'est pas envoyé de nouveau au LLM à chaque exécution.
- Une erreur LLM n'enregistre pas faussement l'article comme analysé ; une reprise est possible.
- Une même actualité n'entraîne pas de duplication dans la base après deux exécutions.
- Tests existants toujours verts et nouveaux tests SQLite sans réseau.
- Instructions de démarrage et dépendances documentées.

## 7. Formation et revue de code

Codex implémente mais doit rendre des changements relisibles : fournir un bref schéma du chemin de données, expliquer les nouveaux concepts techniques **au moment où ils sont utilisés** (transactions, idempotence, cursors, tests), et limiter les grosses modifications non justifiées. L'utilisateur relit le diff, exécute les tests, puis approuve le jalon.

## 8. Incertitudes à clarifier par lecture du dépôt

- Version réellement installée de Python et des dépendances.
- Structure de `database.py` / de la table `processed_news` (notamment ancienne faute `INTERGER`).
- API de `NewsProcessor` réellement utilisée par `main.py`.
- Validation existante du pipeline de bout en bout ; qualité des réponses du modèle OpenRouter choisi.
- Dépendances, fichier `.gitignore`, état Git et scripts de lancement.
- Quelles sources de prix existent réellement ; ne pas inventer d'intégration Binance ou d'autre source.
- Capacité d'accès externe du runtime Codex et budget API ; tests par défaut hors réseau.
