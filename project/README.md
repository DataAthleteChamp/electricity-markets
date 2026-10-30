# Bidding-Language Restrictions and the Price of Anarchy

## Research question

What further effect does a restricted bidding language have on the Price of
Anarchy (PoA), or a valid PoA bound, when generators cannot bid their true costs?

The motivating example is block-form true costs with quadratic-only bids.
Whether this mismatch increases inefficiency is a question to investigate, not
an assumption.

## Controlled comparison

| Case | True costs | Permitted bids |
|---|---|---|
| Matched | Block-form | Block bids capable of expressing the true costs |
| Restricted | The same block-form costs | Quadratic-only bids |

Keep the generators, true costs, capacities, demand, pricing, and tie-breaking
rules the same across the comparison. Change only the permitted bid family.
Truthful bidding being available in the matched case does not imply that it is
an equilibrium.

## Starting scope

Start with a small, single-node, deterministic market. Agree the model and
comparison before introducing project code. Networks, storage, forecasting, and
LLM components are outside the initial scope.

Possible methods are discretizing bids to compute finite-game PoA, deriving or
adapting a certified upper bound, or comparing both if feasible. The method is
not yet fixed.

## Quantities to keep separate

- **Physical optimum:** minimum true production cost among feasible dispatches.
- **Attainable optimum:** minimum true production cost attainable through the
  permitted bid family and any chosen grid.
- **Equilibrium inefficiency:** worst equilibrium cost relative to the stated
  benchmark and solution concept.

Use actual production costs for the social objective, not submitted bid costs,
market prices, or payments. Separate representational or discretization losses
from strategic inefficiency.

A finite-game result does not automatically apply to continuous bidding. A
learning trajectory or the worst equilibrium found by restarts is not a proof
of worst-case PoA.

## Decisions before coding

- Define "block-form" precisely, including whether it means piecewise-linear
  total costs from block marginal costs or a different nonconvex cost model.
- Specify the quadratic bid form, coefficient bounds, and any discretization.
- Agree the dispatch, pricing, capacity, and tie-breaking rules.
- Choose the equilibrium concept and the primary method. For example, an exact
  worst-CCE LP is possible for a sufficiently small finite bid game.

## Bound validity

The [course algorithm notes](../references/algorithm-explanation.pdf) rely on
truthful or scaled-truthful bids being feasible deviations. This premise may
fail in the restricted case. Do not reuse the certificate without establishing
admissible deviations and a valid proof.

For continuous bounds, a local search that finds no violated constraint is not
by itself a certificate of global feasibility.

## Team workflow

Use GitHub Issues to assign and discuss the model and assumptions, methods and
theory, and evaluation and report. Record agreed decisions here and relevant
reading in the [reference guide](../references/README.md).

Keep the project focused enough for the eight-page report limit stated in
[Week 1](../lectures/week-01-slides.pdf), PDF page 28.
