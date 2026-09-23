import time
from data_feed import get_ohlcv
from smc_engine import analyze_timeframe, generate_topdown

SUPPORTED_SYMBOLS = [
    "EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD","EURGBP","EURJPY",
    "GBPJPY","AUDJPY","EURAUD","GBPAUD","EURCHF","GBPCHF","AUDNZD","NZDJPY","CADJPY",
    "CHFJPY","XAUUSD","XAGUSD","NAS100","SPX500",
    "BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BNBUSDT"]
TIMEFRAMES = ["4h", "1h", "15m"]

_cache = {}
TTL = 30

def norm(s):
    return s.replace("/", "").replace("-", "").upper()

def get_signal(symbol: str):
    """Returns the same shape as the original /api/signal/{symbol} response.
    Shared by the REST API route and the Telegram bot so both hit the same
    30s cache instead of double-fetching from OANDA/Capital.com."""
    s = norm(symbol)
    if s not in SUPPORTED_SYMBOLS:
        raise ValueError(f"{s} not supported")
    now = time.time()
    if s in _cache and now - _cache[s][0] < TTL:
        return _cache[s][1]
    tf = {t: analyze_timeframe(get_ohlcv(s, t)) for t in TIMEFRAMES}
    top = generate_topdown(tf)
    response = {
        "symbol": s,
        "generated_at": time.time(),
        "signal": top,
        "timeframes": {t: {
            "trend": tf[t]["structure"]["trend"],
            "last_event": tf[t]["structure"]["last_event"],
            "last_close": tf[t]["last_close"],
            "fvg_zones": tf[t]["fvg_zones"],
            "liquidity_sweep": tf[t]["liquidity_sweep"],
            "order_block": tf[t]["order_block"],
            "ote_zone": tf[t]["ote_zone"],
            "displacement": tf[t]["displacement"],
            "last_time": tf[t]["last_time"]} for t in TIMEFRAMES}}
    _cache[s] = (now, response)
    return response
