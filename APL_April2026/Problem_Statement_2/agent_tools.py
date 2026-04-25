"""
agent_tools.py
--------------
All tool functions the Gemini learning agent can call.
Each tool is a specific capability: explain, quiz, assess, adapt, etc.
"""

import json
import datetime
from learner_profile import (
    LearnerProfile, QuizResult, SessionRecord,
    AGE_GROUPS, LEARNING_STYLES, DIFFICULTY_LEVELS,
    get_store
)

# ── Active session state ──────────────────────────────────────────────────────
_current_profile: LearnerProfile = None
_session_log: list = []
_comprehension_history: list = []


def set_active_profile(profile: LearnerProfile):
    global _current_profile, _session_log, _comprehension_history
    _current_profile = profile
    _session_log = []
    _comprehension_history = []


def get_active_profile() -> LearnerProfile:
    return _current_profile


def get_session_log() -> list:
    return list(_session_log)


# ═══════════════════════════════════════════════════════════════════
# TOOL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_learner_profile() -> str:
    """
    Get the current learner's full profile including name, age group,
    domain, learning style, difficulty level, and comprehension score.
    Always call this at the START of every session.
    """
    if not _current_profile:
        return json.dumps({"error": "No active learner profile."})
    p = _current_profile
    return json.dumps({
        "name": p.name,
        "age_group": p.age_group,
        "domain": p.domain,
        "learning_style": p.learning_style,
        "current_difficulty": p.current_difficulty,
        "current_topic": p.current_topic,
        "comprehension_score": round(p.comprehension_score, 1),
        "total_sessions": p.total_sessions,
        "total_concepts_learned": p.total_concepts_learned,
        "weak_areas": p.weak_areas,
        "strong_areas": p.strong_areas,
        "teaching_instructions": p.get_style_instructions(),
        "difficulty_guidance": p.get_difficulty_context(),
    })


def set_topic(topic: str) -> str:
    """
    Set the topic the learner wants to study in this session.
    topic: e.g. 'Photosynthesis', 'Compound Interest', 'Machine Learning Basics'
    """
    if not _current_profile:
        return json.dumps({"error": "No active profile."})
    _current_profile.current_topic = topic
    _session_log.append({
        "action": "TOPIC_SET",
        "topic": topic,
        "time": datetime.datetime.now().isoformat(),
    })
    return json.dumps({
        "status": "Topic set",
        "topic": topic,
        "difficulty": _current_profile.current_difficulty,
        "learner": _current_profile.name,
    })


def record_comprehension_check(score: int, evidence: str) -> str:
    """
    Record a comprehension assessment (0-100) based on the learner's response.
    Call this after EVERY learner message to track understanding.
    score: 0=no understanding, 50=partial, 80=good, 100=excellent
    evidence: brief reason for the score (e.g. 'answered correctly', 'showed confusion about X')
    """
    if not _current_profile:
        return json.dumps({"error": "No active profile."})

    _comprehension_history.append(score)
    _current_profile.update_comprehension(float(score))
    adjustment = _current_profile.auto_adjust_difficulty()

    _session_log.append({
        "action": "COMPREHENSION_CHECK",
        "score": score,
        "evidence": evidence,
        "running_avg": round(_current_profile.comprehension_score, 1),
        "time": datetime.datetime.now().isoformat(),
    })

    result = {
        "score_recorded": score,
        "running_comprehension": round(_current_profile.comprehension_score, 1),
        "difficulty": _current_profile.current_difficulty,
        "evidence": evidence,
    }
    if adjustment:
        result["difficulty_adjustment"] = adjustment
    return json.dumps(result)


def generate_quiz(num_questions: int = 3) -> str:
    """
    Signal that a quiz should be generated for the current topic.
    Returns quiz parameters — the agent will generate the actual questions.
    num_questions: how many questions to ask (1-5)
    """
    if not _current_profile:
        return json.dumps({"error": "No active profile."})
    p = _current_profile
    age_q = AGE_GROUPS.get(p.age_group, {}).get("quiz_questions", 3)
    actual_q = min(num_questions, age_q)

    _session_log.append({
        "action": "QUIZ_STARTED",
        "topic": p.current_topic,
        "num_questions": actual_q,
        "difficulty": p.current_difficulty,
        "time": datetime.datetime.now().isoformat(),
    })

    return json.dumps({
        "quiz_parameters": {
            "topic": p.current_topic,
            "difficulty": p.current_difficulty,
            "num_questions": actual_q,
            "age_group": p.age_group,
            "domain": p.domain,
            "format": "Ask one question at a time. Wait for answer before next.",
            "question_types": [
                "multiple choice (label options A/B/C/D)",
                "fill in the blank",
                "explain in your own words",
                "real-world application",
            ],
        },
        "instruction": "Generate the quiz now using the above parameters. "
                       "After each answer, call record_quiz_answer with the result.",
    })


def record_quiz_answer(question: str, user_answer: str,
                       is_correct: bool, score: int, feedback: str) -> str:
    """
    Record a quiz answer result.
    question: the question asked
    user_answer: what the learner said
    is_correct: True/False
    score: 0-100
    feedback: personalised feedback to show the learner
    """
    if not _current_profile:
        return json.dumps({"error": "No active profile."})

    result = QuizResult(
        question=question,
        user_answer=user_answer,
        correct=is_correct,
        score=score,
        feedback=feedback,
    )
    _session_log.append({
        "action": "QUIZ_ANSWER",
        "correct": is_correct,
        "score": score,
        "time": datetime.datetime.now().isoformat(),
    })

    # Update comprehension based on quiz performance
    _current_profile.update_comprehension(float(score), weight=0.4)

    return json.dumps({
        "recorded": True,
        "correct": is_correct,
        "score": score,
        "running_comprehension": round(_current_profile.comprehension_score, 1),
    })


def flag_weak_area(concept: str) -> str:
    """
    Flag a concept the learner is struggling with for future focus.
    concept: the specific concept or sub-topic they're weak on
    """
    if not _current_profile:
        return json.dumps({"error": "No active profile."})
    if concept not in _current_profile.weak_areas:
        _current_profile.weak_areas.append(concept)
    return json.dumps({"flagged": concept, "all_weak_areas": _current_profile.weak_areas})


def flag_strong_area(concept: str) -> str:
    """
    Flag a concept the learner has mastered.
    concept: the specific concept they've understood well
    """
    if not _current_profile:
        return json.dumps({"error": "No active profile."})
    if concept not in _current_profile.strong_areas:
        _current_profile.strong_areas.append(concept)
        _current_profile.total_concepts_learned += 1
    return json.dumps({"mastered": concept, "total_mastered": _current_profile.total_concepts_learned})


def suggest_next_topic() -> str:
    """
    Based on the learner's profile, suggest what to study next.
    Call this when learner asks 'what should I learn next?' or at end of session.
    """
    if not _current_profile:
        return json.dumps({"error": "No active profile."})
    p = _current_profile
    return json.dumps({
        "current_topic": p.current_topic,
        "weak_areas": p.weak_areas,
        "strong_areas": p.strong_areas,
        "current_difficulty": p.current_difficulty,
        "domain": p.domain,
        "comprehension": round(p.comprehension_score, 1),
        "instruction": (
            "Suggest 3 next topics. Prioritise weak areas if any. "
            "If comprehension > 75, suggest more advanced topics. "
            "If < 50, suggest reinforcement of current topic."
        ),
    })


def get_session_summary() -> str:
    """
    Generate a summary of the current learning session.
    Call this at the END of each session.
    """
    if not _current_profile:
        return json.dumps({"error": "No active profile."})
    p = _current_profile
    quiz_actions = [s for s in _session_log if s["action"] == "QUIZ_ANSWER"]
    correct = sum(1 for q in quiz_actions if q["correct"])

    p.total_sessions += 1
    _session_log.append({
        "action": "SESSION_END",
        "time": datetime.datetime.now().isoformat(),
    })

    return json.dumps({
        "learner": p.name,
        "topic": p.current_topic,
        "final_comprehension": round(p.comprehension_score, 1),
        "difficulty": p.current_difficulty,
        "quiz_score": f"{correct}/{len(quiz_actions)}" if quiz_actions else "No quiz",
        "concepts_mastered": p.strong_areas,
        "areas_to_revisit": p.weak_areas,
        "total_sessions_ever": p.total_sessions,
        "instruction": (
            "Write a warm, encouraging session summary. "
            "Mention what was learned, quiz performance, and what to focus on next time. "
            "Match tone to the learner's age group."
        ),
    })


def adapt_explanation(reason: str) -> str:
    """
    Signal that the current explanation approach isn't working and needs adaptation.
    reason: why adaptation is needed, e.g. 'learner said they dont understand the analogy'
    Call this when learner shows confusion or asks to explain differently.
    """
    if not _current_profile:
        return json.dumps({"error": "No active profile."})
    p = _current_profile
    current_style = p.learning_style
    all_styles = list(LEARNING_STYLES.keys())
    other_styles = [s for s in all_styles if s != current_style]

    _session_log.append({
        "action": "ADAPT_TRIGGERED",
        "reason": reason,
        "time": datetime.datetime.now().isoformat(),
    })

    return json.dumps({
        "current_style": current_style,
        "adaptation_reason": reason,
        "try_next": other_styles[:2],
        "instruction": (
            f"The current {current_style} approach isn't landing. "
            f"Switch to {other_styles[0]} style for this explanation. "
            f"Re-explain the same concept completely differently."
        ),
    })


# ── Tool registry ─────────────────────────────────────────────────────────────

TOOL_FUNCTIONS = {
    "get_learner_profile":      get_learner_profile,
    "set_topic":                set_topic,
    "record_comprehension_check": record_comprehension_check,
    "generate_quiz":            generate_quiz,
    "record_quiz_answer":       record_quiz_answer,
    "flag_weak_area":           flag_weak_area,
    "flag_strong_area":         flag_strong_area,
    "suggest_next_topic":       suggest_next_topic,
    "get_session_summary":      get_session_summary,
    "adapt_explanation":        adapt_explanation,
}

TOOL_DECLARATIONS = [
    {
        "name": "get_learner_profile",
        "description": "Get the current learner's full profile. Call at the START of every session.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "set_topic",
        "description": "Set the topic the learner wants to study.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic or concept to study"}
            },
            "required": ["topic"],
        },
    },
    {
        "name": "record_comprehension_check",
        "description": "Record comprehension score 0-100 after every learner message.",
        "parameters": {
            "type": "object",
            "properties": {
                "score": {"type": "integer", "description": "0=no understanding, 50=partial, 80=good, 100=excellent"},
                "evidence": {"type": "string", "description": "Why this score was given"},
            },
            "required": ["score", "evidence"],
        },
    },
    {
        "name": "generate_quiz",
        "description": "Trigger a quiz on the current topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "num_questions": {"type": "integer", "description": "Number of quiz questions (1-5)"}
            },
            "required": ["num_questions"],
        },
    },
    {
        "name": "record_quiz_answer",
        "description": "Record the result of a quiz question.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "user_answer": {"type": "string"},
                "is_correct": {"type": "boolean"},
                "score": {"type": "integer", "description": "0-100"},
                "feedback": {"type": "string", "description": "Personalised feedback for this learner"},
            },
            "required": ["question", "user_answer", "is_correct", "score", "feedback"],
        },
    },
    {
        "name": "flag_weak_area",
        "description": "Flag a concept the learner is struggling with.",
        "parameters": {
            "type": "object",
            "properties": {
                "concept": {"type": "string"}
            },
            "required": ["concept"],
        },
    },
    {
        "name": "flag_strong_area",
        "description": "Flag a concept the learner has mastered.",
        "parameters": {
            "type": "object",
            "properties": {
                "concept": {"type": "string"}
            },
            "required": ["concept"],
        },
    },
    {
        "name": "suggest_next_topic",
        "description": "Suggest what to study next based on learner progress.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_session_summary",
        "description": "Generate session summary. Call at END of session.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "adapt_explanation",
        "description": "Signal that explanation approach needs to change. Call when learner is confused.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Why adaptation is needed"}
            },
            "required": ["reason"],
        },
    },
]
