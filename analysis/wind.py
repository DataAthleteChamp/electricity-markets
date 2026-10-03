"""Exercise 3, Sheet 3: curtailment game. Pure NE, social optimum, worst-case CCE via LP."""
from itertools import product
import numpy as np
from scipy.optimize import linprog

n = 4
A = list(product([0, 1], repeat=n))          # 1 = Feed (F), 0 = Curtail (C)
CAP = 2                                       # grid absorbs at most 2 feeders


def u(a, i):
    k = sum(a)
    if a[i] == 0:
        return 3
    return 10 if k <= CAP else 2


def W(a):
    return sum(u(a, i) for i in range(n))


OPT = max(W(a) for a in A)
print("welfare by number of feeders k:")
for k in range(n + 1):
    a = tuple([1] * k + [0] * (n - k))
    print(f"  k={k}: welfare={W(a)}")
print("OPT =", OPT, " attained by k =",
      sorted({sum(a) for a in A if W(a) == OPT}))
print()

pure = [a for a in A if all(u(a, i) >= u(a[:i] + (1 - a[i],) + a[i+1:], i) for i in range(n))]
print(f"pure NE: {len(pure)} profiles, all with k =", sorted({sum(a) for a in pure}),
      "-> welfare", sorted({W(a) for a in pure}))
print("pure-NE PoA =", OPT / min(W(a) for a in pure))
print()

# ---- LP: minimise expected welfare over the CCE polytope ----
idx = {a: j for j, a in enumerate(A)}
c_obj = np.array([W(a) for a in A], dtype=float)      # minimise E[welfare]
rows, rhs = [], []
for i in range(n):
    for dev in (0, 1):                                 # unconditional deviation to fixed action
        row = np.zeros(len(A))
        for a in A:
            a_dev = a[:i] + (dev,) + a[i+1:]
            row[idx[a]] = u(a_dev, i) - u(a, i)         # CCE: E[u(a)] >= E[u(dev,a_-i)]
        rows.append(row)
        rhs.append(0.0)

res = linprog(c_obj, A_ub=np.array(rows), b_ub=np.array(rhs),
              A_eq=np.ones((1, len(A))), b_eq=[1.0],
              bounds=[(0, 1)] * len(A), method="highs")

print("worst-case CCE welfare =", round(res.fun, 6))
print("CCE PoA =", round(OPT / res.fun, 6))
print("support of the worst CCE:")
for a, p in zip(A, res.x):
    if p > 1e-9:
        print(f"  {''.join('F' if x else 'C' for x in a)}  k={sum(a)}  pi={p:.4f}  welfare={W(a)}")

# ---- LP: minimise expected welfare over the (tighter) CE polytope ----
rows_ce = []
for i in range(n):
    for cur in (0, 1):
        for dev in (0, 1):
            if cur == dev:
                continue
            row = np.zeros(len(A))
            for a in A:                      # conditional on being recommended `cur`
                if a[i] != cur:
                    continue
                a_dev = a[:i] + (dev,) + a[i+1:]
                row[idx[a]] = u(a_dev, i) - u(a, i)
            rows_ce.append(row)

res_ce = linprog(c_obj, A_ub=np.array(rows_ce), b_ub=np.zeros(len(rows_ce)),
                 A_eq=np.ones((1, len(A))), b_eq=[1.0],
                 bounds=[(0, 1)] * len(A), method="highs")
print()
print("worst-case CE welfare =", round(res_ce.fun, 6), " CE PoA =", round(OPT / res_ce.fun, 6))
print("=> pure-NE PoA = 1.0  <  CE PoA =", round(OPT / res_ce.fun, 3),
      " <  CCE PoA =", round(OPT / res.fun, 3))
