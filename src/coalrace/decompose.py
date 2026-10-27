"""Split each country's change in carbon intensity into contributions from
coal, gas and oil share changes, plus a residual.

Change = Σ factor_i × Δshare_i + residual, which holds exactly by construction.
The residual captures what shares miss (plant efficiency, fuel quality,
reporting changes) and is used as a warning sign.
"""
import pandas as pd
from .data import FOSSIL, SOURCES, CLEAN


def changes(df: pd.DataFrame, start: int, end: int, min_twh: float) -> pd.DataFrame:
    a = df[df["year"] == start].set_index("country")
    b = df[df["year"] == end].set_index("country")
    large = b.index[b["electricity_generation"] >= min_twh].intersection(a.index)
    a, b = a.loc[large], b.loc[large]
    out = pd.DataFrame(index=large)
    out["ci_start"], out["ci_end"] = a["carbon_intensity_elec"], b["carbon_intensity_elec"]
    out["d_ci"] = out["ci_end"] - out["ci_start"]
    out["pct"] = 100 * out["d_ci"] / out["ci_start"]
    out["gen_change_pct"] = 100 * (b["electricity_generation"] / a["electricity_generation"] - 1)
    for s in SOURCES:
        out[f"d_{s}"] = b[f"{s}_share_elec"] - a[f"{s}_share_elec"]
    out["d_wind_solar"] = out["d_wind"] + out["d_solar"]
    clean = [f"{s}_share_elec" for s in CLEAN]
    clean_a = a[clean].fillna(0).sum(axis=1) / 100 * a["electricity_generation"]
    clean_b = b[clean].fillna(0).sum(axis=1) / 100 * b["electricity_generation"]
    out["clean_twh_change_pct"] = 100 * (clean_b / clean_a.where(clean_a > 0) - 1)
    return out.dropna(subset=["pct"]).sort_values("pct")


def attribute(ch: pd.DataFrame, factors: dict) -> pd.DataFrame:
    out = ch.copy()
    explained = 0
    for f in FOSSIL:
        out[f"from_{f}"] = out[f"d_{f}"].fillna(0) / 100 * factors[f]
        explained = explained + out[f"from_{f}"]
    out["residual"] = out["d_ci"] - explained
    return out
