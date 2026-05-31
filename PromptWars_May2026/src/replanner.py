from typing import Tuple, List, Dict, Set
import copy
from datetime import datetime
from src.models import (
    Itinerary, DaySchedule, ScheduledActivity, TransitStep, 
    Activity, Restaurant, Hotel, Location
)
from src.database import DESTINATIONS
from src.utils import estimate_transit, format_time, float_to_ampm
from src.planner import get_interest_score, find_nearest_restaurant

def replan_itinerary(
    itinerary: Itinerary, 
    day_num: int, 
    event_type: str, 
    event_details: dict
) -> Tuple[Itinerary, str]:
    """
    Executes dynamic replanning on an existing itinerary based on a real-time event.
    Returns the newly optimized Itinerary and a clear user-facing explanation log.
    """
    new_itinerary = copy.deepcopy(itinerary)
    
    # Validate day bounds
    if day_num < 1 or day_num > len(new_itinerary.daily_schedules):
        return itinerary, "Invalid day selection for replanning."
        
    day_schedule: DaySchedule = new_itinerary.daily_schedules[day_num - 1]
    dest_name = new_itinerary.trip_request.destination
    dest_data = DESTINATIONS[dest_name]
    request = new_itinerary.trip_request
    
    explanation_log = []
    
    # Set of already used activities in other days to prevent duplicate scheduling
    used_activities: Set[str] = set()
    for d_idx, d_sched in enumerate(new_itinerary.daily_schedules):
        if d_idx != (day_num - 1): # Skip the day we are replanning
            for act in d_sched.activities:
                if act.type == "activity":
                    used_activities.add(act.item_id)

    # 1. WEATHER RAIN DISRUPTION: SWAP OUTDOOR WITH INDOOR
    if event_type == "weather_rain":
        explanation_log.append("🌧️ **Sudden Heavy Rain Alert!** Outdoor activities have been swapped with premium indoor alternatives.")
        
        # Step A: Identify which scheduled spots are Outdoor
        updated_activities: List[ScheduledActivity] = []
        has_changes = False
        
        for sa in day_schedule.activities:
            # We only touch activities, not restaurants, hotels or transits here
            if sa.type == "activity":
                # Find matching Activity object from database
                db_act = next((a for a in dest_data["activities"] if a.id == sa.item_id), None)
                
                if db_act and db_act.weather_suitability == "Outdoor":
                    # We must replace it with an indoor/any activity!
                    best_swap = None
                    best_swap_score = -float('inf')
                    
                    for candidate in dest_data["activities"]:
                        # Candidate must be indoor, unused on other days, and not currently scheduled on this day
                        if candidate.id in used_activities:
                            continue
                        if candidate.id in [x.item_id for x in day_schedule.activities]:
                            continue
                        if candidate.weather_suitability not in ["Indoor", "Any"]:
                            continue
                        # Wheelchair check
                        if "wheelchair" in request.mobility_constraints and not candidate.accessibility:
                            continue
                            
                        # Score candidate
                        interest_score = get_interest_score(candidate, request.interests)
                        distance_km = estimate_transit(sa.location, candidate.location, request.transport_mode)[2]
                        distance_factor = 10.0 / (1.0 + distance_km)
                        
                        total_score = interest_score * 3.0 + distance_factor
                        
                        if total_score > best_swap_score:
                            best_swap_score = total_score
                            best_swap = candidate
                    
                    if best_swap:
                        has_changes = True
                        explanation_log.append(f"🔄 Swapped outdoor **{db_act.name}** with indoor **{best_swap.name}**.")
                        
                        # Replace the item in schedule
                        sa.original_item_id = db_act.id
                        sa.item_id = best_swap.id
                        sa.name = best_swap.name
                        sa.description = f"[Rain Swap] {best_swap.description} | 🟢 Low Effort | ♿ Accessible" if best_swap.accessibility else f"[Rain Swap] {best_swap.description}"
                        sa.cost = best_swap.cost
                        sa.location = best_swap.location
                    else:
                        explanation_log.append(f"⚠️ Could not find an indoor alternative for **{db_act.name}**, scheduled rest break instead.")
                        sa.item_id = "rest_break"
                        sa.name = "Cozy Cafe & Rain Shelter"
                        sa.type = "rest_break"
                        sa.description = "Relax inside a premium local coffee shop and enjoy warm beverages until the rain subsides."
                        sa.cost = 6.0
                        has_changes = True
            
            updated_activities.append(sa)
            
        if has_changes:
            # Recompute spatiotemporal transit routes for the day because locations changed!
            rebuild_day_transit(day_schedule, new_itinerary.hotel, request.transport_mode, request.budget_level, dest_data["restaurants"])
        else:
            explanation_log.append("✅ No outdoor activities were scheduled today, so your plans remain optimal.")

    # 2. TRANSIT / FLIGHT DELAY: SHIFT TIMELINE AND DROP OVERLAPS
    elif event_type == "transit_delay":
        delay_hrs = event_details.get("delay_hours", 1.0)
        explanation_log.append(f"⏱️ **Transit Delay of {delay_hrs} hours received!** Propagating changes and resolving conflicts...")
        
        # We assume the delay happens after departing the hotel. Let's find the first transit activity and shift everything.
        shifted_activities: List[ScheduledActivity] = []
        dropped_names = []
        
        # We start shifting right after the first item (Depart Hotel)
        current_hour_shift = 0.0
        
        # Keep track of when the delay is injected
        # Let's say the delay hits right at the start of the first activity
        delay_applied = False
        
        for idx, sa in enumerate(day_schedule.activities):
            if idx == 0:
                shifted_activities.append(sa)
                continue
                
            if not delay_applied:
                # Apply delay right after hotel departure
                current_hour_shift = delay_hrs
                delay_applied = True
                
            # Shift slots
            new_start = sa.start_hour + current_hour_shift
            new_end = sa.end_hour + current_hour_shift
            
            # Check if this item is an activity and if its shifted end exceeds its operating hours
            if sa.type == "activity":
                db_act = next((a for a in dest_data["activities"] if a.id == sa.item_id), None)
                if db_act:
                    # If it ends after closing time, we must drop it!
                    if new_end > db_act.end_hour:
                        dropped_names.append(sa.name)
                        # We don't append to shifted_activities (drop it!)
                        # We also don't shift subsequent tasks by its duration, so we decrease the shift
                        # by the duration of this activity to pull the rest of the schedule back!
                        dur = sa.end_hour - sa.start_hour
                        current_hour_shift -= dur
                        continue
            
            # If it's a transit and the destination activity was dropped, we should drop this transit too!
            if sa.type == "transit" and idx + 1 < len(day_schedule.activities):
                next_act = day_schedule.activities[idx + 1]
                if next_act.type == "activity":
                    next_db_act = next((a for a in dest_data["activities"] if a.id == next_act.item_id), None)
                    if next_db_act and (next_act.end_hour + current_hour_shift > next_db_act.end_hour):
                        # Drop this transit since the next activity is dropped
                        continue
            
            # If it's returning to hotel, we don't drop it but let it shift
            sa.start_hour = new_start
            sa.end_hour = new_end
            sa.time_slot = f"{float_to_ampm(sa.start_hour)} - {float_to_ampm(sa.end_hour)}" if sa.start_hour != sa.end_hour else float_to_ampm(sa.start_hour)
            shifted_activities.append(sa)
            
        day_schedule.activities = shifted_activities
        
        if dropped_names:
            explanation_log.append(f"🚫 Dropped **{', '.join(dropped_names)}** because the delay pushed them past their evening closing hours.")
        else:
            explanation_log.append("✅ All scheduled spots were successfully shifted without needing to drop any activities!")
            
        # Re-verify and rebuild transit segments to ensure correctness
        rebuild_day_transit(day_schedule, new_itinerary.hotel, request.transport_mode, request.budget_level, dest_data["restaurants"])

    # 3. ATTRACTION CLOSURE: REMOVE CLOSED AND ADD SWAP ALTERNATIVE
    elif event_type == "attraction_closed":
        closed_id = event_details.get("closed_id", "")
        closed_act = next((a for a in dest_data["activities"] if a.id == closed_id), None)
        closed_name = closed_act.name if closed_act else "Scheduled Attraction"
        
        explanation_log.append(f"🚧 **Closure Warning!** Received alert that **{closed_name}** is closed. Swapping it out...")
        
        has_closed_scheduled = False
        updated_activities = []
        
        for sa in day_schedule.activities:
            if sa.type == "activity" and sa.item_id == closed_id:
                has_closed_scheduled = True
                
                # Find best alternative from database
                best_alt = None
                best_alt_score = -float('inf')
                
                for candidate in dest_data["activities"]:
                    if candidate.id in used_activities:
                        continue
                    if candidate.id in [x.item_id for x in day_schedule.activities]:
                        continue
                    if "wheelchair" in request.mobility_constraints and not candidate.accessibility:
                        continue
                        
                    # Match score
                    interest_score = get_interest_score(candidate, request.interests)
                    dist_km = estimate_transit(sa.location, candidate.location, request.transport_mode)[2]
                    dist_factor = 10.0 / (1.0 + dist_km)
                    
                    total_score = interest_score * 3.0 + dist_factor
                    
                    if total_score > best_alt_score:
                        best_alt_score = total_score
                        best_alt = candidate
                        
                if best_alt:
                    explanation_log.append(f"🔄 Replaced closed {closed_name} with **{best_alt.name}** nearby.")
                    sa.item_id = best_alt.id
                    sa.name = best_alt.name
                    sa.description = f"[Alternative] {best_alt.description}"
                    sa.cost = best_alt.cost
                    sa.location = best_alt.location
                else:
                    explanation_log.append(f"⚠️ No alternative found for {closed_name}, replaced with a relaxing Rest Break.")
                    sa.item_id = "rest_break"
                    sa.name = "Relaxation Break"
                    sa.type = "rest_break"
                    sa.description = "Enjoy some leisure time wandering surrounding streets or sitting down in a local plaza."
                    sa.cost = 0.0
                    
            updated_activities.append(sa)
            
        if has_closed_scheduled:
            day_schedule.activities = updated_activities
            rebuild_day_transit(day_schedule, new_itinerary.hotel, request.transport_mode, request.budget_level, dest_data["restaurants"])
        else:
            explanation_log.append(f"ℹ️ {closed_name} was not scheduled for today, so no changes were made to today's route.")

    # 4. FATIGUE ALERT: DECREASE PACE, INCREASE REST, END EARLY
    elif event_type == "fatigue_high":
        explanation_log.append("🥱 **Energy Level: Low.** Adjusting plan to reduce walking effort, inserting cafe rest breaks, and finishing earlier.")
        
        new_activities: List[ScheduledActivity] = []
        has_high_effort = False
        
        for sa in day_schedule.activities:
            if sa.type == "activity":
                db_act = next((a for a in dest_data["activities"] if a.id == sa.item_id), None)
                if db_act and db_act.physical_intensity in ["High", "Medium"]:
                    has_high_effort = True
                    
                    # Try to swap with a Low effort activity
                    best_low = None
                    best_low_score = -float('inf')
                    
                    for candidate in dest_data["activities"]:
                        if candidate.id in used_activities:
                            continue
                        if candidate.id in [x.item_id for x in day_schedule.activities]:
                            continue
                        if candidate.physical_intensity != "Low":
                            continue
                        if "wheelchair" in request.mobility_constraints and not candidate.accessibility:
                            continue
                            
                        interest_score = get_interest_score(candidate, request.interests)
                        dist_km = estimate_transit(sa.location, candidate.location, request.transport_mode)[2]
                        dist_factor = 10.0 / (1.0 + dist_km)
                        
                        total_score = interest_score * 3.0 + dist_factor
                        
                        if total_score > best_low_score:
                            best_low_score = total_score
                            best_low = candidate
                            
                    if best_low:
                        explanation_log.append(f"💤 Swapped strenuous **{db_act.name}** ({db_act.physical_intensity} Effort) with relaxing **{best_low.name}** (Low Effort).")
                        sa.item_id = best_low.id
                        sa.name = best_low.name
                        sa.description = f"[Low Effort] {best_low.description}"
                        sa.cost = best_low.cost
                        sa.location = best_low.location
                    else:
                        explanation_log.append(f"☕ Replaced intensive **{db_act.name}** with an extended cozy Coffee & Pastry break.")
                        sa.item_id = "rest_break"
                        sa.name = "Extended Coffee & Pastry Break"
                        sa.type = "rest_break"
                        sa.description = "Recharge your battery with warm beverages and artisanal local pastries in a highly-rated cafe."
                        sa.cost = 8.0
                        
            new_activities.append(sa)
            
        day_schedule.activities = new_activities
        
        # If schedule is very long, let's cut it off and return to hotel earlier!
        # Find if we have more than 3 activities, if so, we can drop the last one before dinner to return early
        activity_indices = [i for i, x in enumerate(day_schedule.activities) if x.type == "activity"]
        if len(activity_indices) > 2:
            last_act_idx = activity_indices[-1]
            last_act_name = day_schedule.activities[last_act_idx].name
            explanation_log.append(f"🏠 Dropped the final spot **{last_act_name}** to allow you to return to the hotel early and recover.")
            
            # Remove this last activity, and the transit preceding it
            trimmed = []
            for i, sa in enumerate(day_schedule.activities):
                if i == last_act_idx:
                    continue
                if i == last_act_idx - 1 and sa.type == "transit": # preceding transit
                    continue
                trimmed.append(sa)
            day_schedule.activities = trimmed
            
        rebuild_day_transit(day_schedule, new_itinerary.hotel, request.transport_mode, request.budget_level, dest_data["restaurants"])

    # 5. Recompute total costs
    total_cost = new_itinerary.hotel.price_per_night * len(new_itinerary.daily_schedules)
    for d_sched in new_itinerary.daily_schedules:
        # Sum activities cost in the new day schedule
        day_cost = 0.0
        for sa in d_sched.activities:
            day_cost += sa.cost
        d_sched.total_cost = round(day_cost, 2)
        total_cost += day_cost
        
    new_itinerary.total_cost = round(total_cost, 2)
    
    explanation_str = "\n".join(explanation_log)
    return new_itinerary, explanation_str


def rebuild_day_transit(
    day_schedule: DaySchedule, 
    hotel: Hotel, 
    transport_mode: str, 
    budget_level: str,
    restaurants: List[Restaurant]
):
    """
    Utility that takes a list of activities (with updated geolocations or items), 
    strips existing transit blocks, and re-inserts fresh, geometrically optimized 
    Transit steps and time slots.
    """
    # 1. Filter out all existing transits
    core_items = [sa for sa in day_schedule.activities if sa.type != "transit"]
    
    # 2. Re-sequence and reconstruct transits
    rebuilt_activities: List[ScheduledActivity] = []
    day_transits: List[TransitStep] = []
    
    current_hour = core_items[0].start_hour # Depart Hotel start time
    current_loc = hotel.location
    
    # Add Depart Hotel
    depart_hotel = core_items[0]
    depart_hotel.start_hour = current_hour
    depart_hotel.end_hour = current_hour
    depart_hotel.time_slot = f"{float_to_ampm(current_hour)}"
    rebuilt_activities.append(depart_hotel)
    
    for item in core_items[1:]:
        # Skip the final arrive hotel since we do that at the very end
        if item.name.startswith("Arrive") and item.type == "hotel":
            continue
            
        # Estimate transit from current location to this item
        dur, cost, dist = estimate_transit(current_loc, item.location, transport_mode)
        transit_end = current_hour + (dur / 60.0)
        
        # Schedule transit
        transit_slot = f"{format_time(current_hour)} - {format_time(transit_end)}"
        day_transits.append(TransitStep(
            from_name=current_loc.name,
            to_name=item.name,
            duration_mins=dur,
            distance_km=dist,
            mode=transport_mode,
            cost=cost,
            time_slot=transit_slot
        ))
        rebuilt_activities.append(ScheduledActivity(
            time_slot=transit_slot,
            start_hour=current_hour,
            end_hour=transit_end,
            item_id=f"transit_{item.item_id}",
            name=f"Travel to {item.name}",
            type="transit",
            description=f"Transit via {transport_mode} ({dist} km, ~{int(dur)} mins).",
            cost=cost,
            location=item.location
        ))
        
        current_hour = transit_end
        
        # Schedule the item itself
        dur_item = item.end_hour - item.start_hour
        # If it's a restaurant, its duration is already set, but if we shifted, let's keep it
        item_end = current_hour + dur_item
        
        item.start_hour = current_hour
        item.end_hour = item_end
        item.time_slot = f"{float_to_ampm(current_hour)} - {float_to_ampm(item_end)}"
        rebuilt_activities.append(item)
        
        current_loc = item.location
        current_hour = item_end
        
    # Add return to hotel transit
    dur, cost, dist = estimate_transit(current_loc, hotel.location, transport_mode)
    transit_end = current_hour + (dur / 60.0)
    transit_slot = f"{format_time(current_hour)} - {format_time(transit_end)}"
    
    day_transits.append(TransitStep(
        from_name=current_loc.name,
        to_name=hotel.name,
        duration_mins=dur,
        distance_km=dist,
        mode=transport_mode,
        cost=cost,
        time_slot=transit_slot
    ))
    rebuilt_activities.append(ScheduledActivity(
        time_slot=transit_slot,
        start_hour=current_hour,
        end_hour=transit_end,
        item_id=f"transit_{hotel.id}",
        name=f"Return to {hotel.name}",
        type="transit",
        description=f"Head back to your base hotel via {transport_mode} ({dist} km).",
        cost=cost,
        location=hotel.location
    ))
    
    current_hour = transit_end
    
    # Add final Arrive Hotel
    rebuilt_activities.append(ScheduledActivity(
        time_slot=f"{float_to_ampm(current_hour)}",
        start_hour=current_hour,
        end_hour=current_hour,
        item_id=hotel.id,
        name=f"Arrive {hotel.name}",
        type="hotel",
        description="Rest up and prepare for tomorrow's experiences!",
        cost=0.0,
        location=hotel.location
    ))
    
    day_schedule.activities = rebuilt_activities
    day_schedule.transit_steps = day_transits
