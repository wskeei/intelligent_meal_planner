import json
import random
import numpy as np
from pathlib import Path

OUTPUT_PATH = Path('src/intelligent_meal_planner/data/recipes.json')

# Configuration for generation
TARGET_COUNT = 550 # Generate a bit more to filter if needed
SEED = 42

random.seed(SEED)
np.random.seed(SEED)

def round_stats(val):
    return round(float(val), 1)

class RecipeGenerator:
    def __init__(self):
        self.recipes = []
        self.id_counter = 1
        
    def generate_random_price(self, category, protein, is_premium=False):
        base = 15.0
        if category in ['Poultry', 'Meat', 'Seafood']:
            base += 15.0
        if is_premium:
            base += 10.0
        # Price correlation with protein content
        protein_tax = protein * 0.5
        variance = random.uniform(-5.0, 5.0)
        price = base + protein_tax + variance
        return max(round(price, 1), 5.0) # Min price 5

    def create_item(self, name, meal_types, category, stats, tags):
        # Apply strict logic fixes based on tags
        if "keto" in tags and stats['carbs'] > 15:
            # Force fix keto violation
            stats['carbs'] = random.uniform(2, 12)
            # Add calories back to fat to maintain energy density roughly
            stats['fat'] += (stats['carbs'] * 4) / 9.0 
        
        if "vegan" in tags and category in ["Meat", "Poultry", "Seafood"]:
            # Logic error fix
            category = "Vegan"
            
        # Calorie calculation check (4-4-9 rule)
        calc_cals = (stats['protein']*4 + stats['carbs']*4 + stats['fat']*9)
        # Allow slight deviation for fiber/other but keep close
        stats['calories'] = calc_cals * random.uniform(0.95, 1.05)

        item = {
            "id": self.id_counter,
            "name": name,
            "calories": round_stats(stats['calories']),
            "protein": round_stats(stats['protein']),
            "carbs": round_stats(stats['carbs']),
            "fat": round_stats(stats['fat']),
            "price": self.generate_random_price(category, stats['protein']),
            "meal_type": meal_types,
            "category": category,
            "tags": list(set(tags)) # unique tags
        }
        self.id_counter += 1
        return item

    def generate_all(self):
        # 1. Breakfast (Aim for ~150 items)
        #    - Mains (300-500 kcal): Oats, Eggs, Pancakes (Low Carb/Normal)
        #    - Sides (100-250 kcal): Fruit, Yogurt, Toast, Sausage side
        self.generate_breakfast_mains()
        self.generate_breakfast_sides()
        
        # 2. Lunch/Dinner (Aim for ~400 items, shared)
        #    - Mains (400-700 kcal): Proteins + Carb/Veg
        #    - Sides (100-300 kcal): Salads, Soups, Veggies
        self.generate_main_meals()
        self.generate_sides()

        return self.recipes

    def generate_breakfast_mains(self):
        # Template: (Name Pattern, Category, BaseStats(Pro, Carb, Fat), Tags)
        templates = [
            ("Oatmeal with {}", "Grains", (10, 50, 6), ["vegetarian"], 
             ["Berries", "Banana", "Honey", "Cinnamon"]),
            ("Keto {} with {}", "General", (18, 5, 25), ["keto", "gluten-free", "vegetarian"], 
             ["Scrambled Eggs", "Omelette", "Frittata"], ["Spinach", "Mushrooms", "Cheese"]),
            ("Protein Pancakes ({})", "Dessert", (25, 30, 8), ["vegetarian"], 
             ["Blueberry", "Chocolate Chip", "Plain"]),
            ("Avocado Toast on {}", "Grains", (8, 25, 15), ["vegetarian", "vegan"], 
             ["Sourdough", "Whole Wheat", "Rye"]),
            ("Breakfast Burrito ({})", "General", (20, 40, 18), [], 
             ["Bean & Cheese", "Turkey Sausage", "Tofu Scramble"]),
        ]
        
        for _ in range(70):
            tmpl = random.choice(templates)
            name_fmt, cat, (bp, bc, bf), tags, *options = tmpl
            
            # Resolve name
            fmt_args = [random.choice(opt) for opt in options]
            name = name_fmt.format(*fmt_args)
            
            # Variate stats
            stats = {
                'protein': bp * random.uniform(0.8, 1.2),
                'carbs': bc * random.uniform(0.8, 1.2),
                'fat': bf * random.uniform(0.8, 1.2)
            }
            
            # Custom Tag Logic
            final_tags = tags.copy()
            if "Tofu" in name: final_tags.extend(["vegan", "vegetarian"])
            
            self.recipes.append(self.create_item(name, ["breakfast"], cat, stats, final_tags))

    def generate_breakfast_sides(self):
        templates = [
            ("Greek Yogurt ({})", "Dairy", (15, 8, 0), ["vegetarian", "gluten-free"], ["Plain", "Honey", "Berry"]),
            ("Fresh Fruit Bowl ({})", "Dessert", (2, 25, 0.5), ["vegan", "vegetarian", "gluten-free"], ["Mixed Berries", "Melon", "Citrus"]),
            ("Boiled Egg ({})", "General", (12, 1, 10), ["vegetarian", "keto", "gluten-free"], ["x2", "x1"]),
            ("Side of {}", "Meat", (15, 1, 15), ["keto", "gluten-free"], ["Turkey Bacon", "Sausage Links", "Ham"]),
        ]
        
        for _ in range(60):
            tmpl = random.choice(templates)
            name_fmt, cat, bases, tags, opts = tmpl
            name = name_fmt.format(random.choice(opts))
             
            # Special logic for "x1"
            multiplier = 0.6 if "x1" in name else 1.0
            
            stats = {
                'protein': bases[0] * multiplier * random.uniform(0.9, 1.1),
                'carbs': bases[1] * multiplier * random.uniform(0.9, 1.1),
                'fat': bases[2] * multiplier * random.uniform(0.9, 1.1)
            }
            
            self.recipes.append(self.create_item(name, ["breakfast"], cat, stats, tags))

    def generate_main_meals(self):
        # Lunch and Dinner Items (Mains)
        # High Protein, Controlled Cals
        proteins = [
            ("Grilled Chicken Breast", "Poultry", (30, 0, 5), ["keto", "paleo", "gluten-free"]),
            ("Baked Salmon", "Seafood", (25, 0, 15), ["keto", "paleo", "gluten-free"]),
            ("Tofu Stir-fry", "Vegan", (18, 10, 10), ["vegan", "vegetarian"]),
            ("Lean Beef Steak", "Meat", (35, 0, 20), ["keto", "paleo", "gluten-free"]),
            ("Lentil Curry", "Vegan", (15, 30, 8), ["vegan", "vegetarian"]),
            ("Turkey Meatballs", "Poultry", (25, 5, 12), [])
        ]
        
        sides_carb = [
            ("Brown Rice", 25), ("Quinoa", 22), ("Sweet Potato", 28), ("Cauliflower Rice", 5), ("Whole Wheat Pasta", 35)
        ]
        
        styles = ["Mediterranean", "Spicy", "Garlic Herb", "Teriyaki", "Lemon Pepper"]
        
        for _ in range(250):
            base_prot = random.choice(proteins)
            base_side = random.choice(sides_carb)
            style = random.choice(styles)
            
            name = f"{style} {base_prot[0]} with {base_side[0]}"
            
            # Combine nutrients
            p_stats = base_prot[2]
            s_carbs = base_side[1]
            
            # Logic: If Cauliflower Rice -> Low Carb/Keto friendly
            is_keto_side = base_side[0] == "Cauliflower Rice"
            
            stats = {
                'protein': p_stats[0],
                'carbs': p_stats[1] + s_carbs,
                'fat': p_stats[2] + random.uniform(2, 8) # Cooking oil
            }
            
            tags = base_prot[3].copy()
            if is_keto_side and "keto" in tags:
                pass # Keeps keto
            elif "keto" in tags:
                tags.remove("keto") # Carb side removes keto status
                
            if "Teriyaki" in style:
                stats['carbs'] += 5 # Sugar in sauce
                if "keto" in tags: tags.remove("keto")

            # Variate
            for k in stats: stats[k] *= random.uniform(0.9, 1.1)
            
            self.recipes.append(self.create_item(name, ["lunch", "dinner"], base_prot[1], stats, tags))

    def generate_sides(self):
        # Soups, Salads, Veggies
        parts = [
            ("Steamed Broccoli", "Vegan", (4, 6, 0.5), ["vegan", "keto"]),
            ("Garden Salad", "Salad", (2, 8, 5), ["vegan", "keto"]),
            ("Vegetable Soup", "Soup", (4, 15, 3), ["vegan"]),
            ("Caesar Salad", "Salad", (8, 10, 15), ["vegetarian"]),
            ("Roasted Asparagus", "Vegan", (4, 4, 8), ["vegan", "keto"]),
        ]
        
        for _ in range(170):
            base = random.choice(parts)
            name = base[0]
            cat = base[1]
            
            # Add variation to name to avoid identical duplicates being boring
            adjs = ["Fresh", "Organic", "Seasoned", "Small", "Side of"]
            uniq_name = f"{random.choice(adjs)} {name}"
            
            stats = {
                'protein': base[2][0] * random.uniform(0.8, 1.2),
                'carbs': base[2][1] * random.uniform(0.8, 1.2),
                'fat': base[2][2] * random.uniform(0.8, 1.2)
            }
            
            self.recipes.append(self.create_item(uniq_name, ["lunch", "dinner"], cat, stats, base[3]))

def main():
    gen = RecipeGenerator()
    recipes = gen.generate_all()
    
    # Shuffle
    random.shuffle(recipes)
    
    # Re-assign IDs sequentially
    for i, r in enumerate(recipes):
        r['id'] = i + 1
        
    data = {"recipes": recipes}
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully generated {len(recipes)} recipes to {OUTPUT_PATH}")
    
    # Validation Report
    bk = sum(1 for r in recipes if 'breakfast' in r['meal_type'])
    ld = sum(1 for r in recipes if 'lunch' in r['meal_type'])
    print(f"Stats: Breakfast={bk}, Lunch/Dinner={ld}")
    
if __name__ == "__main__":
    main()
