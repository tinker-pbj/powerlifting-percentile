"""Shared helpers for the generated pages: read a value off the percentile tables built by build.py / build_wl.py."""
import math

def cdf_at(D, sex, lift, bw):
    """CDF (percent) over the lift grid at bodyweight bw, interpolated in log bodyweight. Returns (x0, step, values)."""
    S = D['data'][sex]; L = S['lifts'][lift]; st = D['meta']['bw_step_log']
    i = math.log(bw / S['bw0']) / st
    a = max(0, min(S['nbw'] - 2, math.floor(i))); f = max(0.0, min(1.0, i - a))
    def cum(k):
        s, out = 0, []
        for d in L['rows'][k]: s += d; out.append(s / 100)
        return out
    r0, r1 = cum(a), cum(a + 1)
    return L['x0'], D['meta']['lift_step'], [r0[k] + f * (r1[k] - r0[k]) for k in range(L['n'])]

def quantile(D, sex, lift, bw, p):
    """The lift (kg) at percentile p for this bodyweight."""
    x0, step, c = cdf_at(D, sex, lift, bw)
    k = 0
    while k < len(c) - 1 and c[k + 1] < p: k += 1
    span = c[k + 1] - c[k] if k + 1 < len(c) else 0
    return x0 + step * (k + ((p - c[k]) / span if span > 0 else 0))
