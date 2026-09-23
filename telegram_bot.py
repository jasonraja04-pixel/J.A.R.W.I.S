import os
import requests

from signal_service import get_signal, SUPPORTED_SYMBOLS


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


SYMBOL_ALIASES = {
    "GOLD": "XAUUSD",
    "SILVER": "XAGUSD",
    "NASDAQ": "NAS100",
    "NAS": "NAS100",
    "US100": "NAS100",
    "SPX": "SPX500",
    "SP500": "SPX500",
    "US500": "SPX500",
    "EURO": "EURUSD",
    "CABLE": "GBPUSD",
    "BTC": "BTCUSDT",
    "BITCOIN": "BTCUSDT",
    "ETH": "ETHUSDT",
    "ETHEREUM": "ETHUSDT",
    "SOL": "SOLUSDT",
    "XRP": "XRPUSDT",
    "BNB": "BNBUSDT",
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

    bias = top["bias"]
    state = top["state"]
    score = top["confluence_score"]
    reasons = top["reasons"]
    refs = top["references"]

    parts = [
        f"*{symbol}* — Top-Down SMC/ICT Analysis",
        ""
    ]

    if bias not in ("Bullish", "Bearish"):
        parts.append(
            f"{symbol} ku ipo clean ah oru HTF bias illa — "
            f"market ranging ah irukku, clear direction edhuvum kaanala. "
            f"Structure clarify aagura varaikkum wait pannurathu better."
        )

        parts.append("")
        parts.append("_Analysis only — executable entry/SL/TP instruction illa._")

        return "\n".join(parts)

    tone = "Bullish" if bias == "Bullish" else "Bearish"

    story = (
        f"{symbol} la bigger picture *{tone}* nu leaning aaguthu. "
    )

    if reasons:
        joined_reasons = reasons[0][0].lower() + reasons[0][1:]
        story += f"Idhuku karanam — {joined_reasons}"

        for reason in reasons[1:]:
            story += f", innoru side la {reason[0].lower()}{reason[1:]}"

        story += ". "

    state_line = {
        "High confluence": (
            "Ipo pala vidhamana factors ellame onna align aagi irukku, "
            "so idhu normal setup ah vida konjam strong ah irukku"
        ),
        "Developing": (
            "Setup innum form aaguthu — konjam pieces ready ah irukku, "
            "ana innum fully confirm aagala"
        ),
        "No complete setup": (
            "Ana ippozhudhaikku full setup edhuvum illa, "
            "so idhu entry trigger illa, heads-up mattum thaan"
        ),
    }.get(state, state)

    story += f"{state_line} (confluence {score}/5)."

    parts.append(story)
    parts.append("")

    # Potential entry zone
    ez = refs.get("potential_entry_zone")

    if ez:
        ez_type = ez.get("type", "zone")
        low = ez.get("low")
        high = ez.get("high")

        if low is not None and high is not None:
            parts.append(
                f"Price mattum back vandha, watch pannannumna "
                f"{ez_type} zone — {low} to {high} range la thaan."
            )
        else:
            parts.append(
                f"Price mattum back vandha, watch pannannumna "
                f"{ez_type} zone — {ez.get('price', 'n/a')} area la thaan."
            )

    # Invalidation reference
    inv = refs.get("invalidation_reference")

    if inv is not None:
        parts.append(
            f"Idhu ellame {inv} level structure hold pannuthu nu thaan "
            f"base panni sollura — andha level break aana, "
            f"{tone.lower()} view invalid aagum."
        )

    # Liquidity references
    liq = refs.get("liquidity_references")

    if liq:
        levels_text = ", ".join(str(level["price"]) for level in liq)

        parts.append(
            f"Adhuku mele, {levels_text} arugila liquidity irukku — "
            f"real move varradhuku munnadi idhai magnet ah touch pannalam."
        )

    parts.append("")
    parts.append(
        "_Analysis only — executable entry/SL/TP instruction illa._"
    )

    return "\n".join(parts)


def send_message(chat_id, text: str):
    """
    Send a message to Telegram and print the API response
    so Render logs show exactly what Telegram returns.
    """

    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM ERROR: TELEGRAM_BOT_TOKEN is missing")
        return False

    try:
        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=15
        )

        print("TELEGRAM STATUS:", response.status_code)
        print("TELEGRAM RESPONSE:", response.text)

        if response.ok:
            return True

        return False

    except requests.RequestException as e:
        print("TELEGRAM REQUEST ERROR:", repr(e))
        return False

    except Exception as e:
        print("TELEGRAM ERROR:", repr(e))
        return False


def handle_update(update: dict):
    """
    Process incoming Telegram webhook updates.
    """

    print("TELEGRAM UPDATE RECEIVED")

    msg = update.get("message")

    if not msg:
        print("No message object in update")
        return

    if "text" not in msg:
        print("Update does not contain text")
        return

    chat_id = msg["chat"]["id"]
    text = msg["text"].strip()

    print("TELEGRAM MESSAGE:", text)

    # /start
    if text.startswith("/start"):
        send_message(
            chat_id,
            "Vanakkam! Oru symbol sollunga "
            "(e.g. EURUSD, GBPJPY, Gold, NAS100) — "
            "naan top-down SMC/ICT analysis pannitu sollen. "
            "/symbols nu type panni full list paarunga."
        )
        return

    # /symbols
    if text.startswith("/symbols"):
        send_message(
            chat_id,
            "Supported: " + ", ".join(SUPPORTED_SYMBOLS)
        )
        return

    # Find symbol
    symbol = extract_symbol(text)

    if not symbol:
        send_message(
            chat_id,
            "Andha symbol enakku theriyala. "
            "/symbols nu type pannunga, supported list varum."
        )
        return

    # Generate analysis
    try:
        print("ANALYZING SYMBOL:", symbol)

        data = get_signal(symbol)

        print("SIGNAL GENERATED:", symbol)

        message = format_signal(symbol, data)

        send_message(chat_id, message)

    except Exception as e:
        print("SIGNAL ERROR:", repr(e))

        send_message(
            chat_id,
            f"{symbol} analyze panna error vandhuchu: {e}"
    )
