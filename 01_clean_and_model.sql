-- =====================================================================
-- 01_clean_and_model.sql
-- Raw CSV (loaded as raw_matches) -> clean analytical tables
-- =====================================================================

DROP TABLE IF EXISTS venue_map;
CREATE TABLE venue_map (raw_venue TEXT PRIMARY KEY, venue TEXT);

-- Same stadium appears under multiple names (renames / spelling changes)
INSERT INTO venue_map (raw_venue, venue)
SELECT DISTINCT venue, venue FROM raw_matches;

UPDATE venue_map SET venue = 'M Chinnaswamy Stadium, Bengaluru'
 WHERE raw_venue LIKE 'M Chinnaswamy Stadium%';
UPDATE venue_map SET venue = 'Punjab Cricket Association Stadium, Mohali'
 WHERE raw_venue LIKE 'Punjab Cricket Association%';
UPDATE venue_map SET venue = 'Arun Jaitley Stadium, Delhi'
 WHERE raw_venue IN ('Feroz Shah Kotla, Delhi', 'Arun Jaitley Stadium');
UPDATE venue_map SET venue = 'Narendra Modi Stadium, Ahmedabad'
 WHERE raw_venue IN ('Sardar Patel Stadium, Motera, Ahmedabad', 'Narendra Modi Stadium, Ahmedabad');
UPDATE venue_map SET venue = 'MCA Stadium, Pune'
 WHERE raw_venue IN ('Maharashtra Cricket Association Stadium, Pune', 'Subrata Roy Sahara Stadium, Pune');

-- ---------------------------------------------------------------------
-- Clean fact table
--   * standardised venue
--   * effective_winner: super-over winner for ties (stored in `eliminator`)
--   * batting_first / chasing derived from toss
--   * is_playoff flag
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS matches;
CREATE TABLE matches AS
SELECT
    r.match_id,
    CAST(r.season AS INTEGER)                                    AS season,
    r.match_date,
    COALESCE(r.city, 'Unknown')                                  AS city,
    v.venue,
    r.team1,
    r.team2,
    r.toss_winner,
    r.toss_decision,
    r.result,
    r.match_winner,
    COALESCE(r.match_winner, r.eliminator)                       AS effective_winner,
    r.win_by_runs,
    r.win_by_wickets,
    COALESCE(r.player_of_match, 'N/A')                           AS player_of_match,
    r.stage,
    CASE WHEN r.stage = 'League' THEN 0 ELSE 1 END               AS is_playoff,
    CASE WHEN r.toss_decision = 'bat' THEN r.toss_winner
         ELSE CASE WHEN r.toss_winner = r.team1 THEN r.team2 ELSE r.team1 END
    END                                                          AS batting_first,
    CASE WHEN r.toss_decision = 'bat'
         THEN CASE WHEN r.toss_winner = r.team1 THEN r.team2 ELSE r.team1 END
         ELSE r.toss_winner
    END                                                          AS chasing
FROM raw_matches r
JOIN venue_map v ON v.raw_venue = r.venue;

-- ---------------------------------------------------------------------
-- Long format: one row per team per match (makes team-level SQL easy)
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS team_match;
CREATE TABLE team_match AS
SELECT match_id, season, match_date, stage, is_playoff, venue,
       team1 AS team, team2 AS opponent,
       CASE WHEN batting_first = team1 THEN 'bat_first' ELSE 'chase' END AS role,
       CASE WHEN toss_winner = team1 THEN 1 ELSE 0 END                   AS won_toss,
       CASE WHEN effective_winner = team1 THEN 1 ELSE 0 END              AS won,
       CASE WHEN result = 'no result' THEN 1 ELSE 0 END                  AS no_result
FROM matches
UNION ALL
SELECT match_id, season, match_date, stage, is_playoff, venue,
       team2, team1,
       CASE WHEN batting_first = team2 THEN 'bat_first' ELSE 'chase' END,
       CASE WHEN toss_winner = team2 THEN 1 ELSE 0 END,
       CASE WHEN effective_winner = team2 THEN 1 ELSE 0 END,
       CASE WHEN result = 'no result' THEN 1 ELSE 0 END
FROM matches;

CREATE INDEX idx_tm_team  ON team_match(team, season);
CREATE INDEX idx_m_season ON matches(season);
