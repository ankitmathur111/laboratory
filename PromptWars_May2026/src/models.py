from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from datetime import date

class Location(BaseModel):
    name: str
    lat: float
    lon: float
    address: Optional[str] = None

class Activity(BaseModel):
    id: str
    name: str
    description: str
    cost: float
    categories: List[str]  # e.g. ["Culture", "Nature", "Shopping", "Adventure", "Relaxation", "Food", "Nightlife"]
    avg_duration: float    # in hours (e.g., 2.5)
    start_hour: float      # e.g., 9.0 (9:00 AM)
    end_hour: float        # e.g., 18.0 (6:00 PM)
    location: Location
    physical_intensity: str  # "Low", "Medium", "High"
    accessibility: bool     # True if wheelchair-accessible / mobility-friendly
    weather_suitability: str # "Indoor", "Outdoor", "Any"
    rating: float          # e.g., 4.7

class Restaurant(BaseModel):
    id: str
    name: str
    cuisine: str
    budget_tier: str       # "Budget", "Mid-range", "Luxury"
    dietary_tags: List[str] # e.g. ["vegetarian", "vegan", "halal", "gluten-free"]
    location: Location
    rating: float
    start_hour: float      # e.g., 11.0
    end_hour: float        # e.g., 22.0

class Hotel(BaseModel):
    id: str
    name: str
    description: str
    budget_tier: str       # "Budget", "Mid-range", "Luxury"
    location: Location
    rating: float
    price_per_night: float

class TripRequest(BaseModel):
    destination: str
    start_date: date
    duration_days: int
    budget_level: str      # "Budget", "Mid-range", "Luxury"
    pace: str              # "Relaxed" (2-3 spots), "Moderate" (4-5 spots), "Packed" (6+ spots)
    interests: Dict[str, float] # Category names mapped to weights (0.0 to 1.0)
    dietary_constraints: List[str] # e.g. ["vegetarian", "vegan", "halal", "gluten-free"]
    mobility_constraints: List[str] # e.g. ["wheelchair"]
    transport_mode: str    # "Public Transit", "Walking", "Rental Car", "Taxi"

class ScheduledActivity(BaseModel):
    time_slot: str         # e.g., "09:00 - 11:30"
    start_hour: float      # e.g., 9.0
    end_hour: float        # e.g., 11.5
    item_id: str           # References Activity.id, Restaurant.id, or Hotel.id
    name: str
    type: str              # "hotel", "activity", "restaurant", "transit", "rest_break"
    description: str
    cost: float
    location: Location
    original_item_id: Optional[str] = None  # To track swaps in replanning

class TransitStep(BaseModel):
    from_name: str
    to_name: str
    duration_mins: float
    distance_km: float
    mode: str
    cost: float
    time_slot: str         # e.g., "11:30 - 12:00"

class DaySchedule(BaseModel):
    day_number: int
    date_str: str          # e.g., "2026-06-01"
    activities: List[ScheduledActivity] = Field(default_factory=list)
    transit_steps: List[TransitStep] = Field(default_factory=list)
    total_cost: float = 0.0

class Itinerary(BaseModel):
    trip_request: TripRequest
    hotel: Hotel
    daily_schedules: List[DaySchedule]
    total_cost: float
    summary: str
