import json
import random
import os

os.makedirs('data', exist_ok=True)

restaurants = [
  { "id": "r1", "name": "Green Bowl Co.", "neighborhood": "Downtown" },
  { "id": "r2", "name": "Protein House", "neighborhood": "Midtown" },
  { "id": "r3", "name": "Burger Barn", "neighborhood": "Uptown" },
  { "id": "r4", "name": "Sushi Express", "neighborhood": "Downtown" },
  { "id": "r5", "name": "Taco Fiesta", "neighborhood": "Westside" },
  { "id": "r6", "name": "Vegan Delights", "neighborhood": "Eastside" },
  { "id": "r7", "name": "Pizza Planet", "neighborhood": "Midtown" },
  { "id": "r8", "name": "Salad Station", "neighborhood": "Uptown" }
]

menu_items_raw = {
"r1": [
("m101", "Superfood Bowl", ["veg"], 450, 15),
("m102", "Quinoa Salad", ["veg"], 350, 12),
("m103", "Chicken Protein Bowl", ["high_protein"], 600, 45),
("m104", "Tofu Power Bowl", ["veg", "high_protein"], 500, 25),
("m105", "Acai Bowl", ["veg", "no_egg"], 300, 5)
],
"r2": [
("m201", "Steak & Eggs", ["high_protein"], 700, 55),
("m202", "Grilled Chicken Breast", ["high_protein", "no_egg"], 400, 40),
("m203", "Salmon Filet", ["high_protein", "no_egg"], 500, 35),
("m204", "Turkey Meatballs", ["high_protein"], 450, 30),
("m205", "Egg White Omelette", ["veg", "high_protein"], 250, 20)
],
"r3": [
("m301", "Classic Cheeseburger", [], 800, 30),
("m302", "Double Veggie Burger", ["veg"], 600, 20),
("m303", "Bacon Double Smash", [], 1000, 45),
("m304", "Crispy Chicken Sandwich", [], 750, 25),
("m305", "Black Bean Burger", ["veg", "no_egg"], 550, 18)
],
"r4": [
("m401", "Spicy Tuna Roll", ["no_egg"], 400, 20),
("m402", "Salmon Avocado Roll", ["no_egg"], 450, 22),
("m403", "Veggie Roll", ["veg", "no_egg"], 300, 6),
("m404", "Sashimi Combo", ["high_protein", "no_egg"], 350, 40),
("m405", "Edamame", ["veg", "no_egg"], 150, 12)
],
"r5": [
("m501", "Chicken Tacos (3)", ["no_egg"], 600, 35),
("m502", "Beef Burrito", [], 850, 30),
("m503", "Veggie Fajitas", ["veg", "no_egg"], 500, 15),
("m504", "Shrimp Tacos (3)", ["no_egg"], 550, 25),
("m505", "Bean & Cheese Quesadilla", ["veg", "no_egg"], 650, 20)
],
"r6": [
("m601", "Beyond Burger Classic", ["veg", "no_egg"], 600, 20),
("m602", "Vegan Mac & Cheese", ["veg", "no_egg"], 500, 10),
("m603", "Tempeh Wrap", ["veg", "high_protein", "no_egg"], 450, 25),
("m604", "Lentil Soup", ["veg", "no_egg"], 300, 15),
("m605", "Chickpea Salad", ["veg", "no_egg"], 400, 12)
],
"r7": [
("m701", "Margherita Pizza", ["veg"], 900, 35),
("m702", "Pepperoni Pizza", [], 1000, 40),
("m703", "Meat Lovers Pizza", ["high_protein"], 1200, 55),
("m704", "Vegan Supreme Pizza", ["veg", "no_egg"], 850, 25),
("m705", "Garlic Knots", ["veg", "no_egg"], 400, 8)
],
"r8": [
("m801", "Cobb Salad", ["high_protein"], 600, 35),
("m802", "Caesar Salad with Chicken", ["high_protein"], 550, 40),
("m803", "Greek Salad", ["veg", "no_egg"], 400, 12),
("m804", "Southwest Salad", ["veg"], 450, 15),
("m805", "Spinach & Goat Cheese", ["veg", "no_egg"], 350, 10)
]
}

menu_items = []
for r_id, items in menu_items_raw.items():
    for item_id, name, tags, cals, prot in items:
        menu_items.append({
            "item_id": item_id,
            "restaurant_id": r_id,
            "name": name,
            "tags": tags,
            "calories_est": cals,
            "protein_est": prot
        })

platforms = ["UberEats", "DoorDash", "Grubhub"]
platform_prices = []

random.seed(42)

for item in menu_items:
    base_price = round(random.uniform(9.0, 18.0), 2)
    for plat in platforms:
        plat_price = round(base_price + random.uniform(-1.0, 1.0), 2)
        delivery_fee = round(random.uniform(0.99, 5.99), 2)
        platform_prices.append({
            "item_id": item["item_id"],
            "platform_name": plat,
            "base_price": plat_price,
            "delivery_fee": delivery_fee
        })

coupons = [
    { "code": "UBER10", "platform": "UberEats", "discount_value": 10.0, "min_spend": 30.0 },
    { "code": "DASH5", "platform": "DoorDash", "discount_value": 5.0, "min_spend": 15.0 },
    { "code": "GRUBFREE", "platform": "Grubhub", "discount_value": 3.99, "min_spend": 20.0 },
    { "code": "TREAT15", "platform": "UberEats", "discount_value": 15.0, "min_spend": 40.0 },
    { "code": "DOOR20", "platform": "DoorDash", "discount_value": 0.20, "min_spend": 25.0 }
]

social_ratings = []
for item in menu_items:
    rating = round(random.uniform(3.5, 5.0), 1)
    reviews = random.randint(10, 500)
    social_ratings.append({
        "item_id": item["item_id"],
        "rating": rating,
        "review_count": reviews
    })

with open("data/restaurants.json", "w") as f:
    json.dump(restaurants, f, indent=2)

with open("data/menu_items.json", "w") as f:
    json.dump(menu_items, f, indent=2)

with open("data/platform_prices.json", "w") as f:
    json.dump(platform_prices, f, indent=2)

with open("data/coupons.json", "w") as f:
    json.dump(coupons, f, indent=2)

with open("data/social_ratings.json", "w") as f:
    json.dump(social_ratings, f, indent=2)

print("Finished generating synthetic data files in data/")
