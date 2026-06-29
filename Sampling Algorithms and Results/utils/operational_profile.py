import numpy as np
import pandas as pd


# =========================================================
# OPERATIONAL PROFILE — SCENARIO LEVEL
# =========================================================

def generate_operational_profile(
    df: pd.DataFrame,
    mode: str = "uniform_random",
    seed: int | None = None
) -> np.ndarray:
    """
    Generate an operational profile p_i such that sum(p_i) = 1,
    defined at SCENARIO level.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset of scenarios
    mode : str
        - "uniform"          : p_i = 1/N
        - "uniform_random"   : random + normalization
        - "dirichlet"        : Dirichlet(alpha=1)
    seed : int or None
        Random seed for reproducibility

    Returns
    -------
    p_i : np.ndarray
        Operational profile probabilities (length = N)
    """

    rng = np.random.default_rng(seed)
    N = len(df)

    if N == 0:
        raise ValueError("Dataset is empty")

    if mode == "uniform":
        p_i = np.ones(N) / N

    elif mode == "uniform_random":
        raw = rng.random(N)
        p_i = raw / raw.sum()

    elif mode == "dirichlet":
        p_i = rng.dirichlet(alpha=np.ones(N))

    else:
        raise ValueError(f"Unknown operational profile mode: {mode}")

    # safety check
    if not np.isclose(p_i.sum(), 1.0):
        raise RuntimeError("Operational profile does not sum to 1")

    return p_i


# =========================================================
# OPERATIONAL PROFILE — PROFILE / STRATUM LEVEL
# =========================================================

def generate_profile_distribution(
    df: pd.DataFrame,
    profile_col: str,
) -> dict:
    """
    Generate an operational profile at PROFILE level:

        profile_value -> probability mass

    Used for stratified / profile-based sampling
    (DEEPEST with profiles, GBS, SUPS, 2UPS, etc.)
    """

    if profile_col not in df.columns:
        raise ValueError(f"Column '{profile_col}' not found in dataframe")

    profile_dist = df[profile_col].value_counts(normalize=True)

    return profile_dist.to_dict()
