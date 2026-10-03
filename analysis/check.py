import random
from market import Market

m = Market(cost=[5, 12.5, 25, 40, 65], cap=[100, 40, 50, 30, 30], demand=180, bid_max=80)

print("OPT (truthful least-cost dispatch) =", m.optimal_cost())
print()
print("--- Week 1 slide claims ---")
for name, b in [("truthful   ", [5, 13, 25, 40, 65]),
                ("G3 inflates", [5, 13, 41, 40, 65]),
                ("G1+G3 both ", [26, 13, 41, 40, 65])]:
    pf, d, p = m.profits(b)
    print(f"{name} bids={b} price={p:>3} dispatch={[round(x,1) for x in d]} truecost={m.true_cost(b):.0f}")
print()
print("--- Pivotality check ---")
tot = sum(m.cap)
for i in range(m.n):
    print(f"  without G{i+1}: capacity={tot-m.cap[i]} vs demand={m.demand} -> "
          f"{'PIVOTAL' if tot-m.cap[i] < m.demand else 'not pivotal'}")
print()
print("--- Week 3 slide 2 claims ---")
for b in [[1, 2, 52, 3, 53], [80, 0, 0, 0, 0]]:
    pf, d, p = m.profits(b)
    print(f"  b={b} NE={m.is_nash(b)} price={p} cost={m.true_cost(b):.0f} "
          f"PoA={m.true_cost(b)/m.optimal_cost():.3f} profits={[round(x) for x in pf]}")
