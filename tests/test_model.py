import numpy as np
import pandas as pd
from coalrace.model import fit, grouped_cv


def _synthetic(n_countries=30, years=10, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(n_countries):
        for y in range(years):
            coal, gas = rng.uniform(0, 60), rng.uniform(0, 30)
            oil = rng.uniform(0, 5)
            ci = 900 * coal / 100 + 450 * gas / 100 + 650 * oil / 100 + 15 + rng.normal(0, 5)
            rows.append(dict(country=f"C{c}", year=y, coal_share_elec=coal, gas_share_elec=gas,
                             oil_share_elec=oil, carbon_intensity_elec=ci, electricity_generation=100))
    return pd.DataFrame(rows)


def test_fit_recovers_known_factors():
    f = fit(_synthetic())
    assert abs(f["coal"] - 900) < 15 and abs(f["gas"] - 450) < 20


def test_grouped_cv_is_high_when_model_is_true():
    assert grouped_cv(_synthetic()) > 0.98
