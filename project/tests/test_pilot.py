import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from itertools import product
from math import fsum
from pathlib import Path

from project.run_pilot import load_config, run_pilot


CONFIG = Path(__file__).resolve().parents[1] / "pilot.json"


class PilotTests(unittest.TestCase):
    def test_all_profiles_and_payoffs_against_independent_formulas(self):
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as temporary, redirect_stdout(io.StringIO()):
            output = Path(temporary)
            run_pilot(CONFIG, output)
            with (output / "payoffs.csv").open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
            benchmarks = json.loads((output / "benchmarks.json").read_text())
            metadata = json.loads((output / "metadata.json").read_text())
        self.assertEqual(len(rows), 343)
        self.assertEqual(metadata["profile_count"], 343)
        self.assertFalse(metadata["equilibria_computed"])
        self.assertEqual(
            {
                tuple(float(row[f"bid_{index}_eur_per_mwh2"]) for index in (1, 2, 3))
                for row in rows
            },
            set(product(config.bid_coefficients, repeat=3)),
        )
        for row in rows:
            quantities = [float(row[f"output_{index}_mwh"]) for index in (1, 2, 3)]
            price = float(row["price_eur_per_mwh"])
            self.assertAlmostEqual(fsum(quantities), config.demand_mwh, delta=1e-8)
            quadratic_costs = []
            block_costs = []
            for index, (quantity, generator) in enumerate(zip(quantities, config.generators), 1):
                bid = float(row[f"bid_{index}_eur_per_mwh2"])
                self.assertGreater(quantity, 0)
                self.assertLessEqual(quantity, generator.capacity_mwh)
                if quantity < generator.capacity_mwh:
                    self.assertAlmostEqual(bid * quantity, price, delta=1e-9)
                else:
                    self.assertLessEqual(bid * quantity, price + 1e-9)
                quadratic = 0.5 * generator.coefficient * quantity**2
                width = generator.capacity_mwh / generator.blocks
                block = fsum(
                    generator.coefficient * (segment + 0.5) * width
                    * min(width, max(0.0, quantity - segment * width))
                    for segment in range(generator.blocks)
                )
                quadratic_costs.append(quadratic)
                block_costs.append(block)
                for kind, cost in (("quadratic", quadratic), ("block", block)):
                    self.assertAlmostEqual(
                        float(row[f"{kind}_profit_{index}_eur"]),
                        price * quantity - cost,
                        delta=1e-6,
                    )
            for kind, costs in (("quadratic", quadratic_costs), ("block", block_costs)):
                self.assertAlmostEqual(
                    float(row[f"{kind}_cost_eur"]), fsum(costs), delta=1e-6
                )
        for kind in ("quadratic", "block"):
            self.assertAlmostEqual(
                benchmarks["cases"][kind]["grid_attainable"]["total_cost_eur"],
                min(float(row[f"{kind}_cost_eur"]) for row in rows),
                delta=1e-6,
            )
        self.assertAlmostEqual(
            benchmarks["cases"]["quadratic"]["physical_optimum"]["total_cost_eur"],
            7193.5776,
            delta=1e-6,
        )
        self.assertAlmostEqual(
            benchmarks["cases"]["block"]["physical_optimum"]["total_cost_eur"],
            66682 / 9,
            delta=1e-6,
        )
        self.assertAlmostEqual(
            benchmarks["quadratic_reference_profile"]["block_cost_eur"],
            7709.955555555556,
            delta=1e-6,
        )

    def test_regeneration_is_deterministic_except_local_run_information(self):
        with tempfile.TemporaryDirectory() as temporary, redirect_stdout(io.StringIO()):
            first, second = Path(temporary) / "first", Path(temporary) / "second"
            run_pilot(CONFIG, first)
            run_pilot(CONFIG, second)
            for filename in ("payoffs.csv", "benchmarks.json", "metadata.json"):
                self.assertEqual(
                    (first / filename).read_bytes(), (second / filename).read_bytes()
                )
            run_info = json.loads((second / "run-info.json").read_text())
            self.assertGreater(run_info["elapsed_seconds"], 0)
            self.assertTrue(run_info["python_version"])

    def test_invalid_configuration_fails_explicitly(self):
        original = json.loads(CONFIG.read_text())
        variants = [
            {**original, "unexpected_setting": 1},
            {**original, "bid_coefficients": [0.01, 0.02, 0.04]},
            {**original, "bid_coefficients": [0.01, 0.02, 0.02, 0.04, 0.06]},
            {**original, "tolerances": {**original["tolerances"], "cost_eur": -1}},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.json"
            for data in variants:
                with self.subTest(data=data):
                    path.write_text(json.dumps(data))
                    with self.assertRaises(ValueError):
                        load_config(path)

    def test_cli_reports_missing_configuration_without_creating_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "results"
            result = subprocess.run(
                [
                    sys.executable, "-m", "project.run_pilot",
                    "--config", str(Path(temporary) / "missing.json"),
                    "--output-dir", str(output),
                ],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("error:", result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
