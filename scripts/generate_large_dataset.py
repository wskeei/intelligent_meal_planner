"""
Script to generate a large recipe dataset (>1000 items) for the Intelligent Meal Planner.
Combines high-quality manual entries with procedurally generated variations.
"""

import json
import random
import sys
import io
from pathlib import Path
from itertools import product

# Ensure UTF-8 output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUTPUT_FILE = Path(__file__).parent.parent / "src" / "intelligent_meal_planner" / "data" / "recipes.json"

# --- 1. Base Data (Common Items) ---
# High quality manually defined items (Breakfast, Staples, etc.)
BASE_RECIPES = [
    # 早餐 (Breakfast)
    {"name": "小米粥", "meal_type": ["breakfast"], "calories": 180, "protein": 4.5, "carbs": 38.0, "fat": 0.5, "price": 3.0, "tags": ["清淡", "养胃", "谷物"], "category": "主食"},
    {"name": "煎鸡蛋", "meal_type": ["breakfast", "lunch", "dinner"], "calories": 155, "protein": 13.0, "carbs": 1.1, "fat": 11.0, "price": 2.5, "tags": ["高蛋白", "快手"], "category": "蛋类"},
    {"name": "豆浆", "meal_type": ["breakfast"], "calories": 85, "protein": 7.0, "carbs": 9.0, "fat": 3.5, "price": 3.0, "tags": ["高蛋白", "豆制品"], "category": "饮品"},
    {"name": "全麦面包(2片)", "meal_type": ["breakfast"], "calories": 180, "protein": 8.0, "carbs": 35.0, "fat": 2.0, "price": 5.0, "tags": ["粗粮", "饱腹"], "category": "主食"},
    {"name": "燕麦粥", "meal_type": ["breakfast"], "calories": 200, "protein": 6.0, "carbs": 35.0, "fat": 4.0, "price": 4.0, "tags": ["高纤维", "减脂"], "category": "主食"},
    {"name": "煮玉米", "meal_type": ["breakfast", "lunch"], "calories": 150, "protein": 4.0, "carbs": 30.0, "fat": 1.5, "price": 3.5, "tags": ["粗粮", "饱腹"], "category": "主食"},
    {"name": "肉包子", "meal_type": ["breakfast", "lunch"], "calories": 250, "protein": 8.0, "carbs": 35.0, "fat": 10.0, "price": 3.0, "tags": ["主食", "饱腹"], "category": "主食"},
    {"name": "油条", "meal_type": ["breakfast"], "calories": 388, "protein": 7.0, "carbs": 51.0, "fat": 17.0, "price": 3.0, "tags": ["油炸", "高脂肪"], "category": "主食"},
    {"name": "牛奶", "meal_type": ["breakfast"], "calories": 150, "protein": 8.0, "carbs": 12.0, "fat": 8.0, "price": 4.0, "tags": ["高蛋白", "补钙"], "category": "饮品"},
    {"name": "煮鸡蛋", "meal_type": ["breakfast", "lunch", "dinner"], "calories": 140, "protein": 12.0, "carbs": 1.0, "fat": 9.0, "price": 2.0, "tags": ["高蛋白", "清淡"], "category": "蛋类"},
    
    # 主食 (Staples)
    {"name": "米饭(一碗)", "meal_type": ["lunch", "dinner"], "calories": 200, "protein": 4.0, "carbs": 44.0, "fat": 0.5, "price": 2.0, "tags": ["主食"], "category": "主食"},
    {"name": "馒头", "meal_type": ["lunch", "dinner"], "calories": 220, "protein": 7.0, "carbs": 48.0, "fat": 1.0, "price": 1.5, "tags": ["主食"], "category": "主食"},
    {"name": "糙米饭", "meal_type": ["lunch", "dinner"], "calories": 180, "protein": 4.0, "carbs": 38.0, "fat": 1.5, "price": 3.0, "tags": ["粗粮", "健康"], "category": "主食"},
    {"name": "面条", "meal_type": ["lunch", "dinner"], "calories": 250, "protein": 8.0, "carbs": 52.0, "fat": 1.0, "price": 5.0, "tags": ["主食"], "category": "主食"},
    {"name": "紫薯", "meal_type": ["breakfast", "lunch", "dinner"], "calories": 130, "protein": 2.0, "carbs": 30.0, "fat": 0.2, "price": 4.0, "tags": ["粗粮", "低脂"], "category": "主食"},
]

# --- 2. Procedural Generation Components ---

COOKING_METHODS = [
    {"prefix": "清蒸", "cost_factor": 1.0, "cal_factor": 1.0, "fat_add": 0, "tags": ["清淡", "健康"]},
    {"prefix": "红烧", "cost_factor": 1.2, "cal_factor": 1.5, "fat_add": 10, "tags": ["重口味", "家常"]},
    {"prefix": "爆炒", "cost_factor": 1.1, "cal_factor": 1.3, "fat_add": 8, "tags": ["快手"]},
    {"prefix": "香煎", "cost_factor": 1.1, "cal_factor": 1.4, "fat_add": 12, "tags": ["香酥"]},
    {"prefix": "水煮", "cost_factor": 1.0, "cal_factor": 1.1, "fat_add": 2, "tags": ["清淡"]},
    {"prefix": "麻辣", "cost_factor": 1.2, "cal_factor": 1.6, "fat_add": 15, "tags": ["麻辣", "重口味"]},
    {"prefix": "蒜蓉", "cost_factor": 1.1, "cal_factor": 1.2, "fat_add": 5, "tags": ["蒜香"]},
    {"prefix": "凉拌", "cost_factor": 1.0, "cal_factor": 0.8, "fat_add": 3, "tags": ["凉菜", "清爽"]},
    {"prefix": "椒盐", "cost_factor": 1.1, "cal_factor": 1.4, "fat_add": 10, "tags": ["咸香"]},
    {"prefix": "糖醋", "cost_factor": 1.2, "cal_factor": 1.6, "fat_add": 8, "tags": ["酸甜"]},
]

INGREDIENTS = [
    # Meat
    {"name": "猪肉", "base_cal": 250, "protein": 20, "carbs": 0, "fat": 20, "price": 10, "type": "肉类", "meal": ["lunch", "dinner"]},
    {"name": "牛肉", "base_cal": 200, "protein": 26, "carbs": 0, "fat": 10, "price": 20, "type": "肉类", "meal": ["lunch", "dinner"]},
    {"name": "羊肉", "base_cal": 220, "protein": 24, "carbs": 0, "fat": 15, "price": 22, "type": "肉类", "meal": ["lunch", "dinner"]},
    {"name": "鸡胸肉", "base_cal": 150, "protein": 30, "carbs": 0, "fat": 3, "price": 8, "type": "肉类", "meal": ["lunch", "dinner"]},
    {"name": "鸡腿", "base_cal": 200, "protein": 18, "carbs": 0, "fat": 12, "price": 9, "type": "肉类", "meal": ["lunch", "dinner"]},
    {"name": "鸭肉", "base_cal": 240, "protein": 18, "carbs": 0, "fat": 18, "price": 12, "type": "肉类", "meal": ["lunch", "dinner"]},
    {"name": "排骨", "base_cal": 280, "protein": 18, "carbs": 0, "fat": 22, "price": 18, "type": "肉类", "meal": ["lunch", "dinner"]},
    {"name": "五花肉", "base_cal": 400, "protein": 12, "carbs": 0, "fat": 40, "price": 15, "type": "肉类", "meal": ["lunch", "dinner"]},

    # Seafood
    {"name": "草鱼", "base_cal": 120, "protein": 18, "carbs": 0, "fat": 5, "price": 15, "type": "海鲜", "meal": ["lunch", "dinner"]},
    {"name": "虾仁", "base_cal": 90, "protein": 20, "carbs": 1, "fat": 1, "price": 25, "type": "海鲜", "meal": ["lunch", "dinner"]},
    {"name": "带鱼", "base_cal": 140, "protein": 18, "carbs": 0, "fat": 8, "price": 18, "type": "海鲜", "meal": ["lunch", "dinner"]},
    {"name": "鱿鱼", "base_cal": 80, "protein": 16, "carbs": 2, "fat": 1, "price": 20, "type": "海鲜", "meal": ["lunch", "dinner"]},
    
    # Veggies
    {"name": "白菜", "base_cal": 20, "protein": 1.5, "carbs": 3, "fat": 0.2, "price": 2, "type": "蔬菜", "meal": ["lunch", "dinner"]},
    {"name": "菠菜", "base_cal": 25, "protein": 2.5, "carbs": 4, "fat": 0.3, "price": 3, "type": "蔬菜", "meal": ["lunch", "dinner"]},
    {"name": "西兰花", "base_cal": 35, "protein": 3, "carbs": 5, "fat": 0.4, "price": 5, "type": "蔬菜", "meal": ["lunch", "dinner"]},
    {"name": "土豆", "base_cal": 80, "protein": 2, "carbs": 18, "fat": 0.2, "price": 2, "type": "蔬菜", "meal": ["lunch", "dinner"]},
    {"name": "茄子", "base_cal": 25, "protein": 1, "carbs": 5, "fat": 0.2, "price": 3, "type": "蔬菜", "meal": ["lunch", "dinner"]},
    {"name": "豆角", "base_cal": 30, "protein": 2, "carbs": 6, "fat": 0.2, "price": 4, "type": "蔬菜", "meal": ["lunch", "dinner"]},
    {"name": "西红柿", "base_cal": 20, "protein": 1, "carbs": 4, "fat": 0.2, "price": 3, "type": "蔬菜", "meal": ["lunch", "dinner"]},
    {"name": "黄瓜", "base_cal": 15, "protein": 1, "carbs": 3, "fat": 0.2, "price": 2, "type": "蔬菜", "meal": ["lunch", "dinner"]},
    {"name": "冬瓜", "base_cal": 12, "protein": 0.5, "carbs": 2, "fat": 0.1, "price": 2, "type": "蔬菜", "meal": ["lunch", "dinner"]},
    {"name": "豆腐", "base_cal": 80, "protein": 8, "carbs": 4, "fat": 5, "price": 3, "type": "豆制品", "meal": ["lunch", "dinner"]},
    {"name": "千张", "base_cal": 150, "protein": 15, "carbs": 6, "fat": 8, "price": 5, "type": "豆制品", "meal": ["lunch", "dinner"]},
]

SUFFIXES = [
    {"suffix": "片", "mod": 1.0},
    {"suffix": "丝", "mod": 1.0},
    {"suffix": "丁", "mod": 1.0},
    {"suffix": "块", "mod": 1.0},
    {"suffix": "段", "mod": 1.0},
    # Empty suffix for whole items
    {"suffix": "", "mod": 1.0}
]

def generate_dishes():
    generated_recipes = []
    
    # Combine Method + Ingredient + Suffix
    for ing in INGREDIENTS:
        for method in COOKING_METHODS:
            # Skip senseless combinations (e.g. cold steamed meat isn't standard menu name usually, but let's keep it simple)
            # Filter some weird ones
            if method["prefix"] == "凉拌" and ing["type"] == "肉类" and ing["name"] not in ["鸡胸肉", "牛肉"]:
                # Only cold chicken/beef is common usually
                continue
                
            for surf in SUFFIXES:
                # Name generation
                name = f"{method['prefix']}{ing['name']}{surf['suffix']}"
                
                # Nutritional calculation
                # Base * Method Factor + Added Fat
                calories = ing["base_cal"] * method["cal_factor"] + (method["fat_add"] * 9)
                protein = ing["protein"] # Protein usually stays similar or slight loss, keep simple
                carbs = ing["carbs"] + (5 if method["prefix"] == "糖醋" else 0) # Add sugar carbs
                fat = ing["fat"] + method["fat_add"]
                
                # Price calculation
                price = ing["price"] * method["cost_factor"] + (1 if method["prefix"] in ["麻辣", "糖醋"] else 0)
                
                # Randomized minor variations to avoid identical stats for similar items
                variation = random.uniform(0.9, 1.1)
                
                recipe = {
                    "name": name,
                    "meal_type": ing["meal"],
                    "calories": round(calories * variation, 1),
                    "protein": round(protein * variation, 1),
                    "carbs": round(carbs * variation, 1),
                    "fat": round(fat * variation, 1),
                    "price": round(price * variation, 1),
                    "tags": list(set(ing.get("tags", []) + method["tags"] + ([ing["type"]]))),
                    "category": ing["type"]
                }
                
                # Add to list
                generated_recipes.append(recipe)

    return generated_recipes

def generate_drinks_and_snacks():
    # Helper to generate some drinks/snacks
    items = []
    
    # Drinks
    fruits = ["苹果", "香蕉", "橙子", "西瓜", "葡萄", "芒果", "草莓"]
    for f in fruits:
        items.append({
            "name": f"{f}",
            "meal_type": ["breakfast", "lunch", "dinner"], # Can be eaten anytime
            "calories": 50, # Avg
            "protein": 0.5,
            "carbs": 12,
            "fat": 0.1,
            "price": 3.0,
            "tags": ["水果", "生鲜"],
            "category": "水果"
        })
        items.append({
            "name": f"鲜榨{f}汁",
            "meal_type": ["breakfast", "lunch", "dinner"],
            "calories": 80,
            "protein": 0.5,
            "carbs": 20,
            "fat": 0.1,
            "price": 12.0,
            "tags": ["饮品", "甜"],
            "category": "饮品"
        })
        
    return items

def main():
    print(f"Generating large dataset...")
    
    # 1. Base
    all_recipes = BASE_RECIPES.copy()
    
    # 2. Procedural Dishes
    procedural = generate_dishes()
    all_recipes.extend(procedural)
    
    # 3. Drinks/Snacks
    extras = generate_drinks_and_snacks()
    all_recipes.extend(extras)
    
    print(f"Total recipes generated: {len(all_recipes)}")
    
    # Ensure directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Save
    data = {"recipes": all_recipes}
    with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
