"""
Runs the full SQL pipeline:
  1. Loads the raw CSV into SQLite (ipl.db)
  2. Executes sql/01_clean_and_model.sql  (cleaning + modelling)
  3. Executes every query in sql/02_analysis_queries.sql
  4. Saves each result to outputs/tables/<query>.csv
  5. Draws charts into outputs/charts/

Usage:  python src/run_analysis.py
"""
import re
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "ipl.db"
TABLES = ROOT / "outputs" / "tables"
CHARTS = ROOT / "outputs" / "charts"
TABLES.mkdir(parents=True, exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10})
BLUE, ORANGE, GREY = "#1f4e79", "#e8772e", "#9aa5b1"


def load_and_clean(conn):
    pd.read_csv(ROOT / "data" / "ipl_matches_data_2026.csv").to_sql(
        "raw_matches", conn, if_exists="replace", index=False)
    conn.executescript((ROOT / "sql" / "01_clean_and_model.sql").read_text())


def run_queries(conn):
    text = (ROOT / "sql" / "02_analysis_queries.sql").read_text()
    parts = re.split(r"^-- name: (\w+)\s*$", text, flags=re.M)
    results = {}
    for name, sql in zip(parts[1::2], parts[2::2]):
        df = pd.read_sql_query(sql, conn)
        df.to_csv(TABLES / f"{name}.csv", index=False)
        results[name] = df
        print(f"{name:<36} {len(df):>4} rows")
    return results


def charts(r):
    # 1. All-time win %
    d = r["q03_all_time_team_table"].sort_values("win_pct")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(d["team"], d["win_pct"], color=BLUE)
    ax.axvline(50, color=GREY, ls="--", lw=1)
    ax.set_xlabel("Win % (excluding no-results)")
    ax.set_title("All-time win % by franchise (min 50 matches)")
    for y, v in enumerate(d["win_pct"]):
        ax.text(v + 0.3, y, f"{v}%", va="center", fontsize=8)
    fig.tight_layout(); fig.savefig(CHARTS / "01_alltime_win_pct.png"); plt.close(fig)

    # 2. Chase win % by season + 3yr moving avg
    d = r["q07_bat_first_vs_chase_by_season"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(d["season"], d["chase_win_pct"], color=GREY, label="Chasing team win %")
    ax.plot(d["season"], d["moving_avg_3yr"], color=ORANGE, lw=2.5, marker="o",
            label="3-season moving avg")
    ax.axhline(50, color="black", ls="--", lw=1)
    ax.set_ylim(30, 75); ax.set_xticks(d["season"]); ax.tick_params(axis="x", rotation=60)
    ax.set_ylabel("%"); ax.set_title("Is chasing an advantage? Chasing-team win % by season")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(CHARTS / "02_chase_win_pct_trend.png"); plt.close(fig)

    # 3. Toss decision trend
    d = r["q06_toss_decision_trend"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(d["season"], d["pct_field_first"], color=BLUE, lw=2.5, marker="o",
            label="% of tosses choosing to field")
    ax.plot(d["season"], d["toss_winner_win_pct"], color=ORANGE, lw=2.5, marker="s",
            label="Toss winner's win %")
    ax.axhline(50, color=GREY, ls="--", lw=1)
    ax.set_xticks(d["season"]); ax.tick_params(axis="x", rotation=60)
    ax.set_title("Captains now field first far more often, but the toss barely decides matches")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(CHARTS / "03_toss_trend.png"); plt.close(fig)

    # 4. Venue profile
    d = r["q08_venue_profile"].sort_values("chase_win_pct").copy()
    d["venue"] = d["venue"].str.replace("Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium",
                                        "Ekana Stadium", regex=False)
    colors = [ORANGE if v >= 55 else BLUE if v <= 45 else GREY for v in d["chase_win_pct"]]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh(d["venue"], d["chase_win_pct"], color=colors)
    ax.axvline(50, color="black", ls="--", lw=1)
    ax.set_xlabel("Chasing-team win %")
    ax.set_title("Chasing-team win % by stadium (orange = 55%+, chase-friendly)", loc="right", fontsize=10)
    fig.tight_layout(); fig.savefig(CHARTS / "04_venue_profile.png"); plt.close(fig)

    # 5. Titles
    d = r["q04_titles_won"].sort_values("titles")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(d["champion"], d["titles"], color=BLUE)
    for y, v in enumerate(d["titles"]):
        ax.text(v + 0.05, y, str(v), va="center")
    ax.set_title("IPL titles by franchise (2008–2026)")
    fig.tight_layout(); fig.savefig(CHARTS / "05_titles.png"); plt.close(fig)

    # 6. Player of the match
    d = r["q10_top_player_of_match"].head(10).sort_values("awards")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(d["player"], d["awards"], color=ORANGE)
    ax.set_title("Most Player-of-the-Match awards")
    fig.tight_layout(); fig.savefig(CHARTS / "06_player_of_match.png"); plt.close(fig)

    # 7. Close-match win %
    d = r["q14_close_match_performance"].sort_values("close_win_pct")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(d["team"], d["close_win_pct"], color=BLUE)
    ax.axvline(50, color=GREY, ls="--", lw=1)
    ax.set_xlabel("Win % in close games")
    ax.set_title("Clutch factor: win % in close matches (min 25 close games)")
    fig.tight_layout(); fig.savefig(CHARTS / "07_close_matches.png"); plt.close(fig)

    # 8. Cumulative wins for top franchises
    d = r["q16_cumulative_wins"]
    top = d.groupby("team")["wins_in_season"].sum().nlargest(5).index
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for t in top:
        x = d[d["team"] == t]
        ax.plot(x["season"], x["cumulative_wins"], lw=2, label=t)
    ax.set_title("Cumulative wins of the 5 winningest franchises")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(CHARTS / "08_cumulative_wins.png"); plt.close(fig)


if __name__ == "__main__":
    DB.unlink(missing_ok=True)
    with sqlite3.connect(DB) as conn:
        load_and_clean(conn)
        res = run_queries(conn)
    charts(res)
    print("\nDone. Tables -> outputs/tables, charts -> outputs/charts")
