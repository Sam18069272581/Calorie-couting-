# algorithm.py

# 1. 定义活动等级映射 (对应图1)
ACTIVITY_LEVELS = {
    "久坐(很少或不运动)": 1.2,        # 很少或不运动
    "轻度运动(每周1-3次)": 1.375,   # 每周1-3次
    "中等运动(每周4-5次)": 1.55,    # 每周4-5次
    "活跃运动(每日锻炼或每周中等强度3-4次)": 1.725,   # 每日锻炼或每周中等强度3-4次
    "非常活跃(每周中等强度6-7次)": 1.9,     # 每周中等强度6-7次
    "剧烈运动(每天体力工作 (参考专业运动员))": 2.2      # 每天体力工作 (参考专业运动员)
}

# 2. 定义目标热量系数 (对应图2/3)
GOAL_FACTORS = {
    "极端减脂(38%热量差)": 0.62,
    "减脂(20%热量差)": 0.8,
    "温和减脂(10%热量差)": 0.9,
    "维持体形": 1.0,
    "温和增肌(10%热量差)": 1.1,
    "增肌(20%热量差)": 1.2,
    "极端增肌(38%热量差)": 1.38
}

def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor 计算基础代谢"""
    if gender in ["male", "男"]:
        return 10 * weight + 6.25 * height - 5 * age + 5
    return 10 * weight + 6.25 * height - 5 * age - 161

def get_final_calories(weight: float, height: float, age: int, gender: str, 
                        activity_key: str, goal_key: str) -> dict:
    """
    一步到位计算最终建议摄入
    """
    # 计算基础代谢
    bmr = calculate_bmr(weight, height, age, gender)
    
    # 获取活动系数
    tdee = bmr * ACTIVITY_LEVELS.get(activity_key, 1.2)
    
    # 获取目标摄入
    target_calories = tdee * GOAL_FACTORS.get(goal_key, 1.0)
    
    return {
        "BMR": round(bmr, 2),
        "TDEE": round(tdee, 2),
        "Target": round(target_calories, 2)
    }

# 测试一下
if __name__ == "__main__":
    # 比如：21岁, 180cm, 80kg, 男性, 轻度运动, 想要温和减脂
    res = get_final_calories(88, 183, 21, "男", "活跃运动", "温和减脂")
    print(f"计算结果: {res}")

# algorithm.py  

def calculate_nutrient_gaps(old_food_data: dict, old_weight: float, new_food_data: dict, new_weight: float):
    """
    第一层：纯粹的物理计算。计算两份食物之间的营养素克数差值。
    """
    def get_total(food, weight):
        return {
            "p": (food.get("protein", 0) / 100) * weight,
            "f": (food.get("fat", 0) / 100) * weight,
            "c": (food.get("carbs", 0) / 100) * weight
        }

    old_total = get_total(old_food_data, old_weight)
    new_total = get_total(new_food_data, new_weight)

    # 差值 = 原本需要的 - 现在有的
    # 正数代表缺了，负数代表超了
    return {
        "protein_gap": old_total["p"] - new_total["p"],
        "fat_gap": old_total["f"] - new_total["f"],
        "carbs_gap": old_total["c"] - new_total["c"]
    }

def get_smart_fix_plan(gaps: dict, all_foods: list):
    """
    第二层：逻辑策略。根据计算出的 gap，从数据库（all_foods）中匹配最优补丁。
    """
    recommendations = []
    
    # 1. 蛋白质补救逻辑 (缺口 > 2g 触发)
    if gaps["protein_gap"] > 2:
        # 寻找高蛋白低脂的补丁（按蛋白含量降序，脂肪含量升序）
        protein_patches = [f for f in all_foods if f.category in ["肉类", "补剂"]]
        if protein_patches:
            best_p = sorted(protein_patches, key=lambda x: (-x.protein_100g, x.fat_100g))[0]
            needed = (gaps["protein_gap"] / best_p.protein_100g) * 100
            recommendations.append({
                "type": "补齐蛋白",
                "food": best_p.name,
                "amount": round(needed, 1),
                "reason": f"缺口 {round(gaps['protein_gap'], 1)}g"
            })

    # 2. 脂肪补救逻辑 (缺口 > 1g 触发)
    if gaps["fat_gap"] > 1:
        fat_patches = [f for f in all_foods if f.category == "油脂"]
        if fat_patches:
            best_f = sorted(fat_patches, key=lambda x: -x.fat_100g)[0]
            needed = (gaps["fat_gap"] / best_f.fat_100g) * 100
            recommendations.append({
                "type": "补齐脂肪",
                "food": best_f.name,
                "amount": round(needed, 1),
                "reason": f"缺口 {round(gaps['fat_gap'], 1)}g"
            })

    # 3. 碳水超标警告 (如果新食物碳水比原来多了 10g 以上)
    if gaps["carbs_gap"] < -10:
        recommendations.append({
            "type": "警告",
            "info": f"当前替换导致碳水超标 {round(abs(gaps['carbs_gap']), 1)}g，建议减少其他餐次主食。"
        })

    return recommendations if recommendations else [{"type": "完美", "info": "营养配比极佳，无需调整"}]
# algorithm.py

def calculate_macros_pro(target_calories: float, weight: float, gender: str, goal_key: str):
    """
    谭式硬核算法：根据性别和目标自动切换营养体系
    """
    # 1. 蛋白质分配 (按每公斤体重精确计算)
    if gender in ["male", "男"]:
        # 男性：为了极致增肌/保肌，蛋白质比例极高
        p_factor = 2.5 if "减脂" in goal_key else 2.2
        f_ratio = 0.2  # 男性脂肪忍受度较高，可以压到20%
    else:
        # 女性：保护内分泌，蛋白质适中，脂肪比例必须保底
        p_factor = 1.8 if "减脂" in goal_key else 1.6
        f_ratio = 0.3  # 女性脂肪保底30%热量，防止掉头发/断经
        
    protein_g = weight * p_factor
    protein_cal = protein_g * 4
    
    # 2. 脂肪分配
    fat_cal = target_calories * f_ratio
    fat_g = fat_cal / 9
    
    # 3. 碳水分配 (剩下的全部给碳水)
    # 如果蛋白质+脂肪已经超标（极低热量情况），强制保蛋白质，压低碳水
    remaining_cal = target_calories - protein_cal - fat_cal
    carbs_g = max(remaining_cal / 4, 30)  # 至少保底30g碳水维持大脑供能
    
    return {
        "strategy": f"{gender}性-{goal_key}模式",
        "protein_g": round(protein_g, 1),
        "fat_g": round(fat_g, 1),
        "carbs_g": round(carbs_g, 1),
        "p_ratio": f"{round(protein_cal / target_calories * 100)}%",
        "f_ratio": f"{round(f_ratio * 100)}%",
        "c_ratio": f"{round(remaining_cal / target_calories * 100)}%"
    }

# algorithm.py 追加
# algorithm.py (最终完善版)

def balance_meal_plan(target_cal, target_p, target_f, target_c, current_foods, all_foods_db):
    # 基础数值计算
    current_p = sum([f['p_total'] for f in current_foods])
    current_f = sum([f['f_total'] for f in current_foods])
    current_c = sum([f['c_total'] for f in current_foods])
    
    # 计算原始缺口 (可能为负)
    gap_p = target_p - current_p
    gap_f = target_f - current_f
    gap_c = target_c - current_c

    # 安全地获取补丁食物 (防止空列表报错)
    pro_patches = [f for f in all_foods_db if f.category == "肉类"]
    fat_patches = [f for f in all_foods_db if f.category == "油脂"]
    
    res = {"remedy_p": None, "remedy_f": None, "status": "ok", "gaps": {"p": gap_p, "f": gap_f, "c": gap_c}}

    if gap_p > 1:
        # 在用户这一餐选中的食物里，找蛋白质含量最高的那个
        # 注意：current_foods 里的元素需要包含原始每100g的营养数据，或者我们去 food_options 查
        # 简单起见，我们直接看谁提供的蛋白质最多
        if current_foods:
            # 找到当前所选食物中，蛋白质密度（p_total/重量）最高的食物
            # 这里我们假设 current_foods 已经携带了 per_100 属性（见下一步 app.py 修改）
            best_p_food = sorted(current_foods, key=lambda x: x['p_100'], reverse=True)[0]
            
            if best_p_food['p_100'] > 2: # 只有蛋白质含量够高才用来补齐
                amt = (gap_p / best_p_food['p_100']) * 100
                res["remedy_p"] = {"name": best_p_food['name'], "amount": round(amt, 1)}

    if gap_f > 1:
        if current_foods:
            best_f_food = sorted(current_foods, key=lambda x: x['f_100'], reverse=True)[0]
            
            if best_f_food['f_100'] > 2:
                amt = (gap_f / best_f_food['f_100']) * 100
                res["remedy_f"] = {"name": best_f_food['name'], "amount": round(amt, 1)}

    return res