import math
from typing import Tuple
from src.models import Location
import streamlit as st

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points
    on the Earth in kilometers.
    """
    # Convert decimal degrees to radians
    r_lat1, r_lon1, r_lat2, r_lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = r_lon2 - r_lon1
    dlat = r_lat2 - r_lat1
    a = math.sin(dlat/2)**2 + math.cos(r_lat1) * math.cos(r_lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

def estimate_transit(loc1: Location, loc2: Location, mode: str) -> Tuple[float, float, float]:
    """
    Estimate transit duration (minutes), cost (USD), and distance (km) between two locations.
    """
    dist_km = haversine_distance(loc1.lat, loc1.lon, loc2.lat, loc2.lon)
    
    # Avoid zero distance division issues
    if dist_km < 0.05:
        return 2.0, 0.0, dist_km

    if mode == "Walking":
        speed_kmh = 4.5
        duration_mins = (dist_km / speed_kmh) * 60
        cost = 0.0
    elif mode == "Public Transit":
        speed_kmh = 24.0
        duration_mins = ((dist_km / speed_kmh) * 60) + 12.0  # adding waiting time buffer
        cost = 2.75
    elif mode == "Rental Car":
        speed_kmh = 35.0
        duration_mins = ((dist_km / speed_kmh) * 60) + 6.0   # parking/traffic buffer
        cost = 1.0 + (dist_km * 0.40)  # wear, gas and parking share
    else:  # "Taxi" / Ride-sharing
        speed_kmh = 38.0
        duration_mins = ((dist_km / speed_kmh) * 60) + 4.0   # wait/pickup buffer
        cost = 3.50 + (dist_km * 1.80)

    # Round to realistic values
    return round(duration_mins, 1), round(cost, 2), round(dist_km, 2)

def format_time(hour: float) -> str:
    """
    Convert float hours (e.g. 14.5) to "14:30" string format.
    """
    h = int(hour)
    m = int((hour - h) * 60)
    # Clamp hours to 24h format
    h = h % 24
    return f"{h:02d}:{m:02d}"

def float_to_ampm(hour: float) -> str:
    """
    Convert float hours (e.g. 14.5) to "02:30 PM" string format.
    """
    h = int(hour)
    m = int((hour - h) * 60)
    suffix = "AM"
    
    if h >= 12:
        suffix = "PM"
        if h > 12:
            h -= 12
    elif h == 0:
        h = 12
        
    return f"{h:02d}:{m:02d} {suffix}"

def inject_premium_styles():
    """
    Injects custom CSS to style the Streamlit application with premium,
    white primary background, deep navy blue secondary accents,
    glassmorphism shadow cards, and clean visual typography.
    """
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        /* Force Light Theme Colors on App View Container */
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #FFFFFF !important;
            color: #0B1B3D !important;
        }

        /* Apply fonts */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Outfit', sans-serif !important;
            color: #0B1B3D !important;
        }

        /* Sidebar - styled in Deep Navy Blue for stunning secondary structural contrast */
        [data-testid="stSidebar"] {
            background-color: #0B1B3D !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Ensure all text/labels inside the navy sidebar are bright white / silver */
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h4 {
            color: #FFFFFF !important;
        }
        
        /* Stylize sliders and select elements in the sidebar to pop */
        [data-testid="stSidebar"] .stSlider > label {
            color: rgba(255,255,255,0.8) !important;
        }

        /* Gradient header text */
        .glow-text {
            background: linear-gradient(135deg, #0B1B3D, #1E3A8A, #3B82F6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            text-shadow: 0px 4px 12px rgba(11, 27, 61, 0.08);
        }
        
        /* Clean light glassmorphic card styling */
        .glass-card {
            background: #FFFFFF;
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(11, 27, 61, 0.08);
            margin-bottom: 20px;
            box-shadow: 0 10px 40px 0 rgba(11, 27, 61, 0.05);
            transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
            color: #0B1B3D;
        }
        
        .glass-card:hover {
            transform: translateY(-2px);
            border-color: rgba(11, 27, 61, 0.2);
            box-shadow: 0 15px 45px 0 rgba(11, 27, 61, 0.08);
        }
        
        /* Styled Timeline elements */
        .timeline-container {
            border-left: 2px dashed rgba(11, 27, 61, 0.15);
            padding-left: 20px;
            margin-left: 10px;
            position: relative;
        }
        
        .timeline-badge {
            font-size: 0.82rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
            color: white !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: inline-block;
            margin-bottom: 8px;
        }
        
        .badge-hotel { background: linear-gradient(135deg, #FF3366, #FF3399); }
        .badge-activity { background: linear-gradient(135deg, #00C8FF, #0072FF); }
        .badge-restaurant { background: linear-gradient(135deg, #00FF87, #00C8FF); }
        .badge-rest { background: linear-gradient(135deg, #FFCC00, #FF9900); }
        .badge-transit { background: linear-gradient(135deg, #8A2387, #E94057); }

        .timeline-item {
            position: relative;
            background: #F8FAFC;
            border: 1px solid rgba(11, 27, 61, 0.06);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 4px 15px rgba(11, 27, 61, 0.02);
            transition: border-color 0.2s ease;
        }
        
        .timeline-item:hover {
            border-color: rgba(11, 27, 61, 0.15);
        }
        
        /* Sub-headings and descriptions inside cards */
        .item-title {
            font-size: 1.15rem;
            font-weight: 600;
            color: #0B1B3D !important;
            margin: 0 0 6px 0;
        }
        
        .item-meta {
            font-size: 0.85rem;
            color: rgba(11, 27, 61, 0.6) !important;
            margin-bottom: 8px;
        }
        
        .item-desc {
            font-size: 0.95rem;
            color: #334155 !important;
            line-height: 1.4;
        }
        
        /* Dynamic banner styling */
        .alert-banner {
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            border-left: 6px solid;
            box-shadow: 0 6px 20px rgba(11, 27, 61, 0.04);
        }
        .banner-info {
            background: rgba(30, 58, 138, 0.04);
            border-color: #1E3A8A;
            color: #0B1B3D !important;
        }
        .banner-warning {
            background: rgba(217, 119, 6, 0.04);
            border-color: #D97706;
            color: #78350F !important;
        }
        .banner-success {
            background: rgba(5, 150, 105, 0.04);
            border-color: #059669;
            color: #064E3B !important;
        }
        
        /* Adjust global banner text color */
        .alert-banner strong, .alert-banner div {
            color: inherit !important;
        }

        /* Plotly charts styling override */
        div[data-testid="stPlotlyChart"] {
            border-radius: 16px !important;
            overflow: hidden !important;
            border: 1px solid rgba(11, 27, 61, 0.06) !important;
            background-color: #FFFFFF !important;
        }

        /* Metric card optimization for light theme */
        .stMetric {
            background: #F8FAFC !important;
            border: 1px solid rgba(11, 27, 61, 0.08) !important;
            border-radius: 12px !important;
            padding: 12px !important;
            text-align: center !important;
            color: #0B1B3D !important;
        }
        
        .stMetric [data-testid="stMetricValue"] {
            color: #1E3A8A !important;
        }
        
        .stMetric [data-testid="stMetricLabel"] {
            color: rgba(11, 27, 61, 0.6) !important;
        }
        </style>
    """, unsafe_allow_html=True)
