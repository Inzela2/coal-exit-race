"""Flag leaderboard entries that may not reflect a genuine clean-energy transition.

A falling carbon intensity should mean clean generation replaced fossil
generation. These rules catch the cases where the number improved for another
reason. Thresholds are simple and kept in one place.
"""
import pandas as pd

RULES = {
    "shrinking_not_cleaning": "total generation fell 15%+ while clean generation (TWh) did not grow",
    "hydro_swing": "hydro share moved 15+ percentage points, which often reflects rainfall rather than policy",
    "unexplained": "fossil-share changes explain less than half of the intensity change",
}


def flag(att: pd.DataFrame) -> pd.DataFrame:
    out = att.copy()
    out["shrinking_not_cleaning"] = (out["gen_change_pct"] < -15) & (out["clean_twh_change_pct"] <= 0)
    out["hydro_swing"] = out["d_hydro"].abs() > 15
    explained = out["d_ci"] - out["residual"]
    out["unexplained"] = (out["d_ci"].abs() > 20) & (explained.abs() < 0.5 * out["d_ci"].abs())
    out["flags"] = out[list(RULES)].apply(lambda r: ", ".join(k for k in RULES if r[k]), axis=1)
    return out
