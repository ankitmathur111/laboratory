import datetime
from typing import Dict, List, Set, Tuple, Optional
from src.models import (
    TripRequest, Itinerary, DaySchedule, ScheduledActivity, 
    TransitStep, Activity, Restaurant, Hotel, Location
)
from src.database import DESTINATIONS
from src.utils import estimate_transit, format_time, float_to_ampm

def get_interest_score(activity: Activity, user_interests: Dict[str, float]) -> float:
    """
    Calculate the interest match score of an activity based on user preferences.
    """
    score = 0.0
    for cat in activity.categories:
        if cat in user_interests:
            score += user_interests[cat]
    
    # Add a minor rating boost to prefer highly rated activities when interest is equal
    score += activity.rating * 0.05
    return score

def find_best_hotel(hotels: List[Hotel], budget_level: str) -> Hotel:
    """
    Find the best hotel matching the budget level.
    If no exact match, falls back to the closest available budget tier.
    """
    matched = [h for h in hotels if h.budget_tier == budget_level]
    if matched:
        # Return the highest-rated hotel in that tier
        return max(matched, key=lambda x: x.rating)
    
    # Fallbacks
    if budget_level == "Luxury":
        matched = [h for h in hotels if h.budget_tier == "Mid-range"]
    elif budget_level == "Budget":
        matched = [h for h in hotels if h.budget_tier == "Mid-range"]
    
    if matched:
        return max(matched, key=lambda x: x.rating)
    
    # Absolute fallback
    return hotels[0]

def filter_restaurants(restaurants: List[Restaurant], dietary_constraints: List[str], budget_level: str) -> List[Restaurant]:
    """
    Filter restaurants based on dietary constraints and budget preference.
    """
    filtered = []
    for r in restaurants:
        # Check dietary compatibility
        # Every user dietary constraint must be supported by the restaurant tags
        diet_match = True
        for constraint in dietary_constraints:
            if constraint.lower() not in [tag.lower() for tag in r.dietary_tags]:
                diet_match = False
                break
        
        if diet_match:
            filtered.append(r)
            
    # If filtering strictly left nothing, fall back to all restaurants but issue warning
    if not filtered:
        return restaurants
        
    return filtered

def find_nearest_restaurant(
    current_loc: Location, 
    restaurants: List[Restaurant], 
    budget_level: str, 
    transport_mode: str
) -> Restaurant:
    """
    Find the best nearby restaurant based on current coordinates, transport mode, and budget.
    """
    best_rest = None
    best_score = -float('inf')
    
    for r in restaurants:
        dur_mins, cost, dist_km = estimate_transit(current_loc, r.location, transport_mode)
        
        # Scoring: prefers closer restaurants + budget matches + higher rating
        budget_multiplier = 1.0
        if r.budget_tier == budget_level:
            budget_multiplier = 2.0
            
        distance_score = 10.0 / (1.0 + dist_km)
        rating_score = r.rating * 1.5
        
        total_score = distance_score + rating_score + (budget_multiplier * 5.0)
        
        if total_score > best_score:
            best_score = total_score
            best_rest = r
            
    return best_rest if best_rest else restaurants[0]

def generate_itinerary(request: TripRequest) -> Itinerary:
    """
    Core planner engine. Generates a fully custom, optimized day-by-day itinerary
    based on user constraints, preferences, and geographical layout.
    """
    dest_name = request.destination
    if dest_name not in DESTINATIONS:
        raise ValueError(f"Destination '{dest_name}' is not supported yet.")
        
    dest_data = DESTINATIONS[dest_name]
    
    # 1. Select Hotel
    hotel = find_best_hotel(dest_data["hotels"], request.budget_level)
    
    # 2. Filter Activities based on Mobility constraints
    allowed_activities: List[Activity] = []
    for act in dest_data["activities"]:
        if "wheelchair" in request.mobility_constraints and not act.accessibility:
            # Skip if wheelchair-bound but activity is not accessible
            continue
        allowed_activities.append(act)
        
    # 3. Filter Restaurants by diet
    allowed_restaurants = filter_restaurants(dest_data["restaurants"], request.dietary_constraints, request.budget_level)
    
    # 4. Schedule parameters
    # Adjust daily operational hours based on pace
    if request.pace == "Relaxed":
        day_start = 9.5  # 9:30 AM
        day_end = 16.5   # 4:30 PM
        max_spots = 3
    elif request.pace == "Moderate":
        day_start = 9.0  # 9:00 AM
        day_end = 18.5   # 6:30 PM
        max_spots = 5
    else:  # "Packed"
        day_start = 8.5  # 8:30 AM
        day_end = 21.0   # 9:00 PM
        max_spots = 7
        
    used_activities: Set[str] = set()
    daily_schedules: List[DaySchedule] = []
    total_trip_cost = hotel.price_per_night * request.duration_days
    
    # 5. Build Day-by-Day Schedules
    for day in range(1, request.duration_days + 1):
        day_date = request.start_date + datetime.timedelta(days=day-1)
        day_date_str = day_date.strftime("%Y-%m-%d")
        
        current_loc = hotel.location
        current_hour = day_start
        
        day_activities: List[ScheduledActivity] = []
        day_transits: List[TransitStep] = []
        day_cost = 0.0
        
        # Add morning hotel departure
        day_activities.append(ScheduledActivity(
            time_slot=f"{float_to_ampm(current_hour)}",
            start_hour=current_hour,
            end_hour=current_hour,
            item_id=hotel.id,
            name=f"Depart {hotel.name}",
            type="hotel",
            description="Start your day's journey from the hotel lobby.",
            cost=0.0,
            location=hotel.location
        ))
        
        spots_visited_today = 0
        lunch_scheduled = False
        dinner_scheduled = False
        
        while current_hour < day_end and spots_visited_today < max_spots:
            
            # A. LUNCH CHECK (around 12:00 - 13:30)
            if current_hour >= 12.0 and not lunch_scheduled:
                rest = find_nearest_restaurant(current_loc, allowed_restaurants, request.budget_level, request.transport_mode)
                dur, cost, dist = estimate_transit(current_loc, rest.location, request.transport_mode)
                
                # Add transit to lunch
                transit_slot = f"{format_time(current_hour)} - {format_time(current_hour + dur/60)}"
                day_transits.append(TransitStep(
                    from_name=current_loc.name,
                    to_name=rest.name,
                    duration_mins=dur,
                    distance_km=dist,
                    mode=request.transport_mode,
                    cost=cost,
                    time_slot=transit_slot
                ))
                day_activities.append(ScheduledActivity(
                    time_slot=transit_slot,
                    start_hour=current_hour,
                    end_hour=current_hour + dur/60,
                    item_id=f"transit_{rest.id}",
                    name=f"Travel to {rest.name}",
                    type="transit",
                    description=f"Transit via {request.transport_mode} ({dist} km, ~{int(dur)} mins).",
                    cost=cost,
                    location=rest.location
                ))
                day_cost += cost
                current_hour += dur/60
                
                # Add lunch
                lunch_end = current_hour + 1.25 # 1 hour 15 mins
                lunch_cost = 15.0 if request.budget_level == "Budget" else (35.0 if request.budget_level == "Mid-range" else 90.0)
                lunch_slot = f"{float_to_ampm(current_hour)} - {float_to_ampm(lunch_end)}"
                day_activities.append(ScheduledActivity(
                    time_slot=lunch_slot,
                    start_hour=current_hour,
                    end_hour=lunch_end,
                    item_id=rest.id,
                    name=f"Lunch at {rest.name}",
                    type="restaurant",
                    description=f"Enjoy local {rest.cuisine} cuisine. Highly rated at {rest.rating} stars.",
                    cost=lunch_cost,
                    location=rest.location
                ))
                day_cost += lunch_cost
                current_loc = rest.location
                current_hour = lunch_end
                lunch_scheduled = True
                continue
                
            # B. DINNER CHECK (around 18:30 - 20:00)
            if current_hour >= 18.25 and not dinner_scheduled and request.pace == "Packed":
                rest = find_nearest_restaurant(current_loc, allowed_restaurants, request.budget_level, request.transport_mode)
                dur, cost, dist = estimate_transit(current_loc, rest.location, request.transport_mode)
                
                # Add transit to dinner
                transit_slot = f"{format_time(current_hour)} - {format_time(current_hour + dur/60)}"
                day_transits.append(TransitStep(
                    from_name=current_loc.name,
                    to_name=rest.name,
                    duration_mins=dur,
                    distance_km=dist,
                    mode=request.transport_mode,
                    cost=cost,
                    time_slot=transit_slot
                ))
                day_activities.append(ScheduledActivity(
                    time_slot=transit_slot,
                    start_hour=current_hour,
                    end_hour=current_hour + dur/60,
                    item_id=f"transit_{rest.id}",
                    name=f"Travel to {rest.name}",
                    type="transit",
                    description=f"Transit via {request.transport_mode} ({dist} km, ~{int(dur)} mins).",
                    cost=cost,
                    location=rest.location
                ))
                day_cost += cost
                current_hour += dur/60
                
                # Add dinner
                dinner_end = current_hour + 1.5 # 1.5 hours
                dinner_cost = 25.0 if request.budget_level == "Budget" else (50.0 if request.budget_level == "Mid-range" else 150.0)
                dinner_slot = f"{float_to_ampm(current_hour)} - {float_to_ampm(dinner_end)}"
                day_activities.append(ScheduledActivity(
                    time_slot=dinner_slot,
                    start_hour=current_hour,
                    end_hour=dinner_end,
                    item_id=rest.id,
                    name=f"Dinner at {rest.name}",
                    type="restaurant",
                    description=f"Relax with a fine evening of {rest.cuisine} dishes. Rating: {rest.rating}/5.",
                    cost=dinner_cost,
                    location=rest.location
                ))
                day_cost += dinner_cost
                current_loc = rest.location
                current_hour = dinner_end
                dinner_scheduled = True
                continue

            # C. CHOOSE NEXT BEST ACTIVITY (Nearest-Neighbor TSP heuristic with interest scoring)
            best_act = None
            best_act_score = -float('inf')
            best_transit_metrics = (0.0, 0.0, 0.0) # dur, cost, dist
            
            for act in allowed_activities:
                if act.id in used_activities:
                    continue
                
                # Check transit duration
                dur_mins, t_cost, dist_km = estimate_transit(current_loc, act.location, request.transport_mode)
                arrival_hour = current_hour + (dur_mins / 60.0)
                departure_hour = arrival_hour + act.avg_duration
                
                # Check opening hour constraints
                # Some places are open 24 hours (start_hour=0, end_hour=24)
                if arrival_hour < act.start_hour or departure_hour > act.end_hour:
                    continue
                    
                # Check if it spills past our end of day
                if departure_hour > day_end:
                    continue
                    
                # Calculate scores
                interest_score = get_interest_score(act, request.interests)
                # Distance penalty: closer is better
                distance_factor = 12.0 / (1.0 + dist_km)
                
                total_score = interest_score * 3.0 + distance_factor
                
                if total_score > best_act_score:
                    best_act_score = total_score
                    best_act = act
                    best_transit_metrics = (dur_mins, t_cost, dist_km)
            
            if best_act:
                dur, cost, dist = best_transit_metrics
                
                # Schedule transit to activity
                transit_slot = f"{format_time(current_hour)} - {format_time(current_hour + dur/60)}"
                day_transits.append(TransitStep(
                    from_name=current_loc.name,
                    to_name=best_act.name,
                    duration_mins=dur,
                    distance_km=dist,
                    mode=request.transport_mode,
                    cost=cost,
                    time_slot=transit_slot
                ))
                day_activities.append(ScheduledActivity(
                    time_slot=transit_slot,
                    start_hour=current_hour,
                    end_hour=current_hour + dur/60,
                    item_id=f"transit_{best_act.id}",
                    name=f"Travel to {best_act.name}",
                    type="transit",
                    description=f"Transit via {request.transport_mode} ({dist} km, ~{int(dur)} mins).",
                    cost=cost,
                    location=best_act.location
                ))
                day_cost += cost
                current_hour += dur/60
                
                # Schedule activity
                act_end = current_hour + best_act.avg_duration
                act_slot = f"{float_to_ampm(current_hour)} - {float_to_ampm(act_end)}"
                
                # Check physical intensity description
                intensity_badge = "🟢 Low Effort" if best_act.physical_intensity == "Low" else ("🟡 Moderate Effort" if best_act.physical_intensity == "Medium" else "🔴 High Effort")
                accessibility_badge = "♿ Accessible" if best_act.accessibility else "⚠️ Steps Required"
                
                day_activities.append(ScheduledActivity(
                    time_slot=act_slot,
                    start_hour=current_hour,
                    end_hour=act_end,
                    item_id=best_act.id,
                    name=best_act.name,
                    type="activity",
                    description=f"{best_act.description} | {intensity_badge} | {accessibility_badge}",
                    cost=best_act.cost,
                    location=best_act.location
                ))
                
                day_cost += best_act.cost
                used_activities.add(best_act.id)
                current_loc = best_act.location
                current_hour = act_end
                spots_visited_today += 1
                
            else:
                # If no activities can fit, but we are well below day end, let's take a rest break!
                if current_hour < day_end - 1.5:
                    rest_end = current_hour + 1.0
                    rest_slot = f"{float_to_ampm(current_hour)} - {float_to_ampm(rest_end)}"
                    day_activities.append(ScheduledActivity(
                        time_slot=rest_slot,
                        start_hour=current_hour,
                        end_hour=rest_end,
                        item_id="rest_break",
                        name="Relaxation & Coffee Break",
                        type="rest_break",
                        description="Take a moment to unwind at a cozy local cafe, review photos, and recharge your energy.",
                        cost=5.0,
                        location=current_loc
                    ))
                    day_cost += 5.0
                    current_hour = rest_end
                else:
                    # Time to end the day
                    break
        
        # D. LATE DINNER CHECK (if pace is relaxed/moderate and dinner not scheduled yet)
        if not dinner_scheduled:
            rest = find_nearest_restaurant(current_loc, allowed_restaurants, request.budget_level, request.transport_mode)
            dur, cost, dist = estimate_transit(current_loc, rest.location, request.transport_mode)
            
            # Add transit to dinner
            transit_slot = f"{format_time(current_hour)} - {format_time(current_hour + dur/60)}"
            day_transits.append(TransitStep(
                from_name=current_loc.name,
                to_name=rest.name,
                duration_mins=dur,
                distance_km=dist,
                mode=request.transport_mode,
                cost=cost,
                time_slot=transit_slot
            ))
            day_activities.append(ScheduledActivity(
                time_slot=transit_slot,
                start_hour=current_hour,
                end_hour=current_hour + dur/60,
                item_id=f"transit_{rest.id}",
                name=f"Travel to {rest.name}",
                type="transit",
                description=f"Transit via {request.transport_mode} ({dist} km, ~{int(dur)} mins).",
                cost=cost,
                location=rest.location
            ))
            day_cost += cost
            current_hour += dur/60
            
            # Add dinner
            dinner_end = current_hour + 1.25
            dinner_cost = 20.0 if request.budget_level == "Budget" else (40.0 if request.budget_level == "Mid-range" else 120.0)
            dinner_slot = f"{float_to_ampm(current_hour)} - {float_to_ampm(dinner_end)}"
            day_activities.append(ScheduledActivity(
                time_slot=dinner_slot,
                start_hour=current_hour,
                end_hour=dinner_end,
                item_id=rest.id,
                name=f"Dinner at {rest.name}",
                type="restaurant",
                description=f"Savor {rest.cuisine} flavors. Highly recommended dinner stop.",
                cost=dinner_cost,
                location=rest.location
            ))
            day_cost += dinner_cost
            current_loc = rest.location
            current_hour = dinner_end
            dinner_scheduled = True
            
        # E. RETURN TO HOTEL
        dur, cost, dist = estimate_transit(current_loc, hotel.location, request.transport_mode)
        transit_slot = f"{format_time(current_hour)} - {format_time(current_hour + dur/60)}"
        day_transits.append(TransitStep(
            from_name=current_loc.name,
            to_name=hotel.name,
            duration_mins=dur,
            distance_km=dist,
            mode=request.transport_mode,
            cost=cost,
            time_slot=transit_slot
        ))
        day_activities.append(ScheduledActivity(
            time_slot=transit_slot,
            start_hour=current_hour,
            end_hour=current_hour + dur/60,
            item_id=f"transit_{hotel.id}",
            name=f"Return to {hotel.name}",
            type="transit",
            description=f"Head back to your base hotel via {request.transport_mode} ({dist} km).",
            cost=cost,
            location=hotel.location
        ))
        day_cost += cost
        current_hour += dur/60
        
        # Complete day
        day_activities.append(ScheduledActivity(
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
        
        daily_schedules.append(DaySchedule(
            day_number=day,
            date_str=day_date_str,
            activities=day_activities,
            transit_steps=day_transits,
            total_cost=round(day_cost, 2)
        ))
        
        total_trip_cost += day_cost

    # 6. Final Summary
    summary_text = (
        f"A customized {request.duration_days}-day trip to {dest_name} planned for a "
        f"{request.budget_level} budget at a {request.pace} pace. Base stay at the beautiful "
        f"{hotel.name} ({hotel.rating}★)."
    )

    return Itinerary(
        trip_request=request,
        hotel=hotel,
        daily_schedules=daily_schedules,
        total_cost=round(total_trip_cost, 2),
        summary=summary_text
    )
