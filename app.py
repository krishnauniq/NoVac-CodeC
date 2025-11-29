# -------------------------------------------------------
# NoVac Unified App — AQI Visualizer + AI Copilot
# -------------------------------------------------------

import streamlit as st
import pandas as pd
import requests
import random
import os
import time
from groq import Groq
from dotenv import load_dotenv
from chatbot import vayu_chatbot_ui
from heatmap_openweather import heatmap_ui_openweather

load_dotenv()  # load .env if available

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------
st.set_page_config(page_title="NoVac — Air Quality Copilot", layout="wide")


# -------------------------------------------------------
# UI HELPERS (CSS + PARTICLES)
# -------------------------------------------------------
def load_css():
    try:
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Fallback simple style if file missing
        st.markdown(
            """
            <style>
            body { background: #020617; color: #e5e7eb; }
            .main-title { font-size: 1.6rem; font-weight: 700; display:flex; gap:0.5rem; align-items:center; }
            .logo-dot { width:12px; height:12px; border-radius:999px; background:linear-gradient(135deg,#22d3ee,#a855f7); box-shadow:0 0 12px #22d3ee; display:inline-block; }
            .nv-pill { padding:0.4rem 0.9rem; border-radius:999px; border:1px solid rgba(148,163,184,0.5); font-size:0.8rem; display:flex; gap:0.35rem; align-items:center; background:rgba(15,23,42,0.85); }
            .nv-card { background:rgba(15,23,42,0.9); border-radius:1.2rem; padding:1.0rem 1.1rem; border:1px solid rgba(148,163,184,0.35); box-shadow:0 18px 40px rgba(15,23,42,0.8); margin-bottom:0.9rem; }
            .nv-card-header { font-size:0.85rem; letter-spacing:0.08em; text-transform:uppercase; color:#9ca3af; margin-bottom:0.6rem; }
            .ai-thinking { display:flex; align-items:center; gap:0.5rem; font-size:0.85rem; color:#a5b4fc; }
            .ai-dot { width:8px; height:8px; border-radius:999px; background:linear-gradient(135deg,#22c55e,#22d3ee); box-shadow:0 0 10px #22d3ee; animation:pulse 1.4s infinite; }
            .autonomous-badge { background: linear-gradient(135deg, #22c55e, #22d3ee); color: white; padding: 0.3rem 0.8rem; border-radius: 1rem; font-size: 0.8rem; font-weight: bold; animation: pulse 2s infinite; }
            @keyframes pulse {
                0% { transform:scale(1); opacity:1; }
                50% { transform:scale(1.05); opacity:0.8; }
                100% { transform:scale(1); opacity:1; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


def load_particles():
    # Optional particle background layer if particles.html exists
    try:
        with open("particles.html") as f:
            st.markdown(f.read(), unsafe_allow_html=True)
    except FileNotFoundError:
        pass


load_css()
load_particles()

# ---- Global header ----
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
        <div class="main-title">
            <span class="logo-dot"></span>
            <span>NoVac — Air Quality Copilot</span>
        </div>
        <div class="nv-pill">
            <span>🧠 Agentic AI</span>
            <span>·</span>
            <span>📊 Live AQI & Pollutants</span>
            <span>·</span>
            <span>📲 WhatsApp Alerts</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Switch between **Simple AQI Visualizer** and **Neon AI Copilot** — powered by OpenWeather, OpenAQ, Groq Llama 3 and WhatsApp Cloud API."
)

# -------------------------------------------------------
# AGENTIC AI (Groq)
# -------------------------------------------------------
def ai_agent_analysis(aqi, trend, spike, spike_change, forecast):
    """Generate agent-style explanation using Groq free Llama 3."""
    try:
        api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("groq_api_key", "")
        if not api_key:
            return "AI Agent: GROQ_API_KEY not found in environment or secrets."
        
        client = Groq(api_key=api_key)

        prompt = f"""
        You are NoVac AI — an environmental intelligence agent.
        Analyze the following air quality data and give a smart, concise,
        human-friendly explanation with actionable advice.

        Current PM2.5: {aqi}
        Trend direction: {trend}
        Spike detected: {spike}
        Spike jump: {spike_change}
        Forecast (3 days): {forecast}

        Provide:
        - A short summary in one sentence
        - Health risk level
        - Who should be most careful
        - Whether people should stay indoors
        - Any actionable recommendations
        - Confidence level in your analysis
        """

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI agent unavailable: {e}"


# -------------------------------------------------------
# WHATSAPP ALERTS
# -------------------------------------------------------
def send_whatsapp_alert(text: str):
    """
    Send a WhatsApp message using Cloud API.
    Uses env vars: WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_TO
    """
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    to = os.getenv("WHATSAPP_TO")

    if not token or not phone_id or not to:
        return False, "Missing WHATSAPP_* env variables"

    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": str(to),
        "type": "text",
        "text": {"body": text},
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        data = resp.json()
        if resp.status_code == 200 and "messages" in data:
            return True, "Sent"
        return False, f"API error: {data}"
    except Exception as e:
        return False, str(e)


# -------------------------------------------------------
# AQI FETCHER (OpenAQ for PM2.5) – used by Copilot
# -------------------------------------------------------
def fetch_current_aqi(city, mock=False):
    if mock:
        return random.randint(50, 250)

    url = "https://api.openaq.org/v2/latest"

    params = {
        "limit": 100,
        "page": 1,
        "offset": 0,
        "country": "IN",
        "parameter": "pm25",
        "location": city,  # Works when location matches station name
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        # Fallback: try as city field if no data
        if len(data.get("results", [])) == 0:
            params.pop("location", None)
            params["city"] = city
            r = requests.get(url, params=params, timeout=10)
            data = r.json()

        if len(data.get("results", [])) == 0:
            return None

        # Read PM2.5 from either "measurements" or "parameters"
        try:
            return data["results"][0]["measurements"][0]["value"]
        except Exception:
            for p in data["results"][0].get("parameters", []):
                if p.get("parameter") == "pm25":
                    return p.get("lastValue")

        return None

    except Exception:
        return None


# -------------------------------------------------------
# SPIKE / TREND / FORECAST ENGINE
# -------------------------------------------------------
from spike import (
    detect_spike,
    trend_direction,
    forecast_pm25,
    copilot_decision,
    run_copilot
)

# -------------------------------------------------------
# HELPERS FOR INDIAN AQI (CPCB)
# -------------------------------------------------------
def calc_aqi_subindex(C, breakpoints):
    """
    Generic linear interpolation for AQI sub-index.
    C: concentration
    breakpoints: list of dicts with C_low, C_high, I_low, I_high
    """
    if C is None:
        return None
    for bp in breakpoints:
        if bp["C_low"] <= C <= bp["C_high"]:
            return round(
                ((bp["I_high"] - bp["I_low"]) / (bp["C_high"] - bp["C_low"]))
                * (C - bp["C_low"]) + bp["I_low"]
            )
    # If above highest range, clamp to max index
    last = breakpoints[-1]
    if C > last["C_high"]:
        return last["I_high"]
    return None


# CPCB Indian AQI breakpoints (24-hr) for PM2.5 and PM10
PM25_BREAKPOINTS_IN = [
    {"C_low": 0.0, "C_high": 30.0, "I_low": 0, "I_high": 50},     # Good
    {"C_low": 31.0, "C_high": 60.0, "I_low": 51, "I_high": 100},  # Satisfactory
    {"C_low": 61.0, "C_high": 90.0, "I_low": 101, "I_high": 200}, # Moderate
    {"C_low": 91.0, "C_high": 120.0, "I_low": 201, "I_high": 300},# Poor
    {"C_low": 121.0, "C_high": 250.0, "I_low": 301, "I_high": 400},# Very Poor
    {"C_low": 251.0, "C_high": 500.0, "I_low": 401, "I_high": 500},# Severe
]

PM10_BREAKPOINTS_IN = [
    {"C_low": 0.0, "C_high": 50.0, "I_low": 0, "I_high": 50},      # Good
    {"C_low": 51.0, "C_high": 100.0, "I_low": 51, "I_high": 100},  # Satisfactory
    {"C_low": 101.0, "C_high": 250.0, "I_low": 101, "I_high": 200},# Moderate
    {"C_low": 251.0, "C_high": 350.0, "I_low": 201, "I_high": 300},# Poor
    {"C_low": 351.0, "C_high": 430.0, "I_low": 301, "I_high": 400},# Very Poor
    {"C_low": 431.0, "C_high": 600.0, "I_low": 401, "I_high": 500},# Severe (extended)
]


def get_indian_aqi_category(aqi):
    if aqi is None:
        return "Unknown"
    if aqi <= 50:
        return "Good 😊"
    elif aqi <= 100:
        return "Satisfactory 🙂"
    elif aqi <= 200:
        return "Moderate 😐"
    elif aqi <= 300:
        return "Poor 😷"
    elif aqi <= 400:
        return "Very Poor 🛑"
    else:
        return "Severe ☠️"


def get_indian_aqi_suggestion(aqi):
    if aqi is None:
        return "AQI not available. Please try again."
    if aqi <= 50:
        return "✅ Air quality is good. Great day to be outdoors!"
    elif aqi <= 100:
        return "🙂 Generally satisfactory. Sensitive individuals should monitor symptoms."
    elif aqi <= 200:
        return "😐 May cause breathing discomfort to people with lung/heart disease, children, and older adults."
    elif aqi <= 300:
        return "⚠️ Breathing discomfort likely on prolonged exposure. Consider reducing outdoor activities."
    elif aqi <= 400:
        return "🚫 Very poor air. Avoid prolonged outdoor exposure, especially if you have respiratory or heart conditions."
    else:
        return "☠️ Severe pollution. Stay indoors, use masks/air purifiers if possible, and avoid physical exertion."


# -------------------------------------------------------
# SIMPLE AQI VISUALIZER (OpenWeather → Indian AQI)
# -------------------------------------------------------
def run_visualizer(city):
    st.markdown('<div class="nv-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="nv-card-header">Mode · AQI Visualizer (OpenWeather → Indian AQI)</div>',
        unsafe_allow_html=True,
    )

    st.subheader("NoVac Air Quality Visualizer")
    st.write("Enter a city in the sidebar, then click below to fetch AQI.")

    if not city:
        st.warning("Please enter a city in the sidebar.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if st.button("Get AQI Data"):
        try:
            api_key = st.secrets["api_key"]
        except Exception:
            st.error("Missing `api_key` in Streamlit secrets.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        # Get coordinates
        geocode_url = (
            f"http://api.openweathermap.org/geo/1.0/direct?"
            f"q={city}&limit=1&appid={api_key}"
        )
        geo_res = requests.get(geocode_url).json()

        if geo_res and isinstance(geo_res, list) and len(geo_res) > 0:
            lat = geo_res[0]["lat"]
            lon = geo_res[0]["lon"]

            # Get AQI and components
            aqi_url = (
                f"https://api.openweathermap.org/data/2.5/air_pollution?"
                f"lat={lat}&lon={lon}&appid={api_key}"
            )
            aqi_res = requests.get(aqi_url).json()

            if "list" in aqi_res and len(aqi_res["list"]) > 0:
                components = aqi_res["list"][0]["components"]

                pm2_5 = components.get("pm2_5")
                pm10 = components.get("pm10")

                # Compute Indian AQI sub-indices
                aqi_values = []

                aqi_pm25 = calc_aqi_subindex(pm2_5, PM25_BREAKPOINTS_IN) if pm2_5 is not None else None
                aqi_pm10 = calc_aqi_subindex(pm10, PM10_BREAKPOINTS_IN) if pm10 is not None else None

                if aqi_pm25 is not None:
                    aqi_values.append(aqi_pm25)
                if aqi_pm10 is not None:
                    aqi_values.append(aqi_pm10)

                if not aqi_values:
                    st.error("Could not compute AQI from PM2.5 / PM10.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return

                aqi = max(aqi_values)
                category = get_indian_aqi_category(aqi)
                suggestion = get_indian_aqi_suggestion(aqi)

                st.subheader(f"Air Quality Index (Indian Standard) in {city}:")
                st.metric("AQI (0–500, India)", int(aqi), category)
                st.info(f"AQI Category: {category}")
                st.warning(f"Suggestion: {suggestion}")

                # Optional: show raw PM values as metrics
                col_pm25, col_pm10 = st.columns(2)
                with col_pm25:
                    st.metric("PM2.5 (µg/m³)", f"{pm2_5:.1f}" if pm2_5 is not None else "N/A")
                with col_pm10:
                    st.metric("PM10 (µg/m³)", f"{pm10:.1f}" if pm10 is not None else "N/A")

                st.subheader("📍 Location on Map")
                st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

                # Show pollutant values in chart
                st.subheader("📊 Pollutant Concentrations (μg/m³)")
                df = pd.DataFrame(components.items(), columns=["Pollutant", "Value"])
                df = df.sort_values(by="Value", ascending=False)
                st.bar_chart(df.set_index("Pollutant"))

                # Downloadable CSV
                csv_data = pd.DataFrame(
                    components.items(), columns=["Pollutant", "Value"]
                )
                csv = csv_data.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="📥 Download Pollutant Data as CSV",
                    data=csv,
                    file_name=f"AQI_Pollutants_{city}.csv",
                    mime="text/csv",
                )

            else:
                st.error("Failed to fetch AQI data from OpenWeather.")
        else:
            st.error("City not found or invalid response from geocoding API.")

    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------------
# AI COPILOT UI (from novac_copilot.py, adapted)
# -------------------------------------------------------
def run_copilot_ui(city, mock_mode, auto_mode, whatsapp_enabled):
    # Initialize session state
    if "last_aqi" not in st.session_state:
        st.session_state.last_aqi = None
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_run_time" not in st.session_state:
        st.session_state.last_run_time = 0
    if "run_count" not in st.session_state:
        st.session_state.run_count = 0

    # Dashboard header / run button
    top_bar = st.container()
    with top_bar:
        col_run, col_status = st.columns([1, 2])
        with col_run:
            run_clicked = st.button("Run Analysis Now")
        with col_status:
            if auto_mode:
                st.markdown(
                    '<div class="nv-card nv-card-header">'
                    'Mode · NoVac AI Copilot — <span class="autonomous-badge">AUTONOMOUS MODE ACTIVE</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="nv-card nv-card-header">Mode · NoVac AI Copilot — Live Decision Space</div>',
                    unsafe_allow_html=True,
                )

    # Determine if we should run analysis
    should_run = False
    
    if auto_mode:
        # Auto mode: run every 30 seconds or on first load
        current_time = time.time()
        if current_time - st.session_state.last_run_time > 30 or st.session_state.run_count == 0:
            should_run = True
            st.session_state.last_run_time = current_time
            st.session_state.run_count += 1
    else:
        # Manual mode: run only when button is clicked
        should_run = run_clicked

    if should_run:
        with st.empty():
            result, status, new_last, new_history = run_copilot(
                city,
                st.session_state.last_aqi,
                st.session_state.history,
                mock=mock_mode,
            )

        if result:
            st.session_state.last_aqi = new_last
            st.session_state.history = new_history

            dec = result["decision"]

            # ==== Top dashboard row: METRIC / ALERTS / FORECAST ====
            col_a, col_b, col_c = st.columns([1.2, 1.1, 1.2])

            with col_a:
                st.markdown('<div class="nv-card">', unsafe_allow_html=True)
                st.markdown(
                    '<div class="nv-card-header">Current Load</div>',
                    unsafe_allow_html=True,
                )
                st.metric("PM2.5 (µg/m³)", result["current"])
                trend_label = {
                    "up": "📈 Rising",
                    "down": "📉 Dropping",
                    "stable": "➖ Stable",
                }[result["trend"]]
                st.markdown(f"**Trend:** {trend_label}")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_b:
                st.markdown('<div class="nv-card">', unsafe_allow_html=True)
                st.markdown(
                    '<div class="nv-card-header">System Alerts</div>',
                    unsafe_allow_html=True,
                )
                if result["spike"]:
                    st.error(f"⚠️ Spike Detected (+{result['spike_change']})")
                else:
                    st.info("No sudden spike detected in latest reading.")
                if dec["severity"] == "High":
                    st.error(f"{dec['status']} — {dec['details']}")
                elif dec["severity"] == "Medium":
                    st.warning(f"{dec['status']} — {dec['details']}")
                else:
                    st.success(f"{dec['status']} — {dec['details']}")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_c:
                st.markdown('<div class="nv-card">', unsafe_allow_html=True)
                st.markdown(
                    '<div class="nv-card-header">3-Day Forecast</div>',
                    unsafe_allow_html=True,
                )

                forecast_df = pd.DataFrame(
                    {
                        "Day": ["Day 1", "Day 2", "Day 3"],
                        "PM2.5": result["forecast"],
                    }
                )

                neon_chart = {
                    "width": "container",
                    "height": 260,
                    "background": None,
                    "data": {
                        "values": forecast_df.to_dict(orient="records"),
                    },
                    "mark": {
                        "type": "line",
                        "point": {"filled": True, "size": 80, "color": "#3bffb3"},
                        "strokeWidth": 4,
                        "color": "#ff4dd8",
                    },
                    "encoding": {
                        "x": {
                            "field": "Day",
                            "type": "nominal",
                            "axis": {"labelColor": "#ccc", "labelAngle": 0},
                        },
                        "y": {
                            "field": "PM2.5",
                            "type": "quantitative",
                            "scale": {
                                "domain": [
                                    float(forecast_df["PM2.5"].min()) - 20,
                                    float(forecast_df["PM2.5"].max()) + 20,
                                ]
                            },
                            "axis": {
                                "title": "PM2.5 Forecast",
                                "labelColor": "#ccc",
                                "gridColor": "rgba(255,255,255,0.12)",
                            },
                        },
                    },
                    "config": {
                        "view": {"stroke": "transparent"},
                        "axis": {
                            "domainColor": "#666",
                            "tickColor": "#777",
                        },
                    },
                }

                st.vega_lite_chart(neon_chart, use_container_width=True)
                st.table(forecast_df[["Day", "PM2.5"]])

                st.markdown("</div>", unsafe_allow_html=True)
            
            # ==== AI Insight + Trend (2nd row) ====
            col_ai, col_trend = st.columns([1.35, 1])

            with col_ai:
                st.markdown('<div class="nv-card">', unsafe_allow_html=True)
                st.markdown(
                    '<div class="nv-card-header">NoVac AI Copilot Insight</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="ai-thinking"><div class="ai-dot"></div>'
                    '<span>Copilot is analyzing live data...</span></div><br><br>',
                    unsafe_allow_html=True,
                )
                with st.spinner("🧠 Thinking like an environmental expert..."):
                    ai_text = ai_agent_analysis(
                        result["current"],
                        result["trend"],
                        result["spike"],
                        result["spike_change"],
                        result["forecast"],
                    )
                st.write(ai_text)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_trend:
                st.markdown('<div class="nv-card">', unsafe_allow_html=True)
                st.markdown(
                    '<div class="nv-card-header">Recent PM2.5 Trajectory</div>',
                    unsafe_allow_html=True,
                )
                st.line_chart(result["history"])
                st.markdown("</div>", unsafe_allow_html=True)

            # ===========================
            # WHATSAPP SMART ALERT LOGIC
            # ===========================
            # Only send alerts on manual runs (not in auto_mode) to avoid spam
            if whatsapp_enabled and not auto_mode:
                aqi_val = float(result["current"])
                reasons = []

                if result["spike"]:
                    reasons.append("Spike detected")
                if aqi_val >= 200:
                    reasons.append("Very unhealthy AQI")
                elif aqi_val >= 150:
                    reasons.append("Unhealthy AQI")

                should_alert = len(reasons) > 0

                if should_alert:
                    reasons_str = ", ".join(reasons)
                    short_alert = (
                        f"🩷 NoVac AQI Alert for {city}:\n"
                        f"PM2.5: {aqi_val:.1f}\n"
                        f"Status: {dec['status']}\n"
                        f"Trend: {result['trend']}\n"
                        f"Reason: {reasons_str}"
                    )

                    ok, msg = send_whatsapp_alert(short_alert)
                    if ok:
                        st.success("WhatsApp alert sent (summary).")
                    else:
                        st.warning(f"WhatsApp alert failed: {msg}")

                    # Second message: LLM explanation
                    if ai_text and not ai_text.startswith("AI agent unavailable"):
                        long_msg = f"🧠 NoVac Copilot insight for {city}:\n{ai_text}"
                        if len(long_msg) > 3900:
                            long_msg = long_msg[:3900] + "..."
                        send_whatsapp_alert(long_msg)

        else:
            st.error("API Error! Try enabling Mock Mode.")
    else:
        if auto_mode:
            # Show countdown for next auto-run
            if st.session_state.last_run_time > 0:
                next_run = int(30 - (time.time() - st.session_state.last_run_time))
                if next_run > 0:
                    st.info(f"🔄 Next auto-analysis in {next_run} seconds...")
                else:
                    st.info("🔄 Running analysis now...")
            else:
                st.info("🔄 Initializing autonomous monitoring...")
            
            # Auto-refresh the page to trigger next run
            st.rerun()
        else:
            st.info(
                "Click **Run Analysis Now** or enable **Autonomous Mode** in the sidebar to wake the Copilot."
            )


# -------------------------------------------------------
# MAIN APP: MODE SWITCH
# -------------------------------------------------------
def main():
    st.sidebar.header("⚙️ NoVac Control Center")

    mode = st.sidebar.radio(
        "Choose Mode",
        ["AQI Visualizer", "AI Copilot", "VAYU Gpt", "AQI Heatmap"],
        index=0,
    )

    city = st.sidebar.text_input("City:", value="Mumbai")

    mock_mode = False
    auto_mode = False
    whatsapp_enabled = False

    if mode == "AI Copilot":
        mock_mode = st.sidebar.toggle("Use Mock AQI Data", value=True)
        auto_mode = st.sidebar.toggle("Autonomous Mode", value=False)
        whatsapp_enabled = st.sidebar.toggle("Enable WhatsApp Alerts", value=False)
        st.sidebar.write("Mock Mode is recommended for testing & demos.")

    st.sidebar.markdown("---")
    st.sidebar.caption("NoVac · Pollution Intelligence Copilot")

    if mode == "AQI Visualizer":
        run_visualizer(city)
    elif mode == "AI Copilot":
        run_copilot_ui(city, mock_mode, auto_mode, whatsapp_enabled)
    elif mode == "AQI Heatmap":
        heatmap_ui_openweather(city)
    else:
        vayu_chatbot_ui()


if __name__ == "__main__":
    main()
