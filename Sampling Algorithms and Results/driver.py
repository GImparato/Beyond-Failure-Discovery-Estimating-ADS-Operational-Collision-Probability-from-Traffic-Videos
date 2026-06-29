"""
OASIS driver: runs the full factorial design with corrected estimators
and writes a CSV file

  sampling_method,profile,aux_var,partitioning,budget,run_id,
  theta_hat,theta_true,failures_obs,execution_time
"""
import time
import numpy as np
import pandas as pd
import estimators_fixed as E

SRC = '/mnt/user-data/uploads/scenario_metrics.csv'
OUT = '/home/claude/oasis/ICSE_corrected_results.csv'

PROFILES = ['P0', 'P1', 'P2', 'P3']
AUXES = ['PC', 'TTC']
BUDGETS = [50, 100, 200, 300, 400]
RUNS = 30

# 8 techniques = method x partitioning (partition-based have ODD/HDBSCAN variants)
TECHS = [
    ('SRS', 'none'),
    ('SUPS', 'none'),
    ('RHC', 'none'),
    ('DEEPEST', 'none'),
    ('SSRS', 'ODD'), ('SSRS', 'HDBSCAN'),
    ('2UPS', 'ODD'), ('2UPS', 'HDBSCAN'),
]


def load():
    df = pd.read_csv(SRC).reset_index(drop=True)
    z = df['collision_occurred'].astype(str).str.lower().isin(
        ['true', '1', '1.0']).astype(int).to_numpy()
    df['_z'] = z
    df['_sid'] = np.arange(len(df))
    # auxiliaries (risk-increasing): PC = probability_of_collision,
    # TTC transform = 1/(ttc_min+eps) so larger => higher risk
    df['PC'] = df['probability_of_collision'].astype(float)
    df['TTC'] = 1.0 / (df['ttc_min'].astype(float) + 1e-3)
    return df


def make_profile(df, kind, seed=12345):
    N = len(df); rng = np.random.default_rng(seed)
    if kind == 'P0':
        w = np.ones(N)
    elif kind == 'P1':
        w = rng.uniform(0, 1, N)
    elif kind == 'P2':
        lam_v = {'good': 1, 'moderate': 2, 'poor': 3}
        lam_i = {'day': 1, 'dusk_dawn': 2, 'night': 3}
        lam_p = {False: 1, True: 2}
        w = (df['visibility'].map(lam_v) * df['illumination'].map(lam_i)
             * df['precipitation_visible'].map(lam_p)).to_numpy()
    elif kind == 'P3':
        lam_m = {'on_road_following': 1, 'lane_change': 2,
                 'roundabout': 3, 'intersection': 4}
        lam_t = {'low': 1, 'medium': 2, 'high': 3}
        w = (df['odd_main_category'].map(lam_m)
             * df['traffic_density'].map(lam_t)).to_numpy()
    w = w.astype(float)
    return w / w.sum()


def hdbscan_partition(df, aux):
    """Cluster on the auxiliary; fall back to quantile bins if hdbscan absent."""
    try:
        import hdbscan
        from sklearn.preprocessing import StandardScaler
        X = StandardScaler().fit_transform(df[[aux]].values)
        lab = hdbscan.HDBSCAN(min_cluster_size=30).fit_predict(X)
        lab = pd.Series(lab, index=df.index)
        # merge noise (-1) into nearest by value via quantile fallback
        if (lab == -1).any():
            q = pd.qcut(df[aux].rank(method='first'), 10, labels=False)
            lab = lab.where(lab != -1, 1000 + q)
        return lab.to_numpy()
    except Exception:
        return pd.qcut(df[aux].rank(method='first'), 10,
                       labels=False).to_numpy()


def odd_partition(df):
    return (df['odd_main_category'].astype(str) + '_'
            + df['traffic_density'].astype(str)).to_numpy()


def main():
    df = load()
    # ground truth per profile
    profiles = {k: make_profile(df, k) for k in PROFILES}
    theta_true = {k: float((profiles[k] * df['_z'].to_numpy()).sum())
                  for k in PROFILES}
    print("theta_true:", {k: round(v, 4) for k, v in theta_true.items()})

    # precompute partitions (independent of profile/run)
    part = {
        'ODD': odd_partition(df),
        'HDBSCAN_PC': hdbscan_partition(df, 'PC'),
        'HDBSCAN_TTC': hdbscan_partition(df, 'TTC'),
    }

    rows = []
    for prof in PROFILES:
        d = df.copy()
        d['_p'] = profiles[prof]
        for aux in AUXES:
            d['_part_ODD'] = part['ODD']
            d['_part_HDB'] = part[f'HDBSCAN_{aux}']
            for (meth, pt) in TECHS:
                for budget in BUDGETS:
                    for run in range(1, RUNS + 1):
                        # Common Random Numbers: seed depends only on the run
                        # context, NOT the technique, so all techniques face the
                        # same random draws within a run -> paired blocks for
                        # the Friedman test (matches DeepSample methodology).
                        seed = hash((prof, aux, budget, run)) % (2**32)
                        rng = np.random.default_rng(seed)
                        t0 = time.perf_counter()
                        if meth == 'SRS':
                            th, obs = E.srs_run(d, budget, rng)
                        elif meth == 'SUPS':
                            th, obs = E.sups_run(d, budget, aux, rng)
                        elif meth == 'RHC':
                            th, obs = E.rhc_run(d, budget, aux, rng)
                        elif meth == 'DEEPEST':
                            th, obs = E.deepest_run(d, budget, aux, rng)
                        elif meth == 'SSRS':
                            pc = '_part_ODD' if pt == 'ODD' else '_part_HDB'
                            th, obs = E.ssrs_run(d, budget, pc, rng)
                        elif meth == '2UPS':
                            pc = '_part_ODD' if pt == 'ODD' else '_part_HDB'
                            th, obs = E.twoups_run(d, budget, aux, pc, rng)
                        dt = time.perf_counter() - t0
                        rows.append((meth, prof, aux, pt, budget, run,
                                     th, theta_true[prof], obs, dt))
    out = pd.DataFrame(rows, columns=[
        'sampling_method', 'profile', 'aux_var', 'partitioning', 'budget',
        'run_id', 'theta_hat', 'theta_true', 'failures_obs', 'execution_time'])
    out.to_csv(OUT, index=False)
    print("wrote", OUT, out.shape)


if __name__ == '__main__':
    main()
