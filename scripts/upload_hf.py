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
import json
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
                   best_cost_pct, best_time_min, they_receive, best_via, routes_json
            FROM rate_snapshots
            WHERE substr(replace(substr(captured_at, 1, 19), 'T', ' '), 1, 10) = ?
            ORDER BY captured_at ASC
        """, (date_str,)).fetchall()
    finally:
        conn.close()

    if not rows:
        logger.info(f"No data for {date_str}")
        return None

    # Export TWO files: summary (best route) + detailed (all routes)
    # Summary CSV
    summary_buf = io.StringIO()
    sw = csv.writer(summary_buf)
    sw.writerow(["captured_at_utc", "from_currency", "to_currency", "amount",
                 "best_cost_pct", "best_time_min", "they_receive", "best_via"])
    for r in rows:
        sw.writerow([r["captured_at"], r["from_currency"], r["to_currency"],
                     r["amount"], r["best_cost_pct"], r["best_time_min"],
                     r["they_receive"], r["best_via"]])

    # Detailed CSV — all routes per snapshot expanded
    detail_buf = io.StringIO()
    dw = csv.writer(detail_buf)
    dw.writerow(["captured_at_utc", "from_currency", "to_currency", "amount",
                 "rank", "provider", "cost_pct", "they_receive", "has_public_api",
                 "accuracy_score"])

    LIVE_EXCHANGES = {'Binance','Kraken','Coinbase','OKX','Bybit','KuCoin','Gate','Bitget',
        'MEXC','HTX','Crypto.com','Luno','Bitstamp','Gemini','Bithumb','Bitflyer',
        'BtcTurk','IndependentReserve','WhiteBIT','Bitso','Buda',
        'VALR','CoinDCX','WazirX','SatoshiTango','Binance P2P (live)','Uphold'}
    LIVE_FX = {'Wise'}
    CENTRAL_BANKS = {'BCB PTAX (BR)','TRM (CO)','Bluelytics (AR)','TCMB (TR)',
        'NBP (PL)','CNB (CZ)','NBU (UA)','NBG (GE)','BOI (IL)','BNR (RO)','NRB (NP)'}
    P2P_MONITORS = {'Binance P2P','Yadio (P2P)'}

    def accuracy_score(via: str) -> float:
        """Rate accuracy score per whitepaper Section 10."""
        if any(p in via for p in LIVE_EXCHANGES):
            return 1.0
        if any(p in via for p in LIVE_FX):
            return 0.95
        if any(p in via for p in CENTRAL_BANKS):
            return 0.90
        if any(p in via for p in P2P_MONITORS):
            return 0.80
        if "~est." in via or "est." in via.lower():
            return 0.40
        return 0.60  # published fee + live FX fallback

    detail_count = 0
    for r in rows:
        try:
            routes = json.loads(r["routes_json"])
        except Exception:
            continue
        for route in routes:
            via = route.get("via", "")
            has_api = any(p in via for p in LIVE_EXCHANGES | LIVE_FX)
            score = accuracy_score(via)
            dw.writerow([
                r["captured_at"], r["from_currency"], r["to_currency"], r["amount"],
                route.get("rank", 0), via,
                route.get("total_cost_pct", 0), route.get("they_receive", 0),
                has_api, score
            ])
            detail_count += 1

    logger.info(f"Exported {len(rows)} snapshots + {detail_count} detailed routes for {date_str}")
    return summary_buf.getvalue(), detail_buf.getvalue()


def upload_to_hf(content: bytes, filename: str, commit_msg: str):
    """Upload a file to Hugging Face dataset."""
    if not HF_TOKEN:
        logger.error("HF_TOKEN not set")
        return False

    try:
        from huggingface_hub import HfApi
        api = HfApi(token=HF_TOKEN)

        api.upload_file(
            path_or_fileobj=content,
            path_in_repo=filename,
            repo_id=HF_REPO,
            repo_type="dataset",
            commit_message=commit_msg,
        )
        logger.info(f"Uploaded {filename} to {HF_REPO}")
        return True
    except Exception as e:
        logger.error(f"HF upload failed for {filename}: {e}")
        return False


def main():
    # Upload yesterday's data (today's is still accumulating)
    yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info(f"Exporting data for {yesterday}")

    result = export_day_csv(yesterday)
    if result:
        summary_csv, detail_csv = result
        upload_to_hf(
            summary_csv.encode("utf-8"),
            f"data/rates-{yesterday}.csv",
            f"Add rate snapshots for {yesterday}",
        )
        upload_to_hf(
            detail_csv.encode("utf-8"),
            f"data/routes-{yesterday}.csv",
            f"Add detailed routes for {yesterday}",
        )
    else:
        logger.info("No data to upload")


if __name__ == "__main__":
    main()
