import time
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def run_demo():
    print("=== Demo Replay Script ===")
    user_id = "demo_user_" + str(int(time.time()))
    
    print("\n[STEP 1] Querying: Asking for high protein under $20...")
    req_payload = {
        "user_id": user_id,
        "message": "I want high protein lunch under 20 bucks"
    }
    
    try:
        res1 = requests.post(f"{BASE_URL}/message", json=req_payload)
        res1.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error calling /message. Make sure the FastAPI server is running on port 8000. \nDetails: {e}")
        sys.exit(1)
        
    data1 = res1.json()
    print(f"\nCoach style output: '{data1['coach_text']}'")
    print(f"Mock Audio URL: {data1['coach_audio_url']}")
    
    print("\nTop Results before feedback:")
    for i, r in enumerate(data1['top_results']):
        print(f"  {i+1}. {r['name']} ({r['restaurant']}) | Score: {r['score']:.2f}")
        print(f"     Tags: {r['tags']}")
        print(f"     Price: ${r['best_platform']['effective_price']:.2f} on {r['best_platform']['platform']}")
        
    if len(data1['top_results']) < 2:
        print("\nNot enough results found to run the feedback demo.")
        return
        
    # We choose the SECOND item as feedback, effectively showing how feedback re-ranks it.
    chosen = data1['top_results'][1]
    not_chosen = [r['item_id'] for r in data1['top_results'] if r['item_id'] != chosen['item_id']]
    
    print(f"\n[STEP 2] Feedback: Simulating user choosing '{chosen['name']}' (#2 above)")
    print("User rates it 9/10, providing positive reinforcement to its tags and coach style.")
    
    fb_payload = {
        "user_id": user_id,
        "chosen_item_id": chosen["item_id"],
        "not_chosen_item_ids": not_chosen,
        "rating": 9
    }
    
    fb_res = requests.post(f"{BASE_URL}/feedback", json=fb_payload)
    print("Feedback Response:", fb_res.json())
    
    print("\n[STEP 3] Querying: Re-running the exact same query after updating weights...")
    res2 = requests.post(f"{BASE_URL}/message", json=req_payload)
    data2 = res2.json()
    
    print(f"\nCoach style output (Might have changed!): '{data2['coach_text']}'")
    print("\nTop Results Rankings After Feedback:")
    for i, r in enumerate(data2['top_results']):
        print(f"  {i+1}. {r['name']} ({r['restaurant']}) | Score: {r['score']:.2f}")
        print(f"     Tags: {r['tags']}")
        print(f"     Price: ${r['best_platform']['effective_price']:.2f} on {r['best_platform']['platform']}")
        
    print("\nNotice how the score of the chosen item has increased, pushing it to the #1 spot, and the coach's tone has intensified!")

if __name__ == "__main__":
    run_demo()
