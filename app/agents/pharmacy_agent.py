import os
import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.tools.pharmacy_search import find_multi_medicine_stock, geocode_address
from app.llms.gemini import get_llm

async def pharmacy_agent(state: dict):
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [SystemMessage(content="No user query detected.")], "next_action": "decision_engine"}

    user_query = messages[-1].content
    user_location = state.get("user_location")
    llm = get_llm(temperature=0.0)
    
    # 1. Evaluate and capture location state if missing
    if not user_location:
        location_check_prompt = (
            f"Determine if the following text is primarily a location statement, city name, or address "
            f"(e.g., 'I am at Galle Face', 'Kandy', 'Colombo 03'). "
            f"Respond with ONLY 'YES' or 'NO'.\n\nText: {user_query}"
        )
        is_location = await llm.ainvoke([HumanMessage(content=location_check_prompt)])
        
        if "YES" in is_location.content.upper():
            geo_info = geocode_address(user_query)
            if geo_info:
                state["user_location"] = {
                    "address_name": geo_info["formatted"],
                    "lat": geo_info["lat"],
                    "lng": geo_info["lng"]
                }
                user_location = state["user_location"]
                
                # Re-fetch prescription context from conversation depth history
                if len(messages) >= 3:
                    user_query = messages[-3].content 
            else:
                return {
                    "messages": [SystemMessage(content="📍 We couldn't verify that location structure. Could you please specify a clearer city or landmark name in Sri Lanka?")],
                    "next_action": "pharmacy"
                }
        else:
            return {
                "messages": [SystemMessage(content="📍 To calculate distances precisely, could you please tell me your current city or neighborhood (e.g., Bambalapitiya, Battaramulla)?")],
                "next_action": "pharmacy"
            }

    # 2. Extract medical items
    extraction_prompt = (
        f"Extract all medical drug names mentioned in the text below. "
        f"Correct obvious typos to standard medical names. "
        f"Respond ONLY with a valid JSON string list of strings. Text: {user_query}"
    )
    response = await llm.ainvoke([HumanMessage(content=extraction_prompt)])
    
    try:
        clean_content = response.content.strip().replace("```json", "").replace("```", "")
        drug_list = json.loads(clean_content)
    except Exception:
        drug_list = []
        
    if not drug_list:
        return {
            "messages": [SystemMessage(content="Could you please specify the names of the medicines you are looking for?")],
            "next_action": "decision_engine"
        }

    # 3. Process Optimized Sourcing Map
    USER_LAT = user_location["lat"]
    USER_LNG = user_location["lng"]
    
    results = find_multi_medicine_stock(drug_list, USER_LAT, USER_LNG)
    single_stops = results["single_stop_options"]
    availability = results["availability_map"]
    
    response_msg = f" *Distances calculated relative to:* `{user_location['address_name']}`\n\n"
    
    if single_stops:
        best = single_stops[0]
        response_msg += (
            f" **All-in-One Availability Found!**\n"
            f" **Store:** {best['pharmacy_name']}\n"
            f" **Address:** {best['address']} (**{best['distance_km']} km away**)\n\n"
            f"**Items available there:**\n"
        )
        for item in best["items"]:
            response_msg += f"- {item['exact_drug']} (LKR {item['price']} per unit)\n"
    else:
        response_msg += "**Optimized Split-Order Plan**\n\nNo single pharmacy has everything in stock. Here is your location-optimized combination plan:\n\n"
        store_recommendations = {}
        missing_drugs = []
        
        for drug in drug_list:
            options = availability.get(drug, [])
            if options:
                closest_store = options[0]
                p_name = closest_store['pharmacy_name']
                if p_name not in store_recommendations:
                    store_recommendations[p_name] = {
                        "address": closest_store['address'],
                        "distance": closest_store['distance_km'],
                        "items": []
                    }
                store_recommendations[p_name]["items"].append(f"{closest_store['exact_drug']} (LKR {closest_store['price_lkr']})")
            else:
                missing_drugs.append(drug)
        
        for store, data in store_recommendations.items():
            response_msg += f" **At {store} ({data['distance']} km away):**\n"
            for item in data["items"]:
                response_msg += f"    - {item}\n"
            response_msg += "\n"
            
        if missing_drugs:
            response_msg += f"Out of stock across network: {', '.join(missing_drugs)}"

    return {
        "messages": [SystemMessage(content=response_msg)],
        "user_location": user_location,
        "next_action": "decision_engine"
    }