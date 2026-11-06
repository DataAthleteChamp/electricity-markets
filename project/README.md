# Bidding-Language Restrictions and the Price of Anarchy

## Objective

This project compares production-cost inefficiency and Price of Anarchy (PoA)
upper bounds under quadratic-only bidding, with and without cost-bid mismatch.
The bidding rules remain unchanged; only the true-cost model differs.

| Case | True production costs | Permitted bids |
|---|---|---|
| Matched | Quadratic | Quadratic |
| Mismatch | Block-form | The same quadratic bid family |

Block-form means convex, piecewise-linear total costs with stepwise marginal
costs, not discrete production quantities.

## Research questions

1. **RQ1:** How does worst-case coarse correlated equilibrium (CCE)
   production-cost inefficiency differ between quadratic and block-form true
   costs when generators can submit only quadratic bids?
2. **RQ2:** How do valid finite-game PoA bounds differ between these cases, and
   how closely do they track the corresponding worst-CCE inefficiency?

## Study design

1. **Market:** a stylised, single-node, one-hour case with three generators,
   700 MW capacity each, and 1,148.4 MW demand. Repeat selected cases with four
   generators at the same capacity utilisation, following the paper's setup.
2. **Cost cases:** predefined quadratic/block cost-profile pairs with matching
   full-capacity costs and a fixed block structure. Keep bid form, coefficient
   bounds, demand, capacities, pricing, and tie-breaking identical within each
   pair.
3. **Benchmarks:** compute each case's physical minimum true production cost and
   the cheapest dispatch attainable on the bid grid. Report any attainability
   gap separately from equilibrium losses.
4. **Equilibria:** compute the exact worst CCE by linear programming on a shared
   finite grid of positive quadratic bid coefficients, including truthful
   quadratic profiles. Divide expected true production cost by each case's
   physical optimum. Check selected cases on a finer grid.
5. **Bounds:** construct a fixed-deviation generalized-smoothness upper bound
   using admissible quadratic reference bids and verify every finite-game
   constraint. The scaled-truthful construction must be adapted for block costs.

## Expected outputs and scope

Paired plots will compare inefficiency and bounds across the cost cases. A
bound-versus-inefficiency scatter plot will show how tightly the bound tracks
the exact finite-game result.

No mismatch-severity measurement or scarcity sweep is included, and an increase
in inefficiency is not assumed. Conclusions concern the selected cost models
and finite bid grid, not a certified PoA for continuous bidding.

## Delivery plan

The report is due **14 December 2026 at 23:59:59**, with a maximum of **eight
standard LaTeX pages excluding the title page**. Focus on the experiment setup,
graphical results, and interpretation rather than lengthy algorithm explanations.

See the [work plan](work-plan.md) for milestones, validation gates, numerical
settings to record, and the proposed report structure.

## Calculator

The standard-library Python calculator implements positive fully quadratic bids,
capacity-constrained clearing, and physical optima for quadratic and block costs.
The approved pilot uses true coefficients `(0.02, 0.04, 0.06)` and three equal
blocks per generator. Costs are synthetic, not calibrated Danish costs.

Use Python 3.10 or later and run from the repository root:

```bash
python3 -m unittest discover -s project/tests -v
```

Quantities are MWh over the one-hour interval; prices are EUR/MWh and costs are
EUR. Block costs interpolate the quadratic at four equally spaced knots.
Physical block-cost ties use generator order; quadratic bid clearing has a
unique dispatch. At full aggregate capacity, use the smallest valid dual price.

Payoff-table generation is the next stage. CCE and PoA-bound solvers are not
implemented yet.

## Background references

[Research paper](../references/how-inefficient-can-an-electricity-market-be.pdf),
Sections II and IV-A; [algorithm notes](../references/algorithm-explanation.pdf),
Sections 2-3; [Week 5](../lectures/week-05-slides.pdf), pages 7, 11, and 24;
Exercise Sheets [3](../exercises/week-03-tasks.pdf) and
[4](../exercises/week-04-tasks.pdf).
