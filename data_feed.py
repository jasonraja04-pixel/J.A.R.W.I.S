import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "").strip()
TWELVEDATA_BASE = "https://api.twelvedata.com"


# --------------------------------------------------
# TIMEFRAMES
# --------------------------------------------------

TIMEFRAME_TD = {
    "15m": "15min",
    "1h": "1h",
    "4h": "4h",
}


# --------------------------------------------------
# SYMBOLS
# --------------------------------------------------

FX_SYMBOLS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "USDCHF",
    "USDCAD",
    "AUDUSD",
    "NZDUSD",
    "EURGBP",
    "EURJPY",
    "GBPJPY",
    "AUDJPY",
    "EURAUD",
    "GBPAUD",
    "EURCHF",
    "GBPCHF",
    "AUDNZD",
    "NZDJPY",
    "CADJPY",
    "CHFJPY",
]

METAL_SYMBOLS = [
    "XAUUSD",
    "XAGUSD",
]


# --------------------------------------------------
# TWELVE DATA SYMBOL MAPPING
# --------------------------------------------------

INDEX_TD_SYMBOL = {
    "NAS100": "NDX",
    "SPX500": "SPX",
}

CRYPTO_TD_SYMBOL = {
    "BTCUSDT": "BTC/USD",
    "ETHUSDT": "ETH/USD",
    "SOLUSDT": "SOL/USD",
    "XRPUSDT": "XRP/USD",
    "BNBUSDT": "BNB/USD",
}


# --------------------------------------------------
# SYMBOL CONVERSION
# --------------------------------------------------

def _td_symbol(symbol: str) -> str:

    symbol = symbol.upper().replace("/", "").replace("-", "")

    if symbol in INDEX_TD_SYMBOL:
        return INDEX_TD_SYMBOL[symbol]

    if symbol in CRYPTO_TD_SYMBOL:
        return CRYPTO_TD_SYMBOL[symbol]

    if symbol in FX_SYMBOLS or symbol in METAL_SYMBOLS:
        return symbol[:3] + "/" + symbol[3:]

    raise ValueError(
        f"No Twelve Data mapping for {symbol}"
    )


# --------------------------------------------------
# TWELVE DATA REQUEST
# --------------------------------------------------

def _twelvedata(symbol: str, tf: str, limit: int = 300):

    if not TWELVEDATA_API_KEY:
        raise RuntimeError(
            "TWELVEDATA_API_KEY missing from environment variables"
        )

    if tf not in TIMEFRAME_TD:
        raise ValueError(
            f"Unsupported timeframe: {tf}"
        )

    td_symbol = _td_symbol(symbol)
    td_interval = TIMEFRAME_TD[tf]

    print(
        f"TWELVEDATA REQUEST: "
        f"symbol={td_symbol}, "
        f"interval={td_interval}, "
        f"limit={limit}"
    )

    try:

        response = requests.get(
            f"{TWELVEDATA_BASE}/time_series",
            params={
                "symbol": td_symbol,
                "interval": td_interval,
                "outputsize": min(limit, 5000),
                "apikey": TWELVEDATA_API_KEY,
                "order": "ASC",
            },
            timeout=20,
        )

    except requests.RequestException as e:

        raise RuntimeError(
            f"Twelve Data connection failed: {e}"
        )


    # --------------------------------------------------
    # HTTP ERROR DEBUGGING
    # --------------------------------------------------

    if not response.ok:

        print(
            "TWELVEDATA HTTP STATUS:",
            response.status_code
        )

        print(
            "TWELVEDATA RESPONSE:",
            response.text
        )

        raise RuntimeError(
            f"Twelve Data HTTP {response.status_code}: "
            f"{response.text}"
        )


    # --------------------------------------------------
    # JSON
    # --------------------------------------------------

    try:

        body = response.json()

    except ValueError:

        raise RuntimeError(
            f"Twelve Data returned invalid JSON: "
            f"{response.text[:500]}"
        )


    print(
        "TWELVEDATA STATUS:",
        body.get("status", "unknown")
    )


    # --------------------------------------------------
    # API ERROR
    # --------------------------------------------------

    if body.get("status") == "error":

        message = body.get(
            "message",
            "Unknown Twelve Data error"
        )

        raise RuntimeError(
            f"Twelve Data error: {message}"
        )


    values = body.get("values")

    if not values:

        raise RuntimeError(
            f"No market data returned for "
            f"{td_symbol} ({td_interval})"
        )


    # --------------------------------------------------
    # BUILD DATAFRAME
    # --------------------------------------------------

    rows = []

    for candle in values:

        rows.append({
            "time": candle["datetime"],
            "open": float(candle["open"]),
            "high": float(candle["high"]),
            "low": float(candle["low"]),
            "close": float(candle["close"]),
            "volume": float(
                candle.get("volume", 0) or 0
            ),
        })


    df = pd.DataFrame(rows)


    if df.empty:

        raise RuntimeError(
            f"Empty dataframe returned for {symbol}"
        )


    # Make sure candles are chronological
    df["time"] = pd.to_datetime(df["time"])

    df = df.sort_values(
        "time"
    ).reset_index(drop=True)


    print(
        f"TWELVEDATA SUCCESS: "
        f"{symbol} / {tf} -> {len(df)} candles"
    )

    return df


# --------------------------------------------------
# PUBLIC OHLCV FUNCTION
# --------------------------------------------------

def get_ohlcv(
    symbol: str,
    tf: str,
    limit: int = 300
):

    symbol = (
        symbol
        .replace("/", "")
        .replace("-", "")
        .upper()
    )


    supported = (
        symbol in FX_SYMBOLS
        or symbol in METAL_SYMBOLS
        or symbol in INDEX_TD_SYMBOL
        or symbol in CRYPTO_TD_SYMBOL
    )


    if not supported:

        raise ValueError(
            f"Unsupported symbol: {symbol}"
        )


    return _twelvedata(
        symbol,
        tf,
        limit
  )
