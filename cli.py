"""CLI entry point for the Binance Futures Testnet trading bot.

Examples
--------
  python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001
  python cli.py limit  --symbol BTCUSDT --side SELL --quantity 0.001 --price 70000
  python cli.py stop-limit --symbol BTCUSDT --side SELL --quantity 0.001 \\
                          --price 64000 --stop-price 64500
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Sequence

from binance.exceptions import BinanceAPIException, BinanceRequestException

from bot.client import BinanceFuturesClient, ClientConfigError
from bot.logging_config import setup_logging
from bot.orders import build_order, format_response, place_order
from bot.validators import ValidationError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place orders on Binance Futures Testnet (USDT-M).",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override LOG_LEVEL from .env",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def _common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--symbol", required=True, help="e.g. BTCUSDT")
        p.add_argument("--side", required=True, choices=["BUY", "SELL"])
        p.add_argument("--quantity", required=True, help="order quantity (base asset)")

    market = sub.add_parser("market", help="place a MARKET order")
    _common(market)

    limit = sub.add_parser("limit", help="place a LIMIT order (GTC)")
    _common(limit)
    limit.add_argument("--price", required=True, help="limit price")

    stop = sub.add_parser("stop-limit", help="place a STOP-LIMIT order (bonus)")
    _common(stop)
    stop.add_argument("--price", required=True, help="limit price after trigger")
    stop.add_argument("--stop-price", required=True, help="trigger price")

    return parser


_COMMAND_TO_TYPE = {
    "market": "MARKET",
    "limit": "LIMIT",
    "stop-limit": "STOP_LIMIT",
}


def _print_banner(req) -> None:
    print()
    print("=" * 60)
    print("  ORDER REQUEST")
    print("=" * 60)
    print(f"  {req.summary()}")
    print()


def _print_success(response) -> None:
    print("=" * 60)
    print("  ORDER RESPONSE  [SUCCESS]")
    print("=" * 60)
    print(format_response(response))
    print("=" * 60)
    print()


def _print_failure(message: str) -> None:
    print("=" * 60)
    print("  ORDER FAILED")
    print("=" * 60)
    print(f"  {message}")
    print("=" * 60)
    print()


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    log = setup_logging(args.log_level)
    log.debug("CLI args: %s", vars(args))

    order_type = _COMMAND_TO_TYPE[args.command]

    try:
        req = build_order(
            symbol=args.symbol,
            side=args.side,
            order_type=order_type,
            quantity=args.quantity,
            price=getattr(args, "price", None),
            stop_price=getattr(args, "stop_price", None),
        )
    except ValidationError as exc:
        log.error("Invalid input: %s", exc)
        _print_failure(f"Invalid input: {exc}")
        return 2

    _print_banner(req)

    try:
        client = BinanceFuturesClient()
    except ClientConfigError as exc:
        log.error("Client config error: %s", exc)
        _print_failure(str(exc))
        return 3

    try:
        response = place_order(client, req)
    except BinanceAPIException as exc:
        _print_failure(f"Binance API error [{exc.code}]: {exc.message}")
        return 4
    except BinanceRequestException as exc:
        _print_failure(f"Binance request error: {exc}")
        return 5
    except Exception as exc:  # noqa: BLE001 — surface any unexpected failure to the user
        logging.getLogger(__name__).exception("Unexpected failure")
        _print_failure(f"Unexpected error: {exc}")
        return 1

    _print_success(response)
    return 0


if __name__ == "__main__":
    sys.exit(main())
