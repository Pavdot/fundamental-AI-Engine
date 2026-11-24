import argparse
import asyncio
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from database import initialize, save_analysis
from main import NewsAnalysis


def create_demo(path):
    now = int(time.time())
    with closing(sqlite3.connect(path)) as connection:
        initialize(connection)
        with connection:
            for article_id, headline, direction in (
                (1, "Démo · Hausse des flux vers les ETF Bitcoin", 0.6),
                (2, "Démo · Recul du volume sur Bitcoin", -0.3),
            ):
                article = {
                    "id": article_id, "headline": headline, "datetime": now - 600,
                    "source": "Démo", "url": None,
                }
                analysis = NewsAnalysis(
                    asset="BTCUSDT", direction=direction, importance=0.7,
                    confidence=0.8, horizon_hours=12,
                )
                save_analysis(
                    connection, article, "", now, "BTCUSDT", analysis,
                    "demo", "demo", now + article_id - 2, False,
                )


async def inspect_database(path, asset, limit):
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).with_name("mcp_server.py").resolve()), "--db", str(path)],
    )
    async with stdio_client(server) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Outils MCP disponibles :", ", ".join(tool.name for tool in tools.tools))
            arguments = {"asset": asset, "limit": limit}
            print("Appel de get_latest_analyses", arguments)
            result = await session.call_tool("get_latest_analyses", arguments)
            if result.isError:
                for item in result.content:
                    print(getattr(item, "text", ""), file=sys.stderr)
                return 1
            print(json.dumps(result.structuredContent, ensure_ascii=False, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description="Inspect analyses via a local MCP server")
    parser.add_argument("asset", nargs="?", choices=("BTCUSDT", "XAUUSD"), default="BTCUSDT")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--db", type=Path, help="SQLite database to inspect instead of demo data")
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error("--limit must be between 1 and 50")
    if args.db is not None:
        return asyncio.run(inspect_database(args.db.resolve(), args.asset, args.limit))

    with TemporaryDirectory() as directory:
        path = Path(directory) / "demo.db"
        create_demo(path)
        return asyncio.run(inspect_database(path, args.asset, args.limit))


if __name__ == "__main__":
    raise SystemExit(main())
