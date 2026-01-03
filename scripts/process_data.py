
import pandas as pd
import json
import random
from pathlib import Path

def process_data():
    input_path = Path("d:/Project/intelligent_meal_planner/new_data_temp/healthy_meal_plans.csv")
    output_path = Path("d:/Project/intelligent_meal_planner/src/intelligent_meal_planner/data/recipes.json")
    
    # Create output directory if it implies missing parents (though it should exist)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_csv(input_path)
    
    # Columns: meal_name,num_ingredients,calories,prep_time,protein,fat,carbs,vegan,vegetarian,keto,paleo,gluten_free,mediterranean,is_healthy
    
    recipes_list = []
    
    print(f"Processing {len(df)} recipes...")
    
    for idx, row in df.iterrows():
        # Denormalize logic (Assumptions based on typical meal ranges)
        # Calories: range 150 - 950
        calories = row['calories'] * 800 + 150
        
        # Protein: range 5 - 55g
        protein = row['protein'] * 50 + 5
        
        # Carbs: range 10 - 110g
        carbs = row['carbs'] * 100 + 10
        
        # Fat: range 5 - 45g
        fat = row['fat'] * 40 + 5
        
        # Price: Random between 15 and 50 (CNY? or just units)
        price = random.uniform(15.0, 50.0)
        
        # Tags
        tags = []
        if row['vegan']: tags.append('vegan')
        if row['vegetarian']: tags.append('vegetarian')
        if row['keto']: tags.append('keto')
        if row['paleo']: tags.append('paleo')
        if row['gluten_free']: tags.append('gluten-free')
        
        # Category
        # Infer from name or tags
        name_lower = row['meal_name'].lower()
        category = 'General'
        if 'salad' in name_lower: category = 'Salad'
        elif 'soup' in name_lower: category = 'Soup'
        elif 'steak' in name_lower or 'beef' in name_lower: category = 'Meat'
        elif 'chicken' in name_lower: category = 'Poultry'
        elif 'pasta' in name_lower or 'noodle' in name_lower: category = 'Grains'
        elif 'dessert' in name_lower or 'cake' in name_lower: category = 'Dessert'
        elif 'vegan' in tags: category = 'Vegan'
        
        # Meal Type
        # Heuristics
        meal_type = []
        is_breakfast = False
        if any(x in name_lower for x in ['oat', 'egg', 'pancake', 'waffle', 'toast', 'cereal', 'yogurt', 'smoothie', 'breakfast']):
            meal_type.append('breakfast')
            is_breakfast = True
            
        if not is_breakfast:
            # Randomly assign lunch/dinner or both
            # Most meals can be lunch or dinner
            roll = random.random()
            if roll < 0.4:
                meal_type.append('lunch')
            elif roll < 0.8:
                meal_type.append('dinner')
            else:
                meal_type.extend(['lunch', 'dinner'])
                
        # Ensure at least one type
        if not meal_type:
            meal_type.append('lunch')
            
        recipes_list.append({
            "id": idx + 1,
            "name": row['meal_name'],
            "calories": round(calories, 1),
            "protein": round(protein, 1),
            "carbs": round(carbs, 1),
            "fat": round(fat, 1),
            "price": round(price, 1),
            "meal_type": meal_type,
            "category": category,
            "tags": tags
        })
        
    output_data = {"recipes": recipes_list}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {len(recipes_list)} recipes to {output_path}")

if __name__ == "__main__":
    process_data()
