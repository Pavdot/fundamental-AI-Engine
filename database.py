def initialize(connection):
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
            source_article_id INTEGER PRIMARY KEY,
            source TEXT,
            headline TEXT NOT NULL,
            summary TEXT,
            url TEXT,
            published_at_utc INTEGER NOT NULL,
            fetched_at_utc INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS analyses (
            source_article_id INTEGER NOT NULL REFERENCES articles(source_article_id),
            target_asset TEXT NOT NULL,
            asset TEXT NOT NULL,
            direction REAL NOT NULL,
            importance REAL NOT NULL,
            confidence REAL NOT NULL,
            horizon_hours INTEGER NOT NULL,
            model_id TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            analyzed_at_utc INTEGER NOT NULL,
            PRIMARY KEY (source_article_id, target_asset)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            source_article_id INTEGER NOT NULL,
            target_asset TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            sent_at_utc INTEGER,
            PRIMARY KEY (source_article_id, target_asset),
            FOREIGN KEY (source_article_id, target_asset)
                REFERENCES analyses(source_article_id, target_asset)
        );
    """)


def analysis_exists(connection, article_id, target_asset):
    return connection.execute(
        """SELECT 1 FROM analyses WHERE source_article_id = ? AND target_asset = ?""",
        (article_id, target_asset),
    ).fetchone() is not None


def save_analysis(connection, article, summary, fetched_at, target, analysis,
                  model_id, prompt_version, analyzed_at, enqueue_alert):
    connection.execute(
        """INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(source_article_id) DO NOTHING""",
        (article["id"], article.get("source"), article["headline"], summary,
         article.get("url"), article["datetime"], fetched_at),
    )
    connection.execute(
        "INSERT INTO analyses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (article["id"], target, analysis.asset, analysis.direction, analysis.importance,
         analysis.confidence, analysis.horizon_hours, model_id, prompt_version, analyzed_at),
    )
    if enqueue_alert:
        connection.execute(
            "INSERT INTO alerts (source_article_id, target_asset) VALUES (?, ?)",
            (article["id"], target),
        )
