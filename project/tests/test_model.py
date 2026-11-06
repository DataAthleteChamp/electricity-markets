import unittest
from math import fsum

from project.model import (
    Generator,
    block_optimal_dispatch,
    clear_market,
    physical_benchmarks,
)


class MarketTests(unittest.TestCase):
    def setUp(self):
        self.generators = tuple(
            Generator(coefficient, 700.0, 3) for coefficient in (0.02, 0.04, 0.06)
        )

    def assertQuantities(self, actual, expected):
        for quantity, target in zip(actual, expected, strict=True):
            self.assertAlmostEqual(quantity, target, delta=1e-8)

    def test_truthful_quadratic_dispatch_and_cost(self):
        result = clear_market((0.02, 0.04, 0.06), (700.0,) * 3, 1148.4)
        self.assertQuantities(result.quantities_mwh, (626.4, 313.2, 208.8))
        self.assertAlmostEqual(result.price_eur_per_mwh, 12.528, places=10)
        benchmarks = physical_benchmarks(self.generators, 1148.4)
        self.assertAlmostEqual(
            benchmarks["quadratic"].total_cost_eur, 7193.5776, delta=1e-6
        )

    def test_capacity_constrained_water_filling(self):
        cases = (
            ((1, 4, 8), (1, 1, 1), 2, (1, 2 / 3, 1 / 3), 8 / 3),
            ((1, 2, 10), (1, 1, 1), 2.5, (1, 1, 0.5), 5),
            ((1, 2), (0.25, 2), 1, (0.25, 0.75), 1.5),
        )
        for bids, capacities, demand, expected, price in cases:
            with self.subTest(bids=bids):
                result = clear_market(bids, capacities, demand)
                self.assertQuantities(result.quantities_mwh, expected)
                self.assertAlmostEqual(result.price_eur_per_mwh, price)
                self.assertAlmostEqual(fsum(result.quantities_mwh), demand)

    def test_common_bid_scaling_preserves_dispatch_and_scales_price(self):
        original = clear_market((0.01, 0.08, 0.32), (700,) * 3, 1148.4)
        scaled = clear_market((0.03, 0.24, 0.96), (700,) * 3, 1148.4)
        self.assertQuantities(scaled.quantities_mwh, original.quantities_mwh)
        self.assertAlmostEqual(
            scaled.price_eur_per_mwh, 3 * original.price_eur_per_mwh
        )

    def test_zero_and_full_demand_price_conventions(self):
        self.assertEqual(clear_market((1, 2), (3, 4), 0).quantities_mwh, (0, 0))
        result = clear_market((1, 2), (3, 4), 7)
        self.assertEqual(result.quantities_mwh, (3, 4))
        self.assertEqual(result.price_eur_per_mwh, 8)

    def test_invalid_market_inputs_are_rejected(self):
        cases = (
            ((), (), 0),
            ((1,), (1, 2), 1),
            ((0,), (1,), 1),
            ((float("nan"),), (1,), 1),
            ((1,), (0,), 0),
            ((1,), (1,), -1),
            ((1,), (1,), 2),
            ((1,), (1,), float("inf")),
        )
        for bids, capacities, demand in cases:
            with self.subTest(bids=bids, capacities=capacities, demand=demand):
                with self.assertRaises(ValueError):
                    clear_market(bids, capacities, demand)

    def test_block_interpolation_inside_segments_and_at_knots(self):
        generator = Generator(2.0, 3.0, 3)
        self.assertEqual(generator.block_cost(1.5), 2.5)
        self.assertEqual(generator.quadratic_cost(1.5), 2.25)
        for knot in (0.0, 1.0, 2.0, 3.0):
            self.assertEqual(
                generator.block_cost(knot), generator.quadratic_cost(knot)
            )

    def test_block_physical_optimum(self):
        result = physical_benchmarks(self.generators, 1148.4)["block"]
        self.assertQuantities(
            result.quantities_mwh, (681.7333333333333, 700 / 3, 700 / 3)
        )
        self.assertAlmostEqual(result.total_cost_eur, 66682 / 9, delta=1e-6)

    def test_block_cost_at_the_same_quadratic_bid_dispatch(self):
        quantities = clear_market(
            (0.02, 0.04, 0.06), (700,) * 3, 1148.4
        ).quantities_mwh
        total = fsum(
            generator.block_cost(quantity)
            for generator, quantity in zip(self.generators, quantities)
        )
        self.assertAlmostEqual(total, 7709.955555555556, delta=1e-6)

    def test_block_optimum_can_exclude_a_generator(self):
        generators = tuple(Generator(a, 1.0, 3) for a in (1, 2, 10))
        result = block_optimal_dispatch(generators, 2871 / 1750)
        self.assertQuantities(result, (1, 1121 / 1750, 0))

    def test_equal_block_prices_have_deterministic_ties(self):
        generators = (Generator(1, 1, 1), Generator(1, 1, 1))
        self.assertEqual(block_optimal_dispatch(generators, 0.5), (0.5, 0.0))

    def test_invalid_cost_inputs_are_rejected(self):
        for coefficient, capacity, blocks in (
            (0, 1, 3),
            (1, -1, 3),
            (1, 1, 0),
            (1, 1, 1.5),
            (1, 1, True),
        ):
            with self.subTest(coefficient=coefficient, capacity=capacity, blocks=blocks):
                with self.assertRaises(ValueError):
                    Generator(coefficient, capacity, blocks)
        generator = self.generators[0]
        for quantity in (-1, 701, float("nan")):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    generator.block_cost(quantity)


if __name__ == "__main__":
    unittest.main()
