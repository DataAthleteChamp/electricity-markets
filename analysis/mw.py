"""Exercise 2, Sheet 3: multiplicative weights on the merit-order bidding game."""
import numpy as np
from collections import Counter
from market import Market

rng = np.random.default_rng(1)
m = Market(cost=[5, 12.5, 25, 40, 65], cap=[100, 40, 50, 30, 30], demand=180, bid_max=80)
OPT, K, n = m.optimal_cost(), len(m.bids), m.n

T = 20000
eps = np.sqrt(np.log(K) / T)
logw = np.zeros((n, K))
cum_loss = np.zeros(n)                 # realised loss
cum_fixed = np.zeros((n, K))           # loss of each fixed action in hindsight
counts = Counter()
cost_trace = []

for t in range(T):
    p = np.exp(logw - logw.max(axis=1, keepdims=True))
    p /= p.sum(axis=1, keepdims=True)
    b = [int(rng.choice(K, p=p[i])) for i in range(n)]
    counts[tuple(b)] += 1
    cost_trace.append(m.true_cost(b))

    for i in range(n):
        trial = list(b)
        pi = np.empty(K)
        for x in range(K):
            trial[i] = x
            pi[x] = m.profits(trial)[0][i]
        span = pi.max() - pi.min()
        loss = np.zeros(K) if span < 1e-12 else (pi.max() - pi) / span
        cum_loss[i] += loss[b[i]]
        cum_fixed[i] += loss
        logw[i] += np.log1p(-eps) * loss

regret = (cum_loss[:, None] - cum_fixed) / T
print(f"T={T}, eps={eps:.5f}")
print("max average regret per generator:", np.round(regret.max(axis=1), 5))
print("MW theoretical bound 2*sqrt(ln K / T) =", round(2 * np.sqrt(np.log(K) / T), 5))
print()

tail = int(0.8 * T)
avg_cost_tail = np.mean(cost_trace[tail:])
print(f"OPT = {OPT:.0f}")
print(f"average true dispatch cost over last 20% of rounds = {avg_cost_tail:.0f}")
print(f"=> empirical CCE 'price of anarchy' = {avg_cost_tail / OPT:.3f}")
print()
print("top 8 joint bid profiles in the empirical distribution (= approximate CCE):")
for prof, c in counts.most_common(8):
    print(f"  {list(prof)}  freq={c/T:.4f}  pureNE={m.is_nash(list(prof))}  cost={m.true_cost(list(prof)):.0f}")
print()
print("marginal most-played bid per generator:",
      [int(np.argmax(np.exp(logw[i] - logw[i].max()))) for i in range(n)])
print("true marginal costs:                   ", m.cost)
