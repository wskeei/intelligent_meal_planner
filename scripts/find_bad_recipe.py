import json
from pathlib import Path

path = Path("src/intelligent_meal_planner/data/recipes.json")
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for i, recipe in enumerate(data['recipes']):
    if 'calories' not in recipe:
        print(f"Recipe at index {i} (ID: {recipe.get('id', 'Unknown')}, Name: {recipe.get('name', 'Unknown')}) is missing 'calories'")
    elif 'price' not in recipe:
        print(f"Recipe at index {i} missing 'price'")
    elif 'meal_type' not in recipe:
        print(f"Recipe at index {i} missing 'meal_type'")
