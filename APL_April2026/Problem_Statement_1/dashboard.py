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
from venue_simulator import VenueSimulator, ZONES, GATES

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartVenue AI",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0A0F1E; color: #ffffff; }
    .stApp { background-color: #0A0F1E; }
    .metric-card {
        background: #142038;
        border: 1px solid #1E3560;
        border-left: 4px solid #CC1A1A;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 6px 0;
    }
    .critical { border-left-color: #FF0000 !important; background: #2A0A0A; }
    .high     { border-left-color: #FF6600 !important; background: #2A1A0A; }
    .normal   { border-left-color: #00CC44 !important; }
    .action-log {
        background: #0E1424;
        border: 1px solid #1E3560;
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        font-size: 12px;
        max-height: 300px;
        overflow-y: auto;
    }
    .agent-thinking {
        background: #0D2040;
        border: 1px solid #CC1A1A;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }
    h1, h2, h3 { color: #FFFFFF !important; }
    .stSlider > div > div > div { background: #CC1A1A !important; }
    div[data-testid="metric-container"] {
        background: #142038;
        border: 1px solid #1E3560;
        border-radius: 8px;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
if "sim" not in st.session_state:
    st.session_state.sim = VenueSimulator()
if "agent_result" not in st.session_state:
    st.session_state.agent_result = None
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("GEMINI_API_KEY", "")
if "auto_run" not in st.session_state:
    st.session_state.auto_run = False


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/320px-Google_2015_logo.svg.png", width=120)
    st.markdown("### 🏏 SmartVenue AI")
    st.markdown("*Google Cloud · Build with AI*")
    st.markdown("---")

    api_key = st.text_input(
        "🔑 Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Get free key at aistudio.google.com/apikey",
    )
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


# ── Main dashboard ────────────────────────────────────────────────────────────
st.markdown("# 🏟 SmartVenue AI — Live Operations Dashboard")
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
    st.markdown("### 📍 Zone Density Map")
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
    "SmartVenue AI · Google Cloud Build with AI · Agentic Premier League · 2026"
    "</center>",
    unsafe_allow_html=True,
)
