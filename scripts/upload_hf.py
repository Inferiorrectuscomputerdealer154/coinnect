#!/usr/bin/env python3
"""
Daily upload of rate snapshots to Hugging Face.
Run via cron: 0 0 * * * /home/inge/coinnect/.venv/bin/python /home/inge/coinnect/scripts/upload_hf.py

Uploads yesterday's rate snapshots as a CSV to:
  huggingface.co/datasets/coinnect-dev/coinnect-rates
"""

import os
import io
import csv
import sqlite3
import logging
from datetime import datetime, timedelta, UTC
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hf-upload")

DB_PATH = Path(__file__).parent.parent / "data" / "history.db"
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_REPO = "coinnect-dev/coinnect-rates"


def export_day_csv(date_str: str) -> str | None:
    """Export a day's snapshots as CSV string."""
    if not DB_PATH.exists():
        logger.error(f"DB not found: {DB_PATH}")
        return None

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT captured_at, from_currency, to_currency, amount,
                   best_cost_pct, best_time_min, they_receive, best_via
            FROM rate_snapshots
            WHERE substr(replace(substr(captured_at, 1, 19), 'T', ' '), 1, 10) = ?
            ORDER BY captured_at ASC
        """, (date_str,)).fetchall()
    finally:
        conn.close()

    if not rows:
        logger.info(f"No data for {date_str}")
        return None

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["captured_at_utc", "from_currency", "to_currency", "amount",
                "best_cost_pct", "best_time_min", "they_receive", "best_via"])
    for r in rows:
        w.writerow([r["captured_at"], r["from_currency"], r["to_currency"],
                    r["amount"], r["best_cost_pct"], r["best_time_min"],
                    r["they_receive"], r["best_via"]])

    logger.info(f"Exported {len(rows)} rows for {date_str}")
    return buf.getvalue()


def upload_to_hf(csv_content: str, date_str: str):
    """Upload CSV to Hugging Face dataset."""
    if not HF_TOKEN:
        logger.error("HF_TOKEN not set")
        return False

    try:
        from huggingface_hub import HfApi
        api = HfApi(token=HF_TOKEN)

        filename = f"data/rates-{date_str}.csv"
        api.upload_file(
            path_or_fileobj=csv_content.encode("utf-8"),
            path_in_repo=filename,
            repo_id=HF_REPO,
            repo_type="dataset",
            commit_message=f"Add rate snapshots for {date_str}",
        )
        logger.info(f"Uploaded {filename} to {HF_REPO}")
        return True
    except Exception as e:
        logger.error(f"HF upload failed: {e}")
        return False


def main():
    # Upload yesterday's data (today's is still accumulating)
    yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info(f"Exporting data for {yesterday}")

    csv_content = export_day_csv(yesterday)
    if csv_content:
        upload_to_hf(csv_content, yesterday)
    else:
        logger.info("No data to upload")


if __name__ == "__main__":
    main()
