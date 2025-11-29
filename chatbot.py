# -------------------------------------------------------
# VAYU ULTRA — NoVac Agentic Environmental Chatbot
# -------------------------------------------------------

import streamlit as st
from groq import Groq
import os
from spike import run_copilot
from aqi import fetch_current_aqi, fetch_city_stations


# -------------------------------------------------------
# SYSTEM + PERSONALITY
# -------------------------------------------------------
VAYU_SYSTEM_PROMPT = """
You are VAYU ULTRA — NoVac's advanced environmental intelligence agent.

Personality:
- Calm, scientific, friendly
- Expert in AQI, PM2.5, spikes, forecasting, and health effects
- Explains clearly and concisely
- Uses clean formatting + well-placed emojis 🌱💨📈

Abilities:
- Fetch live AQI for any city
- Analyze spikes, trends, and forecasts
- Provide safety + health recommendations
- Show nearby AQI monitoring stations
"""


# -------------------------------------------------------
# LLM RESPONSE
# -------------------------------------------------------
def vayu_llm(messages):
    try:
        api_key = os.getenv("GROQ_API_KEY") or st.secrets["groq_api_key"]
        client = Groq(api_key=api_key)

        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
        )
        return resp.choices[0].message.content

    except Exception as e:
        return f"⚠️ VAYU offline: {e}"


# -------------------------------------------------------
# CITY DETECTOR
# -------------------------------------------------------
def extract_city(text):
    words = text.lower().replace(",", " ").split()
    possible = [w.capitalize() for w in words if w.isalpha() and len(w) >= 3]
    return possible[-1] if possible else None


# -------------------------------------------------------
# DECISION ENGINE BADGE FORMATTER
# -------------------------------------------------------
def format_decision_engine(dec):
    if not isinstance(dec, dict):
        return "<div>⚠️ Decision data unavailable.</div>"

    # Extract fields
    status = dec.get("status", "N/A")
    severity = dec.get("severity", "N/A")
    action = dec.get("action", "N/A")
    details = dec.get("details", "")
    risk = dec.get("risk", "N/A")

    # Colors
    color_map = {
        "Low": "#8BFF8B",
        "Moderate": "#FFE36E",
        "High": "#FF6B6B"
    }

    sev_color = color_map.get(severity, "#D1D5DB")
    risk_color = color_map.get(risk, "#D1D5DB")

    # Badge function
    def badge(text, col):
        return f"""
        <span style="
            background:{col};
            padding:4px 10px;
            border-radius:8px;
            color:black;
            font-weight:600;
            font-size:0.8rem;">
            {text}
        </span>
        """

    return f"""
    <div style="margin-top:10px;margin-bottom:10px;">
        <h4 style="margin-bottom:6px;">🧠 Decision Engine</h4>
        <div><strong>Status:</strong> {status}</div>
        <div><strong>Severity:</strong> {badge(severity, sev_color)}</div>
        <div><strong>Action:</strong> {action}</div>
        <div><strong>Details:</strong> {details}</div>
        <div><strong>Risk:</strong> {badge(risk, risk_color)}</div>
    </div>
    """


# -------------------------------------------------------
# CHATBOT UI
# -------------------------------------------------------
def vayu_chatbot_ui():
    # Inject CSS styles
    st.markdown("""
        <style>
        .nv-card-header {
            font-size: 1.5rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .chat-bubble-user {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 16px;
            border-radius: 18px 18px 4px 18px;
            margin: 8px 0;
            max-width: 80%;
            margin-left: auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .chat-bubble-vayu {
            background: #f1f3f4;
            color: #333;
            padding: 12px 16px;
            border-radius: 18px 18px 18px 4px;
            margin: 8px 0;
            max-width: 80%;
            margin-right: auto;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .mini-clear-btn button {
            padding: 2px 8px !important;
            font-size: 11px !important;
            border-radius: 6px !important;
            background: linear-gradient(135deg,#ff4dd8,#3bffb3) !important;
            color: black !important;
            border: none !important;
        }
        .stForm {
            border: none !important;
            padding: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="nv-card-header">VAYU · NoVac AI Chatbot</div>
        <p style="opacity:0.7;margin-bottom:10px;">
            Ask me anything about AQI, pollution, PM2.5, health risks, or city conditions.
        </p>
    """, unsafe_allow_html=True)

    # Mini clear button
    _, colB = st.columns([6, 1])
    with colB:
        if st.button("Clear Chat", key="vayu_clear"):
            st.session_state.vayu_history = []
            st.rerun()

    # Chat history container with scroll
    chat_container = st.container()
    
    with chat_container:
        if "vayu_history" not in st.session_state:
            st.session_state.vayu_history = []

        # Show history
        for role, msg in st.session_state.vayu_history:
            if role == "user":
                st.markdown(f"<div class='chat-bubble-user'><b>You:</b> {msg}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-bubble-vayu'><b>VAYU:</b> {msg}</div>", unsafe_allow_html=True)

    # Input form - Fixed to prevent auto-scroll
    with st.form(key="vayu_chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input(
                "Ask VAYU something:",
                key="vayu_input",
                placeholder="e.g., What's the AQI in Delhi?",
                label_visibility="collapsed"
            )
        with col2:
            submitted = st.form_submit_button("Send 🚀")

    if submitted and user_input.strip():
        # Add user message to history
        st.session_state.vayu_history.append(("user", user_input))

        # -------------------------------------------------------
        # Detect AQI query + city
        # -------------------------------------------------------
        msg_low = user_input.lower()
        is_aqi_query = any(k in msg_low for k in ["aqi", "air", "pollution", "pm", "quality"])
        city = extract_city(user_input)

        # -------------------------------------------------------
        # TOOL MODE (AQI)
        # -------------------------------------------------------
        if is_aqi_query and city:
            try:
                # Main AQI
                result, _, _, _ = run_copilot(city, None, [], mock=False)

                if result is None:
                    st.session_state.vayu_history.append(
                        ("vayu", f"⚠️ I couldn't fetch AQI for **{city}**. Please check the city name and try again.")
                    )
                    st.rerun()

                current = result.get("current", "N/A")
                trend = result.get("trend", "-")
                spike = result.get("spike", False)
                spike_change = result.get("spike_change", 0)
                forecast = result.get("forecast", [])
                decision = result.get("decision", {})

                # Sub-stations
                stations = fetch_city_stations(city)
                station_text = (
                    "\n".join([f"- **{s['station']}** → {s['value']}" for s in stations[:6]])
                    if stations else "No monitoring stations available."
                )

                # Decision Engine formatted block
                decision_html = format_decision_engine(decision)

                tool_msg = f"""
📍 **City:** {city}

**PM2.5 (Overall):** {current}  
**Trend:** {trend}  
**Spike:** {spike} (+{spike_change})  
**Forecast:** {forecast}

🏙️ **Nearby AQI Stations:**  
{station_text}

{decision_html}
"""

                messages = [
                    {"role": "system", "content": VAYU_SYSTEM_PROMPT},
                    {"role": "assistant", "content": tool_msg},
                    {"role": "user", "content": user_input}
                ]

                reply = vayu_llm(messages)
                st.session_state.vayu_history.append(("vayu", reply))
                st.rerun()

            except Exception as e:
                error_msg = f"⚠️ Error fetching AQI data: {str(e)}"
                st.session_state.vayu_history.append(("vayu", error_msg))
                st.rerun()

        # -------------------------------------------------------
        # NORMAL CHAT MODE
        # -------------------------------------------------------
        else:
            messages = [{"role": "system", "content": VAYU_SYSTEM_PROMPT}]
            for role, msg in st.session_state.vayu_history:
                messages.append({"role": "assistant" if role == "vayu" else "user", "content": msg})

            reply = vayu_llm(messages)
            st.session_state.vayu_history.append(("vayu", reply))
            st.rerun()