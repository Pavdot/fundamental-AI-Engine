# AGENTS.md — Fundamental AI Engine

## Mission et priorité
Construire et livrer rapidement un moteur d'intelligence fondamentale financière en Python, à partir du dépôt **réel**, sans réécriture injustifiée. L'utilisateur délègue l'implémentation à Codex et apprend en relisant les changements. Privilégier **ship-first**, tout en assurant les garanties minimales de fiabilité et de sécurité.

## Démarrage obligatoire de chaque mission
1. Examiner l'arborescence, le `README`, les dépendances, le Git status et les fichiers Python existants. Le brief séparé `PROJECT_BRIEF.md` décrit l'intention, pas nécessairement l'état réel du code.
2. Exécuter les tests existants et constater l'état avant modification. Identifier les composants déjà fonctionnels ; ne pas les dupliquer.
3. Présenter un plan court, **avec fichiers touchés et critères de validation**. Pour une tâche limitée, passer directement à l'implémentation.
4. Faire des changements petits, cohérents et testables. Ne pas refactoriser hors périmètre.
5. Exécuter les tests et un contrôle manuel représentatif ; rapporter les résultats et limites honnêtement.
6. À la fin de chaque mission, fournir : fonctionnalités livrées, fichiers modifiés, commandes de test, résultats, risques restants et prochaine tâche la plus utile.

## Contraintes fonctionnelles
- Sources actuelles : actualités Finnhub, analyse LLM via API compatible OpenAI/OpenRouter.
- Sortie structurée existante : `asset`, `direction` [-1,1], `importance` [0,1], `confidence` [0,1], `horizon_hours` entier > 0.
- Ne jamais présenter `confidence` du LLM comme une probabilité calibrée de rendement financier.
- Éviter de réanalyser et de réalerter les articles déjà traités ; différencier les états « découvert », « analysé », « échec », « alerte envoyée » si nécessaire.
- Un article ne doit être marqué « traité » qu'après une analyse réellement validée et enregistrée. En cas d'échec, permettre la reprise.
- Conserver le lien entre article d'origine, version du modèle/prompt, analyse, horodatages et éventuellement résultat de marché pour le futur ML.
- MVP : alertes/signaux, **aucun passage d'ordre**, aucune gestion d'exécution de trades.
- Ne pas entraîner de modèle ML avant d'avoir un dataset historique exploitable et une définition stricte des labels/horodatages.

## Hygiène du code
- Ne pas utiliser `from module import *` ; imports explicites.
- Ne pas lancer de requêtes externes lors d'un import de module ; fonctions appelées depuis un point d'entrée clair.
- Ne pas exécuter de requête SQL, d'appel HTTP, d'appel LLM ou de tâche planifiée au chargement d'un module sans justification.
- Ne pas introduire une classe, un framework, ou plusieurs couches d'abstraction lorsque des fonctions simples suffisent.
- Employer des requêtes SQL paramétrées. Prévoir `commit`/`rollback`, fermeture sûre des connexions et gestion des erreurs.
- Préférer les tests sans réseau avec mocks, ajouter des tests d'intégration ciblés avec SQLite temporaire.
- Utiliser `pytest` si déjà installé ; conserver et faire passer les tests existants.
- Gérer les erreurs HTTP, délais, réponse API inattendue (dict d'erreur au lieu d'une liste), JSON invalide, champs manquants, échecs Pydantic et erreurs réseau.
- Mettre les clés dans les variables d'environnement. Ne jamais afficher, enregistrer dans Git, inclure dans les logs, les réponses ou des fixtures les valeurs des secrets (`.env`, tokens).
- Si le dépôt utilise un environnement virtuel `.venv`, l'utiliser ; documenter toute nouvelle dépendance.

## Priorités du produit
**P0 :** audit du code + tests, SQLite correct, analyses persistées, reprise sur erreur, pipeline Finnhub → filtre → LLM → BDD.
**P1 :** sélection pertinente d'actualités, Telegram, exécution périodique, logs et gestion des secrets.
**P2 :** PostgreSQL, FastAPI, Docker, CI, tests d'intégration et monitoring.
**P3 :** RAG/outils/agents si utiles, évaluation LLM, historique prix, datasets ML, modèles supervisés, backtesting walk-forward, MLOps.
Ces priorités ne sont pas une invitation à tout implémenter en une tâche. Avancer verticalement vers une fonctionnalité démontrable.

## Collaboration avec l'utilisateur
- Réponses en français, concises et factuelles.
- L'utilisateur veut revoir le code et apprendre *sur le tas*. Dans le compte rendu, expliquer brièvement le chemin des données et le rôle des modifications nouvelles, sans cours magistral.
- Lorsqu'un point est incertain, inspecter le dépôt plutôt qu'inventer des noms de fichiers, fonctions ou interfaces.
- Ne pas prétendre qu'une fonctionnalité est terminée sans preuve d'exécution et tests pertinents.
- Si une décision impacte le périmètre, les coûts API ou le risque financier, la signaler avant de la prendre.
