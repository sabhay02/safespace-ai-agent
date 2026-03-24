import requests

def find_nearby_therapists_by_location(location: str) -> str:

    headers = {
        "User-Agent": "safespace-ai-agent"
    }

    # Step 1: Convert location → coordinates
    geo_url = "https://nominatim.openstreetmap.org/search"
    geo_params = {
        "q": location,
        "format": "json",
        "limit": 1
    }

    geo_res = requests.get(geo_url, params=geo_params, headers=headers)

    try:
        geo_data = geo_res.json()
    except:
        return "Failed to fetch location coordinates."

    if not geo_data:
        return f"Location not found: {location}"

    lat = geo_data[0]["lat"]
    lon = geo_data[0]["lon"]

    # Step 2: Query therapists from Overpass
    overpass_query = f"""
    [out:json];
    (
      node["healthcare"="psychotherapist"](around:5000,{lat},{lon});
      node["healthcare"="psychologist"](around:5000,{lat},{lon});
      node["amenity"="clinic"](around:5000,{lat},{lon});
    );
    out;
    """

    overpass_url = "https://overpass-api.de/api/interpreter"

    response = requests.post(overpass_url, data=overpass_query, headers=headers)

    try:
        data = response.json()
    except:
        return "Overpass API returned invalid response."

    elements = data.get("elements", [])

    if not elements:
        return f"No therapists found near {location}"

    results = []

    for place in elements[:5]:
        name = place.get("tags", {}).get("name", "Unnamed Clinic")
        lat = place["lat"]
        lon = place["lon"]

        maps_link = f"https://www.google.com/maps?q={lat},{lon}"

        results.append(f"{name}\n📍 {maps_link}")

    return "Therapists near {}:\n\n{}".format(location, "\n\n".join(results))


print(find_nearby_therapists_by_location("Mumbai"))