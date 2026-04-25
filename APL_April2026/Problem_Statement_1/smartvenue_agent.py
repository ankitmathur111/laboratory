#Cmd from this project path to launch the dashboard
#python -m streamlit run dashboard.py

"""
smartvenue_agent.py
-------------------
The core AI agent.
Uses Gemini with function-calling to reason over venue data
and autonomously take actions (notifications, staff alerts, signage).

Run standalone:  python smartvenue_agent.py
"""

import json
import os
import google.generativeai as genai
from agent_tools import (
    TOOL_DECLARATIONS, TOOL_FUNCTIONS,
    set_match_minute, get_action_log, clear_action_log,
)

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are SmartVenue AI — an autonomous agentic coordinator for large-scale cricket events.

Your mission: Keep 50,000 fans safe, comfortable, and happy by proactively managing
crowd flow, queue times, and real-time incidents.

## Your Behavior Protocol

### Step 1 — Situational Awareness (always start here)
- Call scan_all_zones() and scan_all_gates() to get full picture
- Call get_match_phase() to understand timing context

### Step 2 — Triage Alerts
Classify each issue:
- CRITICAL: Zone density > 90 OR gate queue > 20 min → IMMEDIATE action
- HIGH:     Zone density > 75 OR gate queue > 12 min → action within 1 loop
- MEDIUM:   Zone density > 60 OR gate queue > 8 min  → monitor + inform
- NORMAL:   No action needed

### Step 3 — Take Actions (use ALL relevant tools)

For CRITICAL density zones:
→ alert_ground_staff() with URGENT priority
→ send_push_notification() to fans in that zone telling them to move
→ update_digital_signage() on nearest boards

For long gate queues:
→ open_additional_gate() if queue > 20 min
→ send_push_notification() redirecting fans to shorter queues
→ update_digital_signage() at main entrance

For halftime / drinks breaks (check get_match_phase):
→ Proactively push shortest concession stall info to ALL fans
→ Alert staff to prepare for crowd surge in food courts
→ Update food court signage with wait times

For incidents:
→ alert_ground_staff() URGENT
→ Do NOT notify all fans (avoid panic) unless evacuation needed

### Step 4 — Summary
After all actions, write a clear incident report:
- What you found (data)
- What you did (actions taken)
- What to watch next

## Tone Rules
- Be factual and precise. Use numbers.
- Never cry wolf — only alert for real issues
- Fan notifications: friendly, helpful tone
- Staff alerts: terse, military-style instructions
"""


def run_agent_cycle(
    match_minute: int,
    api_key: str,
    custom_query: str = None,
    verbose: bool = True,
) -> dict:
    """
    Run one full agent cycle for the given match_minute.
    Returns a dict with: reasoning, actions_taken, summary
    """
    # Configure Gemini
    genai.configure(api_key=api_key)

    # Advance simulator
    set_match_minute(match_minute)
    clear_action_log()

    # Build user message
    if custom_query:
        user_message = custom_query
    else:
        user_message = (
            f"Match minute: {match_minute}. "
            f"Run a full venue health check and take all necessary actions. "
            f"Be thorough — check zones, gates, and match phase."
        )

    if verbose:
        print(f"\n{'='*60}")
        print(f"  🏟  SmartVenue AI — Match Minute {match_minute}")
        print(f"{'='*60}")
        print(f"Query: {user_message}\n")

    # Set up Gemini model with tools
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
        tools=[{"function_declarations": TOOL_DECLARATIONS}],
    )

    chat = model.start_chat()
    response = chat.send_message(user_message)

    # ── Agentic loop: keep calling tools until agent is done ──────────────────
    reasoning_steps = []
    iterations = 0
    max_iterations = 20  # safety cap

    while iterations < max_iterations:
        iterations += 1
        candidate = response.candidates[0]

        # Collect all function calls in this response
        function_calls = []
        text_parts = []

        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call.name:
                function_calls.append(part.function_call)
            elif hasattr(part, "text") and part.text:
                text_parts.append(part.text)

        # Print any reasoning text
        for text in text_parts:
            if verbose and text.strip():
                print(f"🤖 Agent: {text[:200]}...")
            reasoning_steps.append(text)

        # If no function calls, agent is done
        if not function_calls:
            break

        # Execute each tool call
        tool_results = []
        for fc in function_calls:
            fn_name = fc.name
            fn_args = dict(fc.args) if fc.args else {}

            if verbose:
                print(f"  🔧 Calling: {fn_name}({fn_args})")

            # Execute the actual Python function
            if fn_name in TOOL_FUNCTIONS:
                try:
                    result_str = TOOL_FUNCTIONS[fn_name](**fn_args)
                    result_data = json.loads(result_str)
                    if verbose:
                        _print_result(fn_name, result_data)
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})
                    result_data = {"error": str(e)}
            else:
                result_str = json.dumps({"error": f"Unknown tool: {fn_name}"})
                result_data = {"error": f"Unknown tool: {fn_name}"}

            tool_results.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=fn_name,
                        response={"result": result_data},
                    )
                )
            )

        # Send all results back to model
        response = chat.send_message(tool_results)

    # ── Extract final summary ──────────────────────────────────────────────────
    final_text = ""
    for part in response.candidates[0].content.parts:
        if hasattr(part, "text"):
            final_text += part.text

    if verbose:
        print(f"\n{'─'*60}")
        print("📋 AGENT SUMMARY:")
        print(final_text)
        print(f"{'─'*60}")

    actions = get_action_log()

    return {
        "match_minute": match_minute,
        "reasoning": reasoning_steps,
        "summary": final_text,
        "actions_taken": actions,
        "tool_calls_made": iterations,
    }


def _print_result(fn_name: str, result):
    """Pretty print tool results in terminal."""
    if isinstance(result, list):
        print(f"    → {fn_name}: [{len(result)} items]")
        for item in result[:3]:
            if isinstance(item, dict):
                key_info = {k: v for k, v in item.items()
                            if k in ("zone", "gate", "density_score",
                                     "wait_minutes", "status", "stall")}
                print(f"      {key_info}")
    else:
        simplified = {k: v for k, v in result.items()
                      if k not in ("error",) or "error" in result}
        print(f"    → {simplified}")


# ── CLI entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: Set your GEMINI_API_KEY environment variable first.")
        print("  export GEMINI_API_KEY='your-key-here'")
        print("  Get free key at: https://aistudio.google.com/apikey")
        sys.exit(1)

    # Default: run at halftime for a dramatic demo
    minute = int(sys.argv[1]) if len(sys.argv) > 1 else 185

    result = run_agent_cycle(
        match_minute=minute,
        api_key=api_key,
        verbose=True,
    )

    print(f"\n✅ Done. {len(result['actions_taken'])} actions taken.")
