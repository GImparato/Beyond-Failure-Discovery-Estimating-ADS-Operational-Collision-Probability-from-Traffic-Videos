"""
Generate the ODDRISK auxiliary slice (for RQ4: auxiliary informativeness).

Output: oddrisk_results.csv  (same schema as the canonical results CSV).
Merge with the canonical PC/TTC run to obtain ICSE_results_3aux.csv 
"""
import time
import numpy as np
import pandas as pd
import estimators_fixed as E

SRC = '/mnt/user-data/uploads/scenario_metrics.csv'   # adjust path for your repo
OUT = 'oddrisk_results.csv'

PROFILES = ['P0', 'P1', 'P2', 'P3']
BUDGETS = [50, 100, 200, 300, 400]
RUNS = 30
TECHS = [('SRS', 'none'), ('SUPS', 'none'), ('RHC', 'none'), ('DEEPEST', 'none'),
         ('SSRS', 'ODD'), ('SSRS', 'HDBSCAN'),
         ('2UPS', 'ODD'), ('2UPS', 'HDBSCAN')]

# ODD ordinal multipliers (perceived risk)
LAM_T = {'low': 1, 'medium': 2, 'high': 3}
LAM_V = {'good': 1, 'moderate': 2, 'poor': 3}
LAM_I = {'day': 1, 'dusk_dawn': 2, 'night': 3}
LAM_P = {False: 1, True: 2}


def load():
    df = pd.read_csv(SRC).reset_index(drop=True)
    df['_z'] = df['collision_occurred'].astype(str).str.lower().isin(
        ['true', '1', '1.0']).astype(int)
    df['_sid'] = np.arange(len(df))
    df['ODDRISK'] = (df['traffic_density'].map(LAM_T) * df['visibility'].map(LAM_V)
                     * df['illumination'].map(LAM_I)
                     * df['precipitation_visible'].map(LAM_P)).astype(float)
    return df


def make_profile(df, kind, seed=12345):
    N = len(df); rng = np.random.default_rng(seed)
    if kind == 'P0':
        w = np.ones(N)
    elif kind == 'P1':
        w = rng.uniform(0, 1, N)
    elif kind == 'P2':
        w = (df['visibility'].map(LAM_V) * df['illumination'].map(LAM_I)
             * df['precipitation_visible'].map(LAM_P)).to_numpy()
    elif kind == 'P3':
        lam_m = {'on_road_following': 1, 'lane_change': 2,
                 'roundabout': 3, 'intersection': 4}
        w = (df['odd_main_category'].map(lam_m)
             * df['traffic_density'].map(LAM_T)).to_numpy()
    w = w.astype(float)
    return w / w.sum()


def main():
    df = load()
    # ODDRISK is discrete; strata = 10 rank-based value groups (HDBSCAN-style slot)
    df['_part_HDB'] = pd.qcut(df['ODDRISK'].rank(method='first'), 10,
                              labels=False).to_numpy()
    df['_part_ODD'] = (df['odd_main_category'].astype(str) + '_'
                       + df['traffic_density'].astype(str)).to_numpy()
    rows = []
    for prof in PROFILES:
        d = df.copy(); d['_p'] = make_profile(df, prof)
        tt = float((d['_p'] * d['_z']).sum())
        for (meth, pt) in TECHS:
            for budget in BUDGETS:
                for run in range(1, RUNS + 1):
                    seed = hash((prof, 'ODDRISK', budget, run)) % (2**32)
                    rng = np.random.default_rng(seed)
                    t0 = time.perf_counter()
                    if meth == 'SRS':
                        th, obs = E.srs_run(d, budget, rng)
                    elif meth == 'SUPS':
                        th, obs = E.sups_run(d, budget, 'ODDRISK', rng)
                    elif meth == 'RHC':
                        th, obs = E.rhc_run(d, budget, 'ODDRISK', rng)
                    elif meth == 'DEEPEST':
                        th, obs = E.deepest_run(d, budget, 'ODDRISK', rng)
                    elif meth == 'SSRS':
                        pc = '_part_ODD' if pt == 'ODD' else '_part_HDB'
                        th, obs = E.ssrs_run(d, budget, pc, rng)
                    elif meth == '2UPS':
                        pc = '_part_ODD' if pt == 'ODD' else '_part_HDB'
                        th, obs = E.twoups_run(d, budget, 'ODDRISK', pc, rng)
                    rows.append((meth, prof, 'ODDRISK', pt, budget, run,
                                 th, tt, obs, time.perf_counter() - t0))
    out = pd.DataFrame(rows, columns=[
        'sampling_method', 'profile', 'aux_var', 'partitioning', 'budget',
        'run_id', 'theta_hat', 'theta_true', 'failures_obs', 'execution_time'])
    out.to_csv(OUT, index=False)
    print('wrote', OUT, out.shape)
    # merge with canonical PC/TTC run -> 3-aux dataset
    try:
        can = pd.read_csv('ICSE_corrected_results.csv')
        pd.concat([can, out], ignore_index=True).to_csv(
            'ICSE_results_3aux.csv', index=False)
        print('wrote ICSE_results_3aux.csv')
    except FileNotFoundError:
        print('canonical ICSE_corrected_results.csv not found; skipped merge')


if __name__ == '__main__':
    main()
