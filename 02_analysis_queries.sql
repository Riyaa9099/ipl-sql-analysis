-- =====================================================================
-- 02_analysis_queries.sql
-- Each query starts with "-- name: <id>" (read by src/run_analysis.py)
-- Concepts used: JOIN, CTE, GROUP BY/HAVING, CASE, window functions
-- (RANK, DENSE_RANK, LAG, SUM OVER, moving AVG), subqueries, self-join
-- =====================================================================

-- name: q01_data_quality_check
SELECT
    COUNT(*)                                             AS total_matches,
    COUNT(DISTINCT season)                               AS seasons,
    COUNT(DISTINCT venue)                                AS stadiums,
    SUM(result = 'tie')                                  AS ties,
    SUM(result = 'no result')                            AS no_results,
    SUM(effective_winner IS NULL AND result = 'win')     AS winner_missing
FROM matches;

-- name: q02_season_summary
SELECT
    season,
    COUNT(*)                                   AS matches,
    ROUND(AVG(win_by_runs), 1)                 AS avg_win_margin_runs,
    ROUND(AVG(win_by_wickets), 1)              AS avg_win_margin_wkts,
    SUM(result = 'tie')                        AS ties,
    SUM(result = 'no result')                  AS no_results
FROM matches
GROUP BY season
ORDER BY season;

-- name: q03_all_time_team_table
WITH t AS (
    SELECT team,
           COUNT(*)       AS played,
           SUM(won)       AS wins,
           SUM(no_result) AS no_results
    FROM team_match
    GROUP BY team
    HAVING COUNT(*) >= 50
)
SELECT
    RANK() OVER (ORDER BY 1.0 * wins / (played - no_results) DESC) AS rnk,
    team, played, wins,
    ROUND(100.0 * wins / (played - no_results), 1)                  AS win_pct
FROM t
ORDER BY rnk;

-- name: q04_titles_won
SELECT effective_winner AS champion, COUNT(*) AS titles,
       GROUP_CONCAT(season, ', ') AS seasons
FROM (SELECT * FROM matches WHERE stage = 'Final' ORDER BY season)
GROUP BY effective_winner
ORDER BY titles DESC, champion;

-- name: q05_toss_impact_overall
SELECT
    toss_decision,
    COUNT(*)                                                   AS matches,
    SUM(CASE WHEN toss_winner = effective_winner THEN 1 END)   AS toss_winner_won,
    ROUND(100.0 * SUM(CASE WHEN toss_winner = effective_winner THEN 1 END)
          / COUNT(*), 1)                                       AS toss_winner_win_pct
FROM matches
WHERE effective_winner IS NOT NULL
GROUP BY toss_decision
UNION ALL
SELECT 'ALL', COUNT(*),
       SUM(CASE WHEN toss_winner = effective_winner THEN 1 END),
       ROUND(100.0 * SUM(CASE WHEN toss_winner = effective_winner THEN 1 END) / COUNT(*), 1)
FROM matches
WHERE effective_winner IS NOT NULL;

-- name: q06_toss_decision_trend
SELECT
    season,
    ROUND(100.0 * SUM(toss_decision = 'field') / COUNT(*), 1) AS pct_field_first,
    ROUND(100.0 * SUM(CASE WHEN toss_winner = effective_winner THEN 1 END)
          / COUNT(effective_winner), 1)                        AS toss_winner_win_pct
FROM matches
GROUP BY season
ORDER BY season;

-- name: q07_bat_first_vs_chase_by_season
WITH s AS (
    SELECT season,
           COUNT(effective_winner)                                     AS decided,
           SUM(CASE WHEN effective_winner = chasing THEN 1 ELSE 0 END) AS chase_wins
    FROM matches
    GROUP BY season
)
SELECT
    season, decided, chase_wins,
    ROUND(100.0 * chase_wins / decided, 1) AS chase_win_pct,
    ROUND(AVG(100.0 * chase_wins / decided)
          OVER (ORDER BY season ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS moving_avg_3yr
FROM s
ORDER BY season;

-- name: q08_venue_profile
SELECT
    venue,
    COUNT(*)                                                            AS matches,
    ROUND(100.0 * SUM(CASE WHEN effective_winner = chasing THEN 1 ELSE 0 END)
          / COUNT(effective_winner), 1)                                 AS chase_win_pct,
    ROUND(AVG(win_by_runs), 1)                                          AS avg_runs_margin,
    CASE
        WHEN 100.0 * SUM(CASE WHEN effective_winner = chasing THEN 1 ELSE 0 END)
             / COUNT(effective_winner) >= 55 THEN 'Chase-friendly'
        WHEN 100.0 * SUM(CASE WHEN effective_winner = chasing THEN 1 ELSE 0 END)
             / COUNT(effective_winner) <= 45 THEN 'Defend-friendly'
        ELSE 'Balanced'
    END                                                                 AS venue_type
FROM matches
GROUP BY venue
HAVING COUNT(*) >= 25
ORDER BY chase_win_pct DESC;

-- name: q09_home_advantage_proxy
WITH home AS (
    SELECT team, venue,
           ROW_NUMBER() OVER (PARTITION BY team ORDER BY COUNT(*) DESC) AS rn
    FROM team_match
    GROUP BY team, venue
),
base AS (
    SELECT t.team,
           CASE WHEN t.venue = h.venue THEN 'Home ground' ELSE 'Away / neutral' END AS location,
           t.won, t.no_result
    FROM team_match t
    JOIN home h ON h.team = t.team AND h.rn = 1
)
SELECT team, location,
       COUNT(*) AS matches,
       ROUND(100.0 * SUM(won) / (COUNT(*) - SUM(no_result)), 1) AS win_pct
FROM base
GROUP BY team, location
HAVING COUNT(*) >= 30
ORDER BY team, location;

-- name: q10_top_player_of_match
SELECT * FROM (
    SELECT player_of_match AS player,
           COUNT(*) AS awards,
           COUNT(DISTINCT season) AS seasons_active,
           DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS rnk
    FROM matches
    WHERE player_of_match <> 'N/A'
    GROUP BY player_of_match
)
WHERE rnk <= 12
ORDER BY rnk, player;

-- name: q11_team_season_rank_and_yoy
WITH s AS (
    SELECT team, season,
           COUNT(*) - SUM(no_result) AS played,
           SUM(won)                  AS wins
    FROM team_match
    GROUP BY team, season
),
p AS (
    SELECT team, season, wins, played,
           ROUND(100.0 * wins / played, 1) AS win_pct
    FROM s
)
SELECT
    season, team, wins, played, win_pct,
    RANK() OVER (PARTITION BY season ORDER BY win_pct DESC)                    AS season_rank,
    ROUND(win_pct - LAG(win_pct) OVER (PARTITION BY team ORDER BY season), 1)  AS yoy_change
FROM p
ORDER BY season, season_rank;

-- name: q12_biggest_turnarounds
WITH s AS (
    SELECT team, season,
           100.0 * SUM(won) / (COUNT(*) - SUM(no_result)) AS win_pct
    FROM team_match GROUP BY team, season
),
d AS (
    SELECT team, season,
           ROUND(win_pct, 1) AS win_pct,
           ROUND(win_pct - LAG(win_pct) OVER (PARTITION BY team ORDER BY season), 1) AS jump
    FROM s
)
SELECT team, season, win_pct, jump
FROM d
WHERE jump IS NOT NULL
ORDER BY jump DESC
LIMIT 8;

-- name: q13_head_to_head_top_rivalries
WITH h AS (
    SELECT a.team AS team_a, a.opponent AS team_b,
           COUNT(*)   AS played,
           SUM(a.won) AS a_wins,
           SUM(b.won) AS b_wins
    FROM team_match a
    JOIN team_match b ON a.match_id = b.match_id AND a.team = b.opponent
    WHERE a.team < a.opponent
    GROUP BY a.team, a.opponent
)
SELECT team_a, team_b, played, a_wins, b_wins,
       CASE WHEN a_wins > b_wins THEN team_a
            WHEN b_wins > a_wins THEN team_b ELSE 'Level' END AS leader
FROM h
ORDER BY played DESC
LIMIT 10;

-- name: q14_close_match_performance
WITH c AS (
    SELECT match_id, effective_winner,
           CASE WHEN effective_winner = team1 THEN team2 ELSE team1 END AS loser
    FROM matches
    WHERE effective_winner IS NOT NULL
      AND (win_by_runs <= 10 OR win_by_wickets <= 2 OR result = 'tie')
),
agg  AS (SELECT effective_winner AS team, COUNT(*) AS close_wins   FROM c GROUP BY 1),
lost AS (SELECT loser            AS team, COUNT(*) AS close_losses FROM c GROUP BY 1)
SELECT a.team, a.close_wins, l.close_losses,
       ROUND(100.0 * a.close_wins / (a.close_wins + l.close_losses), 1) AS close_win_pct
FROM agg a JOIN lost l ON l.team = a.team
WHERE a.close_wins + l.close_losses >= 25
ORDER BY close_win_pct DESC;

-- name: q15_playoff_chase_vs_defend
SELECT stage,
       COUNT(*) AS matches,
       SUM(CASE WHEN effective_winner = chasing THEN 1 ELSE 0 END) AS chase_wins,
       ROUND(100.0 * SUM(CASE WHEN effective_winner = chasing THEN 1 ELSE 0 END) / COUNT(*), 1) AS chase_win_pct
FROM matches
WHERE is_playoff = 1 AND effective_winner IS NOT NULL
GROUP BY stage
ORDER BY matches DESC;

-- name: q16_cumulative_wins
SELECT team, season,
       SUM(won) AS wins_in_season,
       SUM(SUM(won)) OVER (PARTITION BY team ORDER BY season) AS cumulative_wins
FROM team_match
GROUP BY team, season
ORDER BY team, season;
