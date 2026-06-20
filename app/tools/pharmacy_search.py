import sqlite3
import math
import urllib.parse
import urllib.request
import json
from typing import List, Dict
from app.config.settings import settings

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates straight-line distance in kilometers using the Haversine formula."""
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def geocode_address(address_text: str) -> dict:
    """
    Converts a conversational address string into coordinates using the Geoapify API.
    Filters specifically for Sri Lanka (countrycode:lk).
    """
    api_key = settings.GEOAPIFY_API_KEY
    if not api_key:
        raise ValueError("GEOAPIFY_API_KEY is missing from configurations.")
        
    encoded_text = urllib.parse.quote(address_text)
    url = f"https://api.geoapify.com/v1/geocode/search?text={encoded_text}&filter=countrycode:lk&apiKey={api_key}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Medora-Agentic-Platform'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
        if data.get("features"):
            first_match = data["features"][0]
            lon, lat = first_match["geometry"]["coordinates"]
            formatted_address = first_match["properties"].get("formatted", address_text)
            
            return {
                "lat": lat,
                "lng": lon,
                "formatted": formatted_address
            }
    except Exception as e:
        # Propagate error up to the agent execution state loop
        raise RuntimeError(f"Geoapify Geocoding network service failure: {e}")
        
    return None

def find_multi_medicine_stock(drug_list: List[str], user_lat: float, user_lng: float) -> Dict:
    """
    Queries inventory availability and optimizes results relative to coordinates.
    """
    conn = sqlite3.connect("pharmacy_mock.db")
    cursor = conn.cursor()
    
    availability_map = {drug: [] for drug in drug_list}
    
    for drug in drug_list:
        query = """
            SELECT p.name, p.address, p.lat, p.lng, i.stock_level, i.price, i.drug_name
            FROM inventory i
            JOIN pharmacies p ON i.pharmacy_id = p.id
            WHERE i.drug_name LIKE ? AND i.stock_level > 0
        """
        cursor.execute(query, (f"%{drug}%",))
        rows = cursor.fetchall()
        
        for row in rows:
            dist = calculate_distance(user_lat, user_lng, row[2], row[3])
            availability_map[drug].append({
                "pharmacy_name": row[0],
                "address": row[1],
                "exact_drug": row[6],
                "stock": row[4],
                "price_lkr": row[5],
                "distance_km": dist
            })
        
        availability_map[drug].sort(key=lambda x: x["distance_km"])
        
    conn.close()
    
    pharmacy_fulfillment = {}
    for drug, options in availability_map.items():
        for opt in options:
            p_name = opt["pharmacy_name"]
            if p_name not in pharmacy_fulfillment:
                pharmacy_fulfillment[p_name] = {"info": opt, "available_items": []}
            pharmacy_fulfillment[p_name]["available_items"].append({
                "requested_item": drug,
                "exact_drug": opt["exact_drug"],
                "price": opt["price_lkr"],
                "stock": opt["stock"]
            })
            
    all_in_one_options = []
    for p_name, data in pharmacy_fulfillment.items():
        if len(data["available_items"]) == len(drug_list):
            all_in_one_options.append({
                "pharmacy_name": p_name,
                "address": data["info"]["address"],
                "distance_km": data["info"]["distance_km"],
                "items": data["available_items"]
            })
            
    all_in_one_options.sort(key=lambda x: x["distance_km"])
    
    return {
        "availability_map": availability_map,
        "single_stop_options": all_in_one_options,
    }