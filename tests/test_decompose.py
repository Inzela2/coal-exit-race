import numpy as np
import pandas as pd
from coalrace.data import SOURCES
from coalrace.decompose import changes, attribute
from coalrace.flags import flag

FACTORS = {"coal": 900, "gas": 500, "oil": 650, "intercept": 10}


def _df():
    rows = []
    spec = {  # country: (start shares, end shares, start gen, end gen, start ci, end ci)
        "Coalland": ({"coal": 80, "gas": 10}, {"coal": 40, "gas": 10, "wind": 40}, 100, 100, 760, 400),
        "Rainland": ({"gas": 50, "hydro": 50}, {"gas": 15, "hydro": 85}, 100, 60, 250, 85),
        "Tiny": ({"coal": 90}, {"coal": 10}, 5, 5, 800, 100),
    }
    for c, (s0, s1, g0, g1, ci0, ci1) in spec.items():
        for year, shares, gen, ci in [(2015, s0, g0, ci0), (2024, s1, g1, ci1)]:
            row = dict(country=c, year=year, electricity_generation=gen, carbon_intensity_elec=ci)
            row.update({f"{s}_share_elec": shares.get(s, 0.0) for s in SOURCES})
            rows.append(row)
    return pd.DataFrame(rows)


def test_size_threshold_excludes_small_grids():
    assert "Tiny" not in changes(_df(), 2015, 2024, min_twh=50).index


def test_attribution_is_an_exact_identity():
    att = attribute(changes(_df(), 2015, 2024, 50), FACTORS)
    rebuilt = att["from_coal"] + att["from_gas"] + att["from_oil"] + att["residual"]
    assert np.allclose(rebuilt, att["d_ci"])


def test_flags_catch_hydro_swing_but_not_genuine_transition():
    f = flag(attribute(changes(_df(), 2015, 2024, 50), FACTORS))
    assert f.loc["Coalland", "flags"] == ""
    assert "hydro_swing" in f.loc["Rainland", "flags"]
    assert "shrinking_not_cleaning" not in f.loc["Rainland", "flags"]  # hydro TWh grew



def _country(name, s0, s1, g0, g1, ci0, ci1):
    rows = []
    for year, shares, gen, ci in [(2015, s0, g0, ci0), (2024, s1, g1, ci1)]:
        row = dict(country=name, year=year, electricity_generation=gen, carbon_intensity_elec=ci)
        row.update({f"{s}_share_elec": shares.get(s, 0.0) for s in SOURCES})
        rows.append(row)
    return rows


def test_shrinking_grid_with_no_clean_growth_is_flagged():
    # fossil output collapsed, clean output fell too (30 -> 27 TWh): intensity improved, mix did not
    df = pd.DataFrame(_country("Shrinkland", {"coal": 70, "hydro": 30}, {"coal": 55, "hydro": 45},
                               100, 60, 640, 500))
    f = flag(attribute(changes(df, 2015, 2024, 50), FACTORS))
    assert "shrinking_not_cleaning" in f.loc["Shrinkland", "flags"]


def test_shrinking_grid_with_clean_growth_is_not_flagged():
    # like the UK: demand fell but wind grew in absolute terms
    df = pd.DataFrame(_country("Windland", {"coal": 70, "wind": 30}, {"coal": 30, "wind": 70},
                               100, 80, 640, 280))
    f = flag(attribute(changes(df, 2015, 2024, 50), FACTORS))
    assert f.loc["Windland", "flags"] == ""
