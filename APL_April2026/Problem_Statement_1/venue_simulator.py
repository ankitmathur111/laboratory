"""
venue_simulator.py
------------------
Simulates IoT sensor data for a cricket stadium.
No real hardware needed — generates realistic crowd density,
queue wait times, and incident events.
"""

import random
import time
from dataclasses import dataclass, field
from typing import Optional


# ── Zone definitions ─────────────────────────────────────────────────────────

ZONES = {
    "North_Stand":    {"capacity": 8000,  "gates": ["G1", "G2"]},
    "South_Stand":    {"capacity": 7500,  "gates": ["G3", "G4"]},
    "East_Pavilion":  {"capacity": 5000,  "gates": ["G5"]},
    "West_Pavilion":  {"capacity": 5000,  "gates": ["G6"]},
    "VIP_Lounge":     {"capacity": 1000,  "gates": ["G7"]},
    "Food_Court_A":   {"capacity": 2000,  "gates": []},
    "Food_Court_B":   {"capacity": 2000,  "gates": []},
    "Parking_Zone":   {"capacity": 10000, "gates": ["G8", "G9"]},
}

GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"]

CONCESSIONS = ["Stall_A1", "Stall_A2", "Stall_B1", "Stall_B2",
                "Stall_C1", "Stall_C2", "Stall_D1"]

# ── Match timeline ────────────────────────────────────────────────────────────

MATCH_PHASES = [
    (0,   15,  "Pre-Match Arrival",    "crowds_arriving"),
    (15,  90,  "1st Innings - 1st Half", "normal"),
    (90,  100, "Drinks Break",          "drinks_break"),
    (100, 180, "1st Innings - 2nd Half", "normal"),
    (180, 210, "Lunch Break",           "halftime"),
    (210, 290, "2nd Innings - 1st Half", "normal"),
    (290, 300, "Drinks Break",           "drinks_break"),
    (300, 380, "2nd Innings - 2nd Half", "normal"),
    (380, 400, "Post-Match Dispersal",  "dispersal"),
]


@dataclass
class ZoneState:
    zone_id: str
    density: int = 0          # 0-100 scale
    crowd_count: int = 0
    temp_celsius: float = 32.0
    incident: Optional[str] = None


@dataclass
class GateState:
    gate_id: str
    queue_minutes: float = 0.0
    throughput_per_min: int = 50
    is_open: bool = True


@dataclass
class VenueSnapshot:
    match_minute: int
    phase_name: str
    phase_type: str
    zones: dict = field(default_factory=dict)        # zone_id -> ZoneState
    gates: dict = field(default_factory=dict)        # gate_id -> GateState
    concession_queues: dict = field(default_factory=dict)  # stall -> minutes
    alert_events: list = field(default_factory=list)


class VenueSimulator:
    """
    Generates realistic crowd data for each match minute.
    Call .tick(match_minute) to advance time.
    """

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.match_minute = 0
        self._base_density = {z: 20 for z in ZONES}
        self._incidents = []

    # ── Public API ────────────────────────────────────────────────────────────

    def get_snapshot(self, match_minute: int) -> VenueSnapshot:
        """Return a full venue snapshot for a given match minute."""
        self.match_minute = match_minute
        phase_name, phase_type = self._get_phase(match_minute)

        zones = {z: self._simulate_zone(z, phase_type) for z in ZONES}
        gates = {g: self._simulate_gate(g, phase_type) for g in GATES}
        concessions = {s: self._simulate_concession(s, phase_type)
                       for s in CONCESSIONS}
        alerts = self._generate_alerts(zones, gates, phase_type)

        return VenueSnapshot(
            match_minute=match_minute,
            phase_name=phase_name,
            phase_type=phase_type,
            zones=zones,
            gates=gates,
            concession_queues=concessions,
            alert_events=alerts,
        )

    def get_zone_density(self, zone_id: str) -> dict:
        snap = self.get_snapshot(self.match_minute)
        if zone_id not in snap.zones:
            return {"error": f"Zone '{zone_id}' not found",
                    "valid_zones": list(ZONES.keys())}
        z = snap.zones[zone_id]
        return {
            "zone": zone_id,
            "density_score": z.density,
            "crowd_count": z.crowd_count,
            "status": self._density_status(z.density),
            "temperature_c": round(z.temp_celsius, 1),
            "incident": z.incident,
        }

    def get_gate_queue(self, gate_id: str) -> dict:
        snap = self.get_snapshot(self.match_minute)
        if gate_id not in snap.gates:
            return {"error": f"Gate '{gate_id}' not found",
                    "valid_gates": GATES}
        g = snap.gates[gate_id]
        return {
            "gate": gate_id,
            "wait_minutes": round(g.queue_minutes, 1),
            "is_open": g.is_open,
            "throughput_per_min": g.throughput_per_min,
            "status": "CRITICAL" if g.queue_minutes > 20 else
                      "HIGH" if g.queue_minutes > 10 else "NORMAL",
        }

    def get_all_zones(self) -> list:
        snap = self.get_snapshot(self.match_minute)
        return [self.get_zone_density(z) for z in ZONES]

    def get_all_gates(self) -> list:
        snap = self.get_snapshot(self.match_minute)
        return [self.get_gate_queue(g) for g in GATES]

    def get_concession_queues(self) -> list:
        snap = self.get_snapshot(self.match_minute)
        results = []
        for stall, mins in snap.concession_queues.items():
            results.append({
                "stall": stall,
                "wait_minutes": round(mins, 1),
                "status": "LONG" if mins > 12 else
                          "MODERATE" if mins > 6 else "SHORT",
            })
        return sorted(results, key=lambda x: x["wait_minutes"])

    def get_match_phase(self) -> dict:
        name, ptype = self._get_phase(self.match_minute)
        return {
            "match_minute": self.match_minute,
            "phase": name,
            "type": ptype,
            "minutes_to_next_break": self._mins_to_next_break(),
        }

    # ── Private simulation helpers ────────────────────────────────────────────

    def _get_phase(self, minute: int):
        for start, end, name, ptype in MATCH_PHASES:
            if start <= minute < end:
                return name, ptype
        return "Post-Event", "dispersal"

    def _mins_to_next_break(self):
        for start, end, name, ptype in MATCH_PHASES:
            if ptype in ("halftime", "drinks_break"):
                if start > self.match_minute:
                    return start - self.match_minute
        return 999

    def _simulate_zone(self, zone_id: str, phase: str) -> ZoneState:
        cap = ZONES[zone_id]["capacity"]
        base = {
            "crowds_arriving": 60,
            "normal":          75,
            "drinks_break":    85,
            "halftime":        90,
            "dispersal":       40,
        }.get(phase, 70)

        # Zone-specific offsets
        offsets = {
            "Food_Court_A": 15, "Food_Court_B": 15,
            "VIP_Lounge": -20, "Parking_Zone": -10,
        }
        base += offsets.get(zone_id, 0)
        noise = random.randint(-8, 8)
        density = max(0, min(100, base + noise))

        # Random incident (1% chance)
        incident = None
        if random.random() < 0.01:
            incident = random.choice([
                "Medical assistance requested",
                "Lost child reported",
                "Overcrowding near stairwell",
                "Crowd surge detected",
            ])

        return ZoneState(
            zone_id=zone_id,
            density=density,
            crowd_count=int(cap * density / 100),
            temp_celsius=32 + random.uniform(-1, 2),
            incident=incident,
        )

    def _simulate_gate(self, gate_id: str, phase: str) -> GateState:
        base_queue = {
            "crowds_arriving": 18,
            "normal":           5,
            "drinks_break":    10,
            "halftime":        12,
            "dispersal":       25,
        }.get(phase, 8)
        noise = random.uniform(-3, 5)
        queue = max(0, base_queue + noise)
        is_open = random.random() > 0.05  # 5% chance gate is closed

        return GateState(
            gate_id=gate_id,
            queue_minutes=queue,
            throughput_per_min=random.randint(40, 70),
            is_open=is_open,
        )

    def _simulate_concession(self, stall_id: str, phase: str) -> float:
        base = {
            "halftime":    16,
            "drinks_break": 12,
            "normal":        6,
            "crowds_arriving": 3,
            "dispersal":     2,
        }.get(phase, 7)
        return max(0, base + random.uniform(-2, 4))

    def _generate_alerts(self, zones, gates, phase) -> list:
        alerts = []
        for z_id, z in zones.items():
            if z.density > 90:
                alerts.append({
                    "type": "CRITICAL_DENSITY",
                    "location": z_id,
                    "detail": f"Density at {z.density}% — {z.crowd_count} people",
                    "priority": "HIGH",
                })
            if z.incident:
                alerts.append({
                    "type": "INCIDENT",
                    "location": z_id,
                    "detail": z.incident,
                    "priority": "URGENT",
                })
        for g_id, g in gates.items():
            if not g.is_open:
                alerts.append({
                    "type": "GATE_CLOSED",
                    "location": g_id,
                    "detail": "Gate unexpectedly closed — reroute fans",
                    "priority": "HIGH",
                })
            elif g.queue_minutes > 20:
                alerts.append({
                    "type": "LONG_QUEUE",
                    "location": g_id,
                    "detail": f"Queue at {round(g.queue_minutes,1)} min",
                    "priority": "MEDIUM",
                })
        return alerts

    @staticmethod
    def _density_status(d: int) -> str:
        if d >= 90: return "CRITICAL"
        if d >= 75: return "HIGH"
        if d >= 50: return "MODERATE"
        return "LOW"
