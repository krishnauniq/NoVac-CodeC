import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from aqi import fetch_city_stations

# -------------------------------------------------------
# CREATE AQI HEATMAP OF A CITY
# -------------------------------------------------------
def generate_aqi_heatmap(city):
    stations = fetch_city_stations(city)

    if not stations:
        return None, "No AQI station data available for this city."

    # Extract lat/long/value for heatmap points
    heat_data = []
    center_lat = 0
    center_lon = 0

    for s in stations:
        try:
            lat = s["lat"]
            lon = s["lon"]
            val = s["value"]  # PM2.5
            heat_data.append([lat, lon, max(val, 20)])  # minimum intensity 20

            center_lat += lat
            center_lon += lon
        except:
            continue

    # Center map
    center_lat /= len(heat_data)
    center_lon /= len(heat_data)

    # Folium map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles="cartodbpositron"
    )

    # Add heatmap layer
    HeatMap(
        heat_data,
        min_opacity=0.3,
        radius=55,
        blur=35,
        max_zoom=1,
    ).add_to(m)

    # Add markers
    for s in stations:
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=6,
            color="#ff006e",
            fill=True,
            fill_opacity=0.9,
            popup=f"{s['station']} — PM2.5: {s['value']}",
        ).add_to(m)

    return m, "OK"


# -------------------------------------------------------
# STREAMLIT UI WRAPPER
# -------------------------------------------------------
def heatmap_ui(city):
    st_header = f"🌍 **{city} — Real-Time AQI Heatmap**"
    import streamlit as st

    st.subheader(st_header)

    m, status = generate_aqi_heatmap(city)

    if m is None:
        st.warning(status)
        return

    st_folium(m, width=800, height=550)
