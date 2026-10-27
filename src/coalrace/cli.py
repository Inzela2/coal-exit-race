"""python -m coalrace report [--start 2015 --end 2024 --min-twh 50]"""
import argparse
import json
from pathlib import Path
from . import data, model, decompose, flags, sensitivity, plots

RESULTS = Path("results")
FOCUS = ["United Kingdom", "Germany", "Australia", "United States", "China", "India", "Venezuela"]


def report(start=2015, end=2024, min_twh=50, focus_country="Australia"):
    RESULTS.mkdir(exist_ok=True)
    df = data.load(data.download())

    rows = model.training_rows(df)
    factors = model.fit(rows)
    in_sample = model.r2(rows["carbon_intensity_elec"], model.predict(factors, rows))
    held_out = model.grouped_cv(rows)

    att = decompose.attribute(decompose.changes(df, start, end, min_twh), factors)
    flagged = flags.flag(att)
    clean = flagged[flagged["flags"] == ""]
    big_coal_cut = flagged[flagged["d_coal"] < -5]

    out = {
        "model": {"factors_g_per_kwh": {k: round(v) for k, v in factors.items()},
                  "n_country_years": len(rows), "n_countries": rows["country"].nunique(),
                  "r2_in_sample": round(in_sample, 3), "r2_held_out_countries": round(held_out, 3)},
        "n_countries": len(flagged),
        "top5_raw": flagged.head(5)[["pct", "flags"]].round(1).to_dict("index"),
        "top5_unflagged": clean.head(5)[["pct"]].round(1).to_dict("index"),
        "focus": {focus_country: {
            "rank": list(flagged.index).index(focus_country) + 1,
            "rank_unflagged": list(clean.index).index(focus_country) + 1 if focus_country in clean.index else None,
            "n_unflagged": len(clean),
            **flagged.loc[focus_country, ["ci_start", "ci_end", "pct", "d_coal", "d_gas", "d_wind", "d_solar",
                                          "from_coal", "from_gas", "residual"]].round(1).to_dict()}},
        "coal_replacement": {"countries": len(big_coal_cut),
                             "avg_d_coal": round(big_coal_cut["d_coal"].mean(), 1),
                             "avg_d_wind_solar": round(big_coal_cut["d_wind_solar"].mean(), 1),
                             "avg_d_gas": round(big_coal_cut["d_gas"].mean(), 1)},
        "corr_pct_vs_wind_solar": round(flagged["pct"].corr(flagged["d_wind_solar"]), 2),
        "flagged": flagged[flagged["flags"] != ""][["pct", "gen_change_pct", "clean_twh_change_pct", "d_hydro", "flags"]].round(1).to_dict("index"),
        "sensitivity": sensitivity.rank_grid(df, focus_country, factors),
    }
    plots.race(flagged, RESULTS / "coal_exit_race.png", start, end)
    plots.attribution(att, FOCUS, RESULTS / "attribution.png")
    flagged.round(2).to_csv(RESULTS / "leaderboard.csv")
    (RESULTS / "summary.json").write_text(json.dumps(out, indent=2, default=str))
    return out


def main():
    p = argparse.ArgumentParser(prog="coalrace")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report")
    r.add_argument("--start", type=int, default=2015)
    r.add_argument("--end", type=int, default=2024)
    r.add_argument("--min-twh", type=float, default=50)
    r.add_argument("--country", default="Australia")
    a = p.parse_args()
    print(json.dumps(report(a.start, a.end, a.min_twh, a.country), indent=2, default=str))


if __name__ == "__main__":
    main()
