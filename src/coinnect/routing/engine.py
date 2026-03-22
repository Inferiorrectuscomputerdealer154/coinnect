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
    min_amount: float = 0.01
    max_amount: float = 1_000_000.0


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
    exchange_rate: float = 1.0  # units of to_currency per 1 from_currency
    min_amount: float = 0.01    # minimum send amount in from_currency
    max_amount: float = 1_000_000.0  # maximum send amount in from_currency


def build_graph(edges: list[Edge]) -> dict[str, list[Edge]]:
    """Build adjacency list from edges."""
    graph: dict[str, list[Edge]] = {}
    for edge in edges:
        graph.setdefault(edge.from_currency, []).append(edge)
    return graph


def _dijkstra(
    graph: dict[str, list[Edge]],
    start: str,
    end: str,
    amount: float,
    optimize: str = "cost",  # "cost" or "time"
    max_routes: int = 5,
    max_steps: int = 3,
) -> list[tuple[float, float, list[Edge]]]:
    """Single Dijkstra run optimizing by cost or time."""
    counter = 0
    heap = [(0.0, counter, 0, start, amount, [])]
    results = []
    visited_states: dict[tuple, float] = {}

    while heap and len(results) < max_routes:
        priority, _, steps, curr, curr_amount, path = heapq.heappop(heap)

        state = (curr, steps)
        if state in visited_states and visited_states[state] <= priority:
            continue
        visited_states[state] = priority

        if curr == end and path:
            total_cost = sum(e.fee_pct for e in path)
            results.append((total_cost, curr_amount, path))
            continue

        if steps >= max_steps:
            continue

        for edge in graph.get(curr, []):
            new_amount = curr_amount * edge.exchange_rate * (1 - edge.fee_pct / 100)
            new_priority = priority + (edge.fee_pct if optimize == "cost" else edge.estimated_minutes)
            counter += 1
            heapq.heappush(heap, (
                new_priority,
                counter,
                steps + 1,
                edge.to_currency,
                new_amount,
                path + [edge],
            ))

    return results


def find_routes(
    graph: dict[str, list[Edge]],
    start: str,
    end: str,
    amount: float,
    max_routes: int = 12,
    max_steps: int = 3,
) -> list[tuple[float, float, list[Edge]]]:
    """
    Find diverse routes — collects all direct single-step routes, then uses
    Dijkstra for multi-step paths (cost and time optimized). Merges and deduplicates.
    Returns list of (total_cost_pct, amount_received, path).
    """
    # 1. All direct routes (single-step, any provider) — sorted by cost
    direct: list[tuple[float, float, list[Edge]]] = []
    for edge in graph.get(start, []):
        if edge.to_currency == end:
            received = amount * edge.exchange_rate * (1 - edge.fee_pct / 100)
            direct.append((edge.fee_pct, received, [edge]))
    direct.sort(key=lambda x: x[0])

    # 2. Multi-step routes via Dijkstra (max_steps >= 2)
    by_cost = _dijkstra(graph, start, end, amount, optimize="cost", max_routes=5, max_steps=max_steps)
    by_time = _dijkstra(graph, start, end, amount, optimize="time", max_routes=3, max_steps=max_steps)
    multi_step = [r for r in by_cost + by_time if len(r[2]) > 1]

    # 3. Merge, deduplicating by path signature
    seen: set[tuple] = set()
    merged = []
    for cost, received, path in direct + multi_step:
        sig = tuple((e.from_currency, e.to_currency, e.via) for e in path)
        if sig not in seen:
            seen.add(sig)
            merged.append((cost, received, path))

    return merged[:max_routes]


def build_quote(
    edges: list[Edge],
    from_currency: str,
    to_currency: str,
    amount: float,
) -> QuoteResult:
    # Only filter below minimum (don't hide providers that cap at lower amounts)
    valid_edges = [e for e in edges if amount >= e.min_amount]
    graph = build_graph(valid_edges)
    raw_routes = find_routes(graph, from_currency, to_currency, amount)

    if not raw_routes:
        return QuoteResult(
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            generated_at=datetime.now(UTC),
            routes=[],
        )

    # Identify special routes
    cheapest_idx = min(range(len(raw_routes)), key=lambda i: raw_routes[i][0])
    fastest_idx = min(range(len(raw_routes)), key=lambda i: sum(e.estimated_minutes for e in raw_routes[i][2]))

    # Assign labels: Cheapest + Fastest featured, rest as Option N
    featured_indices = []
    for idx in [cheapest_idx, fastest_idx]:
        if idx not in featured_indices:
            featured_indices.append(idx)

    labels = ["Cheapest", "Fastest"]
    featured_order = [(idx, labels[i]) for i, idx in enumerate(featured_indices)]
    extra_indices = [i for i in range(len(raw_routes)) if i not in set(featured_indices)]
    all_ordered = featured_order + [(i, f"Option {j+1}") for j, i in enumerate(extra_indices)]

    routes = []
    for rank, (raw_idx, label) in enumerate(all_ordered, start=1):
        total_cost, received, path = raw_routes[raw_idx]
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
                min_amount=e.min_amount,
                max_amount=e.max_amount,
            )
            for j, e in enumerate(path)
        ]
        routes.append(Route(
            rank=rank,
            label=label,
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
