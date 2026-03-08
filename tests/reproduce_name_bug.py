
import re

def test_heuristic(text, target_field, rule_based_data):
    print(f"Testing: '{text}' (Target: {target_field})")
    
    clean_text = text.strip().strip('.').strip()
    
    # Robust Prefix Stripping
    prefixes = ["my name is", "i am", "name is", "this is", "myself", "it is", "called"]
    lower_text = clean_text.lower()
    for prefix in prefixes:
        if lower_text.startswith(prefix + " ") or lower_text == prefix:
            clean_text = clean_text[len(prefix):].strip(" .!,")
            break
            
    words = clean_text.split()
    blacklist = ["hello", "hi", "hey", "ok", "okay", "yes", "no", "what", "why", "who", "confirm", "cancel", "start", "stop", "details", "info"]
    
    # Simulate the logic in local_ai_service.py
    if target_field == 'name' and not rule_based_data.get('name'):
        if len(words) <= 3 and len(words) > 0 and clean_text.lower() not in blacklist:
            print(f"Heuristic MATCH: Treating '{clean_text}' as Name")
            rule_based_data["name"] = clean_text.title()
        else:
            print(f"Heuristic NO MATCH: Words={len(words)}")
    else:
        print(f"Heuristic SKIPPED (Target={target_field})")

# Scenario 1: User says "Hyderabad Telangana" when asked for LOCATION
# target_field should be 'location'
test_heuristic("Hyderabad Telangana", "location", {})

# Scenario 2: User says "Hyderabad Telangana" when asked for NAME
# target_field should be 'name'
test_heuristic("Hyderabad Telangana", "name", {})

# Scenario 3: User says "My name is Rani" when asked for NAME
test_heuristic("My name is Rani", "name", {})
