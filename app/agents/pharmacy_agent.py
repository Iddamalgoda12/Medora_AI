import json
from app.graphs.state import State
from app.tools.pharmacy_search import find_multi_medicine_stock, geocode_address
from app.llms.gemini import ask_gemini_async
from app.agents.response_utils import append_agent_response


async def pharmacy_agent(state: State):
    """
    Pharmacy agent finds medicines and pharmacies based on user location and drug names.
    """
    query = state.get("query", "")
    user_location = state.get("user_location")
    drug_list = state.get("medicine_names", [])

    # Reuse a city already collected by the appointment workflow.
    if not user_location and state.get("location"):
        saved_location = state["location"]
        geo_info = geocode_address(saved_location)
        if geo_info:
            user_location = {
                "address_name": geo_info.get("formatted", saved_location),
                "lat": geo_info.get("lat", 6.9271),
                "lng": geo_info.get("lng", 80.7789),
            }

    # 1. Extract both medicines AND location from the query
    extraction_prompt = (
        f"Extract information from this text:\n"
        f"1. All medicine/drug names (respond with JSON list like [\"Paracetamol\", \"Aspirin\"])\n"
        f"2. Any location/city mentioned (respond with the city name or 'NONE')\n\n"
        f"Format your response as JSON: {{\"medicines\": [...], \"location\": \"...\"}}\n\n"
        f"Text: {query}"
    )
    response = await ask_gemini_async(extraction_prompt)

    try:
        clean_content = response.strip()
        if clean_content.startswith("```json"):
            clean_content = clean_content.replace("```json", "").replace("```", "").strip()

        # Try to extract JSON
        start_idx = clean_content.find("{")
        end_idx = clean_content.rfind("}") + 1
        if start_idx >= 0 and end_idx > start_idx:
            clean_content = clean_content[start_idx:end_idx]

        extracted = json.loads(clean_content)
        extracted_drugs = extracted.get("medicines", [])
        if extracted_drugs:
            drug_list = extracted_drugs
        location_from_query = extracted.get("location", "NONE")

        if location_from_query and location_from_query.upper() != "NONE":
            geo_info = geocode_address(location_from_query)
            if geo_info:
                user_location = {
                    "address_name": geo_info.get("formatted", location_from_query),
                    "lat": geo_info.get("lat", 6.9271),
                    "lng": geo_info.get("lng", 80.7789)
                }
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass

    # 2. If we still don't have a location, ask for it
    if not user_location:
        return {
            **state,
            "response": append_agent_response(
                state.get("response", ""),
                "📍 To find medicines near you, could you please tell me your current city or neighborhood? (e.g., Colombo, Bambalapitiya, Kandy)",
            ),
            "needs_user_input": True,
            "medicine_names": drug_list,
            "pending_tasks": ["pharmacy_agent", *state.get("pending_tasks", [])],
            "execution_trace": [*state["execution_trace"], "pharmacy_agent"]
        }

    # 3. If we don't have medicines, ask for them
    if not drug_list:
        return {
            **state,
            "response": append_agent_response(
                state.get("response", ""),
                "💊 Could you please specify the names of the medicines you're looking for? (e.g., Paracetamol, Aspirin, Antibiotics)",
            ),
            "needs_user_input": True,
            "user_location": user_location,
            "medicine_names": [],
            "pending_tasks": ["pharmacy_agent", *state.get("pending_tasks", [])],
            "execution_trace": [*state["execution_trace"], "pharmacy_agent"]
        }


    # 4. Search for medicines at pharmacies
    try:
        USER_LAT = user_location["lat"]
        USER_LNG = user_location["lng"]

        results = find_multi_medicine_stock(drug_list, USER_LAT, USER_LNG)
        single_stops = results.get("single_stop_options", [])
        availability = results.get("availability_map", {})
    except Exception as e:
        return {
            **state,
            "response": f"Error searching pharmacies: {str(e)}. Please try with a different location.",
            "execution_trace": [*state["execution_trace"], "pharmacy_agent"]
        }

    # 4. Format response
    location_name = user_location.get("address_name", "your location")
    response_msg = f"📍 **Distances calculated from:** {location_name}\n\n"

    if single_stops:
        # All medicines available at one pharmacy
        best = single_stops[0]
        response_msg += (
            f"🛒 **All-in-One Availability Found!**\n\n"
            f"📍 **Pharmacy:** {best.get('pharmacy_name', 'Unknown')}\n"
            f"🗺️ **Address:** {best.get('address', 'N/A')}\n"
            f"📏 **Distance:** {best.get('distance_km', 'N/A')} km away\n\n"
            f"**Medicines Available:**\n"
        )
        items = best.get("items", [])
        for item in items:
            drug_name = item.get("exact_drug", "Unknown")
            price = item.get("price", item.get("price_lkr", "N/A"))
            response_msg += f"  💊 {drug_name} - LKR {price}\n"
    else:
        # Split order between multiple pharmacies
        response_msg += "⚠️ **Split-Order Plan**\n\nNo single pharmacy has all items. Here's your location-optimized plan:\n\n"

        store_recommendations = {}
        missing_drugs = []

        for drug in drug_list:
            options = availability.get(drug, [])
            if options:
                closest_store = options[0]
                p_name = closest_store.get('pharmacy_name', 'Unknown')
                if p_name not in store_recommendations:
                    store_recommendations[p_name] = {
                        "address": closest_store.get('address', 'N/A'),
                        "distance": closest_store.get('distance_km', 'N/A'),
                        "items": []
                    }
                price = closest_store.get('price', closest_store.get('price_lkr', 'N/A'))
                store_recommendations[p_name]["items"].append(f"{drug} - LKR {price}")
            else:
                missing_drugs.append(drug)

        # Format store recommendations
        for store_name, data in store_recommendations.items():
            response_msg += f"📍 **{store_name}** ({data['distance']} km away)\n"
            response_msg += f"   📍 {data['address']}\n"
            for item in data["items"]:
                response_msg += f"   💊 {item}\n"
            response_msg += "\n"

        # Show out of stock items
        if missing_drugs:
            response_msg += f"\n❌ **Out of Stock:** {', '.join(missing_drugs)}\n"

    return {
        **state,
        "response": append_agent_response(
            state.get("response", ""),
            response_msg,
        ),
        "user_location": user_location,
        "medicine_names": [],
        "medicine_request": True,
        "needs_user_input": False,
        "execution_trace": [*state["execution_trace"], "pharmacy_agent"]
    }
