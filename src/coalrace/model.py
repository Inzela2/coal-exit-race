"""Emission factors fitted from the data, and a check that they generalise.

The decomposition later relies on one assumption: a grid's carbon intensity is
roughly a weighted sum of its coal, gas and oil shares. We test that before
leaning on it. Cross-validation holds out whole countries, because a random
split would let the model see other years of the same country and look better
than it is.
"""
import numpy as np
import pandas as pd
from .data import FOSSIL

SHARE_COLS = [f"{f}_share_elec" for f in FOSSIL]


def _design(df):
    X = df[SHARE_COLS].fillna(0).to_numpy() / 100
    return np.c_[X, np.ones(len(X))]


def training_rows(df: pd.DataFrame, min_twh: float = 10) -> pd.DataFrame:
    keep = df.dropna(subset=["carbon_intensity_elec"] + SHARE_COLS[:2])
    return keep[keep["electricity_generation"] >= min_twh]


def fit(df: pd.DataFrame) -> dict:
    """Least squares: intensity ≈ f_coal·coal + f_gas·gas + f_oil·oil + c (g CO2/kWh)."""
    coef, *_ = np.linalg.lstsq(_design(df), df["carbon_intensity_elec"].to_numpy(), rcond=None)
    return dict(zip(FOSSIL + ["intercept"], coef))


def predict(factors: dict, df: pd.DataFrame) -> np.ndarray:
    return _design(df) @ np.array([factors[k] for k in FOSSIL + ["intercept"]])


def r2(y, yhat) -> float:
    y = np.asarray(y)
    return 1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def grouped_cv(df: pd.DataFrame, k: int = 5, seed: int = 0) -> float:
    """R² on countries the model never saw during fitting."""
    countries = df["country"].unique()
    rng = np.random.default_rng(seed)
    folds = np.array_split(rng.permutation(countries), k)
    y_all, p_all = [], []
    for held_out in folds:
        test = df["country"].isin(held_out)
        f = fit(df[~test])
        y_all.append(df.loc[test, "carbon_intensity_elec"].to_numpy())
        p_all.append(predict(f, df[test]))
    return r2(np.concatenate(y_all), np.concatenate(p_all))
