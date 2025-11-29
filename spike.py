import random
from aqi import fetch_current_aqi
   # adjust import if needed

def detect_spike(current, last, threshold=40):
    if last is None:
        return False, 0
    change = current - last
    return change >= threshold, change


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


def forecast_pm25(history, days=3):
    if len(history) < 2:
        return [history[-1]] * days

    last = history[-1]
    prev = history[-2]
    slope = last - prev  # direction

    forecast = []
    value = last

    for _ in range(days):
        if slope > 10:
            value += random.uniform(5, 12)
        elif slope < -10:
            value -= random.uniform(5, 12)
        else:
            value += random.uniform(-4, 4)

        value = max(5, min(value, 400))
        forecast.append(round(value, 2))

    return forecast


def copilot_decision(aqi, last_aqi, trend, spike, spike_change):
    if spike:
        return {
            "status": "Spike Detected",
            "severity": "High",
            "action": "ALERT",
            "details": f"PM2.5 jumped by {spike_change}.",
            "risk": "High",
        }
    if aqi >= 200:
        return {
            "status": "Very Unhealthy",
            "severity": "High",
            "action": "WARNING",
            "details": "Hazardous levels.",
            "risk": "High",
        }
    if aqi >= 150:
        return {
            "status": "Unhealthy",
            "severity": "Medium",
            "action": "CAUTION",
            "details": "Air quality harmful.",
            "risk": "Medium",
        }
    if trend == "up":
        return {
            "status": "Rising Pollution",
            "severity": "Low",
            "action": "MONITOR",
            "details": "Slow rise detected.",
            "risk": "Low",
        }
    return {
        "status": "Normal",
        "severity": "Low",
        "action": "NONE",
        "details": "Air quality acceptable.",
        "risk": "Low",
    }


def run_copilot(city, last_aqi, history, mock=False):
    current = fetch_current_aqi(city, mock=mock)
    if current is None:
        return None, "API error", last_aqi, history

    history.append(current)

    spike, spike_change = detect_spike(current, last_aqi)
    trend = trend_direction(history)
    decision = copilot_decision(current, last_aqi, trend, spike, spike_change)
    forecast = forecast_pm25(history)

    return (
        {
            "current": current,
            "last": last_aqi,
            "trend": trend,
            "spike": spike,
            "spike_change": spike_change,
            "decision": decision,
            "forecast": forecast,
            "history": history[-20:],
        },
        "OK",
        current,
        history,
    )
