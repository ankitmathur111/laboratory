# PROJECT : LearnMate AI — Adaptive Learning Agent
# FILE    : dashboard.py
# DEPLOY  : gcloud run deploy learnmate-ai
"""
dashboard.py
------------
LearnMate AI — Adaptive Learning Assistant
Run: python -m streamlit run dashboard.py
"""

import os
import streamlit as st
from learner_profile import (
    AGE_GROUPS, DOMAINS, LEARNING_STYLES,
    DIFFICULTY_LEVELS, LearnerProfile, get_store
)
from agent_tools import get_session_log, get_active_profile
from key_manager import load_api_key, mask_key, is_running_on_cloud

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LearnMate AI (by Ankit Mathur for APL 2026)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Outfit:wght@300;400;600;700&display=swap');

    :root {
        --bg-dark: #0A0C10;
        --sidebar-bg: #0F1219;
        --card-bg: rgba(23, 28, 40, 0.7);
        --accent-primary: #7C4DFF;
        --accent-secondary: #00E5FF;
        --text-main: #E1E4E8;
        --glass-border: rgba(255, 255, 255, 0.08);
    }

    .stApp { background-color: var(--bg-dark); font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { 
        background-color: var(--sidebar-bg); 
        border-right: 1px solid var(--glass-border);
    }

    /* Message Bubbles */
    .chat-user {
        background: linear-gradient(135deg, var(--accent-primary), #5E35B1);
        border-radius: 20px 20px 4px 20px;
        padding: 14px 20px;
        margin: 10px 0 10px 15%;
        color: #FFFFFF;
        font-size: 15px;
        box-shadow: 0 4px 15px rgba(124, 77, 255, 0.2);
    }
    .chat-agent {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: 4px 20px 20px 20px;
        padding: 16px 22px;
        margin: 10px 15% 10px 0;
        color: var(--text-main);
        font-size: 15px;
        line-height: 1.6;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    /* Profile Card */
    .profile-card {
        background: linear-gradient(145deg, rgba(30, 40, 60, 0.6), rgba(15, 20, 30, 0.8));
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-left: 4px solid var(--accent-secondary);
        border-radius: 16px;
        padding: 16px;
        margin: 10px 0;
        transition: transform 0.2s ease;
    }
    .profile-card:hover { transform: scale(1.02); }

    .metric-mini {
        background: rgba(0, 0, 0, 0.2);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 10px;
        text-align: center;
    }
    .stat-number { 
        font-family: 'Outfit', sans-serif;
        font-size: 26px; 
        font-weight: 700; 
        background: linear-gradient(to right, var(--accent-secondary), #80CBC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label { font-size: 11px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; }

    .log-entry {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        color: #8B949E;
        padding: 6px 0;
        border-bottom: 1px solid var(--glass-border);
    }

    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        margin: 3px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-blue   { background: rgba(0, 229, 255, 0.1); color: var(--accent-secondary); border: 1px solid rgba(0, 229, 255, 0.2); }
    .badge-green  { background: rgba(0, 255, 136, 0.1); color: #00FF88; border: 1px solid rgba(0, 255, 136, 0.2); }
    .badge-red    { background: rgba(255, 51, 102, 0.1); color: #FF3366; border: 1px solid rgba(255, 51, 102, 0.2); }
    .badge-orange { background: rgba(255, 153, 0, 0.1); color: #FF9900; border: 1px solid rgba(255, 153, 0, 0.2); }

    h1, h2, h3 { font-family: 'Outfit', sans-serif; font-weight: 700; color: #FFFFFF !important; }
    
    /* Animation */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    .floating { animation: float 4s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "screen": "onboarding",     # onboarding | chat
        "profile": None,
        "agent": None,
        "messages": [],             # [{role, content}]
        "api_key": load_api_key(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ═══════════════════════════════════════════════════════════════════
# SCREEN 1: ONBOARDING
# ═══════════════════════════════════════════════════════════════════

def show_onboarding():
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px 0;'>
        <div style='font-size:56px;'>🎓</div>
        <h1 style='font-size:36px; margin:8px 0;'>LearnMate AI</h1>
        <p style='color:#6688AA; font-size:16px;'>
            <small style='color:#6688AA; font-size:12px;'>by Ankit Mathur for APL 2026</small><br>
            Your personal adaptive tutor — for any subject, any age, any pace.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Returning user check
    store = get_store()
    existing = store.all_names()
    if existing:
        st.markdown("#### 👋 Welcome back!")
        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            returning_name = st.selectbox("Continue as:", ["— New learner —"] + existing)
        with col_r2:
            st.markdown("<br>", unsafe_allow_html=True)
            if returning_name != "— New learner —" and st.button("Continue →", type="primary"):
                profile = store.load(returning_name)
                st.session_state.profile = profile
                _start_chat_session(profile)
                st.rerun()
        st.markdown("---")

    # New learner form
    st.markdown("#### 🌟 Create your learning profile")
    st.markdown("<small style='color:#6688AA;'>Takes 30 seconds. Makes everything personalised.</small>",
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Your name", placeholder="e.g. Priya, James, Aiko...")
        age_group = st.selectbox("Age group", list(AGE_GROUPS.keys()))
        domain = st.selectbox("What do you most want to learn?", DOMAINS)

    with c2:
        learning_style = st.selectbox(
            "How do you learn best?",
            list(LEARNING_STYLES.keys()),
            help="".join([f"{k}: {v[:80]}..." for k, v in LEARNING_STYLES.items()])
        )
        difficulty = st.selectbox("Starting level", DIFFICULTY_LEVELS)
        # ── API Key: auto-loaded on Cloud, manual fallback locally ──────
        auto_key = st.session_state.api_key
        if auto_key:
            st.markdown(
                f"<div style='background:#0D2A1A; border:1px solid #1A5A2A; border-radius:6px; "
                f"padding:8px 12px; font-size:12px; color:#44CC88;'"
                f">🔒 API Key pre-loaded automatically<br></div>",
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

    st.markdown("<br>", unsafe_allow_html=True)

    # Style preview
    if learning_style:
        st.markdown(f"""
        <div class='profile-card'>
            <small style='color:#4A9EFF;'>✨ Your personalised style</small><br>
            <span style='color:#AABBCC; font-size:13px;'>{LEARNING_STYLES[learning_style]}</span>
        </div>
        """, unsafe_allow_html=True)

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        start = st.button("🚀 Start Learning!", type="primary", use_container_width=True,
                          disabled=not (name.strip() and api_key.strip()))

    if start:
        if not name.strip():
            st.error("Please enter your name!")
            return
        if not api_key.strip():
            st.error("Please enter your Gemini API key!")
            return

        profile = LearnerProfile(
            name=name.strip(),
            age_group=age_group,
            domain=domain,
            learning_style=learning_style,
            current_difficulty=difficulty,
        )
        store = get_store()
        store.save(profile)
        st.session_state.api_key = api_key.strip()
        st.session_state.profile = profile
        _start_chat_session(profile)
        st.rerun()


def _start_chat_session(profile: LearnerProfile):
    from learnmate_agent import LearnMateAgent
    agent = LearnMateAgent(
        api_key=st.session_state.api_key,
        profile=profile,
    )
    st.session_state.agent = agent
    st.session_state.messages = []
    st.session_state.screen = "chat"


# ═══════════════════════════════════════════════════════════════════
# SCREEN 2: CHAT
# ═══════════════════════════════════════════════════════════════════

def show_chat():
    profile: LearnerProfile = st.session_state.profile

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🎓 LearnMate AI (by Ankit Mathur for APL 2026)")
        st.markdown("---")

        # Profile card
        comp = profile.comprehension_score
        comp_color = "#FF6688" if comp < 45 else "#FFAA44" if comp < 65 else "#44CC88"
        diff_colors = {"Beginner": "blue", "Intermediate": "orange",
                       "Advanced": "red", "Expert": "green"}
        diff_color = diff_colors.get(profile.current_difficulty, "blue")

        st.markdown(f"""
        <div class='profile-card'>
            <b style='font-size:16px;'>{profile.name}</b><br>
            <small style='color:#6688AA;'>{profile.age_group} · {profile.domain}</small><br><br>
            <span class='badge badge-blue'>{profile.learning_style}</span>
            <span class='badge badge-{diff_color}'>{profile.current_difficulty}</span>
        </div>
        """, unsafe_allow_html=True)


        # Knowledge Constellation
        st.markdown("<div style='text-align:center;' class='floating'>", unsafe_allow_html=True)
        
        def draw_constellation(learned_count):
            import random
            random.seed(42)
            count = min(max(learned_count, 8), 25)
            stars = [{"x": random.randint(50, 350), "y": random.randint(50, 350), "r": random.randint(2, 5)} for _ in range(count)]
            svg = f'<svg viewBox="0 0 400 400" width="100%" style="max-height:200px;">'
            for i in range(len(stars)-1):
                svg += f'<line x1="{stars[i]["x"]}" y1="{stars[i]["y"]}" x2="{stars[i+1]["x"]}" y2="{stars[i+1]["y"]}" stroke="#7C4DFF" stroke-width="0.5" opacity="0.4" />'
            for s in stars:
                svg += f'<circle cx="{s["x"]}" cy="{s["y"]}" r="{s["r"]}" fill="#00E5FF" opacity="0.8"><animate attributeName="r" values="{s["r"]};{s["r"]+2};{s["r"]}" dur="{random.randint(2,4)}s" repeatCount="indefinite" /></circle>'
            svg += '</svg>'
            return svg
            
        st.markdown(draw_constellation(profile.total_concepts_learned), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # KPIs
        k1, k2 = st.columns(2)
        k1.markdown(f"""<div class='metric-mini'>
            <div class='stat-number' style='color:{comp_color};'>{comp:.0f}</div>
            <div class='stat-label'>Comprehension</div></div>""", unsafe_allow_html=True)
        k2.markdown(f"""<div class='metric-mini'>
            <div class='stat-number'>{profile.total_concepts_learned}</div>
            <div class='stat-label'>Concepts Learned</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Progress bar
        st.markdown(f"**Understanding:** {comp:.0f}/100")
        st.progress(comp / 100)

        if profile.current_topic:
            st.markdown(f"**📚 Topic:** {profile.current_topic}")

        # Mastered / weak
        if profile.strong_areas:
            st.markdown("**✅ Mastered:**")
            for s in profile.strong_areas[-3:]:
                st.markdown(f"<span class='badge badge-green'>{s}</span>", unsafe_allow_html=True)

        if profile.weak_areas:
            st.markdown("**🔁 Needs review:**")
            for w in profile.weak_areas[-3:]:
                st.markdown(f"<span class='badge badge-red'>{w}</span>", unsafe_allow_html=True)

        st.markdown("---")

        # Quick actions
        st.markdown("**Quick prompts:**")
        quick_prompts = [
            "Explain it differently",
            "Give me a quiz",
            "What should I learn next?",
            "Summarise what I've learned",
            "Give me a real-world example",
        ]
        for qp in quick_prompts:
            if st.button(qp, use_container_width=True):
                _handle_message(qp)
                st.rerun()

        st.markdown("---")

        # Agent log (collapsible)
        with st.expander("🔧 Agent Activity Log"):
            logs = get_session_log()
            if logs:
                for log in logs[-10:]:
                    action = log.get("action", "")
                    icon = {
                        "TOPIC_SET": "📌",
                        "COMPREHENSION_CHECK": "📊",
                        "QUIZ_STARTED": "📝",
                        "QUIZ_ANSWER": "✅" if log.get("correct") else "❌",
                        "ADAPT_TRIGGERED": "🔄",
                        "SESSION_END": "🏁",
                    }.get(action, "⚙")
                    score_str = f" [{log.get('score', log.get('running_avg', ''))}]" if "score" in log or "running_avg" in log else ""
                    st.markdown(f"<div class='log-entry'>{icon} {action}{score_str}</div>",
                                unsafe_allow_html=True)
            else:
                st.markdown("<small style='color:#445566;'>No activity yet</small>",
                            unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🔄 New Session / Switch User"):
            st.session_state.screen = "onboarding"
            st.session_state.agent = None
            st.session_state.messages = []
            st.rerun()

    # ── Main chat area ────────────────────────────────────────────────────────
    st.markdown(f"## 🎓 Learning with LearnMate AI (by Ankit Mathur for APL 2026)")
    st.markdown(f"*{profile.age_group} · {profile.domain} · {profile.current_difficulty}*")
    st.markdown("---")

    # Welcome message if no messages
    if not st.session_state.messages:
        greeting = {
            "Child (6–12)": f"Hi {profile.name}! 👋 I'm LearnMate — your super cool learning buddy! What do you want to explore today? 🚀",
            "Teenager (13–17)": f"Hey {profile.name}! Ready to learn something awesome? What topic are we diving into? 🔥",
            "Young Adult (18–25)": f"Hi {profile.name}! Let's get you ahead. What do you want to master today?",
            "Adult (26–45)": f"Welcome back, {profile.name}. What would you like to focus on today?",
            "Senior (46+)": f"Hello {profile.name}! Wonderful to see you. What shall we explore together today?",
        }.get(profile.age_group, f"Hello {profile.name}! What would you like to learn today?")

        st.markdown(f"<div class='chat-agent'>🎓 <b>LearnMate</b><br><br>{greeting}</div>",
                    unsafe_allow_html=True)

    # Render chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-user'>👤 <b>You</b><br><br>{msg['content']}</div>",
                        unsafe_allow_html=True)
        else:
            # Convert markdown-ish content for HTML display
            content = msg["content"].replace("", "<br>").replace("**", "<b>", 1)
            st.markdown(f"<div class='chat-agent'>🎓 <b>LearnMate</b><br><br>{msg['content']}</div>",
                        unsafe_allow_html=True)

    # Input box — always at bottom
    user_input = st.chat_input("Type your message or question here...")
    if user_input:
        _handle_message(user_input)
        st.rerun()


def _handle_message(user_input: str):
    """Send message to agent and store both turns."""
    st.session_state.messages.append({"role": "user", "content": user_input})

    agent = st.session_state.agent
    if not agent:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Session error — please refresh and start again."
        })
        return

    with st.spinner("LearnMate is thinking..."):
        try:
            response = agent.send_message(user_input)
        except Exception as e:
            response = f"Something went wrong: {str(e)} Please check your API key and try again."

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Update profile stats from agent
    profile = st.session_state.profile
    active = get_active_profile()
    if active:
        profile.comprehension_score = active.comprehension_score
        profile.current_topic = active.current_topic
        profile.weak_areas = active.weak_areas
        profile.strong_areas = active.strong_areas
        profile.total_concepts_learned = active.total_concepts_learned
        profile.current_difficulty = active.current_difficulty


# ═══════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════

if st.session_state.screen == "onboarding":
    show_onboarding()
else:
    show_chat()
