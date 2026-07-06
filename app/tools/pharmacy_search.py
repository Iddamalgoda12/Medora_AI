import sqlite3
import math
import urllib.parse
import urllib.request
import json
from typing import List, Dict
from google import genai
from app.config.settings import settings

# Initialize Gemini Client for document analysis
client = genai.Client(api_key=settings.GEMINI_API_KEY)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates straight-line distance in kilometers using the Haversine formula."""
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def geocode_address(address_text: str) -> dict:
    """Converts a conversational address string into coordinates using Geoapify."""
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
            
            return {"lat": lat, "lng": lon, "formatted": formatted_address}
    except Exception as e:
        raise RuntimeError(f"Geoapify Geocoding network service failure: {e}")
        
    return None

def find_multi_medicine_stock(drug_list: List[str], user_lat: float, user_lng: float) -> Dict:
    """Queries inventory availability and optimizes results relative to coordinates."""
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

# ==========================================
# AGENTIC ROUTING & PROACTIVE ANALYSIS
# ==========================================

def analyze_proactive_document(text_content: str) -> dict:
    """
    Classifies the document and generates the exact UI message to proactively send to the user.
    """
    prompt = f"""
    Analyze the following extracted medical document text. Determine if it is a medical prescription or a laboratory test result/blood report.
    
    1. If it is a PRESCRIPTION:
       - Extract an explicit array of drug names along with their dosages.
    
    2. If it is a LAB TEST / MEDICAL REPORT:
       - Provide a "condition_summary" giving a clear overview of the general condition.
       - Assess the "severity" strictly as either "MILD" or "MODERATE_SEVERE".
       - Always provide "doctor_instructions" advising on what type of doctor the user should visit (e.g., General Practitioner, Cardiologist) and how urgently.
       - If the condition is "MILD", provide "mitigation_advice" on lifestyle changes or general advice to reduce the issue safely.

    Document Text:
    \"\"\"{text_content}\"\"\"
    """

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "document_type": {"type": "STRING", "enum": ["PRESCRIPTION", "LAB_REPORT"]},
            "extracted_drugs": {"type": "ARRAY", "items": {"type": "STRING"}},
            "condition_summary": {"type": "STRING"},
            "severity": {"type": "STRING", "enum": ["MILD", "MODERATE_SEVERE"]},
            "doctor_instructions": {"type": "STRING"},
            "mitigation_advice": {"type": "STRING"}
        },
        "required": ["document_type"]
    }

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
                "temperature": 0.1
            }
        )
        
        analysis = json.loads(response.text)

        # Handle Prescriptions
        if analysis.get("document_type") == "PRESCRIPTION":
            drugs = analysis.get("extracted_drugs", [])
            if not drugs:
                return {
                    "ui_message": " I identified this as a prescription, but I couldn't extract specific medication names clearly. Could you verify the document text?",
                    "pending_drugs": None
                }
                
            return {
                "ui_message": f" **Prescription Detected:** I found *{', '.join(drugs)}*.\n\n To check stock and find the nearest pharmacies, please reply with your current city or neighborhood.",
                "pending_drugs": drugs
            }
            
        # Handle Medical/Lab Reports
        elif analysis.get("document_type") == "LAB_REPORT":
            response_md = f"###  Medical Report Overview\n\n"
            response_md += f"**General Condition:**\n{analysis.get('condition_summary', 'No summary available.')}\n\n"
            
            # Append mitigation advice only if the condition is MILD
            if analysis.get("severity") == "MILD":
                response_md += f"### ⚡ Home Mitigation Advice\n{analysis.get('mitigation_advice', 'Stay hydrated and monitor your symptoms.')}\n\n"
                
            response_md += f"###  Doctor Visit Instructions\n{analysis.get('doctor_instructions', 'Please consult a healthcare professional for a complete diagnosis.')}"
                
            return {
                "ui_message": response_md,
                "pending_drugs": None
            }
            
        else:
             return {
                "ui_message": " I've read your document, but it doesn't look like a standard prescription or lab report. How can I help you analyze it?",
                "pending_drugs": None
            }

    # Failsafe: If Gemini parsing crashes, the UI will still send a friendly message instead of going silent
    except Exception as e:
        return {
             "ui_message": f" **Document Analyzed!** I've scanned your upload, but had a little trouble categorizing it automatically. What specific details would you like to know about it?",
             "pending_drugs": None
        }

def execute_pharmacy_routing(drugs: List[str], location_text: str) -> str:
    """
    Called when the user replies with their location. Runs the DB search and formats the final map.
    """
    try:
        geo_data = geocode_address(location_text)
        if not geo_data:
            return f" Could not resolve the location '{location_text}'. Please try a different neighborhood name."
        
        stock_results = find_multi_medicine_stock(drugs, geo_data["lat"], geo_data["lng"])
        
        response_md = f"###  Sourcing Plan for: {geo_data['formatted']}\n\n"
        
        if stock_results["single_stop_options"]:
            response_md += "#### Recommended Single-Stop Option (All items in stock):\n"
            best = stock_results["single_stop_options"][0]
            response_md += f"**{best['pharmacy_name']}** ({best['distance_km']} km away)\n *Address:* {best['address']}\n"
            for item in best["items"]:
                response_md += f"  - {item['exact_drug']}: LKR {item['price']}\n"
            return response_md
            
        response_md += "#### Split Sourcing Required (No single pharmacy has everything):\n"
        for drug, options in stock_results["availability_map"].items():
            response_md += f"**{drug}:**\n"
            if options:
                top = options[0]
                response_md += f"  - Nearest: *{top['pharmacy_name']}* ({top['distance_km']} km) | Stock: {top['stock']} | LKR {top['price_lkr']}\n"
            else:
                response_md += "  - Out of stock locally.\n"
                
        return response_md

    except Exception as e:
        return f"Error searching local inventory: {str(e)}"