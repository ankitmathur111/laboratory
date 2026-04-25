"""
learner_profile.py
------------------
Manages learner profiles — age group, domain, learning style,
knowledge level, session history, and comprehension scores.
All stored in-memory (easily replaceable with Firestore/BigQuery for production).
"""

import json
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS — the agent uses these to personalise
# ═══════════════════════════════════════════════════════════════════

AGE_GROUPS = {
    "Child (6–12)": {
        "style": "Use very simple words, fun analogies, emojis, short sentences. "
                 "Relate everything to games, cartoons, or everyday objects a child knows.",
        "session_length": 10,   # minutes
        "quiz_questions": 2,
    },
    "Teenager (13–17)": {
        "style": "Be cool and relatable. Use pop culture references, memes-style analogies. "
                 "Keep energy high. Short punchy explanations with examples from social media, gaming, sports.",
        "session_length": 15,
        "quiz_questions": 3,
    },
    "Young Adult (18–25)": {
        "style": "Peer-level tone. Use real-world examples, career relevance, "
                 "connect concepts to skills that matter in jobs/college.",
        "session_length": 25,
        "quiz_questions": 4,
    },
    "Adult (26–45)": {
        "style": "Professional and efficient. Respect their time. "
                 "Use workplace analogies, connect to business/life outcomes. No fluff.",
        "session_length": 20,
        "quiz_questions": 4,
    },
    "Senior (46+)": {
        "style": "Patient, clear, and respectful. Avoid jargon. "
                 "Use life experience analogies. Repeat key points. Go slower.",
        "session_length": 15,
        "quiz_questions": 3,
    },
}

DOMAINS = [
    "Technology & AI",
    "Science & Medicine",
    "Finance & Economics",
    "History & Culture",
    "Mathematics",
    "Language & Literature",
    "Business & Management",
    "Arts & Music",
    "Law & Governance",
    "Environment & Climate",
    "Sports & Fitness",
    "Cooking & Nutrition",
    "Philosophy & Ethics",
    "Psychology",
    "Engineering",
]

LEARNING_STYLES = {
    "Visual": "Use diagrams described in text, tables, structured bullet points, flowcharts in words.",
    "Story-based": "Wrap every concept in a narrative or story. Use characters and plot.",
    "Example-first": "Always start with a concrete real-world example before explaining theory.",
    "Theory-first": "Give the formal definition first, then examples.",
    "Socratic": "Guide through questions rather than direct explanation. Make them think.",
    "Analogy-based": "Every concept must be explained through a familiar analogy first.",
}

DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]


# ═══════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class QuizResult:
    question: str
    user_answer: str
    correct: bool
    score: int          # 0-100
    feedback: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


@dataclass
class SessionRecord:
    session_id: str
    topic: str
    domain: str
    difficulty: str
    messages_exchanged: int
    avg_comprehension: float    # 0-100
    quiz_results: list = field(default_factory=list)
    duration_minutes: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


@dataclass
class LearnerProfile:
    name: str
    age_group: str
    domain: str
    learning_style: str
    current_difficulty: str = "Beginner"
    current_topic: str = ""
    comprehension_score: float = 50.0   # 0-100, starts neutral
    streak_days: int = 0
    total_sessions: int = 0
    total_concepts_learned: int = 0
    session_history: list = field(default_factory=list)
    weak_areas: list = field(default_factory=list)
    strong_areas: list = field(default_factory=list)
    preferred_language: str = "English"
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

    def to_dict(self):
        return asdict(self)

    def get_style_instructions(self) -> str:
        age_inst = AGE_GROUPS.get(self.age_group, {}).get("style", "")
        style_inst = LEARNING_STYLES.get(self.learning_style, "")
        return f"{age_inst}\n\nLearning style — {self.learning_style}: {style_inst}"

    def get_difficulty_context(self) -> str:
        score = self.comprehension_score
        if score >= 85:
            return f"Learner is excelling (score {score:.0f}/100). Push to next difficulty level. Give harder examples."
        elif score >= 65:
            return f"Learner is doing well (score {score:.0f}/100). Maintain current difficulty. Add slight complexity."
        elif score >= 45:
            return f"Learner is struggling (score {score:.0f}/100). Simplify explanations. Use more analogies."
        else:
            return f"Learner needs more support (score {score:.0f}/100). Go back to basics. Be very patient."

    def update_comprehension(self, new_score: float, weight: float = 0.3):
        """Exponential moving average — new scores matter but don't reset history."""
        self.comprehension_score = (1 - weight) * self.comprehension_score + weight * new_score

    def auto_adjust_difficulty(self):
        """Auto-promote or demote difficulty based on comprehension."""
        idx = DIFFICULTY_LEVELS.index(self.current_difficulty)
        if self.comprehension_score >= 85 and idx < len(DIFFICULTY_LEVELS) - 1:
            self.current_difficulty = DIFFICULTY_LEVELS[idx + 1]
            return f"⬆️ Promoted to {self.current_difficulty}!"
        elif self.comprehension_score < 40 and idx > 0:
            self.current_difficulty = DIFFICULTY_LEVELS[idx - 1]
            return f"⬇️ Adjusted to {self.current_difficulty} for better understanding."
        return None


# ═══════════════════════════════════════════════════════════════════
# PROFILE STORE (in-memory; swap with Firestore for production)
# ═══════════════════════════════════════════════════════════════════

class ProfileStore:
    def __init__(self):
        self._profiles: dict[str, LearnerProfile] = {}

    def save(self, profile: LearnerProfile):
        self._profiles[profile.name] = profile

    def load(self, name: str) -> Optional[LearnerProfile]:
        return self._profiles.get(name)

    def exists(self, name: str) -> bool:
        return name in self._profiles

    def all_names(self) -> list:
        return list(self._profiles.keys())


# Global store instance
_store = ProfileStore()

def get_store() -> ProfileStore:
    return _store
