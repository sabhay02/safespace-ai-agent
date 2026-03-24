from langchain.tools import tool
from backend.tools import query_medgemma,call_emergency
import requests

@tool
def ask_mental_health_specialist(query: str) -> str:
    """
    Generate a therapeutic response using the MedGemma model.
    Use this for all general user queries, mental health questions, emotional concerns,
    or to offer empathetic, evidence-based guidance in a conversational tone.
    """
    return query_medgemma(query)

@tool
def emergency_call_tool(phone:str) -> str:
    """
    Place an emergency call to the safety helpline's phone number via Twilio.
    Use this only if the user expresses suicidal ideation, intent to self-harm,
    or describes a mental health emergency requiring immediate help.
    """
    return call_emergency(phone)

@tool
def find_nearby_therapists_by_location(location: str) -> str:
    """
    Finds licensed therapists, psychologists, or mental health clinics near a given city.

    This tool:
    1. Converts the city name into geographic coordinates using OpenStreetMap.
    2. Searches for nearby therapists, psychologists, or clinics within a 5 km radius.
    3. Returns up to 5 nearby results with a Google Maps link.

    Args:
        location (str): Name of the city or area where the user wants to find therapists.

    Returns:
        str: A formatted list of nearby therapists including their names and map links.
    """

    headers = {"User-Agent": "safespace-ai-agent"}

    # Step 1: Convert location → coordinates
    geo_url = "https://nominatim.openstreetmap.org/search"
    geo_params = {"q": location, "format": "json", "limit": 1}

    geo_res = requests.get(geo_url, params=geo_params, headers=headers)

    try:
        geo_data = geo_res.json()
    except:
        return "Failed to fetch location coordinates."

    if not geo_data:
        return f"Location not found: {location}"

    lat = geo_data[0]["lat"]
    lon = geo_data[0]["lon"]

    # Step 2: Query therapists from Overpass API
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

    return "Here are therapists near {}:\n\n{}".format(location, "\n\n".join(results))


#step 1 create an ai agent and link to backend
from langgraph.prebuilt import create_react_agent
from backend.config import GROQ_API_KEY

tools=[ask_mental_health_specialist, emergency_call_tool, find_nearby_therapists_by_location]

from langchain_groq import ChatGroq

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.3,
    groq_api_key=GROQ_API_KEY
)
graph = create_react_agent(model=llm, tools=tools)

SYSTEM_PROMPT = """
You are an AI engine supporting mental health conversations with warmth and vigilance.
You have access to three tools:

1. `ask_mental_health_specialist`: Use this tool to answer all emotional or psychological queries with therapeutic guidance.
2. `locate_therapist_tool`: Use this tool if the user asks about nearby therapists or if recommending local professional help would be beneficial.
3. `emergency_call_tool`: Use this immediately if the user expresses suicidal thoughts, self-harm intentions, or is in crisis.

Always take necessary action. Respond kindly, clearly, and supportively.
"""

def parse_response(stream):
    tool_called_name = "None"
    final_response = None

    for s in stream:
        # Check if a tool was called
        tool_data = s.get('tools')
        if tool_data:
            tool_messages = tool_data.get('messages')
            if tool_messages and isinstance(tool_messages, list):
                for msg in tool_messages:
                    tool_called_name = getattr(msg, 'name', 'None')

        # Check if agent returned a message
        agent_data = s.get('agent')
        if agent_data:
            messages = agent_data.get('messages')
            if messages and isinstance(messages, list):
                for msg in messages:
                    if msg.content:
                        final_response = msg.content

    return tool_called_name, final_response


"""
if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        print(f"received user input: {user_input}")
        inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", user_input)]}
        stream = graph.stream(inputs, stream_mode="updates")
        tool_called_name, final_response = parse_response(stream)
        print("TOOL CALLED: ", tool_called_name)
        print("ANSWER: ", final_response)
"""