import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Creator Analytics | CVP System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# DATA LOADING & CLEANING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df_2526 = pd.read_csv("creator_matrices_2526.csv")
    df_2425 = pd.read_csv("creator_metrices_2425.csv")
    df_2324 = pd.read_csv("creator_metrics_2324.csv")
    
    data_dict = {
        "2025/2026": df_2526, 
        "2024/2025": df_2425, 
        "2023/2024": df_2324
    }
    
    # Standardize CVP
    for season, df in data_dict.items():
        for col in df.columns:
            if "Creativity" in col or "Voume" in col:
                df.rename(columns={col: "CVP"}, inplace=True)
                
    return data_dict

data_dict = load_data()

# ─────────────────────────────────────────────
# HELPER: D3 SCATTER PLOT
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
  .remove-btn {{
    cursor: pointer; opacity: 0;
    transition: opacity 0.15s;
    pointer-events: none;
  }}
  .node:hover .remove-btn {{ opacity: 1; pointer-events: all; }}
  #tooltip {{
    position: fixed; pointer-events: none;
    background: #0d1117; border: 1.5px solid #4da6ff;
    border-radius: 14px; opacity: 0;
    transition: opacity 0.18s; z-index: 9999;
    width: 260px; box-shadow: 0 12px 40px rgba(0,0,0,0.7);
    overflow: hidden;
  }}
  #tooltip.visible {{ opacity: 1; }}
  #tt-header {{
    display: flex; align-items: center; gap: 12px;
    padding: 14px; background: #161b22;
    border-bottom: 1px solid #2d333b;
  }}
  #tt-img {{
    width: 50px; height: 50px; border-radius: 50%;
    object-fit: cover; border: 2px solid #4da6ff;
    background: #222;
  }}
  #tt-title {{ display: flex; flex-direction: column; gap: 3px; }}
  #tt-name {{ color: #e6edf3; font-size: 15px; font-weight: 700; line-height: 1.2; }}
  #tt-meta {{ color: #8b949e; font-size: 11px; font-weight: 500; }}
  #tt-body {{ padding: 14px; display: flex; flex-direction: column; gap: 10px; }}
  .tt-row {{ display: flex; justify-content: space-between; align-items: center; }}
  .tt-label {{ color: #8b949e; font-size: 12px; font-weight: 600; }}
  .tt-val {{ color: #e6edf3; font-size: 13px; font-weight: 700; background: #21262d; padding: 2px 8px; border-radius: 6px; }}
  #tt-insight {{
    margin-top: 4px; padding-top: 12px; border-top: 1px dashed #30363d;
    color: #4da6ff; font-size: 11.5px; font-style: italic; line-height: 1.4;
  }}
  .tier-badge {{
    display: inline-block; padding: 2px 6px;
    border-radius: 4px; font-size: 10px; font-weight: 800;
    text-transform: uppercase; margin-top: 4px;
  }}
</style>
</head>
<body>

<div id="controls">
  <span>View Mode:</span>
  <button id="btn-icons" class="toggle-btn active" onclick="setMode('icons')">Icons</button>
  <button id="btn-circles" class="toggle-btn" onclick="setMode('circles')">Circles</button>
</div>

<div id="removed-panel">
  <span>Removed:</span>
  <div id="removed-chips" style="display:flex; gap:6px; flex-wrap:wrap;"></div>
</div>

<div id="chart"></div>

<div id="tooltip">
  <div id="tt-header">
    <img id="tt-img" src="" alt="icon">
    <div id="tt-title">
      <div id="tt-name"></div>
      <div id="tt-meta"></div>
      <div id="tier" class="tier-badge"></div>
    </div>
  </div>
  <div id="tt-body">
    <div class="tt-row"><span class="tt-label">{x_label}</span><span id="tt-x" class="tt-val"></span></div>
    <div class="tt-row"><span class="tt-label">{y_label}</span><span id="tt-y" class="tt-val"></span></div>
    <div class="tt-row"><span class="tt-label">CVP Score</span><span id="tt-ss" class="tt-val" style="color:#00ffcc; background:#003322;"></span></div>
    <div id="tt-insight"></div>
  </div>
</div>

<script>
const allPlayers = {players_json};
let removedSet = new Set();
let mode = "icons"; // icons or circles

const margin = {{top: 40, right: 40, bottom: 60, left: 60}},
      width = window.innerWidth - margin.left - margin.right,
      height = 540 - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

const x = d3.scaleLinear().range([0, width]);
const y = d3.scaleLinear().range([height, 0]);
const sizeScale = d3.scaleLinear().range([16, 28]);

const xAxisGroup = svg.append("g").attr("class", "axis").attr("transform", `translate(0,${{height}})`);
const yAxisGroup = svg.append("g").attr("class", "axis");
const xGrid = svg.append("g").attr("class", "grid").attr("transform", `translate(0,${{height}})`);
const yGrid = svg.append("g").attr("class", "grid");

svg.append("text").attr("class", "axis-label").attr("x", width/2).attr("y", height + 40)
   .style("text-anchor", "middle").text("{x_label}");
svg.append("text").attr("class", "axis-label").attr("transform", "rotate(-90)")
   .attr("x", -height/2).attr("y", -40).style("text-anchor", "middle").text("{y_label}");

const tt = d3.select("#tooltip");

function getTier(score) {{
  if(score >= 6) return {{l:"GOD TIER", c:"#ff00ff", b:"#4d004d"}};
  if(score >= 4.5) return {{l:"ELITE", c:"#00ffcc", b:"#003322"}};
  if(score >= 3.0) return {{l:"WORLD CLASS", c:"#4da6ff", b:"#002244"}};
  return {{l:"STANDARD", c:"#aaaaaa", b:"#222222"}};
}}

function draw() {{
  const activeData = allPlayers.filter(d => !removedSet.has(d.Player_Name));
  
  if (activeData.length === 0) {{
    svg.selectAll(".node").remove();
    return;
  }}

  const xPad = (d3.max(activeData, d => d["{x_col}"]) - d3.min(activeData, d => d["{x_col}"])) * 0.1 || 1;
  const yPad = (d3.max(activeData, d => d["{y_col}"]) - d3.min(activeData, d => d["{y_col}"])) * 0.1 || 1;

  x.domain([d3.min(activeData, d => d["{x_col}"]) - xPad, d3.max(activeData, d => d["{x_col}"]) + xPad]);
  y.domain([d3.min(activeData, d => d["{y_col}"]) - yPad, d3.max(activeData, d => d["{y_col}"]) + yPad]);
  sizeScale.domain([d3.min(allPlayers, p=>p.Sorcerer_Score), d3.max(allPlayers, p=>p.Sorcerer_Score)]);

  xAxisGroup.transition().duration(500).call(d3.axisBottom(x).ticks(8));
  yAxisGroup.transition().duration(500).call(d3.axisLeft(y).ticks(8));
  xGrid.transition().duration(500).call(d3.axisBottom(x).ticks(8).tickSize(-height).tickFormat(""));
  yGrid.transition().duration(500).call(d3.axisLeft(y).ticks(8).tickSize(-width).tickFormat(""));

  const nodes = svg.selectAll(".node").data(activeData, d => d.Player_Name);

  nodes.exit()
    .transition().duration(300)
    .attr("transform", d => `translate(${{x(d["{x_col}"])}},${{height+50}})`)
    .style("opacity", 0)
    .remove();

  const enter = nodes.enter().append("g")
    .attr("class", "node")
    .attr("transform", d => `translate(${{x(d["{x_col}"])}},${{y(d["{y_col}"])-20}})`)
    .style("opacity", 0);

  // Background circle for icons
  enter.append("circle").attr("class", "dot-ring").attr("fill", "#222")
    .attr("stroke", "#4da6ff").attr("stroke-width", 2)
    .attr("r", p=>sizeScale(p.Sorcerer_Score)+2.5);

  // Icon Images
  enter.append("image").attr("class", "dot-image")
    .attr("xlink:href", p=>p.Icons_URL)
    .attr("x", p=>-sizeScale(p.Sorcerer_Score))
    .attr("y", p=>-sizeScale(p.Sorcerer_Score))
    .attr("width",  p=>sizeScale(p.Sorcerer_Score)*2)
    .attr("height", p=>sizeScale(p.Sorcerer_Score)*2)
    .attr("clip-path", p=>`circle(${{sizeScale(p.Sorcerer_Score)}}px at ${{sizeScale(p.Sorcerer_Score)}} ${{sizeScale(p.Sorcerer_Score)}})`);

  // Simple Circles (hidden by default)
  enter.append("circle").attr("class", "dot-circle")
    .attr("fill", "#4da6ff").attr("stroke", "#fff").attr("stroke-width", 1.5)
    .attr("r", p=>sizeScale(p.Sorcerer_Score)+5)
    .style("opacity", 0);

  // Remove Button (Hover to see)
  const btn = enter.append("g").attr("class", "remove-btn")
    .attr("transform", p => `translate(${{sizeScale(p.Sorcerer_Score)+4}}, -${{sizeScale(p.Sorcerer_Score)+4}})`)
    .on("click", (e, p) => {{
      e.stopPropagation();
      removePlayer(p.Player_Name);
    }});
  
  btn.append("circle").attr("r", 9).attr("fill", "#ff4d4d").attr("stroke", "#222");
  btn.append("text").text("✕").attr("fill", "#fff").attr("font-size", "10px").attr("font-weight", "bold")
     .attr("text-anchor", "middle").attr("dy", "3.5px");

  const merged = enter.merge(nodes);

  merged.transition().duration(500)
    .attr("transform", d => `translate(${{x(d["{x_col}"])}},${{y(d["{y_col}"])-10}})`)
    .style("opacity", 1);

  // Interactions
  merged.on("mouseover", (e, p) => {{
    d3.select(e.currentTarget).select(".dot-ring").attr("stroke", "#00ffcc").attr("stroke-width", 3);
    d3.select(e.currentTarget).select(".dot-circle").attr("fill", "#00ffcc");
    
    document.getElementById("tt-img").src = p.Icons_URL;
    document.getElementById("tt-name").textContent = p.Player_Name;
    document.getElementById("tt-meta").textContent = p.Team + " · " + p.Position + " · " + p.Role_Tag;
    document.getElementById("tt-x").textContent = p["{x_col}"].toFixed(2);
    document.getElementById("tt-y").textContent = p["{y_col}"].toFixed(2);
    document.getElementById("tt-ss").textContent = p.Sorcerer_Score.toFixed(2);
    document.getElementById("tt-insight").innerHTML = "💡 " + p.insight;
    
    const tier = getTier(p.Sorcerer_Score);
    const tb = document.getElementById("tier");
    tb.textContent = tier.l;
    tb.style.color = tier.c; tb.style.backgroundColor = tier.b;

    tt.classed("visible", true);
  }}).on("mousemove", (e) => {{
    let mx = e.clientX + 15; let my = e.clientY + 15;
    if(mx + 260 > window.innerWidth) mx = e.clientX - 275;
    tt.style("left", mx + "px").style("top", my + "px");
  }}).on("mouseout", (e) => {{
    d3.select(e.currentTarget).select(".dot-ring").attr("stroke", "#4da6ff").attr("stroke-width", 2);
    d3.select(e.currentTarget).select(".dot-circle").attr("fill", "#4da6ff");
    tt.classed("visible", false);
  }});

  setMode(mode); // Re-apply visibility rules
}}

function removePlayer(name) {{
  removedSet.add(name);
  tt.classed("visible", false);
  updatePanel();
  draw();
}}

function restorePlayer(name) {{
  removedSet.delete(name);
  updatePanel();
  draw();
}}

function updatePanel() {{
  const panel = document.getElementById("removed-panel");
  const chips = document.getElementById("removed-chips");
  chips.innerHTML = "";
  
  if(removedSet.size === 0) {{
    panel.classList.remove("visible");
  }} else {{
    panel.classList.add("visible");
    removedSet.forEach(name => {{
      const chip = document.createElement("div");
      chip.className = "restore-chip";
      chip.innerHTML = `<span class="plus">+</span><span>${{name}}</span>`;
      chip.onclick = () => restorePlayer(name);
      chips.appendChild(chip);
    }});
  }}
}}

function setMode(m) {{
  mode = m;
  document.getElementById("btn-icons").classList.toggle("active", m==="icons");
  document.getElementById("btn-circles").classList.toggle("active", m==="circles");
  
  d3.selectAll(".dot-image").transition().duration(280).style("opacity", m==="icons"?1:0);
  d3.selectAll(".dot-ring").transition().duration(280).style("opacity", m==="icons"?1:0);
  d3.selectAll(".dot-circle").transition().duration(280).style("opacity", m==="circles"?0.82:0);
}}

draw();
</script>
</body>
</html>"""
    st.components.v1.html(html, height=660, scrolling=False)


# ─────────────────────────────────────────────
# HELPER: INSIGHTS
# ─────────────────────────────────────────────
def generate_insights(row, df):
    metrics = ['KP90', 'PrgP90', 'xA90', 'CVP']
    insights = []
    for m in metrics:
        pct = (df[m] < row[m]).mean() * 100
        if pct >= 90:
            insights.append(f"🌟 **Elite in {m}** (Top 10%) at {row[m]}")
        elif pct >= 75:
            insights.append(f"📈 **Strong in {m}** (Top 25%) at {row[m]}")
        elif pct <= 25:
            insights.append(f"⚠️ **Below Average in {m}** (Bottom 25%) at {row[m]}")
            
    if not insights:
        insights.append("⚖️ Balanced performer across all key metrics without major extremes.")
    return insights

# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
st.sidebar.title("⚙️ System Navigation")
selected_season = st.sidebar.selectbox("📅 Select Season:", list(data_dict.keys()))
df = data_dict[selected_season]

st.sidebar.markdown("---")
app_mode = st.sidebar.radio("Go To:", [
    "🏆 Leaderboards", 
    "📊 Graph Explorer", 
    "👤 Player Profile", 
    "⚖️ Comparison"
])

# ─────────────────────────────────────────────
# MAIN APP LOGIC
# ─────────────────────────────────────────────

if app_mode == "🏆 Leaderboards":
    st.title(f"🏆 Creativity Volume by Passes (CVP) - {selected_season}")
    st.markdown("Top 20 most creative players based on overall passing volume & danger generated.")
    
    top_players = df.sort_values("CVP", ascending=False).head(20)
    fig = px.bar(top_players, x="CVP", y="Player", color="Club", orientation="h", title="Top 20 Players by CVP", template="plotly_dark")
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.drop(columns=['Icons_URL', 'Image_URL'], errors='ignore'), use_container_width=True)

elif app_mode == "📊 Graph Explorer":
    st.title(f"📊 Interactive Metric Explorer - {selected_season}")
    st.markdown("Toggle markers between Icons and Circles. **Hover → click ✕ to temporarily remove a player** from the chart. Click their name in the bar at the top to restore them.")
    
    numeric_cols = ['KP90', 'PrgP90', 'Final3rdP90', 'xA90', 'AccLB90', 'AccCr90', 'TotalPasses90', 'GPG', 'EPT', 'Avg. EPT', 'Avg.GPG', 'CVP']
    
    col1, col2 = st.columns(2)
    with col1:
        x_metric = st.selectbox("🎯 X-Axis Metric", numeric_cols, index=1)
    with col2:
        y_metric = st.selectbox("🚀 Y-Axis Metric", numeric_cols, index=11)
        
    players_data = []
    for _, row in df.iterrows():
        # Mapping new CSV structure to the format the D3 JS expects
        entry = {
            "Player_Name":    str(row["Player"]),
            "Team":           str(row["Club"]),
            "Position":       str(row["League"]), 
            "Role_Tag":       str(row["Country"]), 
            "Sorcerer_Score": float(row["CVP"]),  # D3 uses Sorcerer_Score internally for sizing and tiering
            "Icons_URL":      str(row["Icons_URL"]) if not pd.isna(row["Icons_URL"]) else "https://via.placeholder.com/150",
            "insight":        f"CVP Rating: {row['CVP']}",
            x_metric:         float(row[x_metric])
        }
        if y_metric != x_metric:
            entry[y_metric] = float(row[y_metric])
        players_data.append(entry)

    x_label = x_metric.replace("90", " (per 90)").replace("_", " ").title()
    y_label = y_metric.replace("90", " (per 90)").replace("_", " ").title()
    
    render_d3_scatter(players_data, x_metric, y_metric, x_label, y_label)

elif app_mode == "👤 Player Profile":
    st.title(f"👤 Player Profile Viewer - {selected_season}")
    player_name = st.selectbox("Select Player", df["Player"].unique())
    p_row = df[df["Player"] == player_name].iloc[0]
    
    col1, col2, col3 = st.columns([1, 1.5, 2.5])
    with col1:
        st.image(p_row["Image_URL"], use_container_width=True)
    with col2:
        try:
            st.image(p_row["Icons_URL"], width=80)
        except: pass
        st.markdown(f"<h2 style='margin-bottom:0px;'>{p_row['Player']}</h2>", unsafe_allow_html=True)
        st.write(f"**Club:** {p_row['Club']}")
        st.write(f"**League:** {p_row['League']} | **Country:** {p_row['Country']}")
        st.markdown(f"### CVP Score: `{p_row['CVP']}`")
    with col3:
        st.markdown("### 💡 Algorithmic Insights")
        for ins in generate_insights(p_row, df):
            st.markdown(f"- {ins}")
            
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🎯 Danger Zone & Chance Creation", "🚀 Progression & Volume", "📊 Overall Impact"])
    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Key Passes (KP90)", p_row["KP90"])
        c2.metric("Expected Assists (xA90)", p_row["xA90"])
        c3.metric("Acc Crosses (AccCr90)", p_row["AccCr90"])
    with tab2:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Prog Passes (PrgP90)", p_row["PrgP90"])
        c2.metric("Final 3rd Passes", p_row["Final3rdP90"])
        c3.metric("Acc Long Balls", p_row["AccLB90"])
        c4.metric("Total Passes", p_row["TotalPasses90"])
    with tab3:
        c1, c2, c3 = st.columns(3)
        c1.metric("GPG", p_row["GPG"])
        c2.metric("EPT", p_row["EPT"])
        c3.metric("Avg EPT", p_row["Avg. EPT"])

    st.markdown("---")
    st.markdown(f"### {p_row['Player']} Percentile Radar")
    radar_metrics = ['KP90', 'PrgP90', 'Final3rdP90', 'xA90', 'AccLB90', 'AccCr90', 'TotalPasses90']
    pcts = [(df[m] < p_row[m]).mean() * 100 for m in radar_metrics]
    
    fig_radar = go.Figure(go.Scatterpolar(r=pcts, theta=radar_metrics, fill='toself', name=player_name, marker=dict(color='cyan')))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, template="plotly_dark", margin=dict(t=20, b=20))
    st.plotly_chart(fig_radar, use_container_width=True)

elif app_mode == "⚖️ Comparison":
    st.title(f"⚖️ Head-to-Head Comparison - {selected_season}")
    p1_col, p2_col = st.columns(2)
    with p1_col:
        player1 = st.selectbox("Select Player 1", df["Player"].unique())
    with p2_col:
        player2 = st.selectbox("Select Player 2", df["Player"].unique(), index=1 if len(df) > 1 else 0)
        
    r1 = df[df["Player"] == player1].iloc[0]
    r2 = df[df["Player"] == player2].iloc[0]
    
    metrics_to_compare = ['KP90', 'PrgP90', 'Final3rdP90', 'xA90', 'AccLB90', 'AccCr90', 'TotalPasses90', 'CVP']
    
    fig_comp = go.Figure()
    pcts1 = [(df[m] < r1[m]).mean() * 100 for m in metrics_to_compare[:-1]] 
    pcts2 = [(df[m] < r2[m]).mean() * 100 for m in metrics_to_compare[:-1]]
    
    fig_comp.add_trace(go.Scatterpolar(r=pcts1, theta=metrics_to_compare[:-1], fill='toself', name=player1))
    fig_comp.add_trace(go.Scatterpolar(r=pcts2, theta=metrics_to_compare[:-1], fill='toself', name=player2))
    fig_comp.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), template="plotly_dark")
    
    chart_col, table_col = st.columns([1.5, 1])
    with chart_col:
        st.plotly_chart(fig_comp, use_container_width=True)
    with table_col:
        st.markdown("### Raw Stats")
        comp_df = pd.DataFrame({"Metric": metrics_to_compare, player1: [r1[m] for m in metrics_to_compare], player2: [r2[m] for m in metrics_to_compare]})
        st.dataframe(comp_df, hide_index=True, use_container_width=True)