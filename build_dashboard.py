"""Builds dashboard/index.html from the SQL result tables (outputs/tables).
Run after src/run_analysis.py:  python dashboard/build_dashboard.py
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
T = ROOT / "outputs" / "tables"
rd = lambda n: pd.read_csv(next(T.glob(f"{n}_*.csv")))

q1, q3, q4 = rd("q01"), rd("q03"), rd("q04")
q6, q7, q8 = rd("q06"), rd("q07"), rd("q08")
q9, q10, q11 = rd("q09"), rd("q10"), rd("q11")
q14 = rd("q14")

chase_total = round(100 * q7.chase_wins.sum() / q7.decided.sum(), 1)
home = q9.pivot(index="team", columns="location", values="win_pct").dropna().reset_index()

data = {
    "kpi": {"matches": int(q1.total_matches[0]), "seasons": int(q1.seasons[0]),
            "stadiums": int(q1.stadiums[0]), "chase": chase_total},
    "chase": q7[["season", "chase_win_pct", "moving_avg_3yr"]].to_dict("list"),
    "toss": q6.to_dict("list"),
    "teams": q3[["team", "win_pct", "played"]].to_dict("list"),
    "venues": q8[["venue", "chase_win_pct", "matches"]].to_dict("list"),
    "home": {"team": home.team.tolist(), "home": home["Home ground"].tolist(),
             "away": home["Away / neutral"].tolist()},
    "close": q14[["team", "close_win_pct"]].to_dict("list"),
    "pom": q10.head(10)[["player", "awards"]].to_dict("list"),
    "titles": {r.champion: r.seasons for r in q4.itertuples()},
    "season_team": q11[["season", "team", "win_pct", "season_rank"]].to_dict("records"),
}

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IPL Match Analytics (2008–2026)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,400..800&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{--bg:#eef2f4;--ink:#14222e;--mute:#5b6b78;--line:#d3dce2;--surface:#fff;
--red:#b3202a;--green:#2f6b4f;--grey:#a9b6c0;}
@media (prefers-color-scheme:dark){:root{--bg:#0f1a22;--ink:#e8eef2;--mute:#93a4b1;--line:#27384555;
--surface:#16242e;--red:#e0555e;--green:#5fb48d;--grey:#4c5f6d;}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:'Archivo',system-ui,sans-serif;line-height:1.5}
main{max-width:1080px;margin:0 auto;padding:40px 20px 60px}
h1{font-size:clamp(2rem,5vw,3.4rem);font-stretch:75%;font-weight:800;line-height:1.05;margin:0 0 10px;letter-spacing:-.01em}
.sub{color:var(--mute);max-width:60ch;margin:0 0 28px}
.kpis{display:flex;flex-wrap:wrap;gap:0;border-top:2px solid var(--ink);border-bottom:1px solid var(--line);margin-bottom:36px}
.kpi{flex:1 1 160px;padding:14px 16px 14px 0}.kpi b{display:block;font-size:2rem;font-weight:700;font-stretch:80%}
.kpi span{color:var(--mute);font-size:.85rem}
section{margin-bottom:44px}h2{font-size:1.35rem;font-weight:700;font-stretch:85%;margin:0 0 4px}
.note{color:var(--mute);font-size:.92rem;margin:0 0 14px;max-width:70ch}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:28px}
@media(max-width:760px){.grid{grid-template-columns:1fr}}
.box{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:14px}
.hero{height:340px}.h{height:300px}.tall{height:420px}
select{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:6px;background:var(--surface);color:var(--ink);margin-bottom:10px}
select:focus-visible{outline:2px solid var(--red);outline-offset:2px}
.facts{display:flex;gap:24px;flex-wrap:wrap;margin:0 0 8px;color:var(--mute);font-size:.92rem}.facts b{color:var(--ink)}
footer{color:var(--mute);font-size:.85rem;border-top:1px solid var(--line);padding-top:14px}
</style></head><body><main>
<h1>Chasing wins. The toss barely matters.</h1>
<p class="sub">SQL analysis of every IPL match from 2008 to 2026: who wins, where, and what captains get right or wrong.</p>
<div class="kpis" id="kpis"></div>

<section><h2>Chasing teams win more than half the time</h2>
<p class="note">Share of decided matches won by the chasing side each season, with a 3-season moving average. The dashed line is 50%.</p>
<div class="box hero"><canvas id="c_chase"></canvas></div></section>

<section class="grid">
<div><h2>Captains now choose to field</h2><p class="note">Toss decisions shifted sharply after 2015, while the toss winner's win rate stays near 50%.</p>
<div class="box h"><canvas id="c_toss"></canvas></div></div>
<div><h2>All-time win % by franchise</h2><p class="note">Teams with at least 50 matches. Gujarat Titans have only 77 games.</p>
<div class="box h"><canvas id="c_teams"></canvas></div></div>
</section>

<section><h2>Stadiums with at least 25 matches</h2>
<p class="note">Chasing-team win % by ground. Red bars are chase-friendly (55% or more).</p>
<div class="box tall"><canvas id="c_venue"></canvas></div></section>

<section class="grid">
<div><h2>Home vs away win %</h2><p class="note">Home is each team's most-used stadium.</p>
<div class="box h"><canvas id="c_home"></canvas></div></div>
<div><h2>Win % in close matches</h2><p class="note">Won by 10 runs or fewer, 2 wickets or fewer, or a super over.</p>
<div class="box h"><canvas id="c_close"></canvas></div></div>
</section>

<section><h2>Team explorer</h2>
<p class="note">Pick a franchise to see its win % in every season it played.</p>
<label for="team" class="note">Franchise </label><select id="team"></select>
<div class="facts" id="facts"></div>
<div class="box h"><canvas id="c_team"></canvas></div></section>

<section><h2>Most Player-of-the-Match awards</h2>
<div class="box h"><canvas id="c_pom"></canvas></div></section>

<footer>Built with SQL (SQLite), Python and Chart.js. Source: IPL match data 2008–2026. Data is match-level, so batting and bowling stats are not included.</footer>
</main>
<script>
const D = __DATA__;
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const C = {red:css('--red'),green:css('--green'),grey:css('--grey'),ink:css('--ink'),mute:css('--mute')};
Chart.defaults.font.family = "'Archivo',system-ui,sans-serif";
Chart.defaults.color = C.mute; Chart.defaults.maintainAspectRatio = false;
const base = (extra={}) => ({plugins:{legend:{display:false}},...extra});
const pct = v => v + '%';

document.getElementById('kpis').innerHTML = [
 [D.kpi.matches.toLocaleString(),'matches'],[D.kpi.seasons,'seasons'],
 [D.kpi.stadiums,'stadiums (after cleaning venue names)'],[D.kpi.chase+'%','won by the chasing team']
].map(k=>`<div class="kpi"><b>${k[0]}</b><span>${k[1]}</span></div>`).join('');

new Chart('c_chase',{data:{labels:D.chase.season,datasets:[
 {type:'bar',label:'Chasing team win %',data:D.chase.chase_win_pct,backgroundColor:C.grey},
 {type:'line',label:'3-season average',data:D.chase.moving_avg_3yr,borderColor:C.red,backgroundColor:C.red,tension:.3,pointRadius:3}]},
 options:{plugins:{legend:{position:'top',align:'end'}},scales:{y:{min:30,max:75,ticks:{callback:pct}}}}});

new Chart('c_toss',{type:'line',data:{labels:D.toss.season,datasets:[
 {label:'Captains choosing to field',data:D.toss.pct_field_first,borderColor:C.green,backgroundColor:C.green,tension:.3},
 {label:"Toss winner's win %",data:D.toss.toss_winner_win_pct,borderColor:C.red,backgroundColor:C.red,tension:.3}]},
 options:{plugins:{legend:{position:'top'}},scales:{y:{min:30,max:90,ticks:{callback:pct}}}}});

new Chart('c_teams',{type:'bar',data:{labels:D.teams.team,datasets:[{data:D.teams.win_pct,
 backgroundColor:D.teams.win_pct.map(v=>v>=50?C.green:C.grey)}]},
 options:base({indexAxis:'y',scales:{x:{min:30,ticks:{callback:pct}}}})});

new Chart('c_venue',{type:'bar',data:{labels:D.venues.venue.map(v=>v.replace('Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium','Ekana Stadium')),
 datasets:[{data:D.venues.chase_win_pct,backgroundColor:D.venues.chase_win_pct.map(v=>v>=55?C.red:C.grey)}]},
 options:base({indexAxis:'y',scales:{x:{min:30,ticks:{callback:pct}}}})});

new Chart('c_home',{type:'bar',data:{labels:D.home.team,datasets:[
 {label:'Home ground',data:D.home.home,backgroundColor:C.green},
 {label:'Away / neutral',data:D.home.away,backgroundColor:C.grey}]},
 options:{indexAxis:'y',plugins:{legend:{position:'top'}},scales:{x:{min:30,ticks:{callback:pct}}}}});

new Chart('c_close',{type:'bar',data:{labels:D.close.team,datasets:[{data:D.close.close_win_pct,
 backgroundColor:D.close.close_win_pct.map(v=>v>=50?C.green:C.red)}]},
 options:base({indexAxis:'y',scales:{x:{min:30,ticks:{callback:pct}}}})});

new Chart('c_pom',{type:'bar',data:{labels:D.pom.player,datasets:[{data:D.pom.awards,backgroundColor:C.red}]},
 options:base()});

const sel = document.getElementById('team');
const names = [...new Set(D.season_team.map(r=>r.team))].sort();
sel.innerHTML = names.map(n=>`<option>${n}</option>`).join('');
sel.value = 'Royal Challengers Bengaluru';
let tc;
function drawTeam(){
 const rows = D.season_team.filter(r=>r.team===sel.value);
 const titles = D.titles[sel.value];
 document.getElementById('facts').innerHTML =
  `<span>Seasons played <b>${rows.length}</b></span>`+
  `<span>Best season <b>${Math.max(...rows.map(r=>r.win_pct))}%</b></span>`+
  `<span>Titles <b>${titles?titles:'none'}</b></span>`;
 const champ = r => titles && titles.split(', ').includes(String(r.season));
 const cfg = {labels:rows.map(r=>r.season),datasets:[{label:'Win %',data:rows.map(r=>r.win_pct),
  borderColor:C.ink,backgroundColor:rows.map(r=>champ(r)?C.red:C.grey),
  pointRadius:rows.map(r=>champ(r)?8:4),tension:.25}]};
 if(tc){tc.data=cfg;tc.update();return;}
 tc = new Chart('c_team',{type:'line',data:cfg,options:{plugins:{legend:{display:false},
  tooltip:{callbacks:{afterLabel:c=>champ(rows[c.dataIndex])?'Champions':''}}},
  scales:{y:{min:0,max:100,ticks:{callback:pct}}}}});
}
sel.addEventListener('change',drawTeam);drawTeam();
</script></body></html>"""

out = ROOT / "dashboard" / "index.html"
out.write_text(HTML.replace("__DATA__", json.dumps(data)))
print("Wrote", out)
