"""
Route engine — finds cheapest/fastest paths between currencies.
Uses Dijkstra on a live currency graph built from exchange rates.
"""

import heapq
from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class Step:
    step: int
    from_currency: str
    to_currency: str
    via: str
    fee_pct: float
    estimated_minutes: int
    instructions: str


@dataclass
class Route:
    rank: int
    label: str
    total_cost_pct: float
    total_time_minutes: int
    you_send: float
    they_receive: float
    they_receive_currency: str
    steps: list[Step]


@dataclass
class QuoteResult:
    from_currency: str
    to_currency: str
    amount: float
    generated_at: datetime
    routes: list[Route]


@dataclass
class Edge:
    """A single conversion step between two currencies via an exchange."""
    from_currency: str
    to_currency: str
    via: str           # exchange name
    fee_pct: float     # total cost as percentage (fee + spread)
    estimated_minutes: int
    instructions: str = ""


def build_graph(edges: list[Edge]) -> dict[str, list[Edge]]:
    """Build adjacency list from edges."""
    graph: dict[str, list[Edge]] = {}
    for edge in edges:
        graph.setdefault(edge.from_currency, []).append(edge)
    return graph


def find_routes(
    graph: dict[str, list[Edge]],
    start: str,
    end: str,
    amount: float,
    max_routes: int = 3,
    max_steps: int = 3,
) -> list[tuple[float, float, list[Edge]]]:
    """
    Dijkstra to find cheapest routes.
    Returns list of (total_cost_pct, amount_received, path).
    """
    # heap: (total_cost, -amount_received, steps_count, current, amount, path)
    heap = [(0.0, -amount, 0, start, amount, [])]
    results = []
    visited_states = {}

    while heap and len(results) < max_routes:
        cost, neg_received, steps, curr, curr_amount, path = heapq.heappop(heap)

        state = (curr, steps)
        if state in visited_states and visited_states[state] <= cost:
            continue
        visited_states[state] = cost

        if curr == end and path:
            results.append((cost, curr_amount, path))
            continue

        if steps >= max_steps:
            continue

        for edge in graph.get(curr, []):
            new_amount = curr_amount * (1 - edge.fee_pct / 100)
            new_cost = cost + edge.fee_pct
            heapq.heappush(heap, (
                new_cost,
                -new_amount,
                steps + 1,
                edge.to_currency,
                new_amount,
                path + [edge],
            ))

    return results


def build_quote(
    edges: list[Edge],
    from_currency: str,
    to_currency: str,
    amount: float,
) -> QuoteResult:
    graph = build_graph(edges)
    raw_routes = find_routes(graph, from_currency, to_currency, amount)

    routes = []
    labels = ["Cheapest", "Balanced", "Fastest"]

    for i, (total_cost, received, path) in enumerate(raw_routes):
        total_minutes = sum(e.estimated_minutes for e in path)
        steps = [
            Step(
                step=j + 1,
                from_currency=e.from_currency,
                to_currency=e.to_currency,
                via=e.via,
                fee_pct=e.fee_pct,
                estimated_minutes=e.estimated_minutes,
                instructions=e.instructions or f"Convert {e.from_currency} to {e.to_currency} via {e.via}",
            )
            for j, e in enumerate(path)
        ]
        routes.append(Route(
            rank=i + 1,
            label=labels[i] if i < len(labels) else f"Route {i+1}",
            total_cost_pct=round(total_cost, 2),
            total_time_minutes=total_minutes,
            you_send=amount,
            they_receive=round(received, 2),
            they_receive_currency=to_currency,
            steps=steps,
        ))

    return QuoteResult(
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
        generated_at=datetime.now(UTC),
        routes=routes,
    )
