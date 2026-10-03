import random
from market import Market

random.seed(0)
m = Market(cost=[5, 12.5, 25, 40, 65], cap=[100, 40, 50, 30, 30], demand=180, bid_max=80)
OPT = m.optimal_cost()

print("OPT =", OPT)
b = [66, 13, 26, 41, 67]
print("Week1 slide17 reconstruction:", b, "cost =", m.true_cost(b),
      "ratio =", round(m.true_cost(b) / OPT, 3))
print()

found, fails = {}, 0
for trial in range(400):
    b0 = [random.randint(0, 80) for _ in range(m.n)]
    b, ok = m.br_dynamics(b0)
    if ok and m.is_nash(b):
        found[tuple(b)] = m.true_cost(b)
    else:
        fails += 1

print(f"400 random restarts -> {len(found)} distinct pure NE, {fails} non-convergent")
ratios = sorted(found.items(), key=lambda kv: kv[1])
print(f"best  NE cost = {ratios[0][1]:.0f}  PoA = {ratios[0][1]/OPT:.3f}   {list(ratios[0][0])}")
print(f"worst NE cost = {ratios[-1][1]:.0f}  PoA = {ratios[-1][1]/OPT:.3f}   {list(ratios[-1][0])}")
print()
print("worst 5 equilibria found:")
for bb, c in ratios[-5:]:
    _, d, p = m.profits(list(bb))
    print(f"  {list(bb)}  price={p:>3}  cost={c:>6.0f}  PoA={c/OPT:.3f}  dispatch={[round(x,1) for x in d]}")
print()
print("distribution of NE costs:")
import collections
h = collections.Counter(round(c) for c in found.values())
for c in sorted(h):
    print(f"  cost {c:>5} (PoA {c/OPT:.3f}): {h[c]:>3} equilibria")
