import os, requests, pandas as pd
from dotenv import load_dotenv
load_dotenv()

TWELVEDATA_API_KEY=os.getenv("TWELVEDATA_API_KEY","")
TWELVEDATA_BASE="https://api.twelvedata.com"

TIMEFRAME_TD={"15m":"15min","1h":"1h","4h":"4h"}

FX_SYMBOLS=["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD","EURGBP","EURJPY",
"GBPJPY","AUDJPY","EURAUD","GBPAUD","EURCHF","GBPCHF","AUDNZD","NZDJPY","CADJPY","CHFJPY"]
METAL_SYMBOLS=["XAUUSD","XAGUSD"]
# TwelveData index tickers — verify these resolve on your plan; some indices need a paid tier.
INDEX_TD_SYMBOL={"NAS100":"NDX","SPX500":"SPX"}
# Crypto now routed through TwelveData too (Binance blocks Render/cloud IPs with a 451).
CRYPTO_TD_SYMBOL={"BTCUSDT":"BTC/USD","ETHUSDT":"ETH/USD","SOLUSDT":"SOL/USD",
                  "XRPUSDT":"XRP/USD","BNBUSDT":"BNB/USD"}

def _td_symbol(symbol):
    if symbol in INDEX_TD_SYMBOL: return INDEX_TD_SYMBOL[symbol]
    if symbol in CRYPTO_TD_SYMBOL: return CRYPTO_TD_SYMBOL[symbol]
    if symbol in FX_SYMBOLS or symbol in METAL_SYMBOLS: return symbol[:3]+"/"+symbol[3:]
    raise ValueError(f"No TwelveData mapping for {symbol}")

def _twelvedata(symbol,tf,limit=300):
    if not TWELVEDATA_API_KEY: raise RuntimeError("TWELVEDATA_API_KEY missing")
    r=requests.get(f"{TWELVEDATA_BASE}/time_series",params={
        "symbol":_td_symbol(symbol),"interval":TIMEFRAME_TD[tf],
        "outputsize":min(limit,5000),"apikey":TWELVEDATA_API_KEY,"order":"ASC"},timeout=15)
    r.raise_for_status()
    body=r.json()
    if body.get("status")=="error": raise RuntimeError(body.get("message","TwelveData error"))
    rows=[]
    for c in body.get("values",[]):
        rows.append({"time":c["datetime"],"open":c["open"],"high":c["high"],
                     "low":c["low"],"close":c["close"],"volume":c.get("volume",0)})
    return pd.DataFrame(rows)

def get_ohlcv(symbol,tf,limit=300):
    symbol=symbol.replace("/","").replace("-","").upper()
    if (symbol in FX_SYMBOLS or symbol in METAL_SYMBOLS
        or symbol in INDEX_TD_SYMBOL or symbol in CRYPTO_TD_SYMBOL):
        return _twelvedata(symbol,tf,limit)
    raise ValueError(f"Unsupported symbol: {symbol}")
