"""展示模型训练中的饮食策略与营养目标"""

print("=" * 80)
print("DIETARY STRATEGIES & NUTRITION TARGETS IN MODEL TRAINING")
print("=" * 80)

# 营养素热量换算
print("""
[Basic Knowledge]
  Protein: 1g = 4 kcal
  Carbohydrates: 1g = 4 kcal
  Fat: 1g = 9 kcal
""")

print("=" * 80)
print("[Stage 1 & 2: Fixed/Light Random Target]")
print("=" * 80)

print("""
Target Calories: 2000 kcal

Macronutrient Distribution:
  Protein:      100g (20% = 400 kcal)
  Carbohydrates: 250g (50% = 1000 kcal)
  Fat:           65g (30% = 585 kcal)

Total: ~1985 kcal
""")

print("=" * 80)
print("[Stage 3: Three Dietary Modes]")
print("=" * 80)

print("""
--------------------------------------------------------------------------------
Mode 1: Keto/Low-Carb (20% probability)
--------------------------------------------------------------------------------
Target Users: Ketogenic diet, low-carb weight loss

Ratio Range:
  Carbs:   5-15%
  Protein: 20-35%
  Fat:     50-75% (remaining)

Example at 2000 kcal (mid-range values):
  Protein:      138g (28%)
  Carbohydrates: 50g (10%)
  Fat:          139g (62%)

--------------------------------------------------------------------------------
Mode 2: Fitness/High-Protein (30% probability)
--------------------------------------------------------------------------------
Target Users: Muscle building, fitness enthusiasts

Ratio Range:
  Protein: 30-50%
  Fat:     15-25%
  Carbs:   25-55% (remaining)

Example at 2000 kcal (mid-range values):
  Protein:      200g (40%)
  Carbohydrates: 200g (40%)
  Fat:           44g (20%)

--------------------------------------------------------------------------------
Mode 3: Balanced/Normal (50% probability)
--------------------------------------------------------------------------------
Target Users: General population, daily diet

Ratio Range:
  Protein: 15-25%
  Fat:     20-35%
  Carbs:   40-65% (remaining)

Example at 2000 kcal (mid-range values):
  Protein:      100g (20%)
  Carbohydrates: 262g (52%)
  Fat:           61g (28%)
""")

print("=" * 80)
print("[Nutrition Targets at Different Calorie Levels]")
print("=" * 80)
print()
print("Calorie Range: 1200 - 3000 kcal")
print()

# 表格
header = f"{'Calories':^10} | {'Mode':^14} | {'Protein(g)':^12} | {'Carbs(g)':^12} | {'Fat(g)':^10}"
print(header)
print("-" * 70)

for cal in [1200, 1500, 2000, 2500, 3000]:
    # 均衡模式
    protein_ratio = 0.20
    fat_ratio = 0.275
    carb_ratio = 0.525
    protein_g = (cal * protein_ratio) / 4
    carbs_g = (cal * carb_ratio) / 4
    fat_g = (cal * fat_ratio) / 9
    print(f"{cal:^10} | {'Balanced':^14} | {protein_g:^12.0f} | {carbs_g:^12.0f} | {fat_g:^10.0f}")

    # 高蛋白模式
    protein_ratio = 0.40
    fat_ratio = 0.20
    carb_ratio = 0.40
    protein_g = (cal * protein_ratio) / 4
    carbs_g = (cal * carb_ratio) / 4
    fat_g = (cal * fat_ratio) / 9
    print(f"{'':^10} | {'High-Protein':^14} | {protein_g:^12.0f} | {carbs_g:^12.0f} | {fat_g:^10.0f}")

    # 低碳模式
    protein_ratio = 0.275
    fat_ratio = 0.625
    carb_ratio = 0.10
    protein_g = (cal * protein_ratio) / 4
    carbs_g = (cal * carb_ratio) / 4
    fat_g = (cal * fat_ratio) / 9
    print(f"{'':^10} | {'Low-Carb/Keto':^14} | {protein_g:^12.0f} | {carbs_g:^12.0f} | {fat_g:^10.0f}")
    print("-" * 70)

print()
print("=" * 80)
print("[Summary Table - Chinese]")
print("=" * 80)
print("""
+----------+----------+----------+----------+----------+----------+
|   模式   |  热量    | 蛋白质   |  碳水    |   脂肪   |  适用人群 |
+----------+----------+----------+----------+----------+----------+
| 均衡模式 | 2000kcal |  100g    |  262g    |   61g    | 普通人   |
| (50%)    |          |  (20%)   |  (52%)   |  (28%)   | 日常饮食 |
+----------+----------+----------+----------+----------+----------+
| 高蛋白   | 2000kcal |  200g    |  200g    |   44g    | 健身增肌 |
| (30%)    |          |  (40%)   |  (40%)   |  (20%)   | 运动员   |
+----------+----------+----------+----------+----------+----------+
| 低碳/Keto| 2000kcal |  138g    |   50g    |  139g    | 生酮减脂 |
| (20%)    |          |  (28%)   |  (10%)   |  (62%)   | 低碳饮食 |
+----------+----------+----------+----------+----------+----------+
""")
