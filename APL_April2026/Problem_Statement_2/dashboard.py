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

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LearnMate AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0D1117; }
    section[data-testid="stSidebar"] { background-color: #0D1B2A; }

    .chat-user {
        background: #1E3A5F;
        border-radius: 16px 16px 4px 16px;
        padding: 12px 16px;
        margin: 6px 0 6px 15%;
        color: #E8F4FD;
        font-size: 15px;
    }
    .chat-agent {
        background: #142038;
        border: 1px solid #1E4080;
        border-radius: 4px 16px 16px 16px;
        padding: 14px 18px;
        margin: 6px 15% 6px 0;
        color: #FFFFFF;
        font-size: 15px;
        line-height: 1.6;
    }
    .profile-card {
        background: #142038;
        border: 1px solid #1E4080;
        border-left: 4px solid #4A9EFF;
        border-radius: 8px;
        padding: 12px 14px;
        margin: 6px 0;
    }
    .metric-mini {
        background: #0D1B2A;
        border: 1px solid #1E3560;
        border-radius: 8px;
        padding: 8px 12px;
        text-align: center;
    }
    .stat-number { font-size: 22px; font-weight: bold; color: #4A9EFF; }
    .stat-label  { font-size: 11px; color: #6688AA; }
    .log-entry {
        font-family: monospace;
        font-size: 11px;
        color: #6699BB;
        padding: 3px 0;
        border-bottom: 1px solid #1A2A3A;
    }
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
        margin: 2px;
    }
    .badge-blue   { background: #1E3A6E; color: #4A9EFF; }
    .badge-green  { background: #0D3020; color: #44CC88; }
    .badge-red    { background: #3A1020; color: #FF6688; }
    .badge-orange { background: #3A2010; color: #FFAA44; }

    div[data-testid="stChatMessage"] { background: transparent !important; }
    .stTextInput input { background: #1A2A3A !important; color: white !important; }
    .stSelectbox > div { background: #1A2A3A !important; }
    h1, h2, h3 { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "screen": "onboarding",     # onboarding | chat
        "profile": None,
        "agent": None,
        "messages": [],             # [{role, content}]
        "api_key": os.environ.get("GEMINI_API_KEY", ""),
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
            help="\n".join([f"{k}: {v[:80]}..." for k, v in LEARNING_STYLES.items()])
        )
        difficulty = st.selectbox("Starting level", DIFFICULTY_LEVELS)
        api_key = st.text_input(
            "🔑 Gemini API Key",
            value=st.session_state.api_key,
            type="password",
            help="Free key at aistudio.google.com/apikey",
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
        st.session_state.api_key = api_key
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
        st.markdown("### 🎓 LearnMate AI")
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
    st.markdown(f"## 🎓 Learning with LearnMate AI")
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
            content = msg["content"].replace("\n", "<br>").replace("**", "<b>", 1)
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
            response = f"Something went wrong: {str(e)}\n\nPlease check your API key and try again."

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
