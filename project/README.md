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

## Background references

[Research paper](../references/how-inefficient-can-an-electricity-market-be.pdf),
Sections II and IV-A; [algorithm notes](../references/algorithm-explanation.pdf),
Sections 2-3; [Week 5](../lectures/week-05-slides.pdf), pages 7, 11, and 24;
Exercise Sheets [3](../exercises/week-03-tasks.pdf) and
[4](../exercises/week-04-tasks.pdf).
