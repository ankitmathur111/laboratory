import streamlit as st
import google.generativeai as genai
import json
import re
import time
import tempfile
import os
from PIL import Image
import io
import base64
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.analyzer import CricketAnalyzer
from utils.stats import StatsManager
from utils.session import init_session_state

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CricketLens AI",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Load CSS ──────────────────────────────────────────────────────────────────
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────
init_session_state()

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏏 CricketLens AI")
    st.markdown("*AI-powered cricket shot analyzer*")
    st.divider()

    st.markdown("### 🔑 Gemini API Key")
    api_key = st.text_input(
        "Enter your Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Get your key at https://aistudio.google.com",
        key="gemini_api_key_input",
    )

    if api_key:
        st.success("✅ API Key set")
    else:
        st.warning("⚠️ API key required to analyze")

    st.divider()

    st.markdown("### 📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Analyses", st.session_state.total_analyses)
    with col2:
        st.metric("Shots Tracked", st.session_state.total_shots)

    if st.session_state.analyses:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.analyses = []
            st.session_state.total_analyses = 0
            st.session_state.total_shots = 0
            st.rerun()

    st.divider()
    st.markdown("**Build With AI :: APL 2026**")
    st.markdown("Problem Statement 1")

# ─── Main Content ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero-header">
        <h1>🏏 CricketLens AI</h1>
        <p>Upload a cricket image or video frame — get instant shot analysis, ball delivery details & match statistics</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📸 Analyze", "📊 Statistics", "📋 History"])

# ════════════════════════════════════════════════════════════════════
# TAB 1 – ANALYZE
# ════════════════════════════════════════════════════════════════════
with tab1:
    col_upload, col_result = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown("### 📂 Upload Media")
        upload_mode = st.radio(
            "Input type",
            ["Image", "Video Frame"],
            horizontal=True,
            help="Upload a still image or extract a frame from a short video clip.",
        )

        uploaded_file = None
        if upload_mode == "Image":
            uploaded_file = st.file_uploader(
                "Drop an image here",
                type=["jpg", "jpeg", "png", "webp"],
                help="JPG, PNG or WEBP, max 200 MB",
            )
        else:
            uploaded_file = st.file_uploader(
                "Drop a short video clip (≤ 30s recommended)",
                type=["mp4", "mov", "avi", "mkv"],
                help="We will extract the first meaningful frame for analysis.",
            )

        # Extra context
        st.markdown("### ✏️ Add Context (optional)")
        over_number = st.number_input("Over number", min_value=0, max_value=50, value=0, step=1)
        ball_number = st.number_input("Ball number in over", min_value=1, max_value=6, value=1, step=1)
        batting_team = st.text_input("Batting team", placeholder="e.g. Mumbai Indians")
        bowling_team = st.text_input("Bowling team", placeholder="e.g. Chennai Super Kings")
        batsman_name = st.text_input("Batsman", placeholder="e.g. Virat Kohli")
        bowler_name = st.text_input("Bowler", placeholder="e.g. Jasprit Bumrah")
        additional_notes = st.text_area(
            "Any additional notes",
            placeholder="e.g. This was a crucial over in the death overs...",
            height=80,
        )

        analyze_btn = st.button(
            "🔍 Analyze with Gemini", type="primary", use_container_width=True
        )

    with col_result:
        st.markdown("### 🧠 Analysis Result")

        if analyze_btn:
            if not api_key:
                st.error("🔑 Please enter your Gemini API key in the sidebar first.")
            elif not uploaded_file:
                st.error("📂 Please upload an image or video before analyzing.")
            else:
                with st.spinner("Analyzing with Gemini Vision..."):
                    try:
                        analyzer = CricketAnalyzer(api_key)
                        context = {
                            "over": over_number,
                            "ball": ball_number,
                            "batting_team": batting_team,
                            "bowling_team": bowling_team,
                            "batsman": batsman_name,
                            "bowler": bowler_name,
                            "notes": additional_notes,
                        }

                        result = analyzer.analyze(uploaded_file, upload_mode, context)

                        if result["success"]:
                            data = result["data"]

                            # ── Store in session ──
                            entry = {
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "over": over_number,
                                "ball": ball_number,
                                "batsman": batsman_name or "Unknown",
                                "bowler": bowler_name or "Unknown",
                                **data,
                            }
                            st.session_state.analyses.append(entry)
                            st.session_state.total_analyses += 1
                            st.session_state.total_shots += 1

                            # ── Display cards ──
                            st.markdown('<div class="result-grid">', unsafe_allow_html=True)

                            metrics = [
                                ("🏏 Shot Type", data.get("shot_type", "N/A")),
                                ("🎯 Ball Type", data.get("ball_type", "N/A")),
                                ("📍 Pitch Length", data.get("pitch_length", "N/A")),
                                ("💨 Estimated Speed", data.get("ball_speed", "N/A")),
                                ("🏃 Runs Scored", data.get("runs_scored", "N/A")),
                                ("🧭 Shot Direction", data.get("shot_direction", "N/A")),
                                ("⚠️ Outcome", data.get("outcome", "N/A")),
                                ("📐 Batting Position", data.get("batting_stance", "N/A")),
                            ]

                            cols = st.columns(2)
                            for i, (label, value) in enumerate(metrics):
                                with cols[i % 2]:
                                    st.markdown(
                                        f"""<div class="metric-card">
                                            <div class="metric-label">{label}</div>
                                            <div class="metric-value">{value}</div>
                                        </div>""",
                                        unsafe_allow_html=True,
                                    )

                            st.markdown("</div>", unsafe_allow_html=True)

                            st.divider()
                            st.markdown("#### 📝 Detailed Commentary")
                            st.markdown(
                                f'<div class="commentary-box">{data.get("commentary", "")}</div>',
                                unsafe_allow_html=True,
                            )

                            if data.get("player_insights"):
                                st.markdown("#### 💡 Player Insights")
                                st.info(data["player_insights"])

                            if data.get("tactical_observation"):
                                st.markdown("#### 🧩 Tactical Observation")
                                st.success(data["tactical_observation"])

                        else:
                            st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        else:
            st.markdown(
                """
                <div class="placeholder-box">
                    <div style="font-size:4rem;">🏏</div>
                    <div style="font-size:1.2rem; font-weight:600; margin-top:1rem;">Ready to Analyze</div>
                    <div style="opacity:0.7; margin-top:0.5rem;">Upload a cricket image or video and click <strong>Analyze with Gemini</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ════════════════════════════════════════════════════════════════════
# TAB 2 – STATISTICS
# ════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📊 Match Statistics Dashboard")

    if not st.session_state.analyses:
        st.info("📂 No analyses yet. Go to the **Analyze** tab and upload some cricket media!")
    else:
        stats_mgr = StatsManager(st.session_state.analyses)
        df = stats_mgr.to_dataframe()

        # KPI Row
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Deliveries", len(df))
        k2.metric("Total Runs", df["runs_scored_num"].sum() if "runs_scored_num" in df.columns else "N/A")
        k3.metric("Most Common Shot", df["shot_type"].mode()[0] if "shot_type" in df.columns else "N/A")
        k4.metric("Most Common Delivery", df["ball_type"].mode()[0] if "ball_type" in df.columns else "N/A")

        col_a, col_b = st.columns(2)

        with col_a:
            if "shot_type" in df.columns:
                shot_counts = df["shot_type"].value_counts().reset_index()
                shot_counts.columns = ["Shot Type", "Count"]
                fig = px.pie(
                    shot_counts, values="Count", names="Shot Type",
                    title="Shot Distribution", color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

        with col_b:
            if "ball_type" in df.columns:
                ball_counts = df["ball_type"].value_counts().reset_index()
                ball_counts.columns = ["Ball Type", "Count"]
                fig2 = px.bar(
                    ball_counts, x="Ball Type", y="Count",
                    title="Ball Delivery Breakdown",
                    color="Count", color_continuous_scale="Blues",
                )
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)

        if "shot_direction" in df.columns and "runs_scored_num" in df.columns:
            dir_runs = df.groupby("shot_direction")["runs_scored_num"].sum().reset_index()
            dir_runs.columns = ["Direction", "Runs"]
            fig3 = px.bar_polar(
                dir_runs, r="Runs", theta="Direction",
                title="Wagon Wheel – Runs by Shot Direction",
                color="Runs", color_continuous_scale="Reds",
            )
            fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("#### 📋 Raw Data")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode()
        st.download_button("⬇️ Download CSV", csv, "cricket_stats.csv", "text/csv")

# ════════════════════════════════════════════════════════════════════
# TAB 3 – HISTORY
# ════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📋 Analysis History")

    if not st.session_state.analyses:
        st.info("No analyses yet.")
    else:
        for idx, entry in enumerate(reversed(st.session_state.analyses)):
            with st.expander(
                f"🏏 [{entry['timestamp']}] Over {entry['over']}.{entry['ball']} – "
                f"{entry.get('shot_type', 'Unknown Shot')} | {entry.get('runs_scored', '?')} runs",
                expanded=(idx == 0),
            ):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Batsman:** {entry.get('batsman', 'N/A')}")
                c1.markdown(f"**Bowler:** {entry.get('bowler', 'N/A')}")
                c2.markdown(f"**Ball Type:** {entry.get('ball_type', 'N/A')}")
                c2.markdown(f"**Pitch Length:** {entry.get('pitch_length', 'N/A')}")
                c3.markdown(f"**Direction:** {entry.get('shot_direction', 'N/A')}")
                c3.markdown(f"**Outcome:** {entry.get('outcome', 'N/A')}")
                st.markdown(f"**Commentary:** {entry.get('commentary', 'N/A')}")
