import json
import numpy as np
from pathlib import Path

DATA_PATH = Path('src/intelligent_meal_planner/data/recipes.json')

def analyze():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        recipes = data['recipes']
        
    print(f"Total Recipes: {len(recipes)}")
    
    # Check Breakfast
    breakfasts = [r for r in recipes if 'breakfast' in r['meal_type']]
    print(f"\n--- Breakfast Stats ({len(breakfasts)} items) ---")
    if breakfasts:
        b_cals = [r['calories'] for r in breakfasts]
        print(f"Calories: Mean={np.mean(b_cals):.1f}, Min={min(b_cals)}, Max={max(b_cals)}")
        print(f"Sample: {[r['name'] for r in breakfasts[:5]]}")
        
    # Check Keto Integrity
    keto_violations = [r for r in recipes if 'keto' in r['tags'] and r['carbs'] > 20]
    print(f"\n--- Logic Checks ---")
    print(f"Keto Violations (>20g carbs): {len(keto_violations)}")
    if keto_violations:
        print(f"Sample Violation: {keto_violations[0]['name']} (Carbs: {keto_violations[0]['carbs']})")
        
    # Check Distribution
    print(f"\n--- Global Distribution ---")
    cals = [r['calories'] for r in recipes]
    pro = [r['protein'] for r in recipes]
    print(f"Calories: Mean={np.mean(cals):.1f} (Std: {np.std(cals):.1f})")
    print(f"Protein:  Mean={np.mean(pro):.1f} (Std: {np.std(pro):.1f})")
    
    # Check Duplicates
    names = [r['name'] for r in recipes]
    dupes = len(names) - len(set(names))
    print(f"Duplicate Names: {dupes}")

if __name__ == "__main__":
    analyze()
