import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LABEL = ["Australia", "United Kingdom", "Germany", "Netherlands", "Venezuela",
         "China", "India", "United States", "Spain"]


def race(flagged, path, start, end):
    fig, ax = plt.subplots(figsize=(8, 4.8))
    clean, warn = flagged[flagged["flags"] == ""], flagged[flagged["flags"] != ""]
    ax.scatter(clean["d_wind_solar"], clean["pct"], color="grey", s=25, label="no flags")
    ax.scatter(warn["d_wind_solar"], warn["pct"], facecolors="none", edgecolors="#e67e22",
               s=45, lw=1.5, label="flagged (see table)")
    for n in LABEL:
        if n in flagged.index:
            r = flagged.loc[n]
            if r["flags"]:
                ax.scatter(r["d_wind_solar"], r["pct"], facecolors="none", edgecolors="#e67e22", s=60, lw=2)
            else:
                ax.scatter(r["d_wind_solar"], r["pct"], color="#c0392b" if n == "Australia" else "#2c7fb8", s=35)
            ax.annotate(n, (r["d_wind_solar"], r["pct"]), xytext=(4, 3), textcoords="offset points", fontsize=8)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xlabel(f"Change in wind + solar share of electricity, {start}–{end} (pct points)")
    ax.set_ylabel("Change in grid carbon intensity (%)")
    ax.set_title(f"The coal-exit race: {len(flagged)} countries generating 50+ TWh")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def attribution(att, countries, path):
    sub = att.loc[[c for c in countries if c in att.index]]
    parts = ["from_coal", "from_gas", "from_oil", "residual"]
    colours = ["#4d4d4d", "#e6a100", "#8c564b", "#bdbdbd"]
    fig, ax = plt.subplots(figsize=(8, 4))
    left_pos = [0] * len(sub)
    left_neg = [0] * len(sub)
    for p, c in zip(parts, colours):
        vals = sub[p].to_numpy()
        lefts = [lp if v >= 0 else ln for v, lp, ln in zip(vals, left_pos, left_neg)]
        ax.barh(sub.index, vals, left=lefts, color=c, label=p.replace("from_", "").replace("residual", "other / residual"))
        left_pos = [lp + max(v, 0) for v, lp in zip(vals, left_pos)]
        left_neg = [ln + min(v, 0) for v, ln in zip(vals, left_neg)]
    ax.scatter(sub["d_ci"], sub.index, color="k", zorder=3, s=18, label="net change")
    ax.axvline(0, color="k", lw=0.6)
    ax.set_xlabel("Contribution to change in carbon intensity (g CO2/kWh)")
    ax.set_title("What drove each country's change")
    ax.invert_yaxis()
    ax.legend(frameon=False, fontsize=8, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
