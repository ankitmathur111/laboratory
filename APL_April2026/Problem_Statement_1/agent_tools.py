#Cmd from this project path to launch the dashboard
#python -m streamlit run dashboard.py
#Try custom query: "Medical emergency at North Stand, what do we do?"
"""
agent_tools.py
--------------
All the 'tools' that the Gemini agent can call.
Each function is a standalone Python function that talks to the simulator.
The agent decides WHEN to call them and WHAT to do with results.
"""

import json
from venue_simulator import VenueSimulator

# Global simulator instance shared by all tools
_simulator = VenueSimulator()


def set_match_minute(minute: int):
    """Advance the simulator clock. Call this before running the agent."""
    _simulator.match_minute = minute


# ═══════════════════════════════════════════════════════════════════
# TOOL FUNCTIONS  (Gemini will call these by name)
# ═══════════════════════════════════════════════════════════════════

def get_zone_density(zone_id: str) -> str:
    """
    Returns crowd density information for a specific venue zone.
    zone_id options: North_Stand, South_Stand, East_Pavilion, West_Pavilion,
                     VIP_Lounge, Food_Court_A, Food_Court_B, Parking_Zone
    """
    result = _simulator.get_zone_density(zone_id)
    return json.dumps(result)


def get_gate_queue_time(gate_id: str) -> str:
    """
    Returns queue wait time for a specific entrance gate.
    gate_id options: G1, G2, G3, G4, G5, G6, G7, G8, G9
    """
    result = _simulator.get_gate_queue(gate_id)
    return json.dumps(result)


def scan_all_zones() -> str:
    """
    Scans ALL venue zones and returns density + status for each.
    Use this for a full venue health check.
    """
    result = _simulator.get_all_zones()
    return json.dumps(result)


def scan_all_gates() -> str:
    """
    Scans ALL entrance gates and returns queue times.
    Use to find least crowded entry points to redirect fans.
    """
    result = _simulator.get_all_gates()
    return json.dumps(result)


def get_concession_queues() -> str:
    """
    Returns queue times at all food & beverage concession stalls,
    sorted from shortest to longest wait.
    """
    result = _simulator.get_concession_queues()
    return json.dumps(result)


def get_match_phase() -> str:
    """
    Returns current match phase (e.g. halftime, drinks break, normal play)
    and how many minutes until the next break.
    """
    result = _simulator.get_match_phase()
    return json.dumps(result)


def send_push_notification(fan_segment: str, message: str) -> str:
    """
    Sends a push notification to a group of fans via the stadium app.
    fan_segment: 'all', 'north_stand', 'south_stand', 'east_pavilion',
                 'west_pavilion', 'vip', 'parking'
    message: the notification text (keep under 160 chars)
    """
    # In production: FCM / Firebase call here
    log_action("PUSH_NOTIFICATION", {
        "segment": fan_segment,
        "message": message,
        "fans_reached": {
            "all": 48000, "north_stand": 8000, "south_stand": 7500,
            "east_pavilion": 5000, "west_pavilion": 5000,
            "vip": 1000, "parking": 8000,
        }.get(fan_segment, 1000)
    })
    return json.dumps({
        "status": "SENT",
        "segment": fan_segment,
        "message": message,
    })


def update_digital_signage(board_id: str, message: str) -> str:
    """
    Updates a digital display board in the venue.
    board_id options: MAIN_ENTRANCE, NORTH_CONCOURSE, SOUTH_CONCOURSE,
                      FOOD_COURT, PARKING_EXIT, VIP_ENTRANCE
    message: text to display (keep under 80 chars)
    """
    log_action("SIGNAGE_UPDATE", {"board": board_id, "message": message})
    return json.dumps({"status": "UPDATED", "board": board_id, "message": message})


def alert_ground_staff(zone: str, priority: str, instruction: str) -> str:
    """
    Sends an alert to ground staff radio system.
    zone: the venue zone or gate where staff are needed
    priority: 'LOW', 'MEDIUM', 'HIGH', 'URGENT'
    instruction: what staff should do
    """
    log_action("STAFF_ALERT", {
        "zone": zone, "priority": priority, "instruction": instruction
    })
    return json.dumps({
        "status": "ALERTED",
        "zone": zone,
        "priority": priority,
        "instruction": instruction,
    })


def open_additional_gate(gate_id: str) -> str:
    """
    Requests operations team to open an additional entry/exit gate.
    gate_id: one of G1..G9
    """
    log_action("OPEN_GATE", {"gate": gate_id})
    return json.dumps({"status": "REQUEST_SENT", "gate": gate_id,
                        "eta_minutes": 3})


# ── Action log (in-memory, shown in dashboard) ────────────────────────────────

_action_log: list[dict] = []


def log_action(action_type: str, details: dict):
    import datetime
    _action_log.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "type": action_type,
        "details": details,
    })


def get_action_log() -> list[dict]:
    return list(_action_log)


def clear_action_log():
    _action_log.clear()


# ── Tool registry for Gemini function calling ─────────────────────────────────

TOOL_FUNCTIONS = {
    "get_zone_density":       get_zone_density,
    "get_gate_queue_time":    get_gate_queue_time,
    "scan_all_zones":         scan_all_zones,
    "scan_all_gates":         scan_all_gates,
    "get_concession_queues":  get_concession_queues,
    "get_match_phase":        get_match_phase,
    "send_push_notification": send_push_notification,
    "update_digital_signage": update_digital_signage,
    "alert_ground_staff":     alert_ground_staff,
    "open_additional_gate":   open_additional_gate,
}

# Gemini function declarations (schema for the model)
TOOL_DECLARATIONS = [
    {
        "name": "get_zone_density",
        "description": "Get crowd density for a specific venue zone.",
        "parameters": {
            "type": "object",
            "properties": {
                "zone_id": {
                    "type": "string",
                    "description": "Zone name, e.g. North_Stand, Food_Court_A"
                }
            },
            "required": ["zone_id"],
        },
    },
    {
        "name": "get_gate_queue_time",
        "description": "Get queue wait time at a specific entrance gate.",
        "parameters": {
            "type": "object",
            "properties": {
                "gate_id": {
                    "type": "string",
                    "description": "Gate ID, e.g. G1, G2, ... G9"
                }
            },
            "required": ["gate_id"],
        },
    },
    {
        "name": "scan_all_zones",
        "description": "Scan ALL zones at once to get a full venue density overview.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "scan_all_gates",
        "description": "Scan ALL gates at once to find crowded or closed gates.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_concession_queues",
        "description": "Get wait times at all food stalls, sorted shortest first.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_match_phase",
        "description": "Get current match phase and time to next break.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "send_push_notification",
        "description": "Send a push notification to a fan segment via stadium app.",
        "parameters": {
            "type": "object",
            "properties": {
                "fan_segment": {
                    "type": "string",
                    "description": "Target: all, north_stand, south_stand, east_pavilion, west_pavilion, vip, parking"
                },
                "message": {
                    "type": "string",
                    "description": "Notification message, max 160 chars"
                },
            },
            "required": ["fan_segment", "message"],
        },
    },
    {
        "name": "update_digital_signage",
        "description": "Update a digital display board in the venue.",
        "parameters": {
            "type": "object",
            "properties": {
                "board_id": {
                    "type": "string",
                    "description": "Board ID: MAIN_ENTRANCE, NORTH_CONCOURSE, SOUTH_CONCOURSE, FOOD_COURT, PARKING_EXIT, VIP_ENTRANCE"
                },
                "message": {
                    "type": "string",
                    "description": "Message to display, max 80 chars"
                },
            },
            "required": ["board_id", "message"],
        },
    },
    {
        "name": "alert_ground_staff",
        "description": "Alert ground staff via radio with instructions.",
        "parameters": {
            "type": "object",
            "properties": {
                "zone": {"type": "string", "description": "Zone or gate needing attention"},
                "priority": {"type": "string", "description": "LOW, MEDIUM, HIGH, or URGENT"},
                "instruction": {"type": "string", "description": "What staff should do"},
            },
            "required": ["zone", "priority", "instruction"],
        },
    },
    {
        "name": "open_additional_gate",
        "description": "Request operations to open an additional entry/exit gate.",
        "parameters": {
            "type": "object",
            "properties": {
                "gate_id": {"type": "string", "description": "Gate to open: G1..G9"}
            },
            "required": ["gate_id"],
        },
    },
]
