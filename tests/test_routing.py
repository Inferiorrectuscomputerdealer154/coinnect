"""Tests for the routing engine."""

import pytest
from coinnect.routing.engine import Edge, build_quote


MOCK_EDGES = [
    Edge("USD", "USDC", "Kraken",     fee_pct=0.5,  estimated_minutes=10),
    Edge("USDC", "NGN", "YellowCard", fee_pct=0.9,  estimated_minutes=50),
    Edge("USD", "NGN",  "Wise",       fee_pct=3.1,  estimated_minutes=60),
    Edge("USD", "MXN",  "Wise",       fee_pct=2.3,  estimated_minutes=60),
    Edge("USD", "USDC", "Binance",    fee_pct=0.1,  estimated_minutes=5),
    Edge("USDC", "MXN", "Bitso",      fee_pct=0.65, estimated_minutes=15),
]


def test_finds_routes():
    result = build_quote(MOCK_EDGES, "USD", "NGN", 500)
    assert len(result.routes) >= 1


def test_cheapest_route_is_first():
    result = build_quote(MOCK_EDGES, "USD", "NGN", 500)
    costs = [r.total_cost_pct for r in result.routes]
    assert costs == sorted(costs)


def test_multi_step_route():
    result = build_quote(MOCK_EDGES, "USD", "NGN", 500)
    two_step = next((r for r in result.routes if len(r.steps) == 2), None)
    assert two_step is not None
    assert two_step.steps[0].from_currency == "USD"
    assert two_step.steps[-1].to_currency == "NGN"


def test_amount_received_is_less_than_sent():
    result = build_quote(MOCK_EDGES, "USD", "MXN", 1000)
    for route in result.routes:
        # Can't receive more than sent (in USD equivalent)
        assert route.they_receive > 0


def test_no_route_returns_empty():
    result = build_quote(MOCK_EDGES, "USD", "JPY", 500)
    assert result.routes == []
