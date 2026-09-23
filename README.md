# SMC Engine V6 — Top-Down SMC/ICT Analysis

Endpoints (same contract as before):
- GET /api/signal/{symbol}
- GET /api/timeframe/{symbol}/{tf}
- GET /api/symbols
- POST /telegram/webhook (Telegram bot updates)

Data sources:
- **TwelveData** (free API key, no broker/trading account needed — works from India): FX majors + XAU/USD + XAG/USD, and NAS100 + SPX500. Free tier is 800 requests/day, 8/min — each signal check costs 3 calls (4h+1h+15m), so watch usage if scanning many symbols
- **Binance public API** (no account/key needed): BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BNBUSDT — extend `CRYPTO_SYMBOLS` in `data_feed.py` for more pairs

Env vars needed (.env):
```
TWELVEDATA_API_KEY=
TELEGRAM_BOT_TOKEN=
```

Top-down logic:
4H -> directional market structure
1H -> POI/context (order block, FVG, OTE, structure alignment)
15M -> trigger context (liquidity raid, displacement, structure event)

The engine is analysis-only: it does not place orders and does not generate executable entry/SL/TP instructions.

Telegram bot:
- Free-text chat, no menu buttons — send a symbol or alias (e.g. "EURUSD", "gold", "btc", "nasdaq") and get a top-down analysis reply
- `/start` and `/symbols` are the only commands
- Set the webhook once after deploying: `curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://yourapp.com/telegram/webhook"`

Important:
- Index tickers (NDX, SPX) on TwelveData may require a paid plan depending on your account — verify against your key before relying on them.
- All candles used for analysis are completed candles where the provider exposes completion state.
- Fractal swing confirmation inherently requires candles to the right of the swing; this is safe for live analysis but historical backtests must timestamp swing confirmation correctly.
