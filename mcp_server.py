import argparse
from contextlib import closing
from pathlib import Path
import sqlite3
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field


def main():
    parser = argparse.ArgumentParser(description="Serve SQLite analyses over MCP stdio")
    parser.add_argument("--db", type=Path, default=Path(__file__).with_name("news.db"))
    db_uri = parser.parse_args().db.resolve().as_uri() + "?mode=ro"
    server = FastMCP("Fundamental AI Engine")

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def get_latest_analyses(
        asset: Literal["BTCUSDT", "XAUUSD"],
        limit: Annotated[int, Field(ge=1, le=50)] = 5,
    ) -> list[dict]:
        """Read the latest saved analyses for an asset, newest first. An empty list means no saved analysis for that asset."""
        try:
            with closing(sqlite3.connect(db_uri, uri=True)) as connection:
                connection.row_factory = sqlite3.Row
                rows = connection.execute(
                    """
                    SELECT n.headline, n.url, n.source, n.published_at_utc,
                           a.target_asset, a.asset, a.direction, a.importance,
                           a.confidence, a.horizon_hours, a.analyzed_at_utc
                    FROM analyses AS a
                    JOIN articles AS n USING (source_article_id)
                    WHERE a.target_asset = ?
                    ORDER BY a.analyzed_at_utc DESC, a.source_article_id DESC
                    LIMIT ?
                    """,
                    (asset, limit),
                ).fetchall()
        except sqlite3.Error:
            raise RuntimeError(
                "Impossible de lire la base SQLite. Vérifie le chemin et lance le moteur "
                "une fois pour initialiser les tables articles et analyses."
            ) from None
        return [dict(row) for row in rows]

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
