"""
OASIS sampling estimators (profile-weighted-mean formulation).

Columns expected on the scenario dataframe passed to samplers:
  '_z'   : binary outcome (collision 0/1)
  '_p'   : operational-profile mass for the active profile (sum to 1 over pop)
  '_sid' : stable scenario id (int)
  aux_var column (e.g. 'PC' or 'TTC' transform)  -- see driver
"""

import numpy as np
import pandas as pd

EPS = 1e-12


# ----------------------------------------------------------------------
# SRS  (sample proportional to profile p_i; q_i = p_i)
# ----------------------------------------------------------------------
def srs_run(df, budget, rng):
    N = len(df)
    n = min(budget, N)
    p = df['_p'].to_numpy()
    idx = rng.choice(N, size=n, replace=True, p=p)
    s = df.iloc[idx]
    z = s['_z'].to_numpy(float)
    # q_i = p_i  ->  (p z)/q = z ,  p/q = 1  -> theta_hat = mean(z)
    theta = float(z.mean())
    return theta, int(z.sum())


# ----------------------------------------------------------------------
# SUPS  (PPS with replacement; q_i proportional to aux)
# ----------------------------------------------------------------------
def sups_run(df, budget, aux, rng):
    N = len(df)
    n = min(budget, N)
    x = df[aux].to_numpy(float)
    if np.any(x < 0):
        x = x - x.min()
    x = np.clip(x, EPS, None)
    q = x / x.sum()                      # per-draw selection prob
    idx = rng.choice(N, size=n, replace=True, p=q)
    s = df.iloc[idx]
    z = s['_z'].to_numpy(float)
    p = s['_p'].to_numpy(float)
    qi = q[idx]
    num = np.sum((p * z) / qi)
    den = np.sum(p / qi)
    theta = float(num / den) if den > 0 else np.nan
    return theta, int(z.sum())


# ----------------------------------------------------------------------
# RHC  (grouped PPS without replacement)
# ----------------------------------------------------------------------
def rhc_run(df, budget, aux, rng):
    N = len(df)
    n = min(budget, N)
    x = df[aux].to_numpy(float)
    if np.any(x < 0):
        x = x - x.min()
    x = np.clip(x, EPS, None)
    c = x / x.sum()
    z = df['_z'].to_numpy(float)
    p = df['_p'].to_numpy(float)

    perm = rng.permutation(N)
    base, rem = N // n, N % n
    sizes = [base + (1 if g < rem else 0) for g in range(n)]

    num = 0.0
    den = 0.0
    obs = 0
    start = 0
    for size in sizes:
        gpos = perm[start:start + size]
        start += size
        cg = c[gpos]
        qr = cg.sum()                    # group total of c
        pin = cg / qr
        j = rng.choice(gpos, size=1, p=pin)[0]
        # RHC weight for a total: (q_r / c_j); profile-weighted-mean normalizes
        w = qr / c[j]
        num += w * (p[j] * z[j])
        den += w * p[j]
        obs += int(z[j])
    theta = float(num / den) if den > 0 else np.nan
    return theta, obs


# ----------------------------------------------------------------------
# SSRS  (stratified, Neyman allocation; profile enters via P_h)
#   theta_hat = sum_h P_h * mean_h(z)
# ----------------------------------------------------------------------
def ssrs_run(df, budget, part_col, rng):
    N = len(df)
    n = min(budget, N)
    z = df['_z'].to_numpy(float)
    p = df['_p'].to_numpy(float)
    parts = df[part_col].to_numpy()
    uniq = pd.unique(parts)

    # Neyman allocation n_h ∝ N_h * S_h  (S_h = within-stratum std of z)
    Nh, Sh = {}, {}
    for h in uniq:
        m = parts == h
        Nh[h] = int(m.sum())
        Sh[h] = float(z[m].std(ddof=0)) if Nh[h] > 1 else 0.0
    raw = {h: Nh[h] * Sh[h] for h in uniq}
    tot = sum(raw.values())
    if tot <= 0:                          # degenerate -> proportional
        raw = {h: Nh[h] for h in uniq}; tot = sum(raw.values())
    alloc = {h: max(1, int(round(n * raw[h] / tot))) for h in uniq}

    P_h = {h: float(p[parts == h].sum()) for h in uniq}
    theta = 0.0
    obs = 0
    for h in uniq:
        pos = np.where(parts == h)[0]
        k = min(alloc[h], len(pos))
        sel = rng.choice(pos, size=k, replace=False)
        zh = z[sel]
        theta += P_h[h] * float(zh.mean())
        obs += int(zh.sum())
    return float(theta), obs


# ----------------------------------------------------------------------
# 2-UPS  (two-stage: partition by alpha_k, SRS within; q_i = alpha_k / N_k)
#   first-stage score uses AUX (no Outcome leakage)
# ----------------------------------------------------------------------
def twoups_run(df, budget, aux, part_col, rng):
    N = len(df)
    n = min(budget, N)
    z = df['_z'].to_numpy(float)
    p = df['_p'].to_numpy(float)
    parts = df[part_col].to_numpy()
    uniq = pd.unique(parts)

    # first-stage selection prob alpha_k ∝ mean aux in partition (NOT outcome)
    score = {}
    for h in uniq:
        xa = df.loc[parts == h, aux].to_numpy(float)
        score[h] = float(np.clip(xa, EPS, None).mean())
    ssum = sum(score.values())
    alpha = {h: score[h] / ssum for h in uniq}
    Nk = {h: int((parts == h).sum()) for h in uniq}

    hs = rng.choice(list(uniq), size=n, replace=True, p=[alpha[h] for h in uniq])
    num = den = 0.0
    obs = 0
    for h in hs:
        pos = np.where(parts == h)[0]
        j = pos[rng.integers(len(pos))]
        qi = alpha[h] * (1.0 / Nk[h])     # per-draw prob of unit j
        num += (p[j] * z[j]) / qi
        den += p[j] / qi
        obs += int(z[j])
    theta = float(num / den) if den > 0 else np.nan
    return theta, obs


# ----------------------------------------------------------------------
# DEEPEST  (adaptive; step-wise q; profile-weighted-mean normalized)
# ----------------------------------------------------------------------
def deepest_run(df, budget, aux, rng, threshold=0.7, r=0.8):
    N = len(df)
    n = min(budget, N)
    chi = df[aux].to_numpy(float)
    # normalize chi to [0,1] so threshold is meaningful across aux scales
    cmin, cmax = chi.min(), chi.max()
    chin = (chi - cmin) / (cmax - cmin + EPS)
    z = df['_z'].to_numpy(float)
    p = df['_p'].to_numpy(float)
    mask = (chin > threshold).astype(float)
    # W[i,j] = chi_j if chi_i>thr else 0
    Wj = chin

    remaining = list(range(N))
    selected = []
    qs = []
    # step 1 uniform
    first = rng.integers(N)
    selected.append(first); remaining.remove(first); qs.append(1.0 / N)
    for step in range(2, n + 1):
        rem = np.array(remaining)
        if rem.size == 0:
            break
        # s_i = sum_{j in selected} W[i,j] = mask_i * sum_j chi_j(selected)
        sel_chi_sum = Wj[selected].sum()
        s = mask[rem] * sel_chi_sum
        if s.sum() > 0:
            p_wbs = s / s.sum()
        else:
            p_wbs = np.ones(rem.size) / rem.size
        p_unif = np.ones(rem.size) / rem.size
        qvec = r * p_wbs + (1 - r) * p_unif
        ci = rng.choice(rem.size, p=qvec)
        chosen = int(rem[ci])
        selected.append(chosen); remaining.remove(chosen); qs.append(float(qvec[ci]))

    sel = np.array(selected)
    qa = np.array(qs)
    zz = z[sel]; pp = p[sel]
    y = pp * zz                          # y_i = p_i z_i
    # DeepSample-style adaptive total (Eq. 8 adapted; y already carries p,
    # so the outer 1/N is dropped). Hajek normalization is NOT valid for the
    # adaptive design and introduces bias, so we use the native total form.
    n2 = len(sel)
    y1 = y[0]
    sum_prev = y1
    step_totals = []
    for t in range(1, n2):
        step_totals.append(sum_prev + y[t] / qa[t])
        sum_prev += y[t]
    theta = float((y1 + sum(step_totals)) / n2)
    return theta, int(zz.sum())
