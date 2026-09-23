import os, requests
from signal_service import get_signal, SUPPORTED_SYMBOLS

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

SYMBOL_ALIASES = {
    "GOLD": "XAUUSD", "SILVER": "XAGUSD",
    "NASDAQ": "NAS100", "NAS": "NAS100", "US100": "NAS100",
    "SPX": "SPX500", "SP500": "SPX500", "US500": "SPX500",
    "EURO": "EURUSD", "CABLE": "GBPUSD",
    "BTC": "BTCUSDT", "BITCOIN": "BTCUSDT", "ETH": "ETHUSDT", "ETHEREUM": "ETHUSDT",
    "SOL": "SOLUSDT", "XRP": "XRPUSDT", "BNB": "BNBUSDT",
}

def extract_symbol(text: str):
    t = text.upper().replace("/", "").replace("-", "").replace(" ", "")
    for alias, sym in SYMBOL_ALIASES.items():
        if alias in t:
            return sym
    for sym in SUPPORTED_SYMBOLS:
        if sym in t:
            return sym
    return None

def format_signal(symbol: str, data: dict) -> str:
    top = data["signal"]
    bias, state, score = top["bias"], top["state"], top["confluence_score"]
    lines = [f"*{symbol}* — Top-Down SMC/ICT Analysis", "",
              f"Bias: *{bias}*", f"Setup state: *{state}* (confluence {score}/5)", ""]
    if top["reasons"]:
        lines.append("Reasoning:")
        lines += [f"• {r}" for r in top["reasons"]]
        lines.append("")
    refs = top["references"]
    if refs.get("potential_entry_zone"):
        lines.append(f"Potential entry zone reference: {refs['potential_entry_zone']}")
    if refs.get("invalidation_reference"):
        lines.append(f"Invalidation reference: {refs['invalidation_reference']}")
    if refs.get("liquidity_references"):
        lines.append("Nearby liquidity references:")
        lines += [f"• {lvl['price']} ({lvl['type']})" for lvl in refs["liquidity_references"]]
    lines.append("")
    lines.append("_Analysis only — not an executable entry/SL/TP instruction._")
    return "\n".join(lines)

def send_message(chat_id, text: str):
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage",
                       json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                       timeout=15)
    except Exception:
        pass  # don't let a Telegram-side failure crash the webhook response

def handle_update(update: dict):
    msg = update.get("message")
    if not msg or "text" not in msg:
        return
    chat_id = msg["chat"]["id"]
    text = msg["text"].strip()

    if text.startswith("/start"):
        send_message(chat_id,
            "Vanakkam! Oru symbol sollunga (e.g. EURUSD, GBPJPY, Gold, NAS100) — "
            "naan top-down SMC/ICT analysis pannitu sollen. /symbols nu type panni full list paarunga.")
        return
    if text.startswith("/symbols"):
        send_message(chat_id, "Supported: " + ", ".join(SUPPORTED_SYMBOLS))
        return

    symbol = extract_symbol(text)
    if not symbol:
        send_message(chat_id, "Andha symbol enakku theriyala. /symbols nu type pannunga, supported list varum.")
        return

    try:
        data = get_signal(symbol)
        send_message(chat_id, format_signal(symbol, data))
    except Exception as e:
        send_message(chat_id, f"{symbol} analyze panna error vandhuchu: {e}")
