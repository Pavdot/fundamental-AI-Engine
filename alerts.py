import logging
import time

import requests


def send_pending(connection, token, chat_id):
    pending = connection.execute("""
        SELECT a.source_article_id, a.target_asset, a.direction, a.importance,
               a.horizon_hours, n.headline, n.url
        FROM alerts AS q
        JOIN analyses AS a USING (source_article_id, target_asset)
        JOIN articles AS n USING (source_article_id)
        WHERE q.status = 'pending'
    """).fetchall()
    failed = 0
    for article_id, asset, direction, importance, horizon, headline, url in pending:
        key = (article_id, asset)
        with connection:
            claimed = connection.execute(
                """UPDATE alerts SET status = 'sending'
                   WHERE source_article_id = ? AND target_asset = ? AND status = 'pending'""",
                key,
            ).rowcount
        if not claimed:
            continue

        message = (
            f"{asset} · Direction LLM {direction:+.2f} · Importance {importance:.2f} · {horizon} h\n"
            f"{headline[:600]}\n{str(url or '')[:1200]}"
        )
        status = "uncertain"
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message},
                timeout=15,
            )
            outcome = response.json()
            if isinstance(outcome, dict):
                if response.ok and outcome.get("ok") is True:
                    status = "sent"
                elif outcome.get("ok") is False and response.status_code < 500:
                    status = "pending"
        except requests.RequestException:
            pass

        with connection:
            connection.execute(
                """UPDATE alerts SET status = ?, sent_at_utc = ?
                   WHERE source_article_id = ? AND target_asset = ?""",
                (status, int(time.time()) if status == "sent" else None, *key),
            )
        if status != "sent":
            failed += 1
            logging.warning("Telegram article %s (%s): %s", article_id, asset, status)
    return failed
