import json
import os
import re
import sqlite3
import urllib.parse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data stores
data = {
    "restaurants": [],
    "menu_items": [],
    "platform_prices": [],
    "coupons": [],
    "social_ratings": []
}

DB_PATH = "services/api/database.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT,
            item_id TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_weights (
            user_id TEXT,
            tag TEXT,
            weight REAL,
            PRIMARY KEY (user_id, tag)
        )
    ''')
    conn.commit()
    conn.close()

@app.on_event("startup")
def load_data():
    base_dir = "data"
    files = ["restaurants", "menu_items", "platform_prices", "coupons", "social_ratings"]
    for fname in files:
        path = os.path.join(base_dir, f"{fname}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                data[fname] = json.load(f)
    print(f"Loaded {len(data['menu_items'])} menu items.")
    init_db()

class MessageRequest(BaseModel):
    user_id: str
    message: str

class FeedbackRequest(BaseModel):
    user_id: str
    chosen_item_id: str
    not_chosen_item_ids: List[str]
    rating: int

def get_all_user_weights(user_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT tag, weight FROM user_weights WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def set_user_weight(user_id: str, tag: str, weight: float):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO user_weights (user_id, tag, weight) VALUES (?, ?, ?)", (user_id, tag, weight))
    conn.commit()
    conn.close()

def parse_constraints(message: str):
    msg_lower = message.lower()
    constraints = {"tags": [], "budget": None}
    
    if "veg" in msg_lower or "vegan" in msg_lower:
        constraints["tags"].append("veg")
    if "protein" in msg_lower:
        constraints["tags"].append("high_protein")
    if "no egg" in msg_lower or "eggless" in msg_lower:
        constraints["tags"].append("no_egg")
        
    # Extract budget e.g., "under 15" or "$15"
    budget_match = re.search(r'(?:under|<|\$)\s*(\d+(?:\.\d{2})?)', msg_lower)
    if budget_match:
        constraints["budget"] = float(budget_match.group(1))
    else:
        # Fallback parsing like "15 bucks"
        bucks_match = re.search(r'(\d+(?:\.\d{2})?)\s*(?:bucks|dollars)', msg_lower)
        if bucks_match:
            constraints["budget"] = float(bucks_match.group(1))
            
    return constraints

def calculate_best_price(item_id: str):
    # Get all prices for item
    prices = [p for p in data["platform_prices"] if p["item_id"] == item_id]
    best_eff_price = 9999.0
    best_platform = None
    
    for p in prices:
        base = p["base_price"]
        fee = p["delivery_fee"]
        platform = p["platform_name"]
        
        # Apply best coupon for this platform
        applicable_coupons = [c for c in data["coupons"] if c["platform"] == platform and base >= c["min_spend"]]
        discount = 0.0
        for c in applicable_coupons:
            val = c["discount_value"]
            # Treat values < 1.0 as percentages
            cand_discount = base * val if val < 1.0 else val
            if cand_discount > discount:
                discount = cand_discount
                
        eff = base - discount + fee
        if eff < best_eff_price:
            best_eff_price = eff
            best_platform = {
                "platform": platform,
                "base_price": base,
                "delivery_fee": fee,
                "discount": discount,
                "effective_price": eff
            }
            
    return best_eff_price, best_platform

@app.post("/message")
def handle_message(req: MessageRequest):
    constraints = parse_constraints(req.message)
    budget = constraints["budget"]
    required_tags = set(constraints["tags"])
    
    # Track profile/event
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO user_profiles (user_id) VALUES (?)", (req.user_id,))
    c.execute("INSERT INTO events (user_id, action, details) VALUES (?, ?, ?)", 
              (req.user_id, "message", req.message))
    conn.commit()
    conn.close()
    
    user_weights_map = get_all_user_weights(req.user_id)
    scored_items = []
    
    for item in data["menu_items"]:
        item_tags = set(item.get("tags", []))
        if required_tags and not required_tags.issubset(item_tags):
            continue
            
        eff_price, platform_info = calculate_best_price(item["item_id"])
        
        # Budget constraint
        if budget and eff_price > budget:
            continue
            
        if eff_price == 9999.0:
            continue
            
        tag_weight_sum = sum(user_weights_map.get(t, 0.0) for t in item_tags)
        
        # score = -effective_price + (protein_est / 10) + user_pref_weights(tags)
        protein = item.get("protein_est", 0)
        score = -eff_price + (protein / 10.0) + tag_weight_sum
        
        restaurant = next((r for r in data["restaurants"] if r["id"] == item["restaurant_id"]), None)
        rest_name = restaurant["name"] if restaurant else "Unknown"
        
        scored_items.append({
            "item_id": item["item_id"],
            "name": item["name"],
            "restaurant": rest_name,
            "tags": list(item_tags),
            "protein_est": protein,
            "best_platform": platform_info,
            "score": score
        })
        
    scored_items.sort(key=lambda x: x["score"], reverse=True)
    top_3 = scored_items[:3]
    
    coach_scalar = user_weights_map.get("coach_style", 0.0)
    
    if coach_scalar > 1.0:
        style = "hype"
        tone_desc = "extremely energetic, hyped, and enthusiastic"
    elif coach_scalar < -1.0:
        style = "gentle"
        tone_desc = "gentle, soft, nurturing, and calm"
    else:
        style = "neutral"
        tone_desc = "helpful, friendly, and straightforward"

    coach_text = ""
    airia_api_key = os.getenv("AIRIA_API_KEY", "")
    
    if airia_api_key:
        import requests
        try:
            # Provide the user's intent plus the structural context so Airia AI can form a tailored response
            context_str = f"System: You are an AI Food Coach. The user asked: '{req.message}'. Tone: {tone_desc}.\nHere are the top 3 food options the system found:\n"
            for idx, item in enumerate(top_3):
                price = item['best_platform']['effective_price']
                context_str += f"{idx+1}. {item['name']} from {item['restaurant']} for ${price:.2f}\n"
            context_str += "\nRespond conversationally to the user about these options. Keep it under 3 sentences."

            headers = {
                "X-API-KEY": airia_api_key,
                "Content-Type": "application/json"
            }
            res = requests.post(
                "https://api.airia.ai/v2/PipelineExecution/89ba5741-ca1a-49a9-a618-e231d5c67a30",
                headers=headers,
                json={"userInput": context_str, "asyncOutput": False},
                timeout=12
            )
            
            if res.status_code == 200:
                try:
                    res_data = res.json()
                    if isinstance(res_data, dict):
                        coach_text = res_data.get("output", res_data.get("result", res_data.get("response", res_data.get("text", str(res_data)))))
                    else:
                        coach_text = str(res_data)
                except ValueError:
                    # Fallback to plain text if not JSON
                    coach_text = res.text
        except Exception as e:
            print(f"Airia API failed: {e}")

    # Fallback back to standard programmatic formatting if Airia API key is missing or request fails
    if not coach_text:
        if style == "hype":
            base_tone = "Yo, let's crush it! Here are the ultimate fuel options to hit your macros today! "
        elif style == "gentle":
            base_tone = "Hmm, I've carefully selected these gentle, nourishing options just for you. Take your time deciding. "
        else:
            base_tone = "Hey there! Here are the top 3 options based on your exact preferences. "
            
        spoken_options = []
        for idx, item in enumerate(top_3):
            price = item['best_platform']['effective_price']
            # Replace decimals with "dollars and cents" to make TTS engine read it properly
            price_str = f"{int(price)} dollars and {int((price % 1) * 100)} cents" if (price % 1) > 0 else f"{int(price)} dollars"
            
            if style == "hype":
                spoken_options.append(f"Option {idx + 1}, BOOM! We've got the {item['name']} for just {price_str}! ")
            elif style == "gentle":
                spoken_options.append(f"For option {idx + 1}, perhaps try the beautiful {item['name']}, coming in at {price_str}. ")
            else:
                spoken_options.append(f"Number {idx + 1} is the {item['name']} which will cost {price_str}. ")

        coach_text = base_tone + "".join(spoken_options)
    
    from services.api.modulate_wrapper import generate_voice
    audio_url = generate_voice(coach_text, style)
    
    return {
        "top_results": top_3,
        "coach_text": coach_text,
        "coach_audio_url": audio_url
    }

@app.post("/feedback")
def handle_feedback(req: FeedbackRequest):
    def get_tags(i_id):
        itm = next((m for m in data["menu_items"] if m["item_id"] == i_id), None)
        return itm["tags"] if itm else []
        
    chosen_tags = get_tags(req.chosen_item_id)
    not_chosen_tagsList = [get_tags(i_id) for i_id in req.not_chosen_item_ids]
    
    user_weights_map = get_all_user_weights(req.user_id)
    
    # Increase weights for chosen item tags
    for t in chosen_tags:
        w = user_weights_map.get(t, 0.0)
        set_user_weight(req.user_id, t, w + 1.0)
        
    # Decrease weights for items not chosen
    for tags in not_chosen_tagsList:
        for t in tags:
            # Avoid penalizing tags that were in the chosen item
            if t not in chosen_tags:
                w = user_weights_map.get(t, 0.0)
                set_user_weight(req.user_id, t, w - 0.5)
                
    # Adjust coach style based on rating (scalar)
    coach_w = user_weights_map.get("coach_style", 0.0)
    if req.rating >= 8:
        set_user_weight(req.user_id, "coach_style", coach_w + 1.0)
    elif req.rating <= 4:
        set_user_weight(req.user_id, "coach_style", coach_w - 1.0)
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO events (user_id, action, item_id, details) VALUES (?, ?, ?, ?)", 
              (req.user_id, "feedback", req.chosen_item_id, f"Rating: {req.rating}"))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "Weights updated"}
