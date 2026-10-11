from pathlib import Path
import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
DATA_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Union Budget Intelligence Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual system ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#edf3ff; --muted:#91a0bb; --panel:#101827; --panel2:#141f32; --line:rgba(151,173,211,.16); --cyan:#5de4d0; --blue:#6b8cff; --violet:#ad8cff; }
html, body, [class*="css"] { font-family:'Manrope', sans-serif; }
.stApp { background: radial-gradient(ellipse at 15% 0%, rgba(60,95,175,.18), transparent 35%), radial-gradient(ellipse at 95% 12%, rgba(31,173,159,.10), transparent 30%), #080d17; color:var(--ink); }
.block-container { padding-top:1.2rem; padding-bottom:2rem; max-width:1600px; }
[data-testid="stSidebar"] { background:#0b1220; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:#dfe8fb; }
h1,h2,h3 { letter-spacing:-.04em; }
h1 { font-weight:800; }
.hero { padding:1.5rem 1.7rem; border:1px solid rgba(115,153,220,.23); border-radius:22px; background:linear-gradient(120deg,rgba(28,45,75,.95),rgba(13,24,41,.88)); position:relative; overflow:hidden; margin-bottom:1rem; }
.hero:after { content:""; position:absolute; width:280px;height:280px;right:-65px;top:-150px;border-radius:50%;border:1px solid rgba(93,228,208,.22);box-shadow:0 0 0 28px rgba(93,228,208,.025),0 0 0 58px rgba(107,140,255,.025); }
.eyebrow { text-transform:uppercase; letter-spacing:.19em; font-family:'DM Mono',monospace; color:#5de4d0; font-size:.72rem; }
.hero-title { font-size:2.2rem; font-weight:800; line-height:1.1; margin:.35rem 0 .65rem; color:#f4f7ff; }
.hero-sub { color:#a8b7d2; max-width:760px; font-size:.96rem; }
.pill { display:inline-block; border:1px solid rgba(93,228,208,.35); background:rgba(93,228,208,.08); color:#77f0de; border-radius:999px; padding:.35rem .7rem; font-size:.72rem; font-family:'DM Mono',monospace; }
.metric { border:1px solid var(--line); background:linear-gradient(145deg,rgba(20,31,50,.97),rgba(12,20,34,.97)); border-radius:17px; padding:1rem 1.05rem; min-height:122px; }
.metric-label { color:#91a0bb; font-family:'DM Mono',monospace; font-size:.7rem; letter-spacing:.1em; text-transform:uppercase; }
.metric-value { color:#f2f6ff; font-size:1.65rem; font-weight:800; letter-spacing:-.05em; margin:.3rem 0 .1rem; }
.metric-foot { color:#5de4d0; font-size:.75rem; }
.section-kicker { color:#5de4d0; text-transform:uppercase; font-family:'DM Mono',monospace; font-size:.7rem; letter-spacing:.16em; margin-bottom:.25rem; }
.section-title { font-size:1.35rem; font-weight:800; letter-spacing:-.04em; margin-bottom:.3rem; }
.section-note { color:#91a0bb; font-size:.83rem; margin-bottom:.7rem; }
div[data-testid="stMetric"] { background:rgba(17,27,44,.85); border:1px solid var(--line); padding:14px 16px; border-radius:15px; }
div[data-testid="stMetricLabel"] { color:#91a0bb; }
div[data-testid="stMetricValue"] { color:#f3f6ff; }
.stTabs [data-baseweb="tab-list"] { gap:8px; background:transparent; }
.stTabs [data-baseweb="tab"] { background:#111b2b; border:1px solid var(--line); border-radius:10px; padding:8px 15px; }
.stTabs [aria-selected="true"] { background:rgba(93,228,208,.12)!important; border-color:rgba(93,228,208,.45)!important; }
div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
div.stButton > button, div.stDownloadButton > button { border-radius:10px; border:1px solid rgba(93,228,208,.35); background:rgba(93,228,208,.09); color:#dffefa; font-weight:700; }
div.stButton > button:hover, div.stDownloadButton > button:hover { border-color:#5de4d0; background:rgba(93,228,208,.16); color:white; }
hr { border-color:var(--line); }
footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

CHART_TEMPLATE = "plotly_dark"
PLOT_BG = "rgba(0,0,0,0)"
PAPER_BG = "rgba(0,0,0,0)"
PALETTE = ["#5de4d0", "#6b8cff", "#ad8cff", "#ffb86b", "#ff6f91", "#7bd88f", "#75c9ff", "#e8e47b"]

def polish(fig, height=None, legend=True):
    fig.update_layout(
        template=CHART_TEMPLATE, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=dict(family="Manrope, sans-serif", color="#dce6fa", size=12),
        margin=dict(l=12, r=12, t=54, b=12),
        title=dict(x=0.02, xanchor="left", font=dict(size=17, color="#f0f5ff")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0) if legend else None,
        hoverlabel=dict(bgcolor="#111b2b", bordercolor="#5de4d0", font=dict(color="#f5f8ff")),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(145,160,187,.12)", zerolinecolor="rgba(145,160,187,.18)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(145,160,187,.12)", zerolinecolor="rgba(145,160,187,.18)")
    if height:
        fig.update_layout(height=height)
    return fig

def money(v):
    if pd.isna(v): return "—"
    v = float(v)
    if abs(v) >= 100000:
        return f"₹{v/100000:,.2f}L Cr"
    if abs(v) >= 1000:
        return f"₹{v/1000:,.2f}K Cr"
    return f"₹{v:,.0f} Cr"

def make_demo():
    # Explicitly illustrative data for UI preview only, not official budget figures.
    rng = np.random.default_rng(27)
    sectors = [
        "Defence", "Road Transport & Highways", "Railways", "Home Affairs", "Rural Development",
        "Education", "Health & Family Welfare", "Agriculture", "Jal Shakti", "Housing & Urban Affairs",
        "Consumer Affairs, Food & Public Distribution", "Communications", "New & Renewable Energy",
        "Science & Technology", "Environment, Forest & Climate Change", "Social Justice & Empowerment",
        "Women & Child Development", "Electronics & IT", "Commerce & Industry", "External Affairs",
        "Petroleum & Natural Gas", "Power", "Textiles", "Tourism", "Skill Development",
        "Tribal Affairs", "Labour & Employment", "Micro, Small & Medium Enterprises", "Civil Aviation",
        "Fisheries, Animal Husbandry & Dairying"
    ]
    years = [f"{y}-{str(y+1)[-2:]}" for y in range(2015, 2025)]
    base = np.geomspace(90000, 500, len(sectors))
    rows = []
    for i, sector in enumerate(sectors):
        level = base[i] * rng.uniform(.7, 1.4)
        growth = rng.uniform(-.015, .15)
        for j, year in enumerate(years):
            shock = rng.normal(0, .045)
            value = max(20, level * ((1 + growth) ** j) * np.exp(shock * np.sqrt(j + 1)))
            rows.append({
                "sector": sector, "financial_year": year, "allocation_crore": round(value, 2),
                "estimate_type": "BE", "source": "ILLUSTRATIVE DEMO — NOT OFFICIAL DATA",
                "notes": "Synthetic values used only to preview the dashboard UI"
            })
    return pd.DataFrame(rows)

def normalize(df):
    required = {"sector", "financial_year", "allocation_crore"}
    if not required.issubset(df.columns):
        raise ValueError("Dataset must contain sector, financial_year, allocation_crore.")
    d = df.copy()
    d["sector"] = d["sector"].astype(str).str.strip()
    d["financial_year"] = d["financial_year"].astype(str).str.strip()
    d["allocation_crore"] = pd.to_numeric(d["allocation_crore"], errors="coerce")
    d = d.dropna(subset=["sector", "financial_year", "allocation_crore"])
    d = d[(d["sector"] != "") & (d["allocation_crore"] >= 0)]
    if "estimate_type" not in d: d["estimate_type"] = "BE"
    d["estimate_type"] = d["estimate_type"].fillna("BE").astype(str).str.upper().str.strip()
    if "source" not in d: d["source"] = "Not provided"
    if "notes" not in d: d["notes"] = ""
    dup = d.duplicated(["sector", "financial_year", "estimate_type"], keep=False)
    if dup.any():
        raise ValueError("Duplicate sector/year/estimate_type rows found. Resolve duplicates before analysis.")
    return d

def metrics_for(df):
    years = sorted(df["financial_year"].unique().tolist())
    wide = df.pivot(index="sector", columns="financial_year", values="allocation_crore").reindex(columns=years)
    first, latest = wide[years[0]], wide[years[-1]]
    previous = wide[years[-2]] if len(years) > 1 else pd.Series(index=wide.index, dtype=float)
    m = pd.DataFrame(index=wide.index)
    m["First year"] = first
    m["Latest year"] = latest
    m["Absolute change"] = latest - first
    m["Change %"] = np.where(first.notna() & (first != 0), (latest / first - 1) * 100, np.nan)
    n = max(len(years)-1, 1)
    m["CAGR %"] = np.where(first.notna() & latest.notna() & (first > 0) & (latest >= 0), ((latest / first) ** (1/n)-1)*100, np.nan)
    m["YoY change %"] = np.where(previous.notna() & (previous != 0), (latest / previous - 1)*100, np.nan)
    m["Latest rank"] = latest.rank(ascending=False, method="min")
    return wide, m.sort_values("Latest year", ascending=False), years

# ---------- Sidebar ----------
st.sidebar.markdown('<div class="eyebrow">FINANCIAL INTELLIGENCE</div><h2 style="margin:.2rem 0 0">◈ UBIS</h2><div style="color:#91a0bb;font-size:.78rem;margin-bottom:1rem">Union Budget Intelligence Studio</div>', unsafe_allow_html=True)
mode = st.sidebar.radio("DATA SOURCE", ["Preview dashboard", "Upload official CSV", "Use project CSV"], index=0)
uploaded = None
if mode == "Upload official CSV":
    uploaded = st.sidebar.file_uploader("Upload consolidated CSV", type=["csv"])
elif mode == "Use project CSV":
    candidate = DATA_DIR / "union_budget_allocations.csv"
    if candidate.exists():
        uploaded = candidate
    else:
        st.sidebar.info("No project CSV found yet. Add data/union_budget_allocations.csv.")
        mode = "Preview dashboard"

if mode == "Upload official CSV" and uploaded is not None:
    try:
        raw = pd.read_csv(uploaded)
        df = normalize(raw)
        demo_mode = False
    except Exception as e:
        st.error(f"Could not load dataset: {e}")
        st.stop()
else:
    if mode == "Use project CSV" and isinstance(uploaded, Path):
        try:
            df = normalize(pd.read_csv(uploaded))
            demo_mode = False
        except Exception as e:
            st.error(f"Could not load project CSV: {e}")
            st.stop()
    else:
        df = make_demo()
        demo_mode = True

# Sidebar filters
if demo_mode:
    st.sidebar.warning("DEMO DATA: all figures are synthetic and must not be cited as government allocations.")
types = sorted(df["estimate_type"].dropna().unique().tolist())
selected_type = st.sidebar.selectbox("ESTIMATE CATEGORY", types, index=0)
df = df[df["estimate_type"] == selected_type].copy()
all_years = sorted(df["financial_year"].unique().tolist())
if len(all_years) >= 2:
    year_range = st.sidebar.select_slider("YEAR WINDOW", options=all_years, value=(all_years[0], all_years[-1]))
    chosen_years = all_years[all_years.index(year_range[0]):all_years.index(year_range[1])+1]
else:
    chosen_years = all_years
df = df[df["financial_year"].isin(chosen_years)]
all_sectors = sorted(df["sector"].unique().tolist())
sector_filter = st.sidebar.multiselect("FOCUS SECTORS", all_sectors, default=[])
if sector_filter:
    df = df[df["sector"].isin(sector_filter)]
top_n = st.sidebar.slider("RANKING DEPTH", min_value=5, max_value=30, value=15, step=5)
st.sidebar.markdown("---")
st.sidebar.caption("Designed for comparable year-wise allocations. Keep BE, RE and Actuals separate.")

if df.empty:
    st.warning("No rows match these filters. Adjust the sidebar selections.")
    st.stop()

wide, metrics, years = metrics_for(df)
latest_year = years[-1]
latest_total = df[df["financial_year"] == latest_year]["allocation_crore"].sum()
prev_year = years[-2] if len(years) > 1 else None
prev_total = df[df["financial_year"] == prev_year]["allocation_crore"].sum() if prev_year else np.nan
yoy_total = ((latest_total / prev_total)-1)*100 if pd.notna(prev_total) and prev_total != 0 else np.nan
coverage = df.groupby("financial_year")["sector"].nunique()

# ---------- Hero ----------
st.markdown(f"""
<div class="hero">
  <div class="eyebrow">PUBLIC FINANCE • TEN-YEAR LENS • DATA EXPLORATION</div>
  <div class="hero-title">Follow the money.<br><span style="color:#5de4d0">See the shift.</span></div>
  <div class="hero-sub">An interactive command center for ministry allocations, budget momentum, rank changes and long-run public spending patterns.</div>
  <div style="display:flex;gap:.6rem;flex-wrap:wrap;margin-top:1rem">
    <span class="pill">{len(years)} FINANCIAL YEARS</span>
    <span class="pill">{df['sector'].nunique()} SECTORS IN VIEW</span>
    <span class="pill">{selected_type} SERIES</span>
    <span class="pill">{'DEMO PREVIEW' if demo_mode else 'USER DATASET'}</span>
  </div>
</div>
""", unsafe_allow_html=True)

if demo_mode:
    st.warning("Preview mode is active. Charts use synthetic illustrative data to demonstrate the UI. Upload verified official data before drawing or publishing any budget conclusions.")

# KPI row
c1,c2,c3,c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric"><div class="metric-label">INCLUDED ALLOCATIONS · {latest_year}</div><div class="metric-value">{money(latest_total)}</div><div class="metric-foot">Sum of rows in current filters</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric"><div class="metric-label">YEAR-ON-YEAR MOMENTUM</div><div class="metric-value">{f"{yoy_total:+.1f}%" if pd.notna(yoy_total) else "—"}</div><div class="metric-foot">{f"{prev_year} → {latest_year}" if prev_year else "Needs 2+ years"}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric"><div class="metric-label">SECTORS TRACKED</div><div class="metric-value">{df["sector"].nunique():,}</div><div class="metric-foot">Target: up to 100 sectors</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric"><div class="metric-label">DATA POINTS</div><div class="metric-value">{len(df):,}</div><div class="metric-foot">Rows after filters</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
tabs = st.tabs(["◈ Overview", "↗ Time-lapse", "▦ Sector matrix", "⌁ Growth lab", "◎ Composition", "≋ Data quality"])

# Overview
with tabs[0]:
    left, right = st.columns([1.5, 1])
    with left:
        trend = df.groupby("financial_year", as_index=False)["allocation_crore"].sum()
        fig = px.area(trend, x="financial_year", y="allocation_crore", title="Allocation trajectory",
                      labels={"financial_year":"Financial year","allocation_crore":"Included allocations (₹ crore)"})
        fig.update_traces(line=dict(color="#5de4d0", width=3), fillcolor="rgba(93,228,208,.13)")
        polish(fig, 360, False)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        rank = metrics.head(top_n).reset_index(names="sector")
        fig = px.bar(rank.sort_values("Latest year"), x="Latest year", y="sector", orientation="h",
                     title=f"Allocation leaders · {latest_year}", color="Latest year",
                     color_continuous_scale=["#263b67","#5de4d0"],
                     labels={"Latest year":"₹ crore","sector":""})
        polish(fig, 360, False)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    l2, r2 = st.columns(2)
    with l2:
        if len(years) > 1:
            change = metrics.dropna(subset=["Change %"]).sort_values("Change %").copy()
            show = pd.concat([change.head(5), change.tail(5)]).reset_index(names="sector")
            fig = px.bar(show, x="Change %", y="sector", orientation="h", color="Change %",
                         color_continuous_scale=["#ff6f91","#263b67","#5de4d0"], title="Biggest long-run movers",
                         labels={"Change %":"Change since first year (%)","sector":""})
            polish(fig, 340, False)
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add at least two financial years to view long-run movers.")
    with r2:
        coverage_df = coverage.rename("sectors").reset_index()
        fig = px.line(coverage_df, x="financial_year", y="sectors", markers=True,
                      title="Coverage by financial year", labels={"sectors":"Sectors with data","financial_year":"Financial year"})
        fig.update_traces(line=dict(color="#ad8cff", width=3), marker=dict(size=8))
        polish(fig, 340, False)
        st.plotly_chart(fig, use_container_width=True)

# Time-lapse
with tabs[1]:
    st.markdown('<div class="section-kicker">ANIMATED RANKING</div><div class="section-title">Watch the allocation leaderboard evolve</div><div class="section-note">Use the play control or scrub through financial years. For a fair comparison, the axis is held constant across frames.</div>', unsafe_allow_html=True)
    latest_rank_sectors = metrics.head(100).index.tolist()
    anim = df[df["sector"].isin(latest_rank_sectors)].copy()
    maxv = anim["allocation_crore"].max()
    fig = px.bar(anim, x="allocation_crore", y="sector", color="allocation_crore",
                 animation_frame="financial_year", animation_group="sector", orientation="h",
                 range_x=[0, float(maxv)*1.08 if maxv > 0 else 1],
                 title="Ministry / department ranking by year",
                 labels={"allocation_crore":"Allocation (₹ crore)","sector":""},
                 color_continuous_scale=["#263b67","#6b8cff","#5de4d0"])
    fig.update_layout(yaxis={"categoryorder":"total ascending"}, height=800,
                      transition={"duration":650}, coloraxis_showscale=False,
                      updatemenus=[dict(type="buttons", showactive=False, x=1, y=1.18,
                                        buttons=[dict(label="▶ Play", method="animate", args=[None, {"frame":{"duration":800,"redraw":True},"fromcurrent":True}]),
                                                 dict(label="Ⅱ Pause", method="animate", args=[[None], {"mode":"immediate","frame":{"duration":0,"redraw":False},"transition":{"duration":0}}])])])
    polish(fig, 800, False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Animated charts show only available rows. Missing data is not treated as zero.")

# Heatmap
with tabs[2]:
    st.markdown('<div class="section-kicker">PATTERN DETECTION</div><div class="section-title">Sector × year matrix</div><div class="section-note">Scan for allocation acceleration, plateaus and contraction. Hover for exact values.</div>', unsafe_allow_html=True)
    heat_wide = wide.loc[metrics.head(100).index]
    fig = go.Figure(data=go.Heatmap(
        z=heat_wide.to_numpy(dtype=float), x=heat_wide.columns.astype(str), y=heat_wide.index.astype(str),
        colorscale=[[0,"#111b2b"],[.35,"#263b67"],[.7,"#6b8cff"],[1,"#5de4d0"]],
        colorbar=dict(title="₹ crore"),
        hovertemplate="<b>%{y}</b><br>Year: %{x}<br>Allocation: ₹%{z:,.2f} crore<extra></extra>"
    ))
    fig.update_layout(title="Allocation intensity map", height=max(620,min(1300,18*len(heat_wide))),
                      xaxis_title="Financial year", yaxis_title="Sector")
    polish(fig, max(620,min(1300,18*len(heat_wide))), False)
    st.plotly_chart(fig, use_container_width=True)
    st.download_button("Download sector-year matrix CSV", heat_wide.reset_index().to_csv(index=False).encode("utf-8"), "sector_year_matrix.csv", "text/csv")

# Growth lab
with tabs[3]:
    st.markdown('<div class="section-kicker">MOMENTUM & VOLATILITY</div><div class="section-title">Growth lab</div><div class="section-note">Compare long-run CAGR, absolute movement and latest-year changes.</div>', unsafe_allow_html=True)
    g1,g2 = st.columns(2)
    with g1:
        cagr_df = metrics.dropna(subset=["CAGR %"]).sort_values("CAGR %", ascending=False).head(top_n).reset_index(names="sector")
        fig = px.bar(cagr_df.sort_values("CAGR %"), x="CAGR %", y="sector", orientation="h", color="CAGR %",
                     color_continuous_scale=["#ff6f91","#263b67","#5de4d0"], title="Compound annual growth rate",
                     labels={"sector":"","CAGR %":"CAGR (%)"})
        polish(fig, 520, False); fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        yoy_df = metrics.dropna(subset=["YoY change %"]).sort_values("YoY change %").copy()
        yoy_df = pd.concat([yoy_df.head(min(top_n//2,10)),yoy_df.tail(min(top_n//2,10))]).drop_duplicates().reset_index(names="sector")
        fig = px.bar(yoy_df.sort_values("YoY change %"), x="YoY change %", y="sector", orientation="h",
                     color="YoY change %", color_continuous_scale=["#ff6f91","#263b67","#5de4d0"],
                     title=f"Latest-year change · {years[-2] if len(years)>1 else ''} → {latest_year}",
                     labels={"sector":"","YoY change %":"Change (%)"})
        fig.add_vline(x=0, line_dash="dash", line_color="#91a0bb")
        polish(fig, 520, False); fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Growth vs allocation scale")
    scatter = metrics.dropna(subset=["CAGR %","Latest year"]).reset_index(names="sector")
    fig = px.scatter(scatter, x="Latest year", y="CAGR %", size="Latest year", color="CAGR %",
                     hover_name="sector", size_max=42, color_continuous_scale=["#ff6f91","#6b8cff","#5de4d0"],
                     title="Scale vs growth", labels={"Latest year":"Latest allocation (₹ crore)","CAGR %":"CAGR (%)"})
    polish(fig, 500, False); fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Full metrics table")
    display_metrics = metrics.reset_index(names="sector")
    st.dataframe(display_metrics, use_container_width=True, hide_index=True)
    st.download_button("Download growth metrics CSV", display_metrics.to_csv(index=False).encode("utf-8"), "growth_metrics.csv", "text/csv")

# Composition
with tabs[4]:
    st.markdown('<div class="section-kicker">WHERE THE MONEY SITS</div><div class="section-title">Allocation composition</div><div class="section-note">Switch years to compare the spending mix and concentration of included sectors.</div>', unsafe_allow_html=True)
    pick_year = st.selectbox("Choose financial year", years, index=len(years)-1, key="composition_year")
    comp = df[df["financial_year"] == pick_year].sort_values("allocation_crore", ascending=False)
    comp_top = comp.head(top_n).copy()
    comp_top["Share %"] = comp_top["allocation_crore"] / comp["allocation_crore"].sum() * 100 if comp["allocation_crore"].sum() else 0
    a,b = st.columns([1.2,1])
    with a:
        fig = px.treemap(comp_top, path=["sector"], values="allocation_crore", color="allocation_crore",
                         color_continuous_scale=["#263b67","#6b8cff","#5de4d0"],
                         title=f"Top {len(comp_top)} allocations · {pick_year}")
        polish(fig, 520, False); fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with b:
        fig = px.pie(comp_top, names="sector", values="allocation_crore", hole=.68,
                     title=f"Top {len(comp_top)} share · {pick_year}", color_discrete_sequence=PALETTE)
        fig.update_traces(textposition="inside", textinfo="percent", hole=.68, marker=dict(line=dict(color="#0b1220", width=2)))
        polish(fig, 520, True)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(comp_top[["sector","allocation_crore","Share %","source"]], use_container_width=True, hide_index=True)

# Data quality
with tabs[5]:
    st.markdown('<div class="section-kicker">TRUST BEFORE INSIGHT</div><div class="section-title">Data quality & provenance</div><div class="section-note">Budget analysis is only meaningful when classifications, units and estimate types are comparable.</div>', unsafe_allow_html=True)
    q1,q2,q3 = st.columns(3)
    with q1: st.metric("Rows in current view", f"{len(df):,}")
    with q2: st.metric("Unique sectors", f"{df['sector'].nunique():,}")
    with q3: st.metric("Estimate type", selected_type)
    quality = df.groupby("financial_year").agg(
        records=("sector","size"), unique_sectors=("sector","nunique"),
        missing_source=("source", lambda x: int(x.isna().sum() + (x.astype(str).str.strip().isin(["","Not provided"]).sum()))),
        min_allocation=("allocation_crore","min"), max_allocation=("allocation_crore","max")
    ).reset_index()
    fig = px.bar(quality, x="financial_year", y="unique_sectors", title="Sector coverage by year",
                 labels={"financial_year":"Financial year","unique_sectors":"Unique sectors"},
                 color="unique_sectors", color_continuous_scale=["#263b67","#5de4d0"])
    polish(fig, 350, False); fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Provenance checks")
    st.dataframe(quality, use_container_width=True, hide_index=True)
    st.markdown("""
    **Before publishing results**
    - Use the same estimate category across years: Budget Estimates (BE), Revised Estimates (RE), or Actuals.
    - Confirm all figures use the same unit, preferably ₹ crore.
    - Check ministry renames, splits, mergers and classification changes.
    - Do not count parent-ministry totals together with departmental subtotals.
    - Record source URL, document name, page/table and extraction notes for each figure.
    - Leave unavailable values blank; never silently turn missing values into zero.
    """)

# Footer / export
st.markdown("---")
foot_left, foot_right = st.columns([2,1])
with foot_left:
    st.caption("UNION BUDGET INTELLIGENCE STUDIO · Built with Python + Streamlit + Plotly")
with foot_right:
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button("↓ Export current filtered data", csv_data, "filtered_union_budget_data.csv", "text/csv", use_container_width=True)
