"""Generate finite-game payoff data, without computing equilibria or PoA."""

import argparse
import csv
import hashlib
import json
import platform
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from itertools import product
from math import fsum, isfinite
from pathlib import Path
from time import perf_counter

from project.model import Dispatch, Generator, clear_market, physical_benchmarks


ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILES = ("project/__init__.py", "project/model.py", "project/run_pilot.py")


@dataclass(frozen=True)
class PilotConfig:
    name: str
    demand_mwh: float
    generators: tuple[Generator, ...]
    bid_coefficients: tuple[float, ...]
    balance_tolerance_mwh: float
    cost_tolerance_eur: float
    marginal_tolerance_eur_per_mwh: float
    source_bytes: bytes


def _require_keys(value: object, keys: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must contain exactly: {', '.join(sorted(keys))}")


def load_config(path: Path) -> PilotConfig:
    source = path.read_bytes()
    data = json.loads(source)
    _require_keys(
        data,
        {
            "name",
            "interval_hours",
            "demand_mwh",
            "capacities_mwh",
            "true_cost_coefficients",
            "blocks_per_generator",
            "bid_coefficients",
            "tolerances",
        },
        "configuration",
    )
    tolerances = data["tolerances"]
    _require_keys(
        tolerances,
        {"balance_mwh", "cost_eur", "marginal_price_eur_per_mwh"},
        "tolerances",
    )
    if not isinstance(data["name"], str) or not data["name"].strip():
        raise ValueError("configuration name must be a nonempty string")
    if isinstance(data["interval_hours"], bool) or data["interval_hours"] != 1:
        raise ValueError("this pilot requires a one-hour interval")
    for label, value in (("demand_mwh", data["demand_mwh"]), *tolerances.items()):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or value <= 0
        ):
            raise ValueError(f"{label} must be a positive finite number")
    for label in ("capacities_mwh", "true_cost_coefficients", "bid_coefficients"):
        if not isinstance(data[label], list) or not data[label]:
            raise ValueError(f"{label} must be a nonempty list")
    if len(data["capacities_mwh"]) != len(data["true_cost_coefficients"]):
        raise ValueError("one true coefficient is required per capacity")
    generators = tuple(
        Generator(coefficient, capacity, data["blocks_per_generator"])
        for coefficient, capacity in zip(
            data["true_cost_coefficients"], data["capacities_mwh"], strict=True
        )
    )
    bids = tuple(data["bid_coefficients"])
    clear_market(
        [bids[0]] * len(generators), data["capacities_mwh"], data["demand_mwh"]
    )
    for bid in bids:
        if (
            isinstance(bid, bool)
            or not isinstance(bid, (int, float))
            or not isfinite(bid)
            or bid <= 0
        ):
            raise ValueError("bid coefficients must be positive finite numbers")
    if tuple(sorted(set(bids))) != bids:
        raise ValueError("bid coefficients must be strictly increasing")
    if any(generator.coefficient not in bids for generator in generators):
        raise ValueError("the bid menu must include every truthful quadratic coefficient")
    return PilotConfig(
        data["name"],
        data["demand_mwh"],
        generators,
        bids,
        tolerances["balance_mwh"],
        tolerances["cost_eur"],
        tolerances["marginal_price_eur_per_mwh"],
        source,
    )


def _check_dispatch(
    dispatch: Dispatch, bids: tuple[float, ...], config: PilotConfig
) -> dict[str, float]:
    balance = abs(fsum(dispatch.quantities_mwh) - config.demand_mwh)
    capacity_violation = 0.0
    marginal_violation = 0.0
    if not isfinite(dispatch.price_eur_per_mwh):
        raise ValueError("market clearing returned a nonfinite price")
    for quantity, bid, generator in zip(
        dispatch.quantities_mwh, bids, config.generators, strict=True
    ):
        if not isfinite(quantity):
            raise ValueError("market clearing returned a nonfinite quantity")
        capacity_violation = max(
            capacity_violation, -quantity, quantity - generator.capacity_mwh
        )
        marginal = bid * quantity
        if quantity == generator.capacity_mwh:
            violation = max(0.0, marginal - dispatch.price_eur_per_mwh)
        elif quantity == 0:
            violation = max(0.0, dispatch.price_eur_per_mwh)
        else:
            violation = abs(marginal - dispatch.price_eur_per_mwh)
        marginal_violation = max(marginal_violation, violation)
    if balance > config.balance_tolerance_mwh:
        raise ValueError(f"demand-balance residual exceeds tolerance: {balance}")
    if capacity_violation > config.balance_tolerance_mwh:
        raise ValueError(f"capacity violation exceeds tolerance: {capacity_violation}")
    if marginal_violation > config.marginal_tolerance_eur_per_mwh:
        raise ValueError(f"marginal-price residual exceeds tolerance: {marginal_violation}")
    return {
        "max_balance_residual_mwh": balance,
        "max_capacity_violation_mwh": capacity_violation,
        "max_marginal_residual_eur_per_mwh": marginal_violation,
    }


def _source_provenance() -> dict[str, object]:
    revision = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", *SOURCE_FILES],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain", "--", *SOURCE_FILES],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return {
        "code_revision": revision,
        "uncommitted_source_changes": bool(status),
        "source_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in SOURCE_FILES
        },
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def run_pilot(config_path: Path, output_dir: Path) -> None:
    started = datetime.now(timezone.utc).isoformat()
    timer = perf_counter()
    config = load_config(config_path)
    generators = config.generators
    capacities = tuple(generator.capacity_mwh for generator in generators)
    physical = physical_benchmarks(generators, config.demand_mwh)
    for benchmark in physical.values():
        balance_error = abs(fsum(benchmark.quantities_mwh) - config.demand_mwh)
        if balance_error > config.balance_tolerance_mwh:
            raise ValueError("physical benchmark does not meet demand")
        if not isfinite(benchmark.total_cost_eur) or benchmark.total_cost_eur <= 0:
            raise ValueError("physical benchmark must have a positive finite cost")

    rows: list[dict[str, int | float]] = []
    diagnostics = {
        "max_balance_residual_mwh": 0.0,
        "max_capacity_violation_mwh": 0.0,
        "max_marginal_residual_eur_per_mwh": 0.0,
    }
    reference = None
    true_bids = tuple(generator.coefficient for generator in generators)
    profiles = product(config.bid_coefficients, repeat=len(generators))
    for profile_id, bids in enumerate(profiles):
        dispatch = clear_market(bids, capacities, config.demand_mwh)
        residuals = _check_dispatch(dispatch, bids, config)
        for name, value in residuals.items():
            diagnostics[name] = max(diagnostics[name], value)
        row: dict[str, int | float] = {
            "profile_id": profile_id,
            "price_eur_per_mwh": dispatch.price_eur_per_mwh,
        }
        for index, (bid, quantity) in enumerate(zip(bids, dispatch.quantities_mwh), 1):
            row[f"bid_{index}_eur_per_mwh2"] = bid
            row[f"output_{index}_mwh"] = quantity
        for kind in ("quadratic", "block"):
            costs = tuple(
                generator.quadratic_cost(quantity)
                if kind == "quadratic"
                else generator.block_cost(quantity)
                for generator, quantity in zip(generators, dispatch.quantities_mwh)
            )
            total_cost = fsum(costs)
            if not isfinite(total_cost):
                raise ValueError(f"profile {profile_id}: nonfinite {kind} cost")
            if total_cost < physical[kind].total_cost_eur - config.cost_tolerance_eur:
                raise ValueError(
                    f"profile {profile_id}: cost below the {kind} physical optimum"
                )
            row[f"{kind}_cost_eur"] = total_cost
            for index, (quantity, cost) in enumerate(
                zip(dispatch.quantities_mwh, costs), 1
            ):
                row[f"{kind}_profit_{index}_eur"] = (
                    dispatch.price_eur_per_mwh * quantity - cost
                )
        cost_gap = row["block_cost_eur"] - row["quadratic_cost_eur"]
        if cost_gap < -config.cost_tolerance_eur:
            raise ValueError("secant block costs must not fall below quadratic costs")
        rows.append(row)
        if bids == true_bids:
            reference = row

    if reference is None:
        raise ValueError("truthful quadratic profile is missing from the payoff table")
    reference_error = abs(
        reference["quadratic_cost_eur"] - physical["quadratic"].total_cost_eur
    )
    if reference_error > config.cost_tolerance_eur:
        raise ValueError("truthful quadratic bids do not attain the physical optimum")
    diagnostics["truthful_quadratic_cost_residual_eur"] = reference_error
    cases = {}
    for kind in ("quadratic", "block"):
        best = min(rows, key=lambda row: row[f"{kind}_cost_eur"])
        cases[kind] = {
            "physical_optimum": asdict(physical[kind]),
            "grid_attainable": {
                "profile_id": best["profile_id"],
                "bids_eur_per_mwh2": [
                    best[f"bid_{index}_eur_per_mwh2"]
                    for index in range(1, len(generators) + 1)
                ],
                "quantities_mwh": [
                    best[f"output_{index}_mwh"] for index in range(1, len(generators) + 1)
                ],
                "total_cost_eur": best[f"{kind}_cost_eur"],
            },
            "attainability_ratio": (
                best[f"{kind}_cost_eur"] / physical[kind].total_cost_eur
            ),
        }

    provenance = _source_provenance()
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "payoffs.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    _write_json(
        output_dir / "benchmarks.json",
        {
            "scope": "physical_and_grid_attainability_only",
            "cases": cases,
            "quadratic_reference_profile": reference,
            "diagnostics": diagnostics,
        },
    )
    _write_json(
        output_dir / "metadata.json",
        {
            "scenario": config.name,
            "configuration": json.loads(config.source_bytes),
            "configuration_sha256": hashlib.sha256(config.source_bytes).hexdigest(),
            "profile_count": len(rows),
            "generator_count": len(generators),
            "bid_points_per_generator": len(config.bid_coefficients),
            "clearing_method": "capacity_constrained_water_filling",
            "block_optimum_method": "merit_order_with_generator_order_ties",
            "grid_cost_tie_rule": "first_profile_in_lexicographic_bid_order",
            "solver": None,
            "equilibria_computed": False,
            **provenance,
        },
    )
    elapsed = perf_counter() - timer
    _write_json(
        output_dir / "run-info.json",
        {
            "started_utc": started,
            "elapsed_seconds": elapsed,
            "python_version": platform.python_version(),
            "code_revision": provenance["code_revision"],
            "configuration_sha256": hashlib.sha256(config.source_bytes).hexdigest(),
            "command": [
                "python3", "-m", "project.run_pilot",
                "--config", str(config_path),
                "--output-dir", str(output_dir),
            ],
        },
    )
    print(f"Generated {len(rows)} profiles in {elapsed:.3f}s: {output_dir}")
    for kind, case in cases.items():
        print(
            f"{kind}: physical={case['physical_optimum']['total_cost_eur']:.6f} EUR, "
            f"grid={case['grid_attainable']['total_cost_eur']:.6f} EUR, "
            f"attainability={case['attainability_ratio']:.9f}"
        )
    print("No equilibria, CCE inefficiency, or PoA bounds have been computed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "project/pilot.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "project/results")
    args = parser.parse_args()
    try:
        run_pilot(args.config, args.output_dir)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
