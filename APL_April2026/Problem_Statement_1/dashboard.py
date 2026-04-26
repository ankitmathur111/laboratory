# PROJECT : SmartVenue AI — Crowd Management Agent
# FILE    : dashboard.py
# DEPLOY  : gcloud run deploy smartvenue-ai
"""
dashboard.py
------------
Streamlit dashboard — the demo UI for judges.

Run: streamlit run dashboard.py
"""

import os
import json
import time
import streamlit as st
from key_manager import load_api_key, mask_key
from venue_simulator import VenueSimulator, ZONES, GATES

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartVenue AI APL Ankit Mathur",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""

<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Outfit:wght@300;400;700&display=swap');

    :root {
        --bg-dark: #050810;
        --card-bg: rgba(20, 32, 56, 0.7);
        --accent-red: #FF3333;
        --accent-green: #00FF88;
        --accent-orange: #FF9900;
        --accent-blue: #4A9EFF;
        --border-color: rgba(74, 158, 255, 0.2);
    }

    .main { background-color: var(--bg-dark); color: #ffffff; font-family: 'Outfit', sans-serif; }
    .stApp { background-color: var(--bg-dark); }
    
    /* Glassmorphism Card */
    .metric-card {
        background: var(--card-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: var(--accent-blue);
        transform: translateY(-2px);
    }

    .critical { 
        border-left: 4px solid var(--accent-red); 
        background: rgba(255, 51, 51, 0.1);
        animation: pulse-red 2s infinite;
    }
    .high { 
        border-left: 4px solid var(--accent-orange); 
        background: rgba(255, 153, 0, 0.1);
    }
    .normal { 
        border-left: 4px solid var(--accent-green);
        background: rgba(0, 255, 136, 0.05);
    }

    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 51, 51, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(255, 51, 51, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 51, 51, 0); }
    }

    .action-log {
        background: rgba(10, 15, 30, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        max-height: 300px;
        overflow-y: auto;
    }

    .agent-thinking {
        background: rgba(13, 32, 64, 0.8);
        border: 1px solid var(--accent-red);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 0 20px rgba(255, 51, 51, 0.2);
    }

    h1, h2, h3 { 
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #FFFFFF !important; 
    }

    .stSlider > div > div > div { background: var(--accent-red) !important; }
    
    div[data-testid="metric-container"] {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 12px;
        box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.5);
    }

    /* Custom Ticker */
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background-color: rgba(255, 51, 51, 0.1);
        padding: 10px 0;
        border-bottom: 1px solid var(--accent-red);
        margin-bottom: 20px;
    }
    .ticker {
        display: inline-block;
        white-space: nowrap;
        padding-right: 100%;
        animation: ticker 30s linear infinite;
        color: var(--accent-red);
        font-weight: bold;
        font-family: 'JetBrains Mono', monospace;
    }
    @keyframes ticker {
        0% { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }
</style>

""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
if "sim" not in st.session_state:
    st.session_state.sim = VenueSimulator()
if "agent_result" not in st.session_state:
    st.session_state.agent_result = None
if "api_key" not in st.session_state:
    st.session_state.api_key = load_api_key()
if "auto_run" not in st.session_state:
    st.session_state.auto_run = False


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/320px-Google_2015_logo.svg.png", width=120)
    st.markdown("### 🏏 SmartVenue AI")
    st.markdown("*Google Cloud · Build with AI*")
    st.markdown("---")

    # ── API Key override (when free-tier key exhausts) ────────────────────
    with st.expander("🔑 Use your own API key"):
        st.markdown(
            "<small style='color:#6688AA;'>If the pre-loaded key stops working, "
            "paste your own Gemini key here to continue without interruption.</small>",
            unsafe_allow_html=True,
        )
        override_key = st.text_input(
            "Gemini API Key",
            value="",
            type="password",
            placeholder="Paste your key from aistudio.google.com/apikey",
            key="sidebar_api_key_input",
        )
        if st.button("✅ Apply Key", use_container_width=True, key="apply_override_key"):
            if override_key.strip():
                st.session_state.api_key = override_key.strip()
                st.success("✅ Key applied! You're good to go.")
                st.rerun()
            else:
                st.warning("Please paste a valid API key first.")

    st.markdown("---")

    # Auto-loaded on Cloud Run, manual fallback locally
    auto_key = st.session_state.api_key
    if auto_key:
        st.markdown(
            f"<div style='background:#0D2A1A;border:1px solid #1A5A2A;border-radius:6px;"
            f"padding:8px 12px;font-size:12px;color:#44CC88;'>"
            f"🔒 API Key pre-loaded automatically<br></div>",
            unsafe_allow_html=True
        )
        api_key = auto_key
    else:
        api_key = st.text_input(
            "🔑 Gemini API Key",
            value="",
            type="password",
            help="Get free key at aistudio.google.com/apikey",
        )
        if api_key:
            st.session_state.api_key = api_key

    st.markdown("---")
    match_minute = st.slider(
        "⏱ Match Minute",
        min_value=0, max_value=400, value=185, step=5,
        help="Drag to simulate different points in the match",
    )

    sim = st.session_state.sim
    sim.match_minute = match_minute
    snapshot = sim.get_snapshot(match_minute)

    st.markdown(f"""
    <div class='metric-card'>
        <b>📍 Phase:</b> {snapshot.phase_name}<br>
        <b>🔔 Alerts:</b> {len(snapshot.alert_events)}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🤖 Run AI Agent")

    custom_query = st.text_area(
        "Custom Query (optional)",
        placeholder="e.g. Check Food Court A and send fans to shortest queue",
        height=80,
    )

    run_agent = st.button(
        "▶ Run Agent Cycle",
        disabled=not api_key,
        use_container_width=True,
        type="primary",
    )

    if not api_key:
        st.warning("Add API key to run the agent")

    st.markdown("---")
    st.markdown("**Quick Scenarios:**")
    if st.button("🍔 Halftime Rush (min 185)"):
        match_minute = 185
    if st.button("🚨 Crowd Surge (min 90)"):
        match_minute = 90
    if st.button("🚗 Post-Match Exit (min 385)"):
        match_minute = 385


# ── Ticker ────────────────────────────────────────────────────────────────────
if snapshot.alert_events:
    alerts_text = " • ".join([f"🚨 {a['priority']}: {a['location']} - {a['detail']}" for a in snapshot.alert_events])
    st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker">
            {alerts_text} • {alerts_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Main dashboard ────────────────────────────────────────────────────────────
st.markdown("# 🏟 SmartVenue AI — Live Operations Dashboard")
st.markdown(f"(by Ankit Mathur for APL 2026)")
st.markdown(f"**Match Minute {match_minute}** · Phase: *{snapshot.phase_name}*")

# ── Top KPI row ───────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

all_densities = [snapshot.zones[z].density for z in ZONES]
all_queues = [snapshot.gates[g].queue_minutes for g in GATES]
critical_zones = sum(1 for d in all_densities if d >= 90)
high_zones = sum(1 for d in all_densities if 75 <= d < 90)
closed_gates = sum(1 for g in GATES if not snapshot.gates[g].is_open)

col1.metric("⚡ Alerts", len(snapshot.alert_events),
            delta="Live" if snapshot.alert_events else "Clear",
            delta_color="inverse" if snapshot.alert_events else "normal")
col2.metric("🔴 Critical Zones", critical_zones)
col3.metric("🟡 High Density", high_zones)
col4.metric("🚪 Gates Closed", closed_gates, delta_color="inverse")
col5.metric("⏳ Max Queue", f"{max(all_queues):.0f} min",
            delta="⚠ Long" if max(all_queues) > 15 else "OK",
            delta_color="inverse" if max(all_queues) > 15 else "normal")

st.markdown("---")

# ── Two column layout ─────────────────────────────────────────────────────────
left, right = st.columns([1, 1])

with left:
    st.markdown("### 🗺️ Live Stadium Heatmap")
    
    def get_color(density):
        if density >= 90: return "#FF3333"
        if density >= 75: return "#FF9900"
        return "#00FF88"

    sectors = {
        "North_Stand":   "M200,200 L200,50 A150,150 0 0,1 306,94 Z",
        "Premium_Lounge": "M200,200 L306,94 A150,150 0 0,1 350,200 Z",
        "East_Stand":    "M200,200 L350,200 A150,150 0 0,1 306,306 Z",
        "South_Stand":   "M200,200 L306,306 A150,150 0 0,1 200,350 Z",
        "General_Stand": "M200,200 L200,350 A150,150 0 0,1 94,306 Z",
        "West_Stand":    "M200,200 L94,306 A150,150 0 0,1 50,200 Z",
        "Food_Court_A":  "M200,200 L50,200 A150,150 0 0,1 94,94 Z",
        "Food_Court_B":  "M200,200 L94,94 A150,150 0 0,1 200,50 Z"
    }
    
    svg = """<svg viewBox="0 0 400 400" width="100%" style="max-height:400px; filter: drop-shadow(0 0 10px rgba(0,0,0,0.5));">
        <circle cx="200" cy="200" r="160" fill="none" stroke="#1E3560" stroke-width="1" />
        <circle cx="200" cy="200" r="80" fill="#0D2010" stroke="#00FF88" stroke-width="2" opacity="0.3"/>
        <text x="200" y="205" text-anchor="middle" fill="#00FF88" font-size="12" font-family="Outfit">PITCH</text>
    """
    for zone_id, path in sectors.items():
        density = snapshot.zones.get(zone_id).density if zone_id in snapshot.zones else 0
        color = get_color(density)
        svg += f'<path d="{path}" fill="{color}" stroke="#050810" stroke-width="2" opacity="0.7"><title>{zone_id}: {density}%</title></path>'
    svg += "</svg>"
    
    st.markdown(svg, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 📍 Zone Density Details")
    for zone_id in ZONES:
        z = snapshot.zones[zone_id]
        status = sim._density_status(z.density)
        css_class = "critical" if status == "CRITICAL" else \
                    "high" if status == "HIGH" else "normal"
        bar_width = z.density
        bar_color = "#FF0000" if status == "CRITICAL" else \
                    "#FF6600" if status == "HIGH" else "#00CC44"

        incident_html = ""
        if z.incident:
            incident_html = f"<br>⚠️ <b>{z.incident}</b>"

        st.markdown(f"""
        <div class='metric-card {css_class}'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span><b>{zone_id.replace('_', ' ')}</b></span>
                <span style='color:{bar_color}; font-weight:bold;'>{status} ({z.density}%)</span>
            </div>
            <div style='background:#1a2a3a; border-radius:4px; height:8px; margin:6px 0;'>
                <div style='background:{bar_color}; width:{bar_width}%; height:8px; border-radius:4px;'></div>
            </div>
            <small style='color:#8899BB;'>{z.crowd_count:,} people · {z.temp_celsius:.1f}°C</small>
            {incident_html}
        </div>
        """, unsafe_allow_html=True)


with right:
    st.markdown("### 🚪 Gate Status")
    for gate_id in GATES:
        g = snapshot.gates[gate_id]
        if not g.is_open:
            status_color = "#FF0000"
            status_text = "CLOSED ⛔"
        elif g.queue_minutes > 20:
            status_color = "#FF0000"
            status_text = f"CRITICAL ({g.queue_minutes:.0f} min)"
        elif g.queue_minutes > 10:
            status_color = "#FF6600"
            status_text = f"HIGH ({g.queue_minutes:.0f} min)"
        else:
            status_color = "#00CC44"
            status_text = f"NORMAL ({g.queue_minutes:.0f} min)"

        st.markdown(f"""
        <div class='metric-card' style='padding:8px 14px;'>
            <span><b>Gate {gate_id}</b></span>
            &nbsp;&nbsp;
            <span style='color:{status_color};'>{status_text}</span>
            &nbsp;
            <span style='color:#556688; font-size:11px;'>· {g.throughput_per_min}/min</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🍔 Concession Queues")
    concessions = sim.get_concession_queues()
    for c in concessions:
        color = "#FF6600" if c["wait_minutes"] > 10 else "#00CC44"
        bar = min(int(c["wait_minutes"] / 20 * 100), 100)
        st.markdown(f"""
        <div class='metric-card' style='padding:7px 14px;'>
            <div style='display:flex; justify-content:space-between;'>
                <span>{c["stall"].replace("_", " ")}</span>
                <span style='color:{color};'><b>{c["wait_minutes"]:.1f} min</b></span>
            </div>
            <div style='background:#1a2a3a; border-radius:3px; height:5px; margin-top:4px;'>
                <div style='background:{color}; width:{bar}%; height:5px; border-radius:3px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Active Alerts ─────────────────────────────────────────────────────────────
if snapshot.alert_events:
    st.markdown("---")
    st.markdown("### 🚨 Active Alerts")
    for alert in snapshot.alert_events:
        priority_color = {
            "URGENT": "#FF0000", "HIGH": "#FF6600",
            "MEDIUM": "#FFAA00", "LOW": "#8899BB"
        }.get(alert["priority"], "#8899BB")
        st.markdown(f"""
        <div class='metric-card critical' style='display:flex; gap:16px; align-items:center;'>
            <span style='color:{priority_color}; font-weight:bold; min-width:70px;'>{alert["priority"]}</span>
            <span style='color:#8899BB;'>[{alert["type"]}]</span>
            <span><b>{alert["location"]}</b></span>
            <span style='color:#AABBCC;'>{alert["detail"]}</span>
        </div>
        """, unsafe_allow_html=True)


# ── Agent output ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🤖 AI Agent")

if run_agent:
    if not api_key:
        st.error("Please enter your Gemini API key in the sidebar.")
    else:
        with st.spinner("🧠 Agent is analyzing venue and taking actions..."):
            try:
                from smartvenue_agent import run_agent_cycle
                result = run_agent_cycle(
                    match_minute=match_minute,
                    api_key=api_key,
                    custom_query=custom_query if custom_query.strip() else None,
                    verbose=False,
                )
                st.session_state.agent_result = result
            except Exception as e:
                st.error(f"Agent error: {e}")
                st.exception(e)

if st.session_state.agent_result:
    res = st.session_state.agent_result

    a1, a2 = st.columns([2, 1])

    with a1:
        st.markdown("**📋 Agent Summary:**")
        st.markdown(f"""
        <div class='agent-thinking'>
            {res["summary"].replace(chr(10), "<br>")}
        </div>
        """, unsafe_allow_html=True)

    with a2:
        st.markdown(f"**⚡ Actions Taken ({len(res['actions_taken'])}):**")
        for action in res["actions_taken"]:
            action_icon = {
                "PUSH_NOTIFICATION": "📲",
                "SIGNAGE_UPDATE":    "📺",
                "STAFF_ALERT":       "📻",
                "OPEN_GATE":         "🚪",
            }.get(action["type"], "⚙")
            detail_str = json.dumps(action["details"])[:80]
            st.markdown(f"""
            <div class='metric-card' style='padding:6px 12px; margin:3px 0;'>
                <span>{action_icon}</span>
                <b style='color:#CC1A1A;'>{action["type"]}</b><br>
                <small style='color:#8899BB;'>{action["time"]} · {detail_str}...</small>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("👆 Click **Run Agent Cycle** in the sidebar to let the AI analyze the venue and take actions.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center style='color:#556688; font-size:12px;'>"
    "SmartVenue AI · Google Cloud Build with AI · Ankit Mathur · Agentic Premier League · 2026"
    "</center>",
    unsafe_allow_html=True,
)
