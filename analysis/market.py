"""Merit-order uniform-price market clearing + best-response analysis.

Mirrors Exercise 3, Sheet 2 (DTU 'Game Theory in Electricity Markets').
Nothing is hardcoded: pass any (cost, capacity, demand, bid grid).
"""
from itertools import product


class Market:
    def __init__(self, cost, cap, demand, bid_max=80):
        self.cost = list(cost)
        self.cap = list(cap)
        self.demand = demand
        self.bid_max = bid_max
        self.n = len(cost)
        self.bids = list(range(bid_max + 1))

    def clear(self, b):
        """Return (dispatch vector, clearing price) for bid profile b."""
        dispatch = [0.0] * self.n
        remaining = self.demand
        price = 0.0
        for level in sorted(set(b)):
            tied = [i for i in range(self.n) if b[i] == level]
            avail = sum(self.cap[i] for i in tied)
            if remaining <= 0:
                break
            price = level
            if avail <= remaining:
                for i in tied:
                    dispatch[i] = self.cap[i]
                remaining -= avail
            else:
                # split the residual demand equally, respecting capacities
                share = dict.fromkeys(tied, 0.0)
                left = remaining
                active = list(tied)
                while left > 1e-9 and active:
                    per = left / len(active)
                    filled = []
                    for i in active:
                        room = self.cap[i] - share[i]
                        if room <= per + 1e-12:
                            share[i] += room
                            left -= room
                            filled.append(i)
                    if filled:
                        active = [i for i in active if i not in filled]
                    else:
                        for i in active:
                            share[i] += per
                        left = 0.0
                for i in tied:
                    dispatch[i] = share[i]
                remaining = 0
        return dispatch, price

    def profits(self, b):
        d, p = self.clear(b)
        return [(p - self.cost[i]) * d[i] for i in range(self.n)], d, p

    def true_cost(self, b):
        d, _ = self.clear(b)
        return sum(self.cost[i] * d[i] for i in range(self.n))

    def optimal_cost(self):
        """Least-cost dispatch = the bid profile b = c (truthful)."""
        order = sorted(range(self.n), key=lambda i: self.cost[i])
        rem, total = self.demand, 0.0
        for i in order:
            take = min(self.cap[i], rem)
            total += take * self.cost[i]
            rem -= take
            if rem <= 0:
                break
        return total

    def br_profits(self, b, i):
        out = []
        trial = list(b)
        for x in self.bids:
            trial[i] = x
            out.append(self.profits(trial)[0][i])
        return out

    def best_response(self, b, i, keep_current=True):
        """Argmax of player i's profit. Ties keep the incumbent bid if optimal."""
        pis = self.br_profits(b, i)
        best_pi = max(pis)
        if keep_current and pis[b[i]] >= best_pi - 1e-9:
            return b[i], best_pi
        for x, pi in enumerate(pis):
            if pi >= best_pi - 1e-9:
                return x, best_pi
        return b[i], best_pi

    def br_dynamics(self, b0, max_iter=200):
        """Sequential best-response. Returns (profile, converged)."""
        b = list(b0)
        for _ in range(max_iter):
            changed = False
            for i in range(self.n):
                x, _ = self.best_response(b, i)
                if x != b[i]:
                    b[i] = x
                    changed = True
            if not changed:
                return b, True
        return b, False

    def is_nash(self, b):
        for i in range(self.n):
            cur = self.profits(b)[0][i]
            if max(self.br_profits(b, i)) > cur + 1e-9:
                return False
        return True
