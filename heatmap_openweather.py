import requests
import folium
import random
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import streamlit as st

from chatbot import vayu_chatbot_ui


# ---------------------------
# GET CITY COORDS
# ---------------------------
def get_city_coordinates(city, api_key):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"

    try:
        r = requests.get(url, timeout=10).json()
    except Exception:
        return None, None

    # Check API returned valid array
    if not isinstance(r, list) or len(r) == 0:
        return None, None

    # Defensive: ensure keys exist
    lat = r[0].get("lat")
    lon = r[0].get("lon")
    if lat is None or lon is None:
        return None, None

    return float(lat), float(lon)


# ---------------------------
# GET POLLUTION DATA
# ---------------------------
def get_pollution(lat, lon, api_key):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"

    try:
        r = requests.get(url, timeout=10).json()
    except Exception:
        return None

    if "list" not in r or not r["list"]:
        return None

    comp = r["list"][0].get("components", {})
    return {
        "pm25": comp.get("pm2_5", 0),
        "pm10": comp.get("pm10", 0),
        "no2": comp.get("no2", 0),
    }


# ---------------------------
# CACHE HEATMAP DATA
# ---------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fetch_heatmap_points(city, api_key):

    lat, lon = get_city_coordinates(city, api_key)

    # ALWAYS return 5 values, even if failure
    if lat is None or lon is None:
        return None, None, [], [], []

    # Generate grid
    offsets = [-0.1, 0, 0.1]

    pm25_points = []
    pm10_points = []
    no2_points = []

    for dx in offsets:
        for dy in offsets:
            glat = lat + dx + random.uniform(-0.01, 0.01)
            glon = lon + dy + random.uniform(-0.01, 0.01)

            pol = get_pollution(glat, glon, api_key)
            if pol is None:
                continue

            pm25_points.append([glat, glon, pol["pm25"]])
            pm10_points.append([glat, glon, pol["pm10"]])
            no2_points.append([glat, glon, pol["no2"]])

    # Return EXACT 5-tuple every time
    return lat, lon, pm25_points, pm10_points, no2_points


# ---------------------------
# HEATMAP UI
# ---------------------------
def heatmap_ui_openweather(city):

    st.subheader(f"🌍 {city} — Real-Time AQI Heatmap (Optimized)")

    api_key = st.secrets.get("api_key")

    lat, lon, pm25, pm10, no2 = fetch_heatmap_points(city, api_key)

    if lat is None:
        st.warning("City not found or API error.")
        return

    # Folium map
    m = folium.Map(location=[lat, lon], zoom_start=11, tiles="cartodbpositron")

    if pm25:
        HeatMap(pm25, radius=30, blur=20, min_opacity=0.3, name="PM2.5").add_to(m)
    if pm10:
        HeatMap(pm10, radius=25, blur=18, min_opacity=0.25, name="PM10").add_to(m)
    if no2:
        HeatMap(no2, radius=20, blur=15, min_opacity=0.2, name="NO₂").add_to(m)

    folium.LayerControl().add_to(m)

    st_folium(m, width=900, height=550, returned_objects=[])

    st.markdown("---")
    st.subheader("🤖 VAYU GPT — Ask About Your City's Air Quality")
    vayu_chatbot_ui()
