"""Order placement logic — assembles request params and delegates to the client."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from .validators import (
    normalize_order_type,
    normalize_side,
    normalize_symbol,
    positive_decimal,
    require_price_for_limit,
    require_stop_price,
)

if TYPE_CHECKING:
    from .client import BinanceFuturesClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrderRequest:
    """Validated, normalized order parameters ready for the API."""

    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None = None
    stop_price: Decimal | None = None

    def summary(self) -> str:
        parts = [
            f"symbol={self.symbol}",
            f"side={self.side}",
            f"type={self.order_type}",
            f"quantity={self.quantity}",
        ]
        if self.price is not None:
            parts.append(f"price={self.price}")
        if self.stop_price is not None:
            parts.append(f"stopPrice={self.stop_price}")
        return " ".join(parts)


def build_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
    stop_price=None,
) -> OrderRequest:
    """Validate raw user input and return a normalized OrderRequest."""
    sym = normalize_symbol(symbol)
    s = normalize_side(side)
    t = normalize_order_type(order_type)
    qty = positive_decimal(quantity, "quantity")
    p = require_price_for_limit(t, price)
    sp = require_stop_price(t, stop_price)
    return OrderRequest(
        symbol=sym, side=s, order_type=t, quantity=qty, price=p, stop_price=sp
    )


def _to_api_params(req: OrderRequest) -> dict[str, Any]:
    """Map an OrderRequest into Binance Futures REST parameters."""
    params: dict[str, Any] = {
        "symbol": req.symbol,
        "side": req.side,
        "quantity": format(req.quantity.normalize(), "f"),
    }

    if req.order_type == "MARKET":
        params["type"] = "MARKET"
    elif req.order_type == "LIMIT":
        params["type"] = "LIMIT"
        params["timeInForce"] = "GTC"
        params["price"] = format(req.price.normalize(), "f")  # type: ignore[union-attr]
    elif req.order_type == "STOP_LIMIT":
        # Binance Futures uses type=STOP for stop-limit (limit order triggered at stopPrice)
        params["type"] = "STOP"
        params["timeInForce"] = "GTC"
        params["price"] = format(req.price.normalize(), "f")  # type: ignore[union-attr]
        params["stopPrice"] = format(req.stop_price.normalize(), "f")  # type: ignore[union-attr]
        params["workingType"] = "MARK_PRICE"
    else:
        raise ValueError(f"Unsupported order type: {req.order_type}")

    return params


def place_order(client: "BinanceFuturesClient", req: OrderRequest) -> dict[str, Any]:
    """Submit a validated OrderRequest to the exchange."""
    params = _to_api_params(req)
    return client.place_order(**params)


def format_response(response: dict[str, Any]) -> str:
    """Pull the user-facing fields out of a Binance order response."""
    fields = [
        ("orderId", response.get("orderId")),
        ("status", response.get("status")),
        ("executedQty", response.get("executedQty")),
        ("avgPrice", response.get("avgPrice")),
        ("price", response.get("price")),
        ("type", response.get("type")),
        ("side", response.get("side")),
    ]
    return "\n".join(f"  {k:<12} {v}" for k, v in fields if v not in (None, ""))
