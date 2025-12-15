"""
生成包含200道菜品的数据库
"""

import json
import sys
import io

# 设置 UTF-8 编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 基础菜品数据
base_recipes = [
    # 早餐 (25道)
    {"name": "小米粥", "meal_type": ["breakfast"], "calories": 360, "protein": 9.0, "carbs": 76.0, "fat": 1.0, "price": 3.0, "tags": ["清淡", "养胃", "谷物"], "category": "主食"},
    {"name": "煎鸡蛋", "meal_type": ["breakfast", "lunch", "dinner"], "calories": 155, "protein": 13.0, "carbs": 1.1, "fat": 11.0, "price": 2.5, "tags": ["高蛋白", "快手"], "category": "蛋类"},
    {"name": "豆浆", "meal_type": ["breakfast"], "calories": 85, "protein": 7.0, "carbs": 9.0, "fat": 3.5, "price": 3.0, "tags": ["高蛋白", "豆制品"], "category": "饮品"},
    {"name": "全麦面包", "meal_type": ["breakfast"], "calories": 246, "protein": 8.0, "carbs": 46.0, "fat": 3.0, "price": 5.0, "tags": ["粗粮", "饱腹"], "category": "主食"},
    {"name": "燕麦粥", "meal_type": ["breakfast"], "calories": 389, "protein": 16.9, "carbs": 66.0, "fat": 7.0, "price": 4.0, "tags": ["高纤维", "减脂"], "category": "主食"},
    {"name": "煮玉米", "meal_type": ["breakfast"], "calories": 196, "protein": 4.0, "carbs": 41.0, "fat": 2.0, "price": 3.5, "tags": ["粗粮", "饱腹"], "category": "主食"},
    {"name": "香煎培根", "meal_type": ["breakfast", "lunch"], "calories": 541, "protein": 37.0, "carbs": 1.4, "fat": 42.0, "price": 12.0, "tags": ["高蛋白", "高脂肪"], "category": "肉类"},
    {"name": "煎饺", "meal_type": ["breakfast", "lunch"], "calories": 320, "protein": 12.0, "carbs": 38.0, "fat": 14.0, "price": 8.0, "tags": ["主食", "快手"], "category": "主食"},
    {"name": "牛奶", "meal_type": ["breakfast"], "calories": 150, "protein": 8.0, "carbs": 12.0, "fat": 8.0, "price": 4.0, "tags": ["高蛋白", "补钙"], "category": "饮品"},
    {"name": "油条", "meal_type": ["breakfast"], "calories": 388, "protein": 7.0, "carbs": 51.0, "fat": 17.0, "price": 3.0, "tags": ["油炸", "高脂肪"], "category": "主食"},
    {"name": "包子", "meal_type": ["breakfast", "lunch"], "calories": 285, "protein": 10.0, "carbs": 42.0, "fat": 9.0, "price": 5.0, "tags": ["主食", "饱腹"], "category": "主食"},
    {"name": "皮蛋瘦肉粥", "meal_type": ["breakfast"], "calories": 180, "protein": 12.0, "carbs": 28.0, "fat": 3.0, "price": 8.0, "tags": ["清淡", "养胃"], "category": "主食"},
    {"name": "煎蛋三明治", "meal_type": ["breakfast"], "calories": 310, "protein": 15.0, "carbs": 35.0, "fat": 12.0, "price": 10.0, "tags": ["快手", "西式"], "category": "主食"},
    {"name": "豆腐脑", "meal_type": ["breakfast"], "calories": 95, "protein": 8.0, "carbs": 6.0, "fat": 4.0, "price": 4.0, "tags": ["豆制品", "清淡"], "category": "饮品"},
    {"name": "水煮青菜", "meal_type": ["breakfast", "lunch", "dinner"], "calories": 45, "protein": 3.0, "carbs": 8.0, "fat": 0.5, "price": 3.0, "tags": ["低脂", "清淡"], "category": "蔬菜"},
    {"name": "酸奶", "meal_type": ["breakfast"], "calories": 120, "protein": 6.0, "carbs": 18.0, "fat": 3.0, "price": 5.0, "tags": ["高蛋白", "益生菌"], "category": "饮品"},
    {"name": "水果麦片", "meal_type": ["breakfast"], "calories": 350, "protein": 10.0, "carbs": 65.0, "fat": 6.0, "price": 8.0, "tags": ["高纤维", "快手"], "category": "主食"},
    {"name": "蒸蛋", "meal_type": ["breakfast", "lunch", "dinner"], "calories": 143, "protein": 12.6, "carbs": 1.1, "fat": 9.5, "price": 3.0, "tags": ["高蛋白", "清淡"], "category": "蛋类"},
    {"name": "肉夹馍", "meal_type": ["breakfast", "lunch"], "calories": 380, "protein": 18.0, "carbs": 42.0, "fat": 15.0, "price": 12.0, "tags": ["主食", "肉类"], "category": "主食"},
    {"name": "煎饼果子", "meal_type": ["breakfast"], "calories": 420, "protein": 14.0, "carbs": 55.0, "fat": 16.0, "price": 9.0, "tags": ["主食", "快手"], "category": "主食"},
    {"name": "豆沙包", "meal_type": ["breakfast"], "calories": 260, "protein": 8.0, "carbs": 48.0, "fat": 4.0, "price": 4.0, "tags": ["甜食", "主食"], "category": "主食"},
    {"name": "蔬菜沙拉", "meal_type": ["breakfast", "lunch"], "calories": 120, "protein": 3.0, "carbs": 15.0, "fat": 5.0, "price": 15.0, "tags": ["低脂", "西式"], "category": "蔬菜"},
    {"name": "黑米粥", "meal_type": ["breakfast"], "calories": 340, "protein": 8.0, "carbs": 72.0, "fat": 2.0, "price": 4.0, "tags": ["粗粮", "养生"], "category": "主食"},
    {"name": "鸡蛋灌饼", "meal_type": ["breakfast"], "calories": 350, "protein": 14.0, "carbs": 45.0, "fat": 13.0, "price": 8.0, "tags": ["主食", "快手"], "category": "主食"},
    {"name": "南瓜粥", "meal_type": ["breakfast"], "calories": 180, "protein": 4.0, "carbs": 40.0, "fat": 1.0, "price": 3.0, "tags": ["清淡", "养胃"], "category": "主食"},
]

# 午餐晚餐主食 (30道)
lunch_dinner_staples = [
    {"name": "米饭", "meal_type": ["lunch", "dinner"], "calories": 116, "protein": 2.6, "carbs": 25.6, "fat": 0.3, "price": 1.5, "tags": ["主食"], "category": "主食"},
    {"name": "炒饭", "meal_type": ["lunch", "dinner"], "calories": 228, "protein": 6.0, "carbs": 38.0, "fat": 6.0, "price": 8.0, "tags": ["快手", "主食"], "category": "主食"},
    {"name": "炒年糕", "meal_type": ["lunch", "dinner"], "calories": 245, "protein": 4.0, "carbs": 50.0, "fat": 3.0, "price": 10.0, "tags": ["主食", "饱腹"], "category": "主食"},
    {"name": "拌面", "meal_type": ["lunch", "dinner"], "calories": 312, "protein": 10.0, "carbs": 58.0, "fat": 4.0, "price": 8.0, "tags": ["主食", "快手"], "category": "面食"},
    {"name": "牛肉面", "meal_type": ["lunch", "dinner"], "calories": 450, "protein": 25.0, "carbs": 60.0, "fat": 12.0, "price": 18.0, "tags": ["高蛋白"], "category": "面食"},
    {"name": "烤红薯", "meal_type": ["lunch", "dinner"], "calories": 86, "protein": 1.6, "carbs": 20.0, "fat": 0.1, "price": 3.0, "tags": ["粗粮", "低脂"], "category": "主食"},
    {"name": "馒头", "meal_type": ["lunch", "dinner"], "calories": 230, "protein": 7.0, "carbs": 48.0, "fat": 1.0, "price": 1.0, "tags": ["主食"], "category": "主食"},
    {"name": "花卷", "meal_type": ["lunch", "dinner"], "calories": 240, "protein": 7.5, "carbs": 50.0, "fat": 1.5, "price": 1.5, "tags": ["主食"], "category": "主食"},
    {"name": "刀削面", "meal_type": ["lunch", "dinner"], "calories": 380, "protein": 12.0, "carbs": 72.0, "fat": 3.0, "price": 15.0, "tags": ["主食"], "category": "面食"},
    {"name": "意大利面", "meal_type": ["lunch", "dinner"], "calories": 340, "protein": 11.0, "carbs": 68.0, "fat": 2.0, "price": 18.0, "tags": ["西式", "主食"], "category": "面食"},
    {"name": "焖饭", "meal_type": ["lunch", "dinner"], "calories": 280, "protein": 8.0, "carbs": 52.0, "fat": 4.0, "price": 12.0, "tags": ["主食"], "category": "主食"},
    {"name": "杂粮饭", "meal_type": ["lunch", "dinner"], "calories": 150, "protein": 4.0, "carbs": 32.0, "fat": 1.0, "price": 3.0, "tags": ["粗粮", "健康"], "category": "主食"},
    {"name": "紫米饭", "meal_type": ["lunch", "dinner"], "calories": 120, "protein": 3.0, "carbs": 26.0, "fat": 0.5, "price": 2.5, "tags": ["粗粮"], "category": "主食"},
    {"name": "糙米饭", "meal_type": ["lunch", "dinner"], "calories": 110, "protein": 2.8, "carbs": 24.0, "fat": 0.9, "price": 2.0, "tags": ["粗粮", "健身"], "category": "主食"},
    {"name": "担担面", "meal_type": ["lunch", "dinner"], "calories": 420, "protein": 15.0, "carbs": 65.0, "fat": 12.0, "price": 16.0, "tags": ["川菜"], "category": "面食"},
    {"name": "酸辣粉", "meal_type": ["lunch", "dinner"], "calories": 350, "protein": 8.0, "carbs": 68.0, "fat": 6.0, "price": 12.0, "tags": ["酸辣"], "category": "面食"},
    {"name": "热干面", "meal_type": ["lunch", "dinner"], "calories": 480, "protein": 14.0, "carbs": 70.0, "fat": 16.0, "price": 14.0, "tags": ["主食"], "category": "面食"},
    {"name": "兰州拉面", "meal_type": ["lunch", "dinner"], "calories": 420, "protein": 20.0, "carbs": 65.0, "fat": 10.0, "price": 20.0, "tags": ["高蛋白"], "category": "面食"},
    {"name": "炸酱面", "meal_type": ["lunch", "dinner"], "calories": 450, "protein": 18.0, "carbs": 68.0, "fat": 12.0, "price": 15.0, "tags": ["主食"], "category": "面食"},
    {"name": "阳春面", "meal_type": ["lunch", "dinner"], "calories": 290, "protein": 9.0, "carbs": 58.0, "fat": 3.0, "price": 10.0, "tags": ["清淡"], "category": "面食"},
    {"name": "蛋炒河粉", "meal_type": ["lunch", "dinner"], "calories": 380, "protein": 12.0, "carbs": 62.0, "fat": 10.0, "price": 14.0, "tags": ["快手"], "category": "主食"},
    {"name": "米线", "meal_type": ["lunch", "dinner"], "calories": 320, "protein": 10.0, "carbs": 62.0, "fat": 4.0, "price": 15.0, "tags": ["主食"], "category": "面食"},
    {"name": "砂锅粥", "meal_type": ["lunch", "dinner"], "calories": 200, "protein": 8.0, "carbs": 38.0, "fat": 2.0, "price": 18.0, "tags": ["养胃"], "category": "主食"},
    {"name": "煲仔饭", "meal_type": ["lunch", "dinner"], "calories": 450, "protein": 20.0, "carbs": 65.0, "fat": 12.0, "price": 22.0, "tags": ["主食"], "category": "主食"},
    {"name": "盖浇饭", "meal_type": ["lunch", "dinner"], "calories": 420, "protein": 18.0, "carbs": 62.0, "fat": 11.0, "price": 16.0, "tags": ["快手"], "category": "主食"},
    {"name": "饺子", "meal_type": ["lunch", "dinner"], "calories": 280, "protein": 12.0, "carbs": 36.0, "fat": 10.0, "price": 15.0, "tags": ["主食"], "category": "主食"},
    {"name": "馄饨", "meal_type": ["lunch", "dinner"], "calories": 260, "protein": 11.0, "carbs": 34.0, "fat": 9.0, "price": 14.0, "tags": ["主食"], "category": "主食"},
    {"name": "荞麦面", "meal_type": ["lunch", "dinner"], "calories": 310, "protein": 12.0, "carbs": 60.0, "fat": 2.0, "price": 16.0, "tags": ["粗粮", "健身"], "category": "面食"},
    {"name": "乌冬面", "meal_type": ["lunch", "dinner"], "calories": 330, "protein": 9.0, "carbs": 68.0, "fat": 2.0, "price": 18.0, "tags": ["日式"], "category": "面食"},
    {"name": "凉皮", "meal_type": ["lunch", "dinner"], "calories": 240, "protein": 6.0, "carbs": 48.0, "fat": 3.0, "price": 10.0, "tags": ["清淡"], "category": "主食"},
]

# 肉类菜品 (40道)
meat_dishes = [
    {"name": "红烧肉", "meal_type": ["lunch", "dinner"], "calories": 489, "protein": 15.0, "carbs": 12.0, "fat": 43.0, "price": 25.0, "tags": ["高脂肪", "重口味"], "category": "肉类"},
    {"name": "宫保鸡丁", "meal_type": ["lunch", "dinner"], "calories": 280, "protein": 19.0, "carbs": 14.0, "fat": 16.0, "price": 18.0, "tags": ["高蛋白", "川菜"], "category": "肉类"},
    {"name": "回锅肉", "meal_type": ["lunch", "dinner"], "calories": 352, "protein": 14.0, "carbs": 8.0, "fat": 31.0, "price": 22.0, "tags": ["川菜", "高脂肪"], "category": "肉类"},
    {"name": "水煮鸡胸肉", "meal_type": ["lunch", "dinner"], "calories": 165, "protein": 31.0, "carbs": 0.0, "fat": 3.6, "price": 15.0, "tags": ["高蛋白", "健身"], "category": "肉类"},
    {"name": "鱼香肉丝", "meal_type": ["lunch", "dinner"], "calories": 198, "protein": 12.0, "carbs": 15.0, "fat": 10.0, "price": 16.0, "tags": ["川菜"], "category": "肉类"},
    {"name": "糖醋里脊", "meal_type": ["lunch", "dinner"], "calories": 254, "protein": 16.0, "carbs": 22.0, "fat": 12.0, "price": 20.0, "tags": ["酸甜"], "category": "肉类"},
    {"name": "水煮牛肉", "meal_type": ["lunch", "dinner"], "calories": 280, "protein": 26.0, "carbs": 8.0, "fat": 16.0, "price": 30.0, "tags": ["川菜", "麻辣"], "category": "肉类"},
    {"name": "黄焖鸡", "meal_type": ["lunch", "dinner"], "calories": 320, "protein": 24.0, "carbs": 18.0, "fat": 18.0, "price": 20.0, "tags": ["高蛋白"], "category": "肉类"},
    {"name": "酸汤肥牛", "meal_type": ["lunch", "dinner"], "calories": 305, "protein": 22.0, "carbs": 8.0, "fat": 20.0, "price": 35.0, "tags": ["高蛋白"], "category": "肉类"},
    {"name": "煎牛排", "meal_type": ["lunch", "dinner"], "calories": 271, "protein": 26.0, "carbs": 0.0, "fat": 19.0, "price": 50.0, "tags": ["高蛋白", "低碳水"], "category": "肉类"},
    {"name": "东坡肉", "meal_type": ["lunch", "dinner"], "calories": 550, "protein": 18.0, "carbs": 15.0, "fat": 48.0, "price": 35.0, "tags": ["高脂肪", "名菜"], "category": "肉类"},
    {"name": "蒜泥白肉", "meal_type": ["lunch", "dinner"], "calories": 295, "protein": 18.0, "carbs": 3.0, "fat": 23.0, "price": 18.0, "tags": ["川菜"], "category": "肉类"},
    {"name": "小炒肉", "meal_type": ["lunch", "dinner"], "calories": 280, "protein": 16.0, "carbs": 10.0, "fat": 20.0, "price": 18.0, "tags": ["湘菜"], "category": "肉类"},
    {"name": "京酱肉丝", "meal_type": ["lunch", "dinner"], "calories": 310, "protein": 18.0, "carbs": 20.0, "fat": 18.0, "price": 22.0, "tags": ["京菜"], "category": "肉类"},
    {"name": "木须肉", "meal_type": ["lunch", "dinner"], "calories": 240, "protein": 15.0, "carbs": 12.0, "fat": 16.0, "price": 16.0, "tags": ["家常菜"], "category": "肉类"},
    {"name": "辣子鸡", "meal_type": ["lunch", "dinner"], "calories": 320, "protein": 22.0, "carbs": 15.0, "fat": 20.0, "price": 24.0, "tags": ["川菜", "麻辣"], "category": "肉类"},
    {"name": "口水鸡", "meal_type": ["lunch", "dinner"], "calories": 250, "protein": 24.0, "carbs": 8.0, "fat": 14.0, "price": 22.0, "tags": ["川菜", "凉菜"], "category": "肉类"},
    {"name": "左宗棠鸡", "meal_type": ["lunch", "dinner"], "calories": 380, "protein": 20.0, "carbs": 30.0, "fat": 22.0, "price": 26.0, "tags": ["湘菜"], "category": "肉类"},
    {"name": "咕咾肉", "meal_type": ["lunch", "dinner"], "calories": 420, "protein": 16.0, "carbs": 45.0, "fat": 20.0, "price": 24.0, "tags": ["粤菜", "酸甜"], "category": "肉类"},
    {"name": "梅菜扣肉", "meal_type": ["lunch", "dinner"], "calories": 480, "protein": 18.0, "carbs": 15.0, "fat": 40.0, "price": 28.0, "tags": ["客家菜"], "category": "肉类"},
    {"name": "粉蒸肉", "meal_type": ["lunch", "dinner"], "calories": 420, "protein": 16.0, "carbs": 35.0, "fat": 25.0, "price": 20.0, "tags": ["蒸菜"], "category": "肉类"},
    {"name": "糖醋排骨", "meal_type": ["lunch", "dinner"], "calories": 380, "protein": 18.0, "carbs": 28.0, "fat": 22.0, "price": 28.0, "tags": ["酸甜"], "category": "肉类"},
    {"name": "红烧排骨", "meal_type": ["lunch", "dinner"], "calories": 420, "protein": 20.0, "carbs": 15.0, "fat": 32.0, "price": 30.0, "tags": ["重口味"], "category": "肉类"},
    {"name": "盐水鸭", "meal_type": ["lunch", "dinner"], "calories": 260, "protein": 22.0, "carbs": 3.0, "fat": 18.0, "price": 32.0, "tags": ["苏菜"], "category": "肉类"},
    {"name": "北京烤鸭", "meal_type": ["lunch", "dinner"], "calories": 450, "protein": 24.0, "carbs": 20.0, "fat": 32.0, "price": 80.0, "tags": ["名菜", "高脂肪"], "category": "肉类"},
    {"name": "烧鸡", "meal_type": ["lunch", "dinner"], "calories": 380, "protein": 26.0, "carbs": 8.0, "fat": 28.0, "price": 35.0, "tags": ["高蛋白"], "category": "肉类"},
    {"name": "白切鸡", "meal_type": ["lunch", "dinner"], "calories": 220, "protein": 24.0, "carbs": 0.0, "fat": 14.0, "price": 30.0, "tags": ["粤菜", "清淡"], "category": "肉类"},
    {"name": "手撕鸡", "meal_type": ["lunch", "dinner"], "calories": 240, "protein": 26.0, "carbs": 5.0, "fat": 14.0, "price": 28.0, "tags": ["高蛋白"], "category": "肉类"},
    {"name": "铁板牛肉", "meal_type": ["lunch", "dinner"], "calories": 320, "protein": 28.0, "carbs": 10.0, "fat": 20.0, "price": 38.0, "tags": ["高蛋白"], "category": "肉类"},
    {"name": "孜然羊肉", "meal_type": ["lunch", "dinner"], "calories": 350, "protein": 22.0, "carbs": 12.0, "fat": 24.0, "price": 35.0, "tags": ["新疆菜"], "category": "肉类"},
    {"name": "羊肉串", "meal_type": ["lunch", "dinner"], "calories": 280, "protein": 20.0, "carbs": 5.0, "fat": 20.0, "price": 25.0, "tags": ["烧烤"], "category": "肉类"},
    {"name": "葱爆羊肉", "meal_type": ["lunch", "dinner"], "calories": 320, "protein": 24.0, "carbs": 10.0, "fat": 22.0, "price": 32.0, "tags": ["鲁菜"], "category": "肉类"},
    {"name": "小炒黄牛肉", "meal_type": ["lunch", "dinner"], "calories": 300, "protein": 26.0, "carbs": 8.0, "fat": 18.0, "price": 35.0, "tags": ["湘菜"], "category": "肉类"},
    {"name": "黑椒牛柳", "meal_type": ["lunch", "dinner"], "calories": 310, "protein": 28.0, "carbs": 10.0, "fat": 18.0, "price": 40.0, "tags": ["西式"], "category": "肉类"},
    {"name": "孜然牛肉", "meal_type": ["lunch", "dinner"], "calories": 340, "protein": 26.0, "carbs": 12.0, "fat": 22.0, "price": 36.0, "tags": ["新疆菜"], "category": "肉类"},
    {"name": "青椒炒肉片", "meal_type": ["lunch", "dinner"], "calories": 260, "protein": 18.0, "carbs": 10.0, "fat": 18.0, "price": 16.0, "tags": ["家常菜"], "category": "肉类"},
    {"name": "蒜苗炒肉", "meal_type": ["lunch", "dinner"], "calories": 270, "protein": 16.0, "carbs": 12.0, "fat": 18.0, "price": 15.0, "tags": ["家常菜"], "category": "肉类"},
    {"name": "香干肉丝", "meal_type": ["lunch", "dinner"], "calories": 240, "protein": 18.0, "carbs": 10.0, "fat": 15.0, "price": 14.0, "tags": ["家常菜"], "category": "肉类"},
    {"name": "酱爆肉丁", "meal_type": ["lunch", "dinner"], "calories": 290, "protein": 18.0, "carbs": 15.0, "fat": 18.0, "price": 18.0, "tags": ["鲁菜"], "category": "肉类"},
    {"name": "荔枝肉", "meal_type": ["lunch", "dinner"], "calories": 380, "protein": 16.0, "carbs": 35.0, "fat": 20.0, "price": 24.0, "tags": ["闽菜", "酸甜"], "category": "肉类"},
]

# 海鲜菜品 (25道)
seafood_dishes = [
    {"name": "清蒸鱼", "meal_type": ["lunch", "dinner"], "calories": 206, "protein": 22.0, "carbs": 0.0, "fat": 13.0, "price": 30.0, "tags": ["高蛋白", "清淡"], "category": "海鲜"},
    {"name": "西兰花炒虾仁", "meal_type": ["lunch", "dinner"], "calories": 120, "protein": 18.0, "carbs": 8.0, "fat": 2.5, "price": 22.0, "tags": ["高蛋白", "低脂"], "category": "海鲜"},
    {"name": "酸菜鱼", "meal_type": ["lunch", "dinner"], "calories": 230, "protein": 28.0, "carbs": 5.0, "fat": 11.0, "price": 