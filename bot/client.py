"""Thin wrapper around python-binance's UMFutures client, pinned to the testnet."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DEFAULT_TESTNET_URL = "https://testnet.binancefuture.com"


class ClientConfigError(RuntimeError):
    """Raised when API credentials are missing or malformed."""


class BinanceFuturesClient:
    """
    Wraps python-binance's `Client` for Binance Futures Testnet (USDT-M).

    Routes all futures REST calls to the testnet base URL and centralises
    request/response logging plus a friendlier error surface.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
    ) -> None:
        load_dotenv()

        self.api_key = api_key or os.getenv("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET", "")
        self.base_url = base_url or os.getenv("BINANCE_BASE_URL", DEFAULT_TESTNET_URL)

        if not self.api_key or not self.api_secret:
            raise ClientConfigError(
                "Missing API credentials. Set BINANCE_API_KEY and BINANCE_API_SECRET "
                "in your .env file (see .env.example)."
            )

        self._client = Client(self.api_key, self.api_secret, testnet=True)
        # python-binance defaults the futures endpoint to the testnet when
        # `testnet=True`, but pin it explicitly so the URL is auditable.
        self._client.FUTURES_URL = f"{self.base_url.rstrip('/')}/fapi"
        self._sync_time()
        logger.info("Binance Futures client initialised (base_url=%s)", self.base_url)

    def _sync_time(self) -> None:
        """
        Adjust for local clock drift.

        Binance rejects signed requests whose timestamp is more than ~1s ahead
        of server time (error -1021). We fetch server time once and let
        python-binance subtract the offset from every subsequent timestamp.
        """
        try:
            server_time = self._client.futures_time()["serverTime"]
            local_time = int(time.time() * 1000)
            # python-binance computes the request timestamp as
            #   `int(time.time() * 1000 + timestamp_offset)`,
            # so the correction is `server - local` (negative if our clock is ahead).
            offset = server_time - local_time
            self._client.timestamp_offset = offset
            logger.info(
                "Time sync: local=%d server=%d offset=%d ms",
                local_time, server_time, offset,
            )
        except Exception as exc:  # noqa: BLE001 — non-fatal, surface and continue
            logger.warning("Failed to sync time with Binance, proceeding anyway: %s", exc)

    # --- Account / market data ----------------------------------------------

    def ping(self) -> dict[str, Any]:
        logger.debug("Ping testnet")
        return self._client.futures_ping()

    def get_symbol_info(self, symbol: str) -> dict[str, Any] | None:
        info = self._client.futures_exchange_info()
        for s in info.get("symbols", []):
            if s.get("symbol") == symbol:
                return s
        return None

    # --- Orders --------------------------------------------------------------

    def place_order(self, **params: Any) -> dict[str, Any]:
        """
        Send an order to Binance Futures. Caller is responsible for assembling
        the parameter dict (see bot.orders).
        """
        redacted = {k: v for k, v in params.items() if k != "signature"}
        logger.info("Order request: %s", redacted)
        try:
            response = self._client.futures_create_order(**params)
        except BinanceAPIException as exc:
            logger.error(
                "Binance API error: code=%s message=%s status=%s",
                exc.code,
                exc.message,
                exc.status_code,
            )
            raise
        except BinanceRequestException as exc:
            logger.error("Binance request error: %s", exc)
            raise
        except Exception:
            logger.exception("Unexpected error placing order")
            raise

        logger.info("Order response: %s", response)
        return response
