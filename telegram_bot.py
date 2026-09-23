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
    reasons = top["reasons"]
    refs = top["references"]

    parts = [f"*{symbol}* — Top-Down SMC/ICT Analysis", ""]

    if bias not in ("Bullish", "Bearish"):
        parts.append(
            f"{symbol} ku ipo clean ah oru HTF bias illa — market ranging ah irukku, "
            f"clear direction edhுவும் kaanala. Structure clarify aagura varaikkum wait pannுறathu better."
        )
        return "\n".join(parts)

    tone = "Bullish" if bias == "Bullish" else "Bearish"

    story = f"{symbol} la bigger picture *{tone}* nu leaning aagிறுthu. "
    if reasons:
        joined_reasons = reasons[0][0].lower() + reasons[0][1:]
        story += f"Idhுக்கு காரணம் — {joined_reasons}"
        for r in reasons[1:]:
            story += f", innoru side la {r[0].lower()}{r[1:]}"
        story += ". "

    state_line = {
        "High confluence": "Ipo palaVidhamana factors ellame ஒண்ணா align aagி irukku, so idhு normal setup ah விட konjam strong ah irukku",
        "Developing": "Setup innும் form aagிறuthu — konjam pieces ready ah irukku, ana innும் fully confirm aagala",
        "No complete setup": "Ana ippozhudhaikku full setup edhுவும் illa, so idhு entry trigger illa, heads-up mattum thaan",
    }.get(state, state)
    story += f"{state_line} (confluence {score}/5)."
    parts.append(story)
    parts.append("")

    ez = refs.get("potential_entry_zone")
    if ez:
        ez_type = ez.get("type", "zone")
        low, high = ez.get("low"), ez.get("high")
        if low is not None and high is not None:
            parts.append(f"Price mattum back வந்தா, watch pண்ணனும்னா {ez_type} zone — {low} to {high} range la than.")
        else:
            parts.append(f"Price mattum back வந்தா, watch pண்ணனும்னா {ez_type} zone — {ez.get('price', 'n/a')} area la than.")

    inv = refs.get("invalidation_reference")
    if inv is not None:
        parts.append(f"Idhு ellame {inv} level structure hold pண்ணுthu nu than base pண்ணி sollura — andha level break aana, {tone.lower()} view invalid aagும்.")

    liq = refs.get("liquidity_references")
    if liq:
        levels_text = ", ".join(f"{lvl['price']}" for lvl in liq)
        parts.append(f"Adhுக்கு mேலே, {levels_text} arugila liquidity irukku — real move varradhுக்கு munnadi idhை magnet ah touch pண்ணலாம்.")

    parts.append("")
    parts.append("_Analysis only — executable entry/SL/TP instruction illa._")
    return "\n".join(parts)

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
