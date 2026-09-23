from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from data_feed import get_ohlcv
from smc_engine import analyze_timeframe
from signal_service import get_signal, norm, SUPPORTED_SYMBOLS, TIMEFRAMES
import telegram_bot

app=FastAPI(title="SMC/ICT Top-Down Analysis API")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

@app.get("/api/symbols")
def symbols(): return {"symbols":SUPPORTED_SYMBOLS,"timeframes":TIMEFRAMES}

@app.get("/api/timeframe/{symbol}/{tf}")
def timeframe(symbol:str,tf:str):
    s=norm(symbol)
    if s not in SUPPORTED_SYMBOLS or tf not in TIMEFRAMES: raise HTTPException(400,"Unsupported symbol/timeframe")
    try: return analyze_timeframe(get_ohlcv(s,tf))
    except Exception as e: raise HTTPException(502,str(e))

@app.get("/api/signal/{symbol}")
def signal(symbol:str):
    s=norm(symbol)
    if s not in SUPPORTED_SYMBOLS: raise HTTPException(404,f"{s} not supported")
    try: return get_signal(s)
    except Exception as e: raise HTTPException(502,f"Data fetch/analysis failed for {s}: {e}")

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    telegram_bot.handle_update(update)
    return {"ok": True}
