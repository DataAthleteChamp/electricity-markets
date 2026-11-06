"""Quadratic bidding and continuous, convex block-cost benchmarks."""

from dataclasses import dataclass
from math import fsum, isfinite
from typing import Sequence


def _finite_number(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    if not isfinite(value):
        raise ValueError(f"{name} must be a finite number")


def _positive_number(value: float, name: str) -> None:
    _finite_number(value, name)
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _validate_market(capacities: Sequence[float], demand: float) -> None:
    if not capacities:
        raise ValueError("at least one generator is required")
    for capacity in capacities:
        _positive_number(capacity, "capacity")
    _finite_number(demand, "demand")
    if not 0 <= demand <= fsum(capacities):
        raise ValueError("demand must lie between zero and total capacity")


@dataclass(frozen=True)
class Generator:
    coefficient: float
    capacity_mwh: float
    blocks: int

    def __post_init__(self) -> None:
        _positive_number(self.coefficient, "true cost coefficient")
        _positive_number(self.capacity_mwh, "capacity")
        if isinstance(self.blocks, bool) or not isinstance(self.blocks, int):
            raise ValueError("block count must be a positive integer")
        if self.blocks <= 0:
            raise ValueError("block count must be a positive integer")

    def _validate_quantity(self, quantity: float) -> None:
        _finite_number(quantity, "quantity")
        if not 0 <= quantity <= self.capacity_mwh:
            raise ValueError("quantity must lie between zero and capacity")

    def quadratic_cost(self, quantity: float) -> float:
        self._validate_quantity(quantity)
        return 0.5 * self.coefficient * quantity**2

    def block_segments(self) -> tuple[tuple[float, float], ...]:
        segments = []
        for index in range(self.blocks):
            lower = self.capacity_mwh * index / self.blocks
            upper = self.capacity_mwh * (index + 1) / self.blocks
            marginal_cost = 0.5 * self.coefficient * (lower + upper)
            segments.append((upper - lower, marginal_cost))
        return tuple(segments)

    def block_cost(self, quantity: float) -> float:
        self._validate_quantity(quantity)
        index = min(int(quantity / self.capacity_mwh * self.blocks), self.blocks - 1)
        lower = self.capacity_mwh * index / self.blocks
        upper = self.capacity_mwh * (index + 1) / self.blocks
        marginal_cost = 0.5 * self.coefficient * (lower + upper)
        return self.quadratic_cost(lower) + marginal_cost * (quantity - lower)


@dataclass(frozen=True)
class Dispatch:
    quantities_mwh: tuple[float, ...]
    price_eur_per_mwh: float


@dataclass(frozen=True)
class Benchmark:
    quantities_mwh: tuple[float, ...]
    total_cost_eur: float


def clear_market(
    bids: Sequence[float], capacities_mwh: Sequence[float], demand_mwh: float
) -> Dispatch:
    """Clear bids b_i(q) = 0.5 * h_i * q^2 by capacity-constrained water filling."""
    _validate_market(capacities_mwh, demand_mwh)
    if len(bids) != len(capacities_mwh):
        raise ValueError("one bid coefficient is required per generator")
    for bid in bids:
        _positive_number(bid, "bid coefficient")

    if demand_mwh == 0:
        return Dispatch(tuple(0.0 for _ in bids), 0.0)
    if demand_mwh == fsum(capacities_mwh):
        # At full capacity the dual price is not unique; use its smallest value.
        price = max(bid * capacity for bid, capacity in zip(bids, capacities_mwh))
        return Dispatch(tuple(capacities_mwh), price)

    free = list(range(len(bids)))
    quantities = [0.0] * len(bids)
    remaining = demand_mwh
    while free:
        price = remaining / fsum(1.0 / bids[index] for index in free)
        capped = [
            index
            for index in free
            if price / bids[index] >= capacities_mwh[index]
        ]
        if not capped:
            for index in free:
                quantities[index] = price / bids[index]
            break
        for index in capped:
            quantities[index] = capacities_mwh[index]
        remaining = demand_mwh - fsum(quantities)
        free = [index for index in free if index not in capped]

    return Dispatch(tuple(quantities), price)


def block_optimal_dispatch(
    generators: Sequence[Generator], demand_mwh: float
) -> tuple[float, ...]:
    """Fill true marginal-cost blocks in merit order; ties use generator order."""
    _validate_market([generator.capacity_mwh for generator in generators], demand_mwh)
    segments = sorted(
        (marginal_cost, index, block, width)
        for index, generator in enumerate(generators)
        for block, (width, marginal_cost) in enumerate(generator.block_segments())
    )
    quantities = [0.0] * len(generators)
    remaining = demand_mwh
    for _, index, _, width in segments:
        if remaining <= 0:
            break
        amount = min(width, remaining)
        quantities[index] += amount
        remaining -= amount
    return tuple(quantities)


def physical_benchmarks(
    generators: Sequence[Generator], demand_mwh: float
) -> dict[str, Benchmark]:
    capacities = [generator.capacity_mwh for generator in generators]
    quadratic = clear_market(
        [generator.coefficient for generator in generators], capacities, demand_mwh
    ).quantities_mwh
    block = block_optimal_dispatch(generators, demand_mwh)
    return {
        "quadratic": Benchmark(
            quadratic,
            fsum(
                generator.quadratic_cost(quantity)
                for generator, quantity in zip(generators, quadratic)
            ),
        ),
        "block": Benchmark(
            block,
            fsum(
                generator.block_cost(quantity)
                for generator, quantity in zip(generators, block)
            ),
        ),
    }
