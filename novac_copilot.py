# -------------------------------------------------------
# NOVAC AI COPILOT — GROQ LLM + WHATSAPP SMART ALERTS
# Futuristic Neon Dashboard (Particles + Agent UI)
# -------------------------------------------------------

import streamlit as st
import pandas as pd
import requests
import random
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # load .env if available


# ===========================
# FREE AI AGENT (Groq Llama 3)
# ===========================
def ai_agent_analysis(aqi, trend, spike, spike_change, forecast):
    """Generate agent-style explanation using Groq free Llama 3."""
    try:
        api_key = os.getenv("GROQ_API_KEY") or st.secrets["groq_api_key"]
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
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI agent unavailable: {e}"


# ===========================
# WHATSAPP ALERTS (Cloud API)
# ===========================
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
        "text": {"body": text}
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        data = resp.json()
        if resp.status_code == 200 and "messages" in data:
            return True, "Sent"
        return False, f"API error: {data}"
    except Exception as e:
        return False, str(e)


# ===========================
# AQI FETCHER
# ===========================
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
        "location": city  # ★ KEY FIX → works for ANY town / village / city
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        # Fallback: try as city field if no data
        if len(data["results"]) == 0:
            params.pop("location", None)
            params["city"] = city
            r = requests.get(url, params=params, timeout=10)
            data = r.json()

        if len(data["results"]) == 0:
            return None

        # Some locations store pm2.5 under "measurements", some under "parameters"
        try:
            return data["results"][0]["measurements"][0]["value"]
        except:
            for p in data["results"][0].get("parameters", []):
                if p["parameter"] == "pm25":
                    return p["lastValue"]

        return None

    except:
        return None



# ===========================
# SPIKE DETECTION
# ===========================
def detect_spike(current, last, threshold=40):
    if last is None:
        return False, 0
    change = current - last
    return (change >= threshold, change)


# ===========================
# TREND
# ===========================
def trend_direction(history, window=5):
    if len(history) < window:
        return "stable"
    recent = history[-window:]
    slope = recent[-1] - recent[0]
    if slope > 15:
        return "up"
    elif slope < -15:
        return "down"
    return "stable"


# ===========================
# FORECAST
# ===========================
def forecast_pm25(history, days=3):
    if len(history) < 2:
        return [history[-1]] * days

    last = history[-1]
    prev = history[-2]
    slope = last - prev  # direction

    forecast = []
    value = last

    for _ in range(days):
        # Trend influences
        if slope > 10:
            value += random.uniform(5, 12)   # rising pollution
        elif slope < -10:
            value -= random.uniform(5, 12)   # improving
        else:
            value += random.uniform(-4, 4)   # small variation

        # Keep inside normal bounds
        value = max(5, min(value, 400))
        forecast.append(round(value, 2))

    return forecast


# ===========================
# DECISION ENGINE
# ===========================
def copilot_decision(aqi, last_aqi, trend, spike, spike_change):
    if spike:
        return {
            "status": "Spike Detected",
            "severity": "High",
            "action": "ALERT",
            "details": f"PM2.5 jumped by {spike_change}.",
            "risk": "High"
        }
    if aqi >= 200:
        return {
            "status": "Very Unhealthy",
            "severity": "High",
            "action": "WARNING",
            "details": "Hazardous levels.",
            "risk": "High"
        }
    if aqi >= 150:
        return {
            "status": "Unhealthy",
            "severity": "Medium",
            "action": "CAUTION",
            "details": "Air quality harmful.",
            "risk": "Medium"
        }
    if trend == "up":
        return {
            "status": "Rising Pollution",
            "severity": "Low",
            "action": "MONITOR",
            "details": "Slow rise detected.",
            "risk": "Low"
        }
    return {
        "status": "Normal",
        "severity": "Low",
        "action": "NONE",
        "details": "Air quality acceptable.",
        "risk": "Low"
    }


# ===========================
# COPILOT ENGINE
# ===========================
def run_copilot(city, last_aqi, history, mock=False):
    current = fetch_current_aqi(city, mock=mock)
    if current is None:
        return None, "API error", last_aqi, history

    history.append(current)
    spike, spike_change = detect_spike(current, last_aqi)
    trend = trend_direction(history)
    decision = copilot_decision(current, last_aqi, trend, spike, spike_change)
    forecast = forecast_pm25(history)

    return {
        "current": current,
        "last": last_aqi,
        "trend": trend,
        "spike": spike,
        "spike_change": spike_change,
        "decision": decision,
        "forecast": forecast,
        "history": history[-20:]
    }, "OK", current, history


# ===========================
# UI HELPERS (CSS + PARTICLES)
# ===========================
def load_css():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def load_particles():
    with open("particles.html") as f:
        st.markdown(f.read(), unsafe_allow_html=True)


# -------------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------------

st.set_page_config(page_title="NoVac Copilot", layout="wide")

# Load CSS + particle layer
load_css()
load_particles()

# ---- Title row ----
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
        <div class="main-title">
            <span class="logo-dot"></span>
            <span>NoVac Air Quality Copilot</span>
        </div>
        <div class="nv-pill">
            <span>🧠 Agentic AI</span>
            <span>·</span>
            <span>📲 WhatsApp Alerts</span>
            <span>·</span>
            <span>🌌 Neon Dashboard</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Real-time AQI brain with dual-tone neon UI, Groq LLM insights, and WhatsApp smart alerts.")

# Session State
if "last_aqi" not in st.session_state:
    st.session_state.last_aqi = None

if "history" not in st.session_state:
    st.session_state.history = []


# Sidebar
st.sidebar.header("⚙️ Settings")
city = st.sidebar.text_input("City:", value="Mumbai")
mock_mode = st.sidebar.toggle("Use Mock AQI Data", value=True)
auto_mode = st.sidebar.toggle("Autonomous Mode", value=False)
whatsapp_enabled = st.sidebar.toggle("Enable WhatsApp Alerts", value=False)
# st.sidebar.caption("WhatsApp uses WHATSAPP_* keys from your .env file.")
st.sidebar.write("Mock Mode recommended for testing & demos.")

# Dashboard header / run button
top_bar = st.container()
with top_bar:
    col_run, col_status = st.columns([1, 2])
    with col_run:
        run_clicked = st.button("Run Analysis Now")
    with col_status:
        st.markdown(
            '<div class="nv-card nv-card-header">Copilot Status • Live Decision Space</div>',
            unsafe_allow_html=True,
        )

trigger_run = auto_mode or run_clicked

if trigger_run:

    result, status, new_last, new_history = run_copilot(
        city,
        st.session_state.last_aqi,
        st.session_state.history,
        mock=mock_mode
    )

    if result:

        st.session_state.last_aqi = new_last
        st.session_state.history = new_history

        dec = result["decision"]

        # ==== Top dashboard row: METRIC / ALERTS / FORECAST ====
        col_a, col_b, col_c = st.columns([1.2, 1.1, 1.2])

        with col_a:
            st.markdown('<div class="nv-card">', unsafe_allow_html=True)
            st.markdown('<div class="nv-card-header">Current Load</div>', unsafe_allow_html=True)
            st.metric("PM2.5 (µg/m³)", result["current"])
            trend_label = {
                "up": "📈 Rising",
                "down": "📉 Dropping",
                "stable": "➖ Stable"
            }[result["trend"]]
            st.markdown(f"**Trend:** {trend_label}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="nv-card">', unsafe_allow_html=True)
            st.markdown('<div class="nv-card-header">System Alerts</div>', unsafe_allow_html=True)
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
            st.markdown('<div class="nv-card-header">3-Day Forecast</div>', unsafe_allow_html=True)

            forecast_df = pd.DataFrame(
        {
            "Day": ["Day 1", "Day 2", "Day 3"],
            "PM2.5": result["forecast"]
        }
    )
            forecast_df["X"] = [1, 2, 3]

            neon_chart = {
    "width": "container",
    "height": 260,
    "background": None,
    "data": {"values": forecast_df.to_dict(orient="records")},
    "mark": {
        "type": "line",
        "point": {"filled": True, "size": 80, "color": "#3bffb3"},
        "strokeWidth": 4,
        "color": "#ff4dd8"
    },
    "encoding": {
        "x": {
            "field": "Day",
            "type": "nominal",
            "axis": {
                "labelColor": "#ccc",
                "labelAngle": 0
            }
        },
        "y": {
            "field": "PM2.5",
            "type": "quantitative",
            "scale": {
                "domain": [
                    float(forecast_df["PM2.5"].min()) - 20,
                    float(forecast_df["PM2.5"].max()) + 20
                ]
            },
            "axis": {
                "title": "PM2.5 Forecast",
                "labelColor": "#ccc",
                "gridColor": "rgba(255,255,255,0.12)"
            }
        }
    },
    "config": {
        "view": {"stroke": "transparent"},
        "axis": {
            "domainColor": "#666",
            "tickColor": "#777"
        }
    }
}


        st.vega_lite_chart(neon_chart, use_container_width=True)

        
        st.table(forecast_df[["Day", "PM2.5"]])

        st.markdown("</div>", unsafe_allow_html=True)
        # ==== AI Insight + Trend (2nd row) ====
        col_ai, col_trend = st.columns([1.35, 1])

        with col_ai:
            st.markdown('<div class="nv-card">', unsafe_allow_html=True)
            st.markdown('<div class="nv-card-header">NoVac AI Copilot Insight</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="ai-thinking"><div class="ai-dot"></div><span>Copilot is analyzing live data...</span></div><br><br>',
                unsafe_allow_html=True,
            )
            with st.spinner("🧠 Thinking like an environmental expert..."):
                ai_text = ai_agent_analysis(
                    result["current"],
                    result["trend"],
                    result["spike"],
                    result["spike_change"],
                    result["forecast"]
                )
            st.write(ai_text)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_trend:
            st.markdown('<div class="nv-card">', unsafe_allow_html=True)
            st.markdown('<div class="nv-card-header">Recent PM2.5 Trajectory</div>', unsafe_allow_html=True)
            st.line_chart(result["history"])
            st.markdown("</div>", unsafe_allow_html=True)

        # ===========================
        # WHATSAPP SMART ALERT LOGIC
        # ===========================
        # Only send alerts on manual runs (not in auto_mode)
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
    st.info("Click **Run Analysis Now** or enable **Autonomous Mode** to wake the Copilot.")
