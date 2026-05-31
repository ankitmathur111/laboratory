import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import pydeck as pdk

from src.models import TripRequest, Itinerary, DaySchedule
from src.database import DESTINATIONS
from src.planner import generate_itinerary
from src.replanner import replan_itinerary
from src.utils import inject_premium_styles, float_to_ampm

# Configure page metadata and layout
st.set_page_config(
    page_title="VoyageFlow | Dynamic Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply premium visual design system
inject_premium_styles()

# Initialize session states for storing itineraries and simulated conditions
if "itinerary" not in st.session_state:
    st.session_state.itinerary = None
if "replanned_itinerary" not in st.session_state:
    st.session_state.replanned_itinerary = None
if "current_event" not in st.session_state:
    st.session_state.current_event = None
if "event_explanation" not in st.session_state:
    st.session_state.event_explanation = ""

# App header layout
col_header_title, col_header_logo = st.columns([5, 1])
with col_header_title:
    st.markdown("<h1 class='glow-text' style='font-size: 3rem; margin-bottom: 0px;'>VOYAGEFLOW</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.1rem; color: rgba(11, 27, 61, 0.7); margin-top: 5px; margin-bottom: 25px;'>Spatiotemporal AI Travel Planner with Real-Time Dynamic Rerouting | <strong>Prompt Wars May 2026 Submission by Ankit Mathur</strong></p>", unsafe_allow_html=True)

# -------------------------------------------------------------
# SIDEBAR - THE PREFERENCE & CONSTRAINT HUB
# -------------------------------------------------------------
st.sidebar.markdown("<h2 style='color:#FF3366; font-weight:600;'>Trip Configurator</h2>", unsafe_allow_html=True)

selected_dest = st.sidebar.selectbox(
    "Destination",
    options=list(DESTINATIONS.keys()),
    index=0
)

# Date and duration settings
start_date = st.sidebar.date_input("Start Date", datetime.date.today())
duration_days = st.sidebar.slider("Trip Duration (Days)", min_value=1, max_value=7, value=3)

# Preferences
st.sidebar.markdown("<hr style='opacity:0.1; margin: 15px 0;'/>", unsafe_allow_html=True)
st.sidebar.markdown("<h4 style='font-weight:500;'>Traveler Vibe</h4>", unsafe_allow_html=True)

budget_level = st.sidebar.radio(
    "Budget Tier",
    options=["Budget", "Mid-range", "Luxury"],
    index=1
)

transport_mode = st.sidebar.radio(
    "Preferred Transportation",
    options=["Public Transit", "Walking", "Rental Car", "Taxi"],
    index=0
)

pace = st.sidebar.radio(
    "Daily Pace",
    options=["Relaxed", "Moderate", "Packed"],
    index=1,
    help="Relaxed: ~2-3 spots | Moderate: ~4-5 spots | Packed: ~6+ spots"
)

# Constraints (Dietary & Mobility)
st.sidebar.markdown("<hr style='opacity:0.1; margin: 15px 0;'/>", unsafe_allow_html=True)
st.sidebar.markdown("<h4 style='font-weight:500;'>Constraints & Health</h4>", unsafe_allow_html=True)

mobility_checks = st.sidebar.checkbox("Wheelchair Accessible Required")
mobility_constraints = ["wheelchair"] if mobility_checks else []

dietary_options = ["Vegetarian", "Vegan", "Halal", "Gluten-Free"]
selected_diets = []
for diet in dietary_options:
    if st.sidebar.checkbox(diet):
        selected_diets.append(diet.lower())

# Personalized Interests (Weights)
st.sidebar.markdown("<hr style='opacity:0.1; margin: 15px 0;'/>", unsafe_allow_html=True)
with st.sidebar.expander("⭐ Tailor Your Interests", expanded=False):
    st.markdown("<p style='font-size:0.85rem; color:rgba(255,255,255,0.6);'>Drag sliders to prioritize activity categories:</p>", unsafe_allow_html=True)
    interest_culture = st.slider("Culture & History", 0.0, 1.0, 0.8)
    interest_nature = st.slider("Nature & Outdoors", 0.0, 1.0, 0.5)
    interest_food = st.slider("Food & Culinary", 0.0, 1.0, 0.7)
    interest_shopping = st.slider("Shopping", 0.0, 1.0, 0.3)
    interest_adventure = st.slider("Adventure & Thrills", 0.0, 1.0, 0.4)
    interest_relaxation = st.slider("Relaxation & Wellness", 0.0, 1.0, 0.6)
    interest_nightlife = st.slider("Nightlife & Entertainment", 0.0, 1.0, 0.4)

interests = {
    "Culture": interest_culture,
    "Nature": interest_nature,
    "Food": interest_food,
    "Shopping": interest_shopping,
    "Adventure": interest_adventure,
    "Relaxation": interest_relaxation,
    "Nightlife": interest_nightlife
}

st.sidebar.markdown("<br/>", unsafe_allow_html=True)
generate_btn = st.sidebar.button("✈️ GENERATE TRIP PLAN", use_container_width=True, type="primary")

# Execute planner on button press
if generate_btn:
    # Build the TripRequest object
    req = TripRequest(
        destination=selected_dest,
        start_date=start_date,
        duration_days=duration_days,
        budget_level=budget_level,
        pace=pace,
        interests=interests,
        dietary_constraints=selected_diets,
        mobility_constraints=mobility_constraints,
        transport_mode=transport_mode
    )
    
    # Generate itinerary
    with st.spinner("VoyageFlow engine calculating optimal spatiotemporal routes..."):
        try:
            itinerary = generate_itinerary(req)
            st.session_state.itinerary = itinerary
            st.session_state.replanned_itinerary = None  # Clear previous disruptions
            st.session_state.current_event = None
            st.session_state.event_explanation = ""
            st.toast(f"Trip to {selected_dest} successfully generated!", icon="✅")
        except Exception as e:
            st.error(f"Error generating itinerary: {str(e)}")


# -------------------------------------------------------------
# MAIN APP WORKSPACE
# -------------------------------------------------------------
active_itinerary: Itinerary = st.session_state.replanned_itinerary if st.session_state.replanned_itinerary else st.session_state.itinerary

if active_itinerary is None:
    # ONBOARDING / WELCOME STATE
    st.markdown("""
        <div class='glass-card' style='text-align: center; padding: 40px 20px; background: #F8FAFC; border: 1px solid rgba(11, 27, 61, 0.08);'>
            <span style='font-size: 4rem;'>🧭</span>
            <h2 style='margin-top:15px; color:#1E3A8A;'>Welcome to VoyageFlow!</h2>
            <p style='font-size: 1.1rem; color: #334155; max-width: 700px; margin: 10px auto;'>
                Configure your destination and preferences in the sidebar to generate a premium travel itinerary. 
                VoyageFlow optimizes geographic routing, integrates meal stops according to your dietary restrictions, 
                and features real-time update simulators (rain storms, flight delays, fatigue) to show how it dynamically adapts!
            </p>
            <div style='margin-top:30px; display:flex; justify-content:center; gap: 40px; flex-wrap:wrap;'>
                <div style='background:#FFFFFF; padding:20px; border-radius:12px; border:1px solid rgba(11, 27, 61, 0.08); width:180px; box-shadow: 0 4px 15px rgba(11, 27, 61, 0.02);'>
                    <div style='font-size:2rem;'>🗺️</div>
                    <div style='font-weight:600; margin-top:8px; color:#0B1B3D;'>Spatial Optimization</div>
                    <div style='font-size:0.85rem; color:#475569; margin-top:4px;'>Minimizes travel time using coordinate routing.</div>
                </div>
                <div style='background:#FFFFFF; padding:20px; border-radius:12px; border:1px solid rgba(11, 27, 61, 0.08); width:180px; box-shadow: 0 4px 15px rgba(11, 27, 61, 0.02);'>
                    <div style='font-size:2rem;'>🕒</div>
                    <div style='font-weight:600; margin-top:8px; color:#0B1B3D;'>Time-Window Checks</div>
                    <div style='font-size:0.85rem; color:#475569; margin-top:4px;'>Strict verification of opening hours.</div>
                </div>
                <div style='background:#FFFFFF; padding:20px; border-radius:12px; border:1px solid rgba(11, 27, 61, 0.08); width:180px; box-shadow: 0 4px 15px rgba(11, 27, 61, 0.02);'>
                    <div style='font-size:2rem;'>⚡</div>
                    <div style='font-weight:600; margin-top:8px; color:#0B1B3D;'>Dynamic Replanning</div>
                    <div style='font-size:0.85rem; color:#475569; margin-top:4px;'>Simulate delays, storm alerts, and re-route instantly.</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    # 1. NOTIFICATION BANNER IF DYNAMIC REPLANNING ACTIVE
    if st.session_state.current_event:
        st.markdown(f"""
            <div class="alert-banner banner-warning">
                <div style="font-size: 1.6rem; margin-right: 15px;">⚡</div>
                <div>
                    <strong style="font-size: 1.1rem; color: #FFCC00;">Real-Time Updates Engaged: {st.session_state.current_event.replace('_', ' ').title()}</strong>
                    <div style="margin-top: 5px; font-size: 0.95rem;">{st.session_state.event_explanation}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 2. OVERVIEW PANEL (Summary, Metrics & Budget breakdown)
    col_summary, col_budget = st.columns([3, 2])
    
    with col_summary:
        st.markdown(f"""
            <div class='glass-card' style='height: 100%; display: flex; flex-direction: column; justify-content: center; background: #F8FAFC;'>
                <h3 style='margin:0 0 10px 0; color:#FF3366;'>📋 Trip Itinerary Overview</h3>
                <h4 style='margin:0 0 15px 0; font-weight: 500; color: #0B1B3D;'>{active_itinerary.summary}</h4>
                <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 10px;'>
                    <div class='stMetric'>
                        <span style='font-size: 0.85rem; color: #475569;'>TOTAL ESTIMATED COST</span>
                        <h3 style='margin: 5px 0 0 0; color: #059669;'>${active_itinerary.total_cost:,.2f}</h3>
                    </div>
                    <div class='stMetric'>
                        <span style='font-size: 0.85rem; color: #475569;'>BASE STAY HOTEL</span>
                        <h4 style='margin: 8px 0 0 0; font-size:1.0rem; color: #1E3A8A; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;'>{active_itinerary.hotel.name}</h4>
                    </div>
                    <div class='stMetric'>
                        <span style='font-size: 0.85rem; color: #475569;'>TRANSPORT MODE</span>
                        <h3 style='margin: 5px 0 0 0; color: #D97706; font-size: 1.15rem; font-weight:600;'>{active_itinerary.trip_request.transport_mode}</h3>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_budget:
        # Calculate budget components
        hotel_cost = active_itinerary.hotel.price_per_night * len(active_itinerary.daily_schedules)
        activity_cost = 0.0
        food_cost = 0.0
        transit_cost = 0.0
        
        for ds in active_itinerary.daily_schedules:
            for sa in ds.activities:
                if sa.type == "activity":
                    activity_cost += sa.cost
                elif sa.type == "restaurant":
                    food_cost += sa.cost
                elif sa.type == "transit":
                    transit_cost += sa.cost
                elif sa.type == "rest_break":
                    food_cost += sa.cost  # café breaks classified as food share
                    
        budget_df = pd.DataFrame({
            "Category": ["Hotel Stay", "Activities/Tickets", "Dining/Cafes", "Transit Fares"],
            "Cost": [hotel_cost, activity_cost, food_cost, transit_cost]
        })
        
        fig_budget = px.pie(
            budget_df, 
            values="Cost", 
            names="Category", 
            hole=0.5,
            color_discrete_sequence=["#6622FF", "#00C8FF", "#00FF87", "#FF9933"],
            height=200
        )
        fig_budget.update_layout(
            margin=dict(l=0, r=0, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#0B1B3D",
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="right", x=1.1)
        )
        
        st.markdown("<div class='glass-card' style='padding:15px; height: 100%;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin:0 0 8px 0; color:#FF9933; font-size:1.0rem; text-align:center;'>Budget Breakdown</h4>", unsafe_allow_html=True)
        st.plotly_chart(fig_budget, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. SPATIOTEMPORAL DETAILED TIMELINE & ROUTE MAPS
    st.markdown("<br/><h3 style='color:#00C8FF; font-weight:600; margin-bottom:15px;'>📍 Day-by-Day Journey Planner</h3>", unsafe_allow_html=True)
    
    # Create Tabs for each day
    days_labels = [f"📅 Day {ds.day_number} ({ds.date_str})" for ds in active_itinerary.daily_schedules]
    tabs = st.tabs(days_labels)
    
    for idx, tab in enumerate(tabs):
        with tab:
            selected_day: DaySchedule = active_itinerary.daily_schedules[idx]
            
            col_timeline, col_map = st.columns([11, 10])
            
            # --- LEFT: Visual HTML Timeline ---
            with col_timeline:
                st.markdown(f"<h4>Timeline Schedule - Day {selected_day.day_number}</h4>", unsafe_allow_html=True)
                st.markdown("<div class='timeline-container'>", unsafe_allow_html=True)
                
                for sa in selected_day.activities:
                    # Assign badge css color class
                    badge_class = "badge-activity"
                    if sa.type == "hotel":
                        badge_class = "badge-hotel"
                    elif sa.type == "restaurant":
                        badge_class = "badge-restaurant"
                    elif sa.type == "transit":
                        badge_class = "badge-transit"
                    elif sa.type == "rest_break":
                        badge_class = "badge-rest"
                        
                    meta_div = f"<div class='item-meta'>💵 Cost: ${sa.cost:.2f} | 📍 Location: {sa.location.name}</div>" if sa.type not in ["transit"] else ""
                    card_html = (
                        f"<div class='timeline-item'>"
                        f"<span class='timeline-badge {badge_class}'>{sa.type}</span>"
                        f"<span style='float: right; font-weight: 500; font-size:0.9rem; color: #D97706;'>{sa.time_slot}</span>"
                        f"<div class='item-title'>{sa.name}</div>"
                        f"{meta_div}"
                        f"<div class='item-desc'>{sa.description}</div>"
                        f"</div>"
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:right; font-weight:500; color:#059669; margin-top:10px;'>Day Total Expenses: ${selected_day.total_cost:.2f}</div>", unsafe_allow_html=True)
            
            # --- RIGHT: Geographic PyDeck Map ---
            with col_map:
                st.markdown("<h4>Route Map (3D Geo-Visualizer)</h4>", unsafe_allow_html=True)
                
                # Gather location points for this day
                map_points = []
                path_coords = []
                
                for sa in selected_day.activities:
                    if sa.type in ["activity", "restaurant", "hotel"] and not sa.name.startswith("Depart"):
                        color = [255, 51, 102] if sa.type == "activity" else ([5, 150, 105] if sa.type == "restaurant" else [102, 34, 255])
                        
                        map_points.append({
                            "name": sa.name,
                            "lat": sa.location.lat,
                            "lon": sa.location.lon,
                            "type": sa.type,
                            "color": color,
                            "radius": 150 if sa.type == "hotel" else 80
                        })
                        
                    if sa.type != "transit":
                        path_coords.append([sa.location.lon, sa.location.lat])
                
                # Ensure we have coordinates to display
                if map_points:
                    df_points = pd.DataFrame(map_points)
                    
                    # Target center based on coordinates
                    avg_lat = df_points["lat"].mean()
                    avg_lon = df_points["lon"].mean()
                    
                    # Create scatter layer for dots
                    scatter_layer = pdk.Layer(
                        "ScatterplotLayer",
                        df_points,
                        get_position="[lon, lat]",
                        get_color="color",
                        get_radius="radius",
                        pickable=True,
                        radius_scale=1.0,
                        radius_min_pixels=6,
                        radius_max_pixels=15
                    )
                    
                    # Create PathLayer for connecting lines
                    path_data = [{"path": path_coords, "color": [255, 153, 51, 170]}]
                    path_layer = pdk.Layer(
                        "PathLayer",
                        path_data,
                        get_path="path",
                        get_color="color",
                        width_min_pixels=3,
                        width_max_pixels=6,
                        pickable=True
                    )
                    
                    # Text Labels Layer
                    text_layer = pdk.Layer(
                        "TextLayer",
                        df_points,
                        get_position="[lon, lat]",
                        get_text="name",
                        get_color="[11, 27, 61, 240]",
                        get_size=13,
                        get_alignment_baseline="'bottom'",
                        get_pixel_offset="[0, -10]",
                        pickable=False
                    )
                    
                    # Build deck
                    deck = pdk.Deck(
                        layers=[path_layer, scatter_layer, text_layer],
                        initial_view_state=pdk.ViewState(
                            latitude=avg_lat,
                            longitude=avg_lon,
                            zoom=11.5,
                            pitch=40
                        ),
                        map_style="mapbox://styles/mapbox/light-v9",
                        tooltip={"html": "<b>Location:</b> {name}<br/><b>Type:</b> {type}"}
                    )
                    
                    st.pydeck_chart(deck, use_container_width=True)
                else:
                    st.warning("No geographical coordinates available for map rendering.")

    # 4. SIMULATION CONTROL CENTER
    st.markdown("<br/><hr style='opacity:0.1;'/><br/>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#FF9933; font-weight:600; margin-bottom:15px;'>⚡ Real-Time Trip Disruption Simulator</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.95rem; color:#334155;'>Trip disruptions are an inevitable part of travel. VoyageFlow handles sudden real-world events by recalculating paths, swapping slots, and re-satisfying constraints dynamically. Test the simulation engines below:</p>", unsafe_allow_html=True)
    
    col_sim_1, col_sim_2, col_sim_3, col_sim_4 = st.columns(4)
    
    with col_sim_1:
        st.markdown("<div class='glass-card' style='padding:15px; height:100%; text-align:center;'>", unsafe_allow_html=True)
        st.markdown("🌧️ <h4 style='color:#0B1B3D;'>Torrential Rain Storm</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8rem; color:#475569; min-height:45px;'>Scans remaining items, replaces outdoor sights with indoor ones and updates route maps.</p>", unsafe_allow_html=True)
        rain_btn = st.button("Simulate Heavy Rain", use_container_width=True)
        if rain_btn:
            new_it, exp = replan_itinerary(st.session_state.itinerary, 1, "weather_rain", {})
            st.session_state.replanned_itinerary = new_it
            st.session_state.current_event = "weather_rain"
            st.session_state.event_explanation = exp
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_sim_2:
        st.markdown("<div class='glass-card' style='padding:15px; height:100%; text-align:center;'>", unsafe_allow_html=True)
        st.markdown("⏱️ <h4 style='color:#0B1B3D;'>Transit & Flight Delay</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8rem; color:#475569; min-height:35px;'>Choose delay hours. Shifts the subsequent timeline and drops spots that conflict with closing hours.</p>", unsafe_allow_html=True)
        delay_hrs_input = st.slider("Delay Duration (Hrs)", 1.0, 4.0, 2.0, 0.5)
        delay_btn = st.button("Inject Transit Delay", use_container_width=True)
        if delay_btn:
            new_it, exp = replan_itinerary(st.session_state.itinerary, 1, "transit_delay", {"delay_hours": delay_hrs_input})
            st.session_state.replanned_itinerary = new_it
            st.session_state.current_event = "transit_delay"
            st.session_state.event_explanation = exp
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_sim_3:
        st.markdown("<div class='glass-card' style='padding:15px; height:100%; text-align:center;'>", unsafe_allow_html=True)
        st.markdown("🚧 <h4 style='color:#0B1B3D;'>Attraction Closure</h4>", unsafe_allow_html=True)
        
        # Pull active activities for Day 1 to allow selective closure
        day_1_activities = [sa for sa in st.session_state.itinerary.daily_schedules[0].activities if sa.type == "activity"]
        options_names = [a.name for a in day_1_activities]
        
        if options_names:
            st.markdown("<p style='font-size:0.8rem; color:#475569; min-height:35px;'>Select an active landmark to simulate a closure. Swaps with nearby options.</p>", unsafe_allow_html=True)
            selected_close_name = st.selectbox("Landmark", options=options_names, index=0)
            close_btn = st.button("Force Closure", use_container_width=True)
            if close_btn:
                # Find ID
                target_sa = next((x for x in day_1_activities if x.name == selected_close_name), None)
                if target_sa:
                    new_it, exp = replan_itinerary(st.session_state.itinerary, 1, "attraction_closed", {"closed_id": target_sa.item_id})
                    st.session_state.replanned_itinerary = new_it
                    st.session_state.current_event = "attraction_closed"
                    st.session_state.event_explanation = exp
                    st.rerun()
        else:
            st.markdown("<p style='font-size:0.8rem; color:#475569; min-height:45px;'>No active activities available on Day 1 to close.</p>", unsafe_allow_html=True)
            st.button("Force Closure", disabled=True, use_container_width=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_sim_4:
        st.markdown("<div class='glass-card' style='padding:15px; height:100%; text-align:center;'>", unsafe_allow_html=True)
        st.markdown("🥱 <h4 style='color:#0B1B3D;'>Traveler Fatigue Alert</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8rem; color:#475569; min-height:45px;'>Decreases activity difficulty, adds coffee breaks, drops strenuous blocks and finishes early.</p>", unsafe_allow_html=True)
        fatigue_btn = st.button("Simulate Fatigue Alert", use_container_width=True)
        if fatigue_btn:
            new_it, exp = replan_itinerary(st.session_state.itinerary, 1, "fatigue_high", {})
            st.session_state.replanned_itinerary = new_it
            st.session_state.current_event = "fatigue_high"
            st.session_state.event_explanation = exp
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Revert control
    st.markdown("<br/>", unsafe_allow_html=True)
    col_reset_1, col_reset_2 = st.columns([1, 4])
    with col_reset_1:
        reset_btn = st.button("🔄 Reset to Original Plan", type="secondary", use_container_width=True)
        if reset_btn:
            st.session_state.replanned_itinerary = None
            st.session_state.current_event = None
            st.session_state.event_explanation = ""
            st.toast("Itinerary reset back to pristine original constraints.", icon="🔄")
            st.rerun()
    with col_reset_2:
        st.markdown("<div style='margin-top: 8px; font-size: 0.85rem; color: #475569;'>Tip: Resetting clears the simulated updates and loads your original, perfectly-balanced spatiotemporal optimization schedule.</div>", unsafe_allow_html=True)
