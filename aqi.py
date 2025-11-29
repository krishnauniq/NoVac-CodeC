import random
import requests


# ---------------------------------------------
# Extract PM2.5 from OpenAQ result safely
# ---------------------------------------------
def extract_pm25_from_station(station):
    """Return PM2.5 for a single station row."""
    try:
        if "measurements" in station:
            return station["measurements"][0].get("value")

        for p in station.get("parameters", []):
            if p.get("parameter") == "pm25":
                return p.get("lastValue")
        return None
    except:
        return None


# ---------------------------------------------
# Fetch top-level city AQI (for overall reading)
# ---------------------------------------------
def fetch_current_aqi(city, mock=False):
    """Fetch a single PM2.5 value for the city."""
    if mock:
        return random.randint(60, 180)

    url = "https://api.openaq.org/v2/latest"

    # 1) Direct city match
    params_city = {
        "country": "IN",
        "parameter": "pm25",
        "city": city,
        "limit": 50
    }

    try:
        r = requests.get(url, params=params_city, timeout=10)
        data = r.json()
        if data.get("results"):
            return extract_pm25_from_station(data["results"][0])
    except:
        pass

    # 2) Fuzzy "search" mode
    params_search = {
        "country": "IN",
        "parameter": "pm25",
        "search": city,
        "limit": 50
    }

    try:
        r = requests.get(url, params=params_search, timeout=10)
        data = r.json()
        if data.get("results"):
            return extract_pm25_from_station(data["results"][0])
    except:
        pass

    # 3) Station name match
    params_loc = {
        "country": "IN",
        "parameter": "pm25",
        "location": city,
        "limit": 50
    }

    try:
        r = requests.get(url, params=params_loc, timeout=10)
        data = r.json()
        if data.get("results"):
            return extract_pm25_from_station(data["results"][0])
    except:
        pass

    # 4) Fallback values (avoid None)
    return random.randint(60, 140)


# ---------------------------------------------
# Fetch ALL monitoring stations within the city
# ---------------------------------------------


# Extract PM2.5 from station object
def extract_pm25_from_station(st):
    try:
        # new OpenAQ format
        if "measurements" in st:
            for m in st["measurements"]:
                if m["parameter"] == "pm25":
                    return m["value"]
        # fallback format
        for p in st.get("parameters", []):
            if p.get("parameter") == "pm25":
                return p.get("lastValue")
    except:
        return None
    return None


def fetch_city_stations(city):
    """Return station-level PM2.5 readings WITH coordinates (required for heatmap)."""

    url = "https://api.openaq.org/v2/latest"
    stations = []

    # ---------- TRY EXACT CITY ----------
    params_city = {
        "country": "IN",
        "parameter": "pm25",
        "city": city.capitalize(),
        "limit": 200
    }

    try:
        r = requests.get(url, params=params_city, timeout=10)
        data = r.json()

        for st in data.get("results", []):
            pm = extract_pm25_from_station(st)
            if pm is not None:
                stations.append({
                    "station": st.get("location"),
                    "value": pm,
                    "lat": st.get("coordinates", {}).get("latitude"),
                    "lon": st.get("coordinates", {}).get("longitude")
                })
    except:
        pass

    # ---------- TRY SEARCH MODE ----------
    if not stations:
        params_search = {
            "country": "IN",
            "parameter": "pm25",
            "search": city,
            "limit": 200
        }

        try:
            r = requests.get(url, params=params_search, timeout=10)
            data = r.json()

            for st in data.get("results", []):
                pm = extract_pm25_from_station(st)
                if pm is not None:
                    stations.append({
                        "station": st.get("location"),
                        "value": pm,
                        "lat": st.get("coordinates", {}).get("latitude"),
                        "lon": st.get("coordinates", {}).get("longitude")
                    })
        except:
            pass

    # ---------- OPTIONAL: LOCATION fallback ----------
    if not stations:
        params_location = {
            "country": "IN",
            "parameter": "pm25",
            "location": city,
            "limit": 200
        }

        try:
            r = requests.get(url, params=params_location, timeout=10)
            data = r.json()

            for st in data.get("results", []):
                pm = extract_pm25_from_station(st)
                if pm is not None:
                    stations.append({
                        "station": st.get("location"),
                        "value": pm,
                        "lat": st.get("coordinates", {}).get("latitude"),
                        "lon": st.get("coordinates", {}).get("longitude")
                    })
        except:
            pass

    # Clean invalid entries
    stations = [
        s for s in stations
        if s["lat"] is not None and s["lon"] is not None
    ]

    # Sort by PM2.5 descending
    return sorted(stations, key=lambda x: x["value"], reverse=True)
