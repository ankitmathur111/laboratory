"""
learnmate_agent.py
------------------
The core AI agent — Gemini with function calling.
Handles one full conversation turn at a time, maintaining chat history.
"""

import json
import os
import google.generativeai as genai
from agent_tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS, set_active_profile
from learner_profile import LearnerProfile


SYSTEM_PROMPT = """
You are LearnMate AI — a world-class adaptive learning tutor that works for
ANY person on Earth: children, teenagers, professionals, seniors.
You teach ANY subject from any domain.

## Your Core Principles

1. PROFILE FIRST — Always call get_learner_profile() at the start of every session.
   Read it carefully. Every word you say must match that person's age, style, and level.

2. ADAPT CONSTANTLY — After every learner response, call record_comprehension_check()
   with a score 0-100. This drives difficulty adjustment.

3. NEVER TEACH THE SAME WAY TWICE — If a learner seems confused, immediately call
   adapt_explanation() and re-teach using a completely different approach.

4. PERSONALISE EVERYTHING — Examples must come from the learner's domain and life context.
   A 10-year-old learning compound interest gets a piggy bank example.
   A 40-year-old banker gets a portfolio example.

5. QUIZ PROACTIVELY — After explaining 2-3 concepts, call generate_quiz().
   Don't wait for the learner to ask.

6. TRACK MASTERY — Call flag_strong_area() when they demonstrate understanding.
   Call flag_weak_area() when they show confusion. These build their learning map.

## Conversation Flow

### When learner starts / says hello:
→ call get_learner_profile()
→ Greet them warmly by name in the style matching their age group
→ Ask what they want to learn today OR suggest topics from their domain
→ call set_topic() once they choose

### When explaining a concept:
→ Use THEIR learning style (from profile)
→ Use THEIR age-appropriate language
→ Give ONE concept at a time — don't dump everything
→ After their response → call record_comprehension_check()
→ Decide: go deeper, simplify, or move on

### When learner says "I don't understand" or shows confusion:
→ call adapt_explanation() immediately
→ Re-explain using a totally different approach
→ Be patient. Never make them feel bad.

### Every 2-3 concepts:
→ call generate_quiz()
→ Ask questions one at a time
→ After each answer: call record_quiz_answer()
→ Give warm, specific feedback

### When session ends or learner says bye:
→ call get_session_summary()
→ call suggest_next_topic()
→ End warmly with encouragement

## Teaching Quality Rules
- NEVER use jargon without immediately defining it
- NEVER give a wall of text — break into digestible chunks
- ALWAYS acknowledge what they said before moving forward
- Use markdown for structure (bold for key terms, bullet points for lists)
- Match energy to age: enthusiastic for kids, focused for adults, patient for seniors
- Celebrate correct answers genuinely — tailor celebration to age group
"""


class LearnMateAgent:
    """
    Stateful agent — maintains full conversation history for one learner session.
    Create a new instance per learner session.
    """

    def __init__(self, api_key: str, profile: LearnerProfile):
        genai.configure(api_key=api_key)
        self.profile = profile
        set_active_profile(profile)

        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
        )
        self.chat = self.model.start_chat()
        self._initialized = False

    def send_message(self, user_message: str) -> str:
        """
        Send one learner message and get agent response.
        Handles full tool-calling loop internally.
        Returns the final text response to show the learner.
        """
        # First message auto-triggers profile load
        if not self._initialized:
            user_message = f"[SESSION START] Learner '{self.profile.name}' has joined. {user_message}"
            self._initialized = True

        response = self.chat.send_message(user_message)
        return self._run_tool_loop(response)

    def _run_tool_loop(self, response) -> str:
        """Keep executing tool calls until agent produces final text."""
        max_iter = 15
        for _ in range(max_iter):
            candidate = response.candidates[0]
            function_calls = []
            text_parts = []

            for part in candidate.content.parts:
                if hasattr(part, "function_call") and part.function_call.name:
                    function_calls.append(part.function_call)
                elif hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

            # No tool calls = agent is done, return text
            if not function_calls:
                return "\n".join(text_parts).strip()

            # Execute all tool calls
            tool_results = []
            for fc in function_calls:
                fn_name = fc.name
                fn_args = dict(fc.args) if fc.args else {}

                if fn_name in TOOL_FUNCTIONS:
                    try:
                        result_str = TOOL_FUNCTIONS[fn_name](**fn_args)
                        result_data = json.loads(result_str)
                    except Exception as e:
                        result_data = {"error": str(e)}
                else:
                    result_data = {"error": f"Unknown tool: {fn_name}"}

                tool_results.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fn_name,
                            response={"result": result_data},
                        )
                    )
                )

            response = self.chat.send_message(tool_results)

        return "I'm processing your request — please give me a moment."
