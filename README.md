# IPL Match Analytics with SQL (2008–2026)

**Live Dashboard:** [https://riyaa9099.github.io/ipl-sql-analysis/](https://riyaa9099.github.io/ipl-sql-analysis/)

End-to-end data analysis of **1,243 IPL matches across 19 seasons** using **SQL (SQLite)** for cleaning, modelling and analysis, and **Python (pandas, matplotlib)** for orchestration and visualisation.

**Business questions answered**
1. Does winning the toss matter, and has captains' toss behaviour changed?
2. Is chasing really an advantage, overall and at each stadium?
3. Which franchises are the most consistent, the most "clutch", and the biggest turnaround stories?
4. Do teams actually enjoy a home advantage?
5. Who wins the most Player-of-the-Match awards?

## Interactive dashboard
Explore the results live: **[https://riyaa9099.github.io/ipl-sql-analysis/](https://riyaa9099.github.io/ipl-sql-analysis/)**

It includes a franchise explorer, stadium profiles, home vs away win %, toss trends and close-match performance, all generated from the SQL outputs via `python dashboard/build_dashboard.py`.

## Tech stack
SQL (SQLite) · Python 3 · pandas · matplotlib · Chart.js

## Project structure
```
ipl-sql-analysis/
├── data/                      # raw match + team CSVs
├── sql/
│   ├── 01_clean_and_model.sql # cleaning, venue standardisation, fact tables
│   └── 02_analysis_queries.sql# 16 analysis queries
├── src/run_analysis.py        # loads data, runs SQL, exports tables + charts
├── dashboard/                 # interactive HTML dashboard (index.html + builder)
├── outputs/
│   ├── tables/                # one CSV per query
│   └── charts/                # 8 PNG charts
└── requirements.txt
```
Run it: `pip install -r requirements.txt && python src/run_analysis.py`

## Data cleaning & modelling (SQL)
- **Venue standardisation:** 41 raw stadium names mapped to **36 unique grounds** (e.g. *Feroz Shah Kotla* = *Arun Jaitley Stadium*, *Sardar Patel Stadium, Motera* = *Narendra Modi Stadium*, Bangalore/Bengaluru spellings).
- **Ties:** the super-over winner (stored in the `eliminator` column) is used to build an `effective_winner`, so tied matches still have a winner and the 9 "no result" games are excluded from win % calculations.
- **Derived columns:** `batting_first` and `chasing` derived from toss winner + toss decision; `is_playoff` flag.
- **Modelling:** a `team_match` table (one row per team per match, built with `UNION ALL`) makes team-level aggregations simple.
- **Validation:** `q01` checks row counts, seasons, ties, no-results and missing winners (0 missing).

## SQL concepts used
`JOIN` · self-join · `CTE` · `GROUP BY / HAVING` · `CASE WHEN` · subqueries · `UNION ALL` · window functions: `RANK`, `DENSE_RANK`, `ROW_NUMBER`, `LAG`, running `SUM() OVER`, moving `AVG() OVER`

## Key findings

**1. Chasing wins more, and captains have noticed.**
Chasing teams won **54.5%** of decided matches. The share of captains choosing to field first rose from ~35–40% (2009–10) to **80%+** in most recent seasons (82.4% in 2026).

**2. The toss itself is nearly a coin flip, but the decision matters.**
Toss winners won only **51.4%** of matches. However, toss winners who chose to *field* won **54.4%**, versus **45.4%** for those who chose to *bat*.

**3. Stadiums have clear personalities.**
Most chase-friendly: **Jaipur (64.7%)** and **Sharjah (64.3%)**. Most defend-friendly: **MCA Pune (45.1%)** and **Chepauk, Chennai (45.9%)**. Eden Gardens, Ekana Lucknow, Abu Dhabi and Chinnaswamy also favour the chasing side (56–57%).

**4. Home advantage is real, but it depends on the team.**
Using each team's most-used stadium as "home": **SRH 62.3% at home vs 42.6% away (+19.7 pts)**, **CSK 65.5% vs 51.4% (+14.1)**, Rajasthan, Mumbai and Kolkata also gain 9–12 pts. **RCB shows almost no home edge (51.5% vs 51.1%)** and **Delhi actually wins less at home (43.0% vs 48.4%)**.

**5. Consistency vs titles.**
CSK (55.8%) and MI (54.0%) lead among established franchises with 250+ matches, and share the most titles (**5 each**). Gujarat Titans top the table at 61.0% but on only 77 matches, so the sample is small. RCB have won the last two titles (2025, 2026).

**6. Clutch factor.**
In close games (≤10 runs, ≤2 wickets or super over), **RCB (58.8%)** and **Punjab Kings (57.9%)** are the best finishers, while **KKR (38.6%, 17–27)** are the worst.

**7. Biggest turnarounds (YoY win % jump).**
Deccan Chargers 2009 (**+42.0 pts**, went on to win the title), CSK 2023 (+38.1), KKR 2024 (+35.7).

**8. Player of the Match.**
**AB de Villiers (25)** leads, followed by Chris Gayle and Virat Kohli (22 each) and Rohit Sharma (21).

**9. Rivalries.**
In the most-played pairing, MI lead CSK narrowly (21–20 in 41). MI dominate KKR (25–12 in 37).

## Charts

**All-time win % by franchise**

![All-time win % by franchise](outputs/charts/01_alltime_win_pct.png)

**Chasing-team win % by season**

![Chasing-team win % by season](outputs/charts/02_chase_win_pct_trend.png)

**Toss decisions vs toss-winner win %**

![Toss decisions vs toss-winner win %](outputs/charts/03_toss_trend.png)

**Chase-friendly vs balanced stadiums**

![Chase-friendly vs balanced stadiums](outputs/charts/04_venue_profile.png)

**IPL titles by franchise**

![IPL titles by franchise](outputs/charts/05_titles.png)

**Most Player-of-the-Match awards**

![Most Player-of-the-Match awards](outputs/charts/06_player_of_match.png)

**Win % in close matches**

![Win % in close matches](outputs/charts/07_close_matches.png)

**Cumulative wins of top 5 franchises**

![Cumulative wins of top 5 franchises](outputs/charts/08_cumulative_wins.png)

## Limitations
- Dataset is **match-level** (no ball-by-ball), so batting/bowling-level metrics are out of scope.
- "Home ground" is approximated as each team's most-used stadium, since the data has no explicit home/away flag. Franchises that played in the UAE/South Africa seasons are affected by this.
- Small-sample teams (Gujarat Titans, Lucknow, Deccan Chargers) should be read with caution.

## Possible next steps
- Add ball-by-ball data to analyse powerplay/death-over scoring and player-level performance.
- Build a Power BI / Tableau dashboard on top of the exported tables.
- Test whether the toss effect is statistically significant (chi-square).
