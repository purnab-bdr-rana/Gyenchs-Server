import requests

def get_location_from_ip(ip):
    try:
        response = requests.get(f"https://ipwho.is/{ip}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                city = data.get("city", "")
                region = data.get("region", "")
                country = data.get("country", "")
                return f"{city}, {region}, {country}"
    except Exception:
        pass
    return "Unknown location"
