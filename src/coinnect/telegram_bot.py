"""
Coinnect Telegram Bot — query money transfer routes via chat.

Usage:
    TELEGRAM_BOT_TOKEN=xxx python -m coinnect.telegram_bot

Systemd service suggestion:
    # /etc/systemd/system/coinnect-telegram.service
    # [Unit]
    # Description=Coinnect Telegram Bot
    # After=network.target coinnect-api.service
    # Wants=coinnect-api.service
    #
    # [Service]
    # Type=simple
    # User=coinnect
    # WorkingDirectory=/opt/coinnect
    # EnvironmentFile=/opt/coinnect/.env
    # ExecStart=/opt/coinnect/.venv/bin/python -m coinnect.telegram_bot
    # Restart=on-failure
    # RestartSec=5
    #
    # [Install]
    # WantedBy=multi-user.target
"""

import logging
import os
import re

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("coinnect.telegram")

API_BASE = os.getenv("COINNECT_API_URL", "http://localhost:8100")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Matches: USD MXN 500  or  usd mxn 500.50
QUERY_RE = re.compile(r"^([A-Za-z]{3})\s+([A-Za-z]{3})\s+([\d,_.]+)$")


def _format_number(n: float, decimals: int = 2) -> str:
    """Format number with commas: 8940.50 -> 8,940.50"""
    return f"{n:,.{decimals}f}"


def _format_routes(data: dict) -> str:
    """Build the user-facing response from the API JSON."""
    from_c = data["from_currency"]
    to_c = data["to_currency"]
    amount = data["amount"]
    routes = data["routes"][:3]

    lines = [f"\U0001f50d {from_c} \u2192 {to_c} \u00b7 ${_format_number(amount)}\n"]

    for r in routes:
        rank = r["rank"]
        label = r["label"]
        cost = r["total_cost_pct"]
        minutes = r["total_time_minutes"]
        send = r["you_send"]
        receive = r["they_receive"]
        recv_cur = r["they_receive_currency"]

        if rank == 1:
            header = f"#{rank} \u2728 Cheapest \u2014 {cost:.2f}% via {label}"
        else:
            header = f"#{rank} {label} \u2014 {cost:.2f}%"

        time_str = f"{minutes} min" if minutes < 120 else f"{minutes // 60} hr"

        lines.append(header)
        lines.append(
            f"   You send: `${_format_number(send)}` \u2192 "
            f"They receive: `{_format_number(receive)} {recv_cur}`"
        )
        lines.append(f"   \u23f1 ~{time_str}\n")

    lines.append("\U0001f310 More routes: coinnect.bot")
    return "\n".join(lines)


async def _fetch_quote(from_c: str, to_c: str, amount: float) -> str:
    """Call the Coinnect API and return a formatted string."""
    url = f"{API_BASE}/v1/quote"
    params = {"from": from_c.upper(), "to": to_c.upper(), "amount": amount}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)

    if resp.status_code == 404:
        return (
            f"\u274c No routes found for {from_c.upper()} \u2192 {to_c.upper()}.\n"
            "This corridor may not be supported yet.\n"
            "Try /help to see usage."
        )
    if resp.status_code == 429:
        return "\u23f3 Rate limit reached. Please try again in a few minutes."
    if resp.status_code != 200:
        logger.error("API error %s: %s", resp.status_code, resp.text[:200])
        return "\u26a0\ufe0f Something went wrong. Please try again later."

    return _format_routes(resp.json())


WELCOME = (
    "\U0001f4b8 *Coinnect* \u2014 find the cheapest way to send money.\n\n"
    "Send a message like:\n"
    "`USD MXN 500`\n\n"
    "Or use the command:\n"
    "`/quote USD MXN 500`\n\n"
    "I'll show you the top routes with fees and estimated time.\n\n"
    "Supported corridors: USD, MXN, BRL, NGN, KES, GHS, PHP, INR, ARS, EUR and more.\n\n"
    "\U0001f310 coinnect.bot"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME, parse_mode="Markdown")


async def cmd_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quote USD MXN 500"""
    args = context.args
    if not args or len(args) != 3:
        await update.message.reply_text(
            "\u2753 Usage: `/quote USD MXN 500`", parse_mode="Markdown"
        )
        return

    from_c, to_c, raw_amount = args
    try:
        amount = float(raw_amount.replace(",", "").replace("_", ""))
    except ValueError:
        await update.message.reply_text("\u274c Invalid amount. Use a number like `500` or `1,000`.", parse_mode="Markdown")
        return

    if amount <= 0:
        await update.message.reply_text("\u274c Amount must be greater than zero.")
        return

    msg = await update.message.reply_text("\U0001f50e Searching routes...")
    reply = await _fetch_quote(from_c, to_c, amount)
    await msg.edit_text(reply, parse_mode="Markdown")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plain text like 'USD MXN 500'."""
    text = (update.message.text or "").strip()
    match = QUERY_RE.match(text)
    if not match:
        return  # Ignore unrecognized messages silently

    from_c, to_c, raw_amount = match.groups()
    try:
        amount = float(raw_amount.replace(",", "").replace("_", ""))
    except ValueError:
        return

    if amount <= 0:
        return

    msg = await update.message.reply_text("\U0001f50e Searching routes...")
    reply = await _fetch_quote(from_c, to_c, amount)
    await msg.edit_text(reply, parse_mode="Markdown")


def main() -> None:
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set. Exiting.")
        raise SystemExit(1)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("quote", cmd_quote))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Coinnect Telegram bot starting (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
