import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json
import os
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Creator System | CVP Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .big-font {font-size: 46px !important; font-weight: 800; color: #4da6ff; line-height: 1.15;}
    .win-arrow {color: lime; font-weight: bold;}
    .lose-arrow {color: red; font-weight: bold;}
    .comp-table { width: 100%; text-align: left; border-collapse: collapse; margin-top: 20px;}
    .comp-table th { padding: 12px; border-bottom: 2px solid #4da6ff; font-size: 17px; background-color: #111111; position: sticky; top: 0;}
    .comp-table td { padding: 11px; border-bottom: 1px solid #333; font-size: 15px; }
    .comp-table tr:hover { background-color: #1a1a1a; }
    .score-excellent { background: linear-gradient(90deg, #1a3a1a, #0d0d0d); border-left: 5px solid #00e676; padding: 14px 20px; border-radius: 8px; display: inline-block; min-width: 200px;}
    .score-good      { background: linear-gradient(90deg, #1a2e3a, #0d0d0d); border-left: 5px solid #4da6ff; padding: 14px 20px; border-radius: 8px; display: inline-block; min-width: 200px;}
    .score-average   { background: linear-gradient(90deg, #2e2a0d, #0d0d0d); border-left: 5px solid #ffc107; padding: 14px 20px; border-radius: 8px; display: inline-block; min-width: 200px;}
    .score-poor      { background: linear-gradient(90deg, #3a1a1a, #0d0d0d); border-left: 5px solid #ff5252; padding: 14px 20px; border-radius: 8px; display: inline-block; min-width: 200px;}
    .score-label { font-size: 13px; color: #aaa; margin-bottom: 4px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;}
    .score-value { font-size: 30px; font-weight: 900; }
    .score-tag   { font-size: 12px; margin-top: 4px; font-weight: 700; letter-spacing: 1px; }
    .fact-box { background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 16px 20px; margin-bottom: 10px; }
    .fact-icon { font-size: 20px; margin-right: 8px; }
    .fact-text { font-size: 15px; color: #d1d5db; line-height: 1.5; }
    .fact-badge { display: inline-block; background: #1e3a5f; color: #60a5fa; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 20px; margin-bottom: 6px; letter-spacing: 0.5px; text-transform: uppercase; }
    .summary-box { background: #0d1117; border: 1.5px solid #4da6ff; border-radius: 14px; padding: 24px 28px; margin-top: 20px; }
    .summary-box h3 { color: #4da6ff; font-size: 18px; margin-bottom: 16px; }
    .summary-box p { color: #c9d1d9; font-size: 15px; line-height: 1.8; margin-bottom: 12px; }
    .summary-verdict { background: #161b22; border-left: 4px solid #00e676; border-radius: 6px; padding: 14px 18px; margin-top: 16px; color: #e6edf3; font-size: 15px; line-height: 1.7; font-style: italic; }
    .season-badge { display: inline-block; background: #1e3a5f; color: #60a5fa; font-size: 12px; font-weight: 700; padding: 3px 12px; border-radius: 20px; letter-spacing: 0.5px; margin-left: 10px; }
    .insight-card { background: #0d1117; border: 1px solid #21262d; border-radius: 12px; padding: 18px 22px; margin-bottom: 12px; }
    .insight-card h4 { color: #4da6ff; font-size: 15px; margin-bottom: 8px; }
    .insight-card p { color: #c9d1d9; font-size: 14px; line-height: 1.6; margin: 0; }
    </style>
""", unsafe_allow_html=True)

FALLBACK_IMAGE = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"

# ─────────────────────────────────────────────
# TIER LOGIC — CVP-based
# ─────────────────────────────────────────────
def cvp_tier(score):
    if score >= 3.5:
        return "Elite", "#00e676", "score-excellent"
    elif score >= 2.5:
        return "Good", "#4da6ff", "score-good"
    elif score >= 1.5:
        return "Average", "#ffc107", "score-average"
    else:
        return "Below Average", "#ff5252", "score-poor"

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_all_seasons():
    frames = {}
    season_files = {
        "2025/26": "creator_matrices_2526.csv",
        "2024/25": "creator_metrices_2425.csv",
        "2023/24": "creator_metrics_2324.csv",
    }
    for season, fname in season_files.items():
        try:
            df = pd.read_csv(fname)
        except FileNotFoundError:
            try:
                df = pd.read_csv(f"/mnt/user-data/uploads/{fname}")
            except FileNotFoundError:
                st.error(f"Could not load {fname}")
                continue
        # Normalize CVP column name
        df.columns = [c.strip() for c in df.columns]
        for col in df.columns:
            if "creativity" in col.lower() and "volume" in col.lower():
                df.rename(columns={col: "CVP"}, inplace=True)
                break
        df["Season"] = season
        frames[season] = df
    return frames

ALL_DATA = load_all_seasons()
SEASONS = list(ALL_DATA.keys())

# ─────────────────────────────────────────────
# PLAYER INSIGHTS (per season context)
# ─────────────────────────────────────────────
PLAYER_INSIGHTS_2526 = {
    "Ousmane Dembélé":         "Season-best CVP (4.03) — leads all 18 creators. His low-block dribbling and final-third chaos define PSG's attack in 25/26.",
    "Trent Alexander-Arnold":  "Highest PrgP90 (9.63) in the dataset. Real Madrid's right side is built through him — 4.23 CVP cements elite status.",
    "Bruno Fernandes":          "Highest CVP (4.31) in 25/26. Still carrying United's creativity single-handedly with 3.75 KP90 — a true conductor.",
    "Hakan Çalhanoğlu":        "Most progressive passes (10.3/90) — the deepest elite creator. CVP of 2.96 understates his positional influence.",
    "Kevin De Bruyne":          "Relocated to Napoli, still elite. 2.62 KP90 and 5.66 PrgP90 despite reduced system support.",
    "Martin Ødegaard":          "Arsenal's heartbeat. 2.72 KP90 and 2.43 CVP — consistent performer but below peak 23/24 output.",
    "Vinicius Júnior":          "Lowest CVP among Real Madrid's creators (2.35) — his chaos can't be measured in passing metrics alone.",
    "Florian Wirtz":            "At Liverpool, 25/26 CVP (1.82) is his weakest — still adapting to the Premier League pace and system.",
    "Jude Bellingham":          "CVP of 2.06 — his goals-focused role limits creativity metrics, but his box arrivals are unmatched.",
    "Kylian Mbappé":            "2.21 CVP, highest AccLB90 (sort of expected) — his creativity is chaotic, not systemic.",
    "Alejandro Grimaldo":       "Best CVP among fullbacks (1.90). Leverkusen system gives him license to act as a playmaking LB.",
    "Rodri":                    "CVP of 1.73 — deceptively deep position hides his true influence. Efficiency_Ratio of just 0.25 is by design.",
    "Cole Palmer":              "Surprisingly modest CVP (1.46) given his reputation — his impact through carries and dribbles outpaces this metric.",
    "Phil Foden":               "CVP of 1.86 — City's half-spaces are his domain. Less progressive than 23/24 due to positional shift.",
    "Bukayo Saka":              "2.29 CVP — consistent workhorse. His creativity combines with defensive contribution uniquely.",
    "Harry Kane":               "2.26 CVP from a striker position — remarkable. Bayern's system flows through him even without the ball.",
    "Rafael Leão":              "Lowest CVP (0.98) in the 25/26 set. Leão's impact is physical and positional, not statistical.",
    "Vitinha":                  "Bottom CVP (0.83) — has moved from PSG to Genoa, reduced system quality suppresses numbers.",
}

PLAYER_INSIGHTS_2425 = {
    "Bruno Fernandes":    "Highest CVP (3.66) in 24/25 — leads all creators from the Premier League. Assists, key passes, long ball range all elite.",
    "Bukayo Saka":        "2nd in CVP (3.33). Saka's efficiency ratio (0.60) is remarkable — fewest total passes, highest proportion that matter.",
    "Martin Ødegaard":    "3rd in CVP (3.21). Arsenal's creative hub; his numbers drop slightly vs 23/24 but consistency is his hallmark.",
    "Kevin De Bruyne":    "4th in CVP (2.84). Season disrupted by injuries — his numbers when fit were still world-class.",
    "Kylian Mbappé":      "5th in CVP (2.62) in his debut Madrid season — higher than most expected from a winger, 5.07 PrgP90.",
    "Cole Palmer":        "6th in CVP (2.47) — a breakout season at Chelsea. His KP90 (2.88) places him among elite creators.",
    "Trent Alexander-Arnold": "7th in CVP (2.45) — last season at Liverpool before his Madrid move. Still generating at fullback.",
    "Phil Foden":         "8th in CVP (2.28) — best season yet for Foden creatively, operating closer to centre.",
    "Rodri":              "BALLON D'OR winner. 9th in CVP (2.24) — his influence is positional & defensive but creativity numbers hold.",
    "Jude Bellingham":    "10th in CVP (2.00) — first full Madrid season. Charismatic scorer, not yet leading the creativity charts.",
    "Vinicius Júnior":    "11th in CVP (1.86). Still adapting his raw pace into systemic creativity metrics.",
    "Harry Kane":         "12th in CVP (1.80) — first Bundesliga season. Creative by striker standards, above average overall.",
    "Florian Wirtz":      "13th in CVP (1.71) — final Leverkusen season before big move. Signs of elite potential in bursts.",
    "Alejandro Grimaldo": "14th in CVP (1.64) — best fullback by CVP in 24/25. Leverkusen's left channel was his kingdom.",
    "Hakan Çalhanoğlu":   "15th in CVP (1.47) — Inter's deep creator. PrgP90 (8.31) is 2nd highest but efficiency ratio dragged score.",
    "Rafael Leão":        "16th in CVP (1.29). Below expectations — Milan's poor form dented his creativity outlet.",
    "Vitinha":            "17th in CVP (0.86). PSG's build-up anchor — safe, positional, anti-CVP by design.",
    "Ousmane Dembélé":    "18th in CVP (0.86). Surprising low — PSG's system uses him as a carrier not a passer.",
    "İlkay Gündoğan":     "19th in CVP (0.87). Barcelona signing underperformed — mid-table creativity for a supposed elite.",
}

PLAYER_INSIGHTS_2324 = {
    "Kevin De Bruyne":     "Highest CVP in the dataset (5.36). The benchmark. 4.23 KP90 + 9.5 PrgP90 = unmatched playmaking dominance.",
    "Bruno Fernandes":     "2nd in CVP (2.75). Led United's creativity solo — 3.26 KP90 and elite xA despite poor team context.",
    "Rodri":               "3rd in CVP (2.63). Peak defensive-creative duality — the spine of City's title-winning system.",
    "Toni Kroos":          "4th in CVP (2.57). Final Real Madrid season — a masterclass in passing efficiency. Retired at the top.",
    "Hakan Çalhanoğlu":    "5th in CVP (2.44). Inter's Serie A title — Çalha was the engine room. His PrgP90 (11.2) leads all 20.",
    "Trent Alexander-Arnold": "6th in CVP (2.40). Elite from right-back — 8.1 PrgP90 and 2.41 KP90 at Liverpool before Madrid switch.",
    "Ousmane Dembélé":     "7th in CVP (2.37). Dangerous wide creator — KP90 (3.29) shows elite chance creation from wide areas.",
    "Florian Wirtz":       "8th in CVP (2.30). Leverkusen's unbeaten Bundesliga season — Wirtz's creativity was central to it.",
    "Alejandro Grimaldo":  "9th in CVP (2.04). Leverkusen left-back unlocked by Alonso — 2.26 KP90 from fullback is extraordinary.",
    "Cole Palmer":         "10th in CVP (1.93). Loan at Chelsea turned permanent — an immediate impact season, top half CVP.",
    "Jude Bellingham":     "11th in CVP (1.86). First Real Madrid season — goals dominated headlines but creativity was growing.",
    "Martin Ødegaard":     "12th in CVP (1.75). Arsenal's best PL campaign yet — Ødegaard the creative hub, 2.28 KP90.",
    "Harry Kane":          "13th in CVP (1.59). Last season at Spurs — scored 30 PL goals but CVP shows declining pass creativity.",
    "Kylian Mbappé":       "14th in CVP (1.49). Final PSG season — his creativity in a solo-striker role is system-dependent.",
    "Vinicius Junior":     "15th in CVP (1.42). Goals and chaos — his low CVP reflects the lack of pass-based creativity intent.",
    "Bukayo Saka":         "16th in CVP (1.33). Arsenal's workhorse — consistency and pressing over pure chance creation.",
    "Phil Foden":          "17th in CVP (1.26). Excellent season by PL standards — CVP slightly lower, off-ball influence higher.",
    "Ilkay Gündoğan":      "18th in CVP (1.17). Barcelona season — decent by any other measure but CVP exposes system mismatch.",
    "Vitinha":             "19th in CVP (0.83). PSG's deepest builder — safe by design, creative by others' standards.",
    "Rafael Leão":         "20th in CVP (0.68). Lowest in 23/24 set. Leão's value is physical and positional, not this metric.",
}

INSIGHTS_BY_SEASON = {
    "2025/26": PLAYER_INSIGHTS_2526,
    "2024/25": PLAYER_INSIGHTS_2425,
    "2023/24": PLAYER_INSIGHTS_2324,
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_image_url(url):
    if pd.isna(url) or str(url).strip() == "" or not str(url).strip().startswith("http"):
        return FALLBACK_IMAGE
    return str(url).strip()

def safe_index(lst, name, default=0):
    try:
        return lst.index(name)
    except ValueError:
        return default

def get_df(season):
    return ALL_DATA[season].copy()

# ─────────────────────────────────────────────
# COMPARISON SUMMARY (local, stat-based)
# ─────────────────────────────────────────────
def _cmp(v1, v2, n1, n2, metric, high_label, low_label, unit=""):
    diff = abs(v1 - v2)
    if diff < 0.05:
        return f"Both players are virtually identical in {metric} ({v1:.2f}{unit} vs {v2:.2f}{unit}), making this a neutral battleground."
    winner, loser, wv, lv = (n1, n2, v1, v2) if v1 > v2 else (n2, n1, v2, v1)
    gap = "marginally" if diff < 0.3 else ("clearly" if diff < 1.0 else "significantly")
    return f"{winner} {gap} leads in {metric} ({wv:.2f}{unit} vs {lv:.2f}{unit}), marking {winner} as the {high_label} and {loser} as the {low_label} in this matchup."

def generate_local_summary(p1, p2, season):
    n1, n2 = p1["Player"], p2["Player"]
    cvp1, cvp2 = float(p1["CVP"]), float(p2["CVP"])
    kp1, kp2 = float(p1["KP90"]), float(p2["KP90"])
    pp1, pp2 = float(p1["PrgP90"]), float(p2["PrgP90"])
    xa1, xa2 = float(p1["xA90"]), float(p2["xA90"])
    ft1, ft2 = float(p1["Final3rdP90"]), float(p2["Final3rdP90"])
    er1, er2 = float(p1["Efficiency_Ratio"]), float(p2["Efficiency_Ratio"])
    nc1, nc2 = float(p1["Net_Creativity"]), float(p2["Net_Creativity"])
    lb1, lb2 = float(p1["AccLB90"]), float(p2["AccLB90"])
    cr1, cr2 = float(p1["AccCr90"]), float(p2["AccCr90"])
    tp1, tp2 = float(p1["TotalPasses90"]), float(p2["TotalPasses90"])
    gpg1, gpg2 = float(p1["GPG"]), float(p2["GPG"])

    # Chance creation section
    s1 = [
        _cmp(kp1, kp2, n1, n2, "key passes per 90", "more dangerous chance creator", "quieter in final-third execution"),
        _cmp(xa1, xa2, n1, n2, "expected assists", "higher-quality creator", "lower-probability ball carrier"),
    ]
    if abs(lb1 - lb2) > 0.15:
        lbw = n1 if lb1 > lb2 else n2
        s1.append(f"{lbw} is the bigger line-breaker via the long ball with {max(lb1,lb2):.2f} accurate long balls per 90 vs {min(lb1,lb2):.2f}.")
    if abs(cr1 - cr2) > 0.15:
        crw = n1 if cr1 > cr2 else n2
        s1.append(f"{crw} is the more prolific crosser with {max(cr1,cr2):.2f} accurate crosses per 90 — a different dimension of width creativity.")

    # Progression section
    s2 = [
        _cmp(pp1, pp2, n1, n2, "progressive passes per 90", "more forward-thinking distributor", "more conservative in ball movement"),
        _cmp(ft1, ft2, n1, n2, "passes into the final third", "more penetrative in the last zone", "less incisive in dangerous areas"),
    ]
    if abs(tp1 - tp2) > 5:
        vp = n1 if tp1 > tp2 else n2
        s2.append(f"{vp} operates at higher volume ({max(tp1,tp2):.0f} total passes/90 vs {min(tp1,tp2):.0f}) — reflecting a deeper positional role or ball-dominant system.")
    s2.append(_cmp(er1, er2, n1, n2, "efficiency ratio (progressive intent per pass)", "more economical line-breaker", "higher-volume but less targeted distributor"))

    # Net creativity section
    s3 = [
        _cmp(nc1, nc2, n1, n2, "net creativity score", "more systemically impactful creator", "less influential in the overall build-up"),
        _cmp(cvp1, cvp2, n1, n2, "CVP (Creativity Volume by Passes)", "higher composite creative output", "lower composite creative output"),
    ]
    if abs(gpg1 - gpg2) > 0.1:
        gpgw = n1 if gpg1 > gpg2 else n2
        s3.append(f"{gpgw}'s team creates {max(gpg1,gpg2):.2f} goals per game vs {min(gpg1,gpg2):.2f} — a team quality ceiling that artificially limits or inflates individual metrics.")

    # Verdict
    edges = {n1: 0, n2: 0}
    for v1, v2 in [(kp1,kp2),(pp1,pp2),(xa1,xa2),(er1,er2)]:
        if v1 > v2 + 0.05: edges[n1] += 1
        elif v2 > v1 + 0.05: edges[n2] += 1

    dominant = n1 if edges[n1] > edges[n2] else (n2 if edges[n2] > edges[n1] else None)
    if dominant:
        other = n2 if dominant == n1 else n1
        dom_cvp = cvp1 if dominant == n1 else cvp2
        oth_cvp = cvp2 if dominant == n1 else cvp1
        verdict = (
            f"{dominant} wins this {season} head-to-head across {max(edges.values())} of 4 measurable dimensions, backed by a CVP of {dom_cvp:.2f} vs {other}'s {oth_cvp:.2f}. "
            f"The data consistently points in one direction — {dominant} is the more complete creative contributor in this system context. "
            f"{other} has distinct traits that suit specific tactical environments, but the numbers favour {dominant} as the outright pick."
        )
    else:
        verdict = (
            f"This is a genuinely balanced {season} matchup — {n1} and {n2} split the four creativity dimensions with CVPs of {cvp1:.2f} and {cvp2:.2f} respectively. "
            f"Context is the deciding factor here; neither player comprehensively dominates. The right choice is entirely system-dependent."
        )

    return [
        ("Chance Creation", " ".join(s1)),
        ("Passing Profile", " ".join(s2)),
        ("Creative Volume & System Context", " ".join(s3)),
        ("Verdict", verdict),
    ]

# ─────────────────────────────────────────────
# SEASON TOGGLE HELPER
# ─────────────────────────────────────────────
def season_toggle(key_prefix):
    st.markdown("**Season:**")
    cols = st.columns(len(SEASONS) + 1)
    if f"{key_prefix}_season" not in st.session_state:
        st.session_state[f"{key_prefix}_season"] = SEASONS[0]
    for i, s in enumerate(SEASONS):
        is_active = st.session_state[f"{key_prefix}_season"] == s
        if cols[i].button(s, key=f"{key_prefix}_btn_{s}", type="primary" if is_active else "secondary"):
            st.session_state[f"{key_prefix}_season"] = s
            st.rerun()
    return st.session_state[f"{key_prefix}_season"]

# ─────────────────────────────────────────────
# D3 SCATTER CHART
# ─────────────────────────────────────────────
def render_d3_scatter(players_data, x_col, y_col, x_label, y_label):
    players_json = json.dumps(players_data)
    html = f"""<!DOCTYPE html>
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: 'Segoe UI', sans-serif; overflow: hidden; }}
  #controls {{
    display: flex; align-items: center; gap: 10px;
    padding: 10px 16px; background: #0e1117;
    border-bottom: 1px solid #222; flex-wrap: wrap;
  }}
  #controls span {{ color: #aaa; font-size: 13px; font-weight: 600; }}
  .toggle-btn {{
    padding: 6px 18px; border-radius: 20px;
    border: 1.5px solid #4da6ff; background: transparent;
    color: #4da6ff; font-size: 13px; font-weight: 600;
    cursor: pointer; transition: all 0.2s;
  }}
  .toggle-btn.active {{ background: #4da6ff; color: #000; }}
  #removed-panel {{
    display: none; align-items: center; gap: 8px;
    padding: 8px 16px; background: #161b22;
    border-bottom: 1px solid #222; flex-wrap: wrap;
  }}
  #removed-panel.visible {{ display: flex; }}
  #removed-panel span {{ color: #888; font-size: 12px; font-weight: 600; }}
  .restore-chip {{
    display: inline-flex; align-items: center; gap: 5px;
    background: #1e3a1e; border: 1px solid #238636;
    border-radius: 20px; padding: 3px 10px 3px 8px;
    color: #3fb950; font-size: 12px; cursor: pointer;
    transition: background 0.15s;
  }}
  .restore-chip:hover {{ background: #2ea04326; }}
  .restore-chip .plus {{ font-size: 14px; font-weight: 700; line-height: 1; }}
  .axis path, .axis line {{ stroke: #2a2a2a; }}
  .axis text {{ fill: #666; font-size: 11px; }}
  .grid line {{ stroke: #1a1a1a; stroke-dasharray: 3,3; }}
  .grid path {{ stroke: none; }}
  .axis-label {{ fill: #888; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; }}
  .remove-btn {{ cursor: pointer; opacity: 0; transition: opacity 0.15s; pointer-events: none; }}
  .node:hover .remove-btn {{ opacity: 1; pointer-events: all; }}
  #tooltip {{
    position: fixed; pointer-events: none;
    background: #0d1117; border: 1.5px solid #4da6ff;
    border-radius: 14px; opacity: 0;
    transition: opacity 0.18s; z-index: 9999;
    width: 270px; box-shadow: 0 12px 40px rgba(0,0,0,0.7);
    overflow: hidden;
  }}
  #tooltip.visible {{ opacity: 1; }}
  #tt-header {{
    display: flex; align-items: center; gap: 12px;
    padding: 14px; background: #161b22;
    border-bottom: 1px solid #21262d;
  }}
  #tt-img {{
    width: 54px; height: 54px; border-radius: 50%;
    object-fit: cover; border: 2px solid #4da6ff;
    flex-shrink: 0; background: #1a1a1a;
  }}
  #tt-name {{ color: #e6edf3; font-size: 14px; font-weight: 700; line-height: 1.3; }}
  #tt-meta {{ color: #8b949e; font-size: 11px; margin-top: 3px; }}
  #tt-body {{ padding: 12px 14px; }}
  #tt-stats {{
    display: flex; justify-content: space-between;
    margin-bottom: 10px; padding-bottom: 10px;
    border-bottom: 1px solid #21262d;
  }}
  .tt-stat {{ text-align: center; flex: 1; }}
  .tt-stat-val {{ color: #4da6ff; font-size: 17px; font-weight: 800; }}
  .tt-stat-lbl {{ color: #8b949e; font-size: 9px; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; }}
  #tt-insight {{ color: #c9d1d9; font-size: 12px; line-height: 1.55; font-style: italic; }}
  #tt-tier {{
    display: inline-block; font-size: 10px; font-weight: 700;
    padding: 2px 8px; border-radius: 10px; margin-bottom: 8px;
    letter-spacing: 0.5px; text-transform: uppercase;
  }}
  #remove-hint {{
    padding: 4px 16px 6px; background: #0e1117;
    color: #555; font-size: 11px; font-style: italic;
  }}
</style>
</head>
<body>
<div id="controls">
  <span>Marker Style:</span>
  <button class="toggle-btn active" id="btn-icons" onclick="setMode('icons')">👤 Face Icons</button>
  <button class="toggle-btn" id="btn-circles" onclick="setMode('circles')">⬤ Circles</button>
</div>
<div id="removed-panel">
  <span>Removed:</span>
  <div id="removed-chips"></div>
</div>
<div id="remove-hint">Hover over a player → click ✕ to remove from chart</div>
<svg id="chart"></svg>
<div id="tooltip">
  <div id="tt-header">
    <img id="tt-img" src="" onerror="this.src='{FALLBACK_IMAGE}'"/>
    <div>
      <div id="tt-name"></div>
      <div id="tt-meta"></div>
    </div>
  </div>
  <div id="tt-body">
    <div id="tt-stats">
      <div class="tt-stat">
        <div class="tt-stat-val" id="tt-x"></div>
        <div class="tt-stat-lbl">{x_label}</div>
      </div>
      <div class="tt-stat">
        <div class="tt-stat-val" id="tt-y"></div>
        <div class="tt-stat-lbl">{y_label}</div>
      </div>
      <div class="tt-stat">
        <div class="tt-stat-val" id="tt-cvp"></div>
        <div class="tt-stat-lbl">CVP</div>
      </div>
    </div>
    <div id="tt-tier"></div>
    <div id="tt-insight"></div>
  </div>
</div>
<script>
const allPlayers = {players_json};
const xKey = "{x_col}";
const yKey = "{y_col}";
let mode = "icons";
let removedSet = new Set();

const TIER_COLORS = {{ "Elite":"#00e676","Good":"#4da6ff","Average":"#ffc107","Below Average":"#ff5252" }};
function getTier(s) {{
  if (s >= 3.5) return "Elite";
  if (s >= 2.5) return "Good";
  if (s >= 1.5) return "Average";
  return "Below Average";
}}

const W = Math.min(document.documentElement.clientWidth, 1100);
const H = 520;
const margin = {{ top: 28, right: 28, bottom: 58, left: 68 }};
const innerW = W - margin.left - margin.right;
const innerH = H - margin.top - margin.bottom;

const svg = d3.select("#chart").attr("width", W).attr("height", H);
const g = svg.append("g").attr("transform", `translate(${{margin.left}},${{margin.top}})`);

const xVals = allPlayers.map(p => +p[xKey]);
const yVals = allPlayers.map(p => +p[yKey]);
const xPad = (d3.max(xVals) - d3.min(xVals)) * 0.1;
const yPad = (d3.max(yVals) - d3.min(yVals)) * 0.1;

const xScale = d3.scaleLinear().domain([d3.min(xVals)-xPad, d3.max(xVals)+xPad]).range([0,innerW]);
const yScale = d3.scaleLinear().domain([d3.min(yVals)-yPad, d3.max(yVals)+yPad]).range([innerH,0]);
const sizeScale = d3.scaleSqrt()
  .domain([d3.min(allPlayers, p=>+p.CVP), d3.max(allPlayers, p=>+p.CVP)])
  .range([18,42]);

g.append("g").attr("class","grid").attr("transform",`translate(0,${{innerH}})`)
  .call(d3.axisBottom(xScale).tickSize(-innerH).tickFormat(""));
g.append("g").attr("class","grid").call(d3.axisLeft(yScale).tickSize(-innerW).tickFormat(""));
g.append("g").attr("class","axis").attr("transform",`translate(0,${{innerH}})`).call(d3.axisBottom(xScale).ticks(6));
g.append("g").attr("class","axis").call(d3.axisLeft(yScale).ticks(6));
g.append("text").attr("class","axis-label").attr("x",innerW/2).attr("y",innerH+46).attr("text-anchor","middle").text("{x_label}");
g.append("text").attr("class","axis-label").attr("transform","rotate(-90)").attr("x",-innerH/2).attr("y",-54).attr("text-anchor","middle").text("{y_label}");

const defs = svg.append("defs");
allPlayers.forEach((p,i) => {{
  defs.append("clipPath").attr("id",`clip-${{i}}`).append("circle").attr("r", sizeScale(+p.CVP));
}});

const tooltip = document.getElementById("tooltip");
function showTooltip(event, p) {{
  document.getElementById("tt-img").src = p.Icons_URL || "{FALLBACK_IMAGE}";
  document.getElementById("tt-name").textContent = p.Player;
  document.getElementById("tt-meta").textContent = p.Club + " · " + p.League;
  document.getElementById("tt-x").textContent = (+p[xKey]).toFixed(2);
  document.getElementById("tt-y").textContent = (+p[yKey]).toFixed(2);
  document.getElementById("tt-cvp").textContent = (+p.CVP).toFixed(2);
  const tier = getTier(+p.CVP);
  const tierEl = document.getElementById("tt-tier");
  tierEl.textContent = "● " + tier;
  tierEl.style.color = TIER_COLORS[tier];
  tierEl.style.background = TIER_COLORS[tier] + "22";
  document.getElementById("tt-insight").textContent = p.insight || "";
  tooltip.classList.add("visible");
  moveTooltip(event);
}}
function moveTooltip(event) {{
  const tw=270,th=230;
  let left=event.clientX+18, top=event.clientY-70;
  if(left+tw>window.innerWidth) left=event.clientX-tw-18;
  if(top+th>window.innerHeight) top=window.innerHeight-th-10;
  if(top<0) top=10;
  tooltip.style.left=left+"px"; tooltip.style.top=top+"px";
}}
function hideTooltip() {{ tooltip.classList.remove("visible"); }}

const nodes = g.selectAll(".node").data(allPlayers).enter()
  .append("g").attr("class","node").attr("id",(p,i)=>`node-${{i}}`)
  .attr("transform", p=>`translate(${{xScale(+p[xKey])}},${{yScale(+p[yKey])}})`);

nodes.append("circle").attr("class","dot-circle")
  .attr("r",p=>sizeScale(+p.CVP)).attr("fill","#4da6ff").attr("fill-opacity",0.82)
  .attr("stroke","#fff").attr("stroke-width",1.5).style("opacity",0).style("cursor","pointer");

nodes.append("circle").attr("class","dot-ring")
  .attr("r",p=>sizeScale(+p.CVP)+2.5).attr("fill","none")
  .attr("stroke","#4da6ff").attr("stroke-width",2.5).style("cursor","pointer");

nodes.append("image").attr("class","dot-image")
  .attr("href",p=>p.Icons_URL||"{FALLBACK_IMAGE}")
  .attr("x",p=>-sizeScale(+p.CVP)).attr("y",p=>-sizeScale(+p.CVP))
  .attr("width",p=>sizeScale(+p.CVP)*2).attr("height",p=>sizeScale(+p.CVP)*2)
  .attr("clip-path",(p,i)=>`url(#clip-${{i}})`).attr("preserveAspectRatio","xMidYMid slice")
  .style("cursor","pointer");

nodes.each(function(p,i) {{
  const r = sizeScale(+p.CVP);
  const btn = d3.select(this).append("g").attr("class","remove-btn")
    .attr("transform",`translate(${{r-4}},${{-r+4}})`).style("cursor","pointer")
    .on("click",function(event) {{ event.stopPropagation(); removePlayer(i,p.Player); }});
  btn.append("circle").attr("r",9).attr("fill","#ff5252").attr("stroke","#fff").attr("stroke-width",1.5);
  btn.append("text").attr("text-anchor","middle").attr("dy","0.35em")
    .attr("fill","#fff").attr("font-size","11px").attr("font-weight","700").text("✕");
}});

nodes.append("circle").attr("r",p=>sizeScale(+p.CVP)+5).attr("fill","transparent").style("cursor","pointer")
  .on("mouseover",function(event,p) {{
    if(removedSet.has(p.Player)) return;
    d3.select(this.parentNode).raise();
    d3.select(this.parentNode).selectAll("image,.dot-circle,.dot-ring")
      .transition().duration(160).attr("transform","scale(1.22)");
    showTooltip(event,p);
  }})
  .on("mousemove",moveTooltip)
  .on("mouseout",function(event,p) {{
    d3.select(this.parentNode).selectAll("image,.dot-circle,.dot-ring")
      .transition().duration(160).attr("transform","scale(1)");
    hideTooltip();
  }});

function removePlayer(i,name) {{
  hideTooltip();
  removedSet.add(name);
  d3.select(`#node-${{i}}`).transition().duration(300).style("opacity",0).style("pointer-events","none");
  updateRemovedPanel();
}}
function restorePlayer(name) {{
  removedSet.delete(name);
  allPlayers.forEach((p,i)=>{{ if(p.Player===name) d3.select(`#node-${{i}}`).transition().duration(300).style("opacity",1).style("pointer-events","all"); }});
  updateRemovedPanel();
}}
function updateRemovedPanel() {{
  const panel=document.getElementById("removed-panel");
  const chips=document.getElementById("removed-chips");
  chips.innerHTML="";
  if(removedSet.size===0) {{ panel.classList.remove("visible"); return; }}
  panel.classList.add("visible");
  removedSet.forEach(name=>{{
    const chip=document.createElement("div");
    chip.className="restore-chip";
    chip.innerHTML=`<span class="plus">+</span><span>${{name}}</span>`;
    chip.onclick=()=>restorePlayer(name);
    chips.appendChild(chip);
  }});
}}
function setMode(m) {{
  mode=m;
  document.getElementById("btn-icons").classList.toggle("active",m==="icons");
  document.getElementById("btn-circles").classList.toggle("active",m==="circles");
  g.selectAll(".dot-image").transition().duration(280).style("opacity",m==="icons"?1:0);
  g.selectAll(".dot-ring").transition().duration(280).style("opacity",m==="icons"?1:0);
  g.selectAll(".dot-circle").transition().duration(280).style("opacity",m==="circles"?0.82:0);
}}
</script>
</body>
</html>"""
    st.components.v1.html(html, height=640, scrolling=False)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
st.sidebar.title("⚙️ Navigation")
st.sidebar.markdown("---")
app_mode = st.sidebar.radio("Go To:", [
    "🏠 Home",
    "📖 The CVP Formula",
    "📊 Data Explorer",
    "⚖️ Tactical Comparison",
    "🧠 Player Profiles",
])

# ─────────────────────────────────────────────
# MODE 1: HOME
# ─────────────────────────────────────────────
if app_mode == "🏠 Home":
    st.markdown('<p class="big-font">The Creator System</p>', unsafe_allow_html=True)
    st.subheader("Elite Creator Profiling via Creativity Volume by Passes (CVP)")
    st.markdown("---")

    season = season_toggle("home")
    df = get_df(season)
    insights = INSIGHTS_BY_SEASON[season]

    df["CVP"] = pd.to_numeric(df["CVP"], errors="coerce")
    df["Net_Creativity"] = pd.to_numeric(df["Net_Creativity"], errors="coerce")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Players Tracked", len(df))
    col2.metric("Season", season)
    top_cvp = df.loc[df["CVP"].idxmax()]
    col3.metric("Highest CVP", f"{top_cvp['CVP']:.2f}", delta=top_cvp["Player"])
    top_nc = df.loc[df["Net_Creativity"].idxmax()]
    col4.metric("Highest Net Creativity", f"{top_nc['Net_Creativity']:.2f}", delta=top_nc["Player"])

    st.markdown(f"### 🏆 CVP Leaderboard — {season}")
    top_df = df.sort_values("CVP", ascending=False).reset_index(drop=True)
    top_df.index += 1
    display_cols = ["Player", "Club", "League", "CVP", "Net_Creativity", "Efficiency_Ratio", "KP90", "PrgP90", "xA90"]
    display_cols = [c for c in display_cols if c in top_df.columns]
    st.dataframe(top_df[display_cols], use_container_width=True)

    st.markdown("---")
    st.markdown(f"### 📊 CVP Rankings — {season}")
    bar_df = df.sort_values("CVP", ascending=True)
    fig_bar = px.bar(
        bar_df, x="CVP", y="Player", orientation="h",
        template="plotly_dark",
        color="CVP",
        color_continuous_scale=["#ff5252","#ffc107","#4da6ff","#00e676"],
        hover_data=["Club","League","Net_Creativity","Efficiency_Ratio"],
    )
    fig_bar.update_layout(height=max(500, len(df)*28), yaxis_title="", xaxis_title="CVP (Creativity Volume by Passes)", coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.markdown(f"### 💡 Season Insights — {season}")
    insight_cols = st.columns(2)
    for i, (player, insight_text) in enumerate(insights.items()):
        with insight_cols[i % 2]:
            st.markdown(
                f"<div class='insight-card'>"
                f"<h4>⚡ {player}</h4>"
                f"<p>{insight_text}</p>"
                f"</div>",
                unsafe_allow_html=True
            )


# ─────────────────────────────────────────────
# MODE 2: CVP FORMULA
# ─────────────────────────────────────────────
elif app_mode == "📖 The CVP Formula":
    st.title("📖 Creativity Volume by Passes — Explained")
    st.markdown(
        "**CVP** is a composite metric that quantifies *how much creativity a player generates through their passing and chance-creation actions*, "
        "adjusted for team quality, opponent strength, and volume of opportunity. It rewards line-breaking intent, not safe sideways play."
    )
    st.markdown("---")

    st.subheader("🧮 The Formula")
    st.latex(r"\text{CVP} = \text{Net\_Creativity} \times \text{Efficiency\_Ratio} \times \text{Normalization\_Factor}")
    st.markdown("""
    Where:
    - **Net Creativity** = `KP90 + PrgP90 + Final3rdP90 + xA90 + AccLB90 + AccCr90 − TotalPasses90` (weighted raw creativity minus dilution)
    - **Efficiency Ratio** = proportion of passes that are actually progressive or final-third entries
    - **Normalization Factor** = adjusts for team GPG (goals per game) relative to the average, so players at stronger teams aren't over-credited
    """)

    st.markdown("---")
    st.subheader("🎚️ CVP Tier Thresholds")
    tc1, tc2, tc3, tc4 = st.columns(4)
    tc1.markdown("<div class='score-poor'><div class='score-label'>Below Average</div><div class='score-value' style='color:#ff5252'>< 1.5</div><div class='score-tag' style='color:#ff5252'>BOTTOM TIER</div></div>", unsafe_allow_html=True)
    tc2.markdown("<div class='score-average'><div class='score-label'>Average</div><div class='score-value' style='color:#ffc107'>1.5 – 2.49</div><div class='score-tag' style='color:#ffc107'>MID RANGE</div></div>", unsafe_allow_html=True)
    tc3.markdown("<div class='score-good'><div class='score-label'>Good</div><div class='score-value' style='color:#4da6ff'>2.5 – 3.49</div><div class='score-tag' style='color:#4da6ff'>ABOVE AVERAGE</div></div>", unsafe_allow_html=True)
    tc4.markdown("<div class='score-excellent'><div class='score-label'>Elite</div><div class='score-value' style='color:#00e676'>≥ 3.5</div><div class='score-tag' style='color:#00e676'>TOP CREATORS</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🗡️ Part 1: Net Creativity")
        st.info("Raw creative output summed — key passes, progressive passes, final-third entries, xA, long balls, crosses — minus total passes as a dilution penalty.")
        with st.expander("KP90 — Key Passes per 90"):
            st.markdown("Passes that directly lead to a shot. The most direct measure of chance creation.")
        with st.expander("PrgP90 — Progressive Passes per 90"):
            st.markdown("Passes that move the ball meaningfully towards goal — the forward-thinking metric.")
        with st.expander("xA90 — Expected Assists per 90"):
            st.markdown("Probability-weighted quality of chances created. Rewards dangerous passes, not just frequent ones.")
        with st.expander("AccLB90 / AccCr90 — Long Balls & Crosses"):
            st.markdown("Accurate long balls and crosses — two additional dimensions of creative range that CVP captures.")
    with col2:
        st.markdown("### ⚙️ Part 2: Efficiency & Normalization")
        st.success("**Efficiency Ratio** punishes high-volume safe passers. **Normalization Factor** corrects for team quality — a player at a dominant club has more creative opportunity by default.")
        with st.expander("Efficiency Ratio"):
            st.markdown("Progressive + Final-3rd passes divided by total passes. A player passing 100 times sideways gets penalised heavily.")
        with st.expander("Normalization Factor"):
            st.markdown("Derived from team GPG vs league average GPG. Players at top-of-table clubs are scaled down slightly to prevent system inflation.")
        with st.expander("GPG — Goals Per Game"):
            st.markdown("Used as a proxy for team strength in the normalization formula.")

    st.markdown("---")
    st.subheader("📊 Cross-Season CVP Comparison")
    season_sel = st.multiselect("Select seasons to compare:", SEASONS, default=SEASONS)
    if season_sel:
        combined = []
        for s in season_sel:
            d = get_df(s).copy()
            d["CVP"] = pd.to_numeric(d["CVP"], errors="coerce")
            d["Season"] = s
            combined.append(d[["Player", "CVP", "Season"]])
        comb_df = pd.concat(combined)
        players_in_all = comb_df.groupby("Player")["Season"].nunique()
        common_players = players_in_all[players_in_all >= len(season_sel)].index.tolist() if len(season_sel) > 1 else comb_df["Player"].unique().tolist()
        comb_df = comb_df[comb_df["Player"].isin(common_players)]

        fig = px.line(
            comb_df.sort_values("Season"), x="Season", y="CVP", color="Player",
            markers=True, template="plotly_dark",
            title="CVP Trajectory Across Seasons",
        )
        fig.update_layout(height=480, yaxis_title="CVP", xaxis_title="Season")
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# MODE 3: DATA EXPLORER
# ─────────────────────────────────────────────
elif app_mode == "📊 Data Explorer":
    st.title("📊 Interactive Metric Explorer")
    st.markdown("Hover over any player to see their face, stats, and a tactical insight. Toggle markers. **Hover → click ✕ to remove** from the chart.")

    season = season_toggle("explorer")
    df = get_df(season)
    insights = INSIGHTS_BY_SEASON[season]

    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in ["GPG","EPT","Avg. EPT","Avg.GPG","Normalization_Factor"]]
    
    col1, col2 = st.columns(2)
    with col1:
        xi = safe_index(numeric_cols, "PrgP90", 0)
        x_metric = st.selectbox("X-Axis Metric", numeric_cols, index=xi)
    with col2:
        yi = safe_index(numeric_cols, "KP90", 1)
        y_metric = st.selectbox("Y-Axis Metric", numeric_cols, index=yi)

    players_data = []
    for _, row in df.iterrows():
        entry = {
            "Player": row["Player"],
            "Club":   row["Club"],
            "League": row["League"],
            "CVP":    float(row["CVP"]) if not pd.isna(row["CVP"]) else 0.0,
            "Icons_URL": str(row["Icons_URL"]) if "Icons_URL" in row and not pd.isna(row["Icons_URL"]) else FALLBACK_IMAGE,
            "insight": insights.get(row["Player"], ""),
            x_metric:  float(row[x_metric]) if not pd.isna(row[x_metric]) else 0.0,
        }
        if y_metric != x_metric:
            entry[y_metric] = float(row[y_metric]) if not pd.isna(row[y_metric]) else 0.0
        players_data.append(entry)

    x_label = x_metric.replace("90"," p90").replace("_"," ")
    y_label = y_metric.replace("90"," p90").replace("_"," ")
    render_d3_scatter(players_data, x_metric, y_metric, x_label, y_label)

    st.markdown("---")
    st.subheader(f"📈 Distribution Charts — {season}")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_hist = px.histogram(df, x="CVP", nbins=10, template="plotly_dark",
                                title="CVP Distribution", color_discrete_sequence=["#4da6ff"])
        fig_hist.update_layout(height=320)
        st.plotly_chart(fig_hist, use_container_width=True)
    with chart_col2:
        fig_scatter = px.scatter(df, x="Efficiency_Ratio", y="Net_Creativity", size="CVP",
                                 hover_name="Player", color="CVP",
                                 color_continuous_scale=["#ff5252","#ffc107","#4da6ff","#00e676"],
                                 template="plotly_dark", title="Efficiency vs Net Creativity (size = CVP)")
        fig_scatter.update_layout(height=320, coloraxis_showscale=False)
        st.plotly_chart(fig_scatter, use_container_width=True)


# ─────────────────────────────────────────────
# MODE 4: TACTICAL COMPARISON
# ─────────────────────────────────────────────
elif app_mode == "⚖️ Tactical Comparison":
    st.title("⚖️ Head-to-Head Creator Comparison")

    season = season_toggle("compare")
    df = get_df(season)
    df["CVP"] = pd.to_numeric(df["CVP"], errors="coerce")
    player_names = df["Player"].tolist()

    col1, col2 = st.columns(2)
    with col1:
        p1_name = st.selectbox("Player 1", player_names, index=0)
    with col2:
        p2_name = st.selectbox("Player 2", player_names, index=min(1, len(player_names)-1))

    if p1_name and p2_name:
        p1 = df[df["Player"] == p1_name].iloc[0]
        p2 = df[df["Player"] == p2_name].iloc[0]

        # Header cards
        hcol1, hcol2 = st.columns(2)
        for col, p in [(hcol1, p1), (hcol2, p2)]:
            with col:
                tier_label, tier_color, tier_class = cvp_tier(float(p["CVP"]))
                st.image(get_image_url(str(p.get("Icons_URL",""))), width=120)
                st.markdown(f"### {p['Player']}")
                st.markdown(f"**{p['Club']}** | {p['League']}")
                st.markdown(
                    f"<div class='{tier_class}'>"
                    f"<div class='score-label'>CVP Score</div>"
                    f"<div class='score-value' style='color:{tier_color}'>{float(p['CVP']):.2f}</div>"
                    f"<div class='score-tag' style='color:{tier_color}'>● {tier_label.upper()}</div>"
                    f"</div>", unsafe_allow_html=True
                )

        st.markdown("---")
        st.subheader("📋 Full Stat Comparison")

        compare_metrics = ["CVP", "Net_Creativity", "Efficiency_Ratio", "KP90", "PrgP90", "Final3rdP90",
                           "xA90", "AccLB90", "AccCr90", "TotalPasses90"]
        compare_metrics = [m for m in compare_metrics if m in df.columns]

        all_stats_for_summary = []
        table_html = "<table class='comp-table'>\n"
        table_html += (
            f"<tr><th>Metric</th>"
            f"<th>{p1['Player']}<br><span style='font-size:13px;color:gray;font-weight:normal'>{p1['Club']}</span></th>"
            f"<th>{p2['Player']}<br><span style='font-size:13px;color:gray;font-weight:normal'>{p2['Club']}</span></th></tr>\n"
        )
        for m in compare_metrics:
            v1, v2 = float(p1[m]) if not pd.isna(p1[m]) else 0.0, float(p2[m]) if not pd.isna(p2[m]) else 0.0
            all_stats_for_summary.append((m, v1, v2))
            if v1 > v2:
                c1 = f"{v1:.2f} <span class='win-arrow'>↑</span>"
                c2 = f"{v2:.2f} <span class='lose-arrow'>↓</span>"
            elif v2 > v1:
                c1 = f"{v1:.2f} <span class='lose-arrow'>↓</span>"
                c2 = f"{v2:.2f} <span class='win-arrow'>↑</span>"
            else:
                c1 = f"{v1:.2f} <span style='color:gray'>-</span>"
                c2 = f"{v2:.2f} <span style='color:gray'>-</span>"
            label = m.replace("90"," p90").replace("_"," ")
            table_html += f"<tr><td style='font-weight:bold;color:#e0e0e0'>{label}</td><td>{c1}</td><td>{c2}</td></tr>\n"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

        # Radar chart
        st.markdown("---")
        st.subheader("🕸️ Radar Chart Overlay")
        radar_metrics = ["KP90", "PrgP90", "Final3rdP90", "xA90", "AccLB90", "AccCr90"]
        radar_metrics = [r for r in radar_metrics if r in df.columns]
        radar_labels = [r.replace("90"," p90").replace("Acc","Acc. ").replace("LB","Long Ball").replace("Cr","Cross") for r in radar_metrics]
        fig_radar = go.Figure()
        for player, row in [(p1_name, p1), (p2_name, p2)]:
            vals = [float(row[m]) if not pd.isna(row[m]) else 0.0 for m in radar_metrics]
            fig_radar.add_trace(go.Scatterpolar(r=vals, theta=radar_labels, fill="toself", name=player))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), template="plotly_dark", height=500, showlegend=True)
        st.plotly_chart(fig_radar, use_container_width=True)

        # Tactical summary
        st.markdown("---")
        st.subheader("📋 Tactical Breakdown")
        cache_key = f"cmp_{p1_name}_{p2_name}_{season}"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = None

        col_gen1, col_gen2, _ = st.columns([1.5, 1.5, 5])
        with col_gen1:
            generate_btn = st.button("⚡ Generate Analysis", type="primary")
        with col_gen2:
            if st.session_state[cache_key]:
                if st.button("🔄 Regenerate"):
                    st.session_state[cache_key] = None
                    st.rerun()

        if generate_btn:
            with st.spinner(f"Building {p1_name} vs {p2_name} breakdown..."):
                result = generate_local_summary(p1.to_dict(), p2.to_dict(), season)
                st.session_state[cache_key] = result

        if st.session_state[cache_key]:
            sections = st.session_state[cache_key]
            section_icons = {
                "Chance Creation": "⚔️",
                "Passing Profile": "🎯",
                "Creative Volume & System Context": "📈",
                "Verdict": "⚖️",
            }
            st.markdown("<div class='summary-box'>", unsafe_allow_html=True)
            st.markdown(f"<h3>📋 {p1_name} vs {p2_name} — Tactical Breakdown ({season})</h3>", unsafe_allow_html=True)
            for title, body in sections:
                icon = section_icons.get(title, "📌")
                if title == "Verdict":
                    st.markdown(f"<div class='summary-verdict'><strong>{icon} Verdict:</strong> {body}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p><strong>{icon} {title}:</strong> {body}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        elif not generate_btn:
            st.info("Click **⚡ Generate Analysis** to get a stat-driven tactical breakdown of this matchup.")


# ─────────────────────────────────────────────
# MODE 5: PLAYER PROFILES
# ─────────────────────────────────────────────
elif app_mode == "🧠 Player Profiles":
    st.title("🧠 Comprehensive Player Profiles")

    season = season_toggle("profiles")
    df = get_df(season)
    df["CVP"] = pd.to_numeric(df["CVP"], errors="coerce")
    insights = INSIGHTS_BY_SEASON[season]
    player_names = df["Player"].tolist()

    selected = st.multiselect(
        "Search players (start typing...)",
        options=player_names,
        default=[player_names[0]] if player_names else [],
    )

    if selected:
        for _, p in df[df["Player"].isin(selected)].iterrows():
            with st.expander(f"📂 {p['Player']} — {p['Club']} ({season})", expanded=True):
                col_img, col_info = st.columns([1, 4])
                with col_img:
                    img_url = get_image_url(str(p.get("Icons_URL", "")))
                    st.image(img_url, width=140)
                with col_info:
                    st.markdown(f"# {p['Player']}")
                    st.markdown(f"### {p['Club']} | {p['League']}")
                    st.markdown(f"**Country:** `{p.get('Country','N/A')}`")
                    tier_label, tier_color, tier_class = cvp_tier(float(p["CVP"]))
                    st.markdown(
                        f"<div class='{tier_class}'>"
                        f"<div class='score-label'>CVP — Creativity Volume by Passes</div>"
                        f"<div class='score-value' style='color:{tier_color}'>{float(p['CVP']):.2f}</div>"
                        f"<div class='score-tag' style='color:{tier_color}'>● {tier_label.upper()}</div>"
                        f"</div>", unsafe_allow_html=True
                    )

                st.markdown("---")
                player_insight = insights.get(p["Player"])
                if player_insight:
                    st.markdown("### 🔍 Player Intel")
                    st.markdown(
                        f"<div class='fact-box'>"
                        f"<div class='fact-badge'>TACTICAL INSIGHT</div><br>"
                        f"<span class='fact-icon'>⚡</span>"
                        f"<span class='fact-text'>{player_insight}</span>"
                        f"</div>", unsafe_allow_html=True
                    )

                st.markdown("---")
                tab1, tab2, tab3 = st.tabs(["⚔️ Chance Creation", "🎯 Progression & Passing", "📊 CVP Breakdown"])

                with tab1:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Key Passes p90", f"{float(p['KP90']):.2f}")
                    c2.metric("xA p90", f"{float(p['xA90']):.3f}")
                    c3.metric("Acc. Crosses p90", f"{float(p['AccCr90']):.2f}")
                    c4, c5, c6 = st.columns(3)
                    c4.metric("Final 3rd Passes p90", f"{float(p['Final3rdP90']):.2f}")
                    c5.metric("Acc. Long Balls p90", f"{float(p['AccLB90']):.2f}")
                    c6.metric("Net Creativity", f"{float(p['Net_Creativity']):.2f}")

                with tab2:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Progressive Passes p90", f"{float(p['PrgP90']):.2f}")
                    c2.metric("Total Passes p90", f"{float(p['TotalPasses90']):.2f}")
                    c3.metric("Efficiency Ratio", f"{float(p['Efficiency_Ratio']):.3f}")
                    c4, c5, c6 = st.columns(3)
                    c4.metric("Goals Per Game (Team)", f"{float(p['GPG']):.2f}")
                    c5.metric("Norm. Factor", f"{float(p['Normalization_Factor']):.3f}")
                    c6.metric("CVP", f"{float(p['CVP']):.2f}")

                with tab3:
                    # Mini bar chart showing this player's stats vs season average
                    metrics_to_compare = ["KP90", "PrgP90", "xA90", "Efficiency_Ratio", "Net_Creativity"]
                    metrics_to_compare = [m for m in metrics_to_compare if m in df.columns]
                    avg_vals = df[metrics_to_compare].mean()
                    player_vals = p[metrics_to_compare]

                    comp_data = pd.DataFrame({
                        "Metric": metrics_to_compare,
                        "Player": [float(player_vals[m]) for m in metrics_to_compare],
                        "Season Avg": [float(avg_vals[m]) for m in metrics_to_compare],
                    })
                    fig_comp = go.Figure()
                    fig_comp.add_trace(go.Bar(
                        name=p["Player"], x=comp_data["Metric"], y=comp_data["Player"],
                        marker_color="#4da6ff"
                    ))
                    fig_comp.add_trace(go.Bar(
                        name="Season Average", x=comp_data["Metric"], y=comp_data["Season Avg"],
                        marker_color="#333333"
                    ))
                    fig_comp.update_layout(
                        barmode="group", template="plotly_dark", height=340,
                        title=f"{p['Player']} vs {season} Season Average",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02)
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)
