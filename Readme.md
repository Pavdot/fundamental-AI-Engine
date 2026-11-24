# Fundamental AI Engine

Collecte d’actualités Finnhub, analyse OpenRouter par actif, validation Pydantic
et historique SQLite. Filtre initial par mots-clés pour BTCUSDT et XAUUSD.
Une actualité macroéconomique peut être analysée pour les deux actifs. Le
modèle peut renvoyer `unknown` si le lien avec un actif est insuffisant.

## Installation et lancement

Avec Python 3.10 ou plus récent, dans un environnement virtuel actif.

```sh
python -m pip install -r requirements.txt
python main.py
```

Configurer `FINNHUB_API_KEY` et `OPENROUTER_API_KEY` dans les variables
d’environnement ou dans un fichier local `.env`. `OPENROUTER_MODEL` permet
de changer le modèle demandé (par défaut `openrouter/free`).

Par défaut, le moteur examine les actualités des dernières 24 heures et
lance au plus cinq analyses article-actif par passage. Les options
`--max-age-hours`, `--limit` et `--db` permettent d’adapter le lancement.
Le résultat validé et l’article sont enregistrés ensemble. Un échec
d’analyse peut être retenté tant que Finnhub retourne encore l’article et
qu’il reste dans la fenêtre de fraîcheur. La table historique
`processed_news` reste consultable dans la base d’origine.

## Alertes et exécution périodique

Configurer `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID`, puis lancer le mode
voulu, par exemple toutes les 15 minutes.

```sh
python main.py --telegram --interval-minutes 15
```

Les analyses produites avec `--telegram` génèrent une alerte lorsque la
direction est non nulle, l’importance et la confiance atteignent 0,70 et
l’actif est reconnu. La confiance est une appréciation du modèle.
Une alerte confirmée est marquée `sent` et ignorée aux passages suivants.
Un refus explicite de Telegram est retenté au passage suivant. Après un
délai réseau ou une interruption de processus, vérifier les alertes
`uncertain` ou `sending` dans le chat avant toute remise en `pending`.
Cette vérification évite de renvoyer un message potentiellement reçu.

## Consulter les analyses avec MCP

Depuis PowerShell, dans le dossier du projet, utilise le même Python pour
l’installation et le lancement.

```powershell
py -m pip install -r requirements.txt
py mcp_client.py BTCUSDT
py mcp_client.py BTCUSDT --limit 1
py mcp_client.py XAUUSD
```

Ces commandes créent une base temporaire avec deux analyses Bitcoin fictives.
Le client affiche le nom de l’outil découvert, ses arguments et le résultat
JSON. La dernière commande renvoie une liste vide. Pour lire ta vraie base,
lance `py mcp_client.py BTCUSDT --db test-live.db`.

Pour que Codex choisisse lui-même quand appeler l’outil, ajoute le serveur
MCP local dans Codex avec **le chemin absolu de ton interpréteur Python**
comme commande et les arguments suivants.

```text
C:/chemin/fundamental-AI-Engine/mcp_server.py --db C:/chemin/fundamental-AI-Engine/test-live.db
```

Le serveur utilise le transport stdio et ne requiert aucune clé API. Tu peux
ensuite poser ces trois questions à Codex.

1. « Quelles sont les deux dernières analyses BTCUSDT dans ma base ? »
2. « Donne-moi seulement le titre et le lien de la dernière analyse BTCUSDT. »
3. « As-tu une analyse XAUUSD ? Si la base n’en contient aucune, dis-le. »
