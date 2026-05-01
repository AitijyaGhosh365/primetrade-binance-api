# Trading Bot — Binance Futures Testnet (USDT-M)

A small, structured Python CLI that places **MARKET**, **LIMIT**, and (bonus) **STOP-LIMIT**
orders on the Binance Futures Testnet. Built for the Primetrade.ai Python Developer
application task.

## Features

- Places **MARKET** and **LIMIT** orders on USDT-M Futures Testnet
- Supports both **BUY** and **SELL** sides
- **Bonus**: third order type — **STOP-LIMIT**
- Validates input *before* hitting the API (symbol, side, type, quantity, price)
- Logs every request, response, and error to `logs/trading_bot.log`
- Clean separation between API client, order logic, validators, and the CLI

## Project layout

```
primetrade/
├── bot/
│   ├── __init__.py
│   ├── client.py            # Binance client wrapper (testnet-pinned)
│   ├── orders.py            # OrderRequest + place_order
│   ├── validators.py        # input validation helpers
│   └── logging_config.py    # rotating file + console logging
├── logs/                    # log output (rotated)
├── cli.py                   # CLI entry point (argparse)
├── .env.example             # template for credentials
├── requirements.txt
├── ARCHITECTURE.md
└── README.md
```

## Setup

1. **Create a Binance Futures Testnet account** at <https://testnet.binancefuture.com/>
   and generate API key / secret.

2. **Clone & install**:

   ```bash
   git clone <repo-url> primetrade
   cd primetrade
   python -m venv .venv
   source .venv/bin/activate     # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure credentials** — copy the template and paste your testnet keys:

   ```bash
   cp .env.example .env
   # edit .env and fill BINANCE_API_KEY / BINANCE_API_SECRET
   ```

   The shipped `.env` is intentionally blank — fill in real keys before running.

## Usage

The CLI uses subcommands per order type. Common flags: `--symbol`, `--side`, `--quantity`.

### Market order

```bash
python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001
```

### Limit order

```bash
python cli.py limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 70000
```

### Stop-limit order (bonus)

```bash
python cli.py stop-limit --symbol BTCUSDT --side SELL \
    --quantity 0.001 --price 64000 --stop-price 64500
```

`--stop-price` triggers the order; `--price` is the limit price posted once triggered.

### Optional flags

- `--log-level DEBUG|INFO|WARNING|ERROR` — overrides `LOG_LEVEL` from `.env`.

### Sample output

```
============================================================
  ORDER REQUEST
============================================================
  symbol=BTCUSDT side=BUY type=MARKET quantity=0.001

============================================================
  ORDER RESPONSE  [SUCCESS]
============================================================
  orderId      4093284
  status       FILLED
  executedQty  0.001
  avgPrice     67234.50
  type         MARKET
  side         BUY
============================================================
```

Failures (validation, API errors, network issues) print a clear `ORDER FAILED`
banner with the reason, and return a non-zero exit code.

## Logs

All API requests, responses, and errors land in `logs/trading_bot.log`
(rotated at ~2 MB, 5 backups kept). The console shows a concise summary at the
configured `LOG_LEVEL`.

Two example log files are included with the deliverable:

- `logs/trading_bot.log` — covers a MARKET order
- `logs/trading_bot.log.1` — covers a LIMIT order

## Exit codes

| Code | Meaning                           |
|-----:|-----------------------------------|
| 0    | Order placed successfully         |
| 1    | Unexpected runtime error          |
| 2    | Input validation failed           |
| 3    | Missing/invalid API credentials   |
| 4    | Binance API rejected the order    |
| 5    | Network / request transport error |

## Assumptions

- **Testnet only.** The client is pinned to `https://testnet.binancefuture.com`.
  No code path hits production.
- **USDT-M Futures only.** Symbols like `BTCUSDT`, `ETHUSDT`. Coin-M is out of scope.
- **LIMIT orders use `timeInForce=GTC`.** Other TIF values aren't exposed via the CLI.
- **STOP-LIMIT** uses `workingType=MARK_PRICE` so triggers fire on Binance's mark
  price (more stable than last price during volatility).
- **No leverage / margin management.** The bot assumes the testnet account is
  already configured (default isolated/cross, default leverage). Adjust on the
  testnet UI if needed.
- **Decimal precision.** Quantity and price are forwarded to Binance with
  trailing zeros stripped; the exchange enforces symbol-specific lot/tick sizes
  and will reject non-conforming values with a clear API error.

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the module diagram, request flow,
and design rationale.
