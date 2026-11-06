# Project Work Plan

The [project brief](README.md) defines the topic and research questions.
This plan turns them into deliverables. The calculator, analytic verification
tests, and reproducible payoff-table generator are implemented. CCE, PoA bounds,
and the main experiments remain pending.

## Submission requirements

Supervisor's requirements, shared on 6 November 2026:

- **Deadline:** 14 December 2026 at 23:59:59. Confirm the submission platform
  and timezone through the course.
- **Length:** at most eight standard LaTeX pages, excluding the title page.
  Reserve space for references; no other page exclusions were stated.
- Describe the experiment setup, including tolerance levels, discretisation
  point counts, and other settings needed to understand the results.
- Present results graphically and interpret them, especially interesting or
  unexpected observations.
- Keep algorithm explanations brief. Prioritise what we did and observed.

## Delivery sequence

These are proposed internal milestones, not additional course deadlines.
Complete each validation gate before expanding the experiments.

| Target | Deliverable | Completion gate |
|---|---|---|
| 13 November | Agreed mathematical specification | Fix bid form, paired true costs, block structure, bid bounds/grid, pricing, benchmarks, both LPs, and the short certificate argument. |
| 20 November | Verified market and benchmark calculations | Demand and capacities hold; truthful quadratic bids reproduce the physical optimum; the block-cost physical optimum agrees with a merit-order calculation. |
| 27 November | One paired three-generator pilot | Worst-CCE constraints and bound inequalities pass independent residual checks; record runtime and bound tightness. |
| 4 December | Main experiments and selected robustness checks | Predeclare the case list before the main runs and retain all outcomes, including null or unexpected results. |
| 11 December | Figures and complete report draft | Every figure is reproducible and interpreted; setup table includes numerical settings. |
| 13 December | Final reproducibility and page-limit review | Regenerate reported outputs from committed inputs; check captions, references, and the eight-page limit. |
| 14 December | Submission | Submit before 23:59:59 and retain confirmation. |

## Minimal experiment set

- **Main comparison:** three predefined synthetic cost configurations
  (symmetric, moderately asymmetric, strongly asymmetric), each evaluated with
  quadratic and block-form true costs under identical quadratic bidding rules.
  This gives six main games, including the pilot if its case is retained.
- **Replication:** one selected four-generator pair at the same utilisation;
  demand is 1,531.2 MW with 700 MW capacity per generator.
- **Robustness:** refine selected bid grids at fixed bounds, then separately
  test wider bounds. Retain the original actions and truthful quadratic bids.
- **No extra axes:** no mismatch-severity, block-count, or scarcity sweep.

The approved pilot constructs block costs by joining each quadratic curve at
four fixed, equally spaced knots (three blocks). Its true quadratic coefficients
are `(0.02, 0.04, 0.06)`, with shared bid choices
`(0.01, 0.02, 0.04, 0.06, 0.08, 0.16, 0.32)`. Seven choices give 343 joint
profiles with three generators and 2,401 with four. Other cost configurations
and robustness settings still need to be fixed before the main experiments.

## Validation and experiment records

Use one shared market-clearing calculation for both true-cost cases. Evaluate
profits and social cost using the relevant true costs, never submitted costs
or payments.

For each case, calculate the physical optimum, cheapest grid-attainable cost,
worst expected CCE cost, and the physical-benchmark upper bound. Check, within
documented numerical tolerances:

`1 <= grid cost / physical optimum <= worst CCE cost / physical optimum <= bound`

Recompute every CCE deviation gain and bound-constraint residual independently
from the payoff table. Bound reference bids must belong to the allowed grid.
A valid but loose bound or a negligible mismatch effect is a reportable result,
not a failed experiment.

Record with every run:

| Item | Required details |
|---|---|
| Market and costs | Demand, capacities, units, true-cost parameters, block knots/slopes, pricing rules. |
| Bid discretisation | Coefficient bounds, exact action values, points per generator, and joint-profile count. |
| Numerical settings | Solver/version, configured feasibility and optimality tolerances, clearing and CCE-check tolerances, and measured maximum residuals. |
| Certificate | Reference-selection rule, legal reference bids, bound parameters, and any residual correction. |
| Reproducibility | Configuration and code commit, run command, runtime, random seed if applicable, and output locations. |

Generate tables and figures from committed scripts/configurations rather than
manual transcription. Record actual numerical settings and distinguish
benchmark calculations from equilibrium results.

The pilot records validation tolerances in `pilot.json`, code revision and
source/configuration hashes in `results/metadata.json`, and actual residuals in
`results/benchmarks.json`. Local runtime/environment records stay in ignored
`results/run-info.json`. No solver tolerances or equilibrium results exist yet.

## Results-focused report

| Section | Suggested pages |
|---|---|
| Motivation and research questions | 0.5 |
| Market, experiment setup, and brief method summary | 1.5 |
| Results, figures, and interpretation | 4.5 |
| Limitations and conclusion | 1.0 |
| References | 0.5 |

Prioritise three figures: paired inefficiency comparisons, normalised
attainability/equilibrium loss decomposition, and bound versus exact finite-game
inefficiency. Explain what changes, what does not, and plausible mechanisms
behind unexpected observations.

Keep conclusions conditional on the specified true-cost pairs, bid bounds,
finite grids, and CCE concept. Grid refinement does not guarantee monotone
worst-CCE values or certify continuous bidding, and these synthetic cases do
not estimate actual Danish-market PoA.
