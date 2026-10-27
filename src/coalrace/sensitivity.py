"""Does the ranking survive different, equally reasonable analysis choices?

Start year, end year and the size cut-off are judgement calls. If a result
swings across them, it should not be quoted alone. Ranks are reported as
percentiles, because the number of countries changes with the cut-off.
"""
import itertools
from .decompose import changes, attribute
from .flags import flag


def rank_grid(df, country: str, factors: dict, starts=(2014, 2015, 2016), ends=(2023, 2024),
              thresholds=(20, 50, 100), top_n: int = 5) -> dict:
    pct, raw_top, clean_top, runs = [], {}, {}, 0
    for s, e, t in itertools.product(starts, ends, thresholds):
        f = flag(attribute(changes(df, s, e, t), factors))
        runs += 1
        if country in f.index:
            pct.append((list(f.index).index(country) + 1) / len(f))
        for c in f.index[:top_n]:
            raw_top[c] = raw_top.get(c, 0) + 1
        for c in f[f["flags"] == ""].index[:top_n]:
            clean_top[c] = clean_top.get(c, 0) + 1
    top = lambda d: {k: round(v / runs, 2) for k, v in sorted(d.items(), key=lambda kv: -kv[1])[:6]}
    return {"runs": runs, "percentile_range": (round(min(pct), 2), round(max(pct), 2)),
            "top5_frequency_raw": top(raw_top), "top5_frequency_after_flags": top(clean_top)}
