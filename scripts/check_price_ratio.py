import json
import numpy as np

with open('src/intelligent_meal_planner/data/recipes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    recipes = data['recipes']

ratios = []
for r in recipes:
    if r['calories'] > 10: # Avoid div/0
        ratio = r['price'] / (r['calories'] / 100.0)
        ratios.append(ratio)

print(f"Price per 100kcal stats:")
print(f"Mean: {np.mean(ratios):.2f}")
print(f"Median: {np.median(ratios):.2f}")
print(f"Min: {min(ratios):.2f}")
print(f"Max: {max(ratios):.2f}")
