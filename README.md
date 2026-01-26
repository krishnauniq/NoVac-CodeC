# 🌬️ NoVac — The Air Quality Copilot  
### Agentic AI for Real-Time Pollution Awareness & Health Guidance

**Live Demo:** https://novac-codec.streamlit.app/

---

## 🚨 Problem
Air pollution, especially *PM2.5*, is a major health concern in cities like Delhi or Mumbai.  
Most AQI apps only show numbers — they don’t explain risks or tell users what actions to take.

People need *clear, proactive, personalized guidance*, not just raw AQI data.

---

## 🤖 Our Solution — NoVac
NoVac is an *Agentic AI–driven Air Quality Copilot* that interprets air-quality data and recommends real-time actions to protect user health.

### ⭐ Core Features
- **Real-Time AQI Dashboard**  
  Live PM2.5, PM10, and pollutant levels with simple visualization.

- **Interactive AQI Heatmap**  
  City-wide pollution overview with hyper-local concentration zones.

- **VAYU GPT Chatbot**  
  Groq + Llama 3 powered assistant for answering health, AQI, and safety questions.

- **AI Copilot Mode**  
  - Health risk level  
  - Short & clear air-quality summary  
  - Trend detection  
  - 3-day PM2.5 forecast  
  - Actionable recommendations  

- **WhatsApp Alerts**  
  Real-time notifications for sudden spikes or improved conditions.

---

## 📸 Screenshots

### 🔹 Real-Time AQI Visualizer
<img src="screenshots/Screenshot%202026-01-26%20153802.png" width="900"/>

### 🔹 AI Copilot Dashboard (Decision Space)
<img src="screenshots/Screenshot%202026-01-26%20153839.png" width="900"/>

### 🔹 WhatsApp Real-Time Alert System
<img src="screenshots/Screenshot%202026-01-26%20154137.png" width="900"/>

### 🔹 VAYU GPT – AQI Conversational Assistant
<img src="screenshots/Screenshot%202026-01-26%20154346.png" width="900"/>

### 🔹 Interactive City Heatmap
<img src="screenshots/Screenshot%202026-01-26%20154434.png" width="900"/>




---

## 🧠 Tech Stack
- **Frontend:** Streamlit  
- **Backend:** Python  
- **AI Engine:** Groq + Llama 3  
- **Data:** OpenWeather, OpenAQ  
- **Other:** WhatsApp Cloud API  
- **Deployment:** Cloud (GCP)

---

## 🚀 Future Enhancements
- Hyper-local AQI using IoT sensors  
- Computer Vision–based smog detection from sky photos  
- Extended forecasting models  
- Pan-India city support  
- Offline/SMS alerts

---

## 🧪 Run Locally

```bash
git clone https://github.com/krishnauniq/NoVac.git
cd NoVac
pip install -r requirements.txt
streamlit run app.py
