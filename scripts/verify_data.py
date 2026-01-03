
import json
from pathlib import Path

def verify_data():
    path = Path("d:/Project/intelligent_meal_planner/src/intelligent_meal_planner/data/recipes.json")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        recipes = data['recipes']
        
    counts = {'breakfast': 0, 'lunch': 0, 'dinner': 0}
    
    for r in recipes:
        for m in r['meal_type']:
            if m in counts:
                counts[m] += 1
                
    print("Meal Type Counts:", counts)
    
    if counts['breakfast'] < 10:
        print("WARNING: Low breakfast count!")
    else:
        print("Breakfast count seems okay.")

if __name__ == "__main__":
    verify_data()
