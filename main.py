from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import algorithm  # 导入你写的算法文件
from sqlmodel import Session, select
from models import engine, Food  # 导入你的引擎和模型

app = FastAPI(title="个人基础代谢与饮食管理 API")

# --- 定义数据传输模型 (Request Body) ---

class UserProfile(BaseModel):
    name: str
    weight: float
    height: float
    age: int
    gender: str
    activity: str  # 例如: "轻度运动"
    goal: str      # 例如: "温和减脂"

class SubstitutionRequest(BaseModel):
    old_food_name: str
    old_weight: float
    new_food_name: str
    new_weight: float

# --- API 接口设计 ---

@app.get("/")
def read_root():
    return {"message": "欢迎使用 BMR & TDEE 计算接口", "status": "running"}

@app.post("/calculate/target")
def get_user_target(profile: UserProfile):
    """
    接口 1:输入用户基础信息, 返回每日建议摄入热量和三餐分配
    """
    try:
        # 调用 algorithm.py 中的函数
        results = algorithm.get_final_calories(
            profile.weight, profile.height, profile.age, 
            profile.gender, profile.activity, profile.goal
        )
        
        # 自动分配三餐 (默认 3:4:3)
        meals = algorithm.distribute_meals(results["Target"])
        
        return {
            "personal_info": profile,
            "calculated_data": results,
            "meal_distribution": meals
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calculate/substitution")
def get_substitution(req: SubstitutionRequest):
    with Session(engine) as session:
        # 1. 获取食物对象
        old_f = session.exec(select(Food).where(Food.name == req.old_food_name)).first()
        new_f = session.exec(select(Food).where(Food.name == req.new_food_name)).first()
        all_f = session.exec(select(Food)).all()

        if not old_f or not new_f:
            raise HTTPException(status_code=404, detail="食物库数据不足")

        # 2. 转换成字典格式供算法使用
        old_dict = {"protein": old_f.protein_100g, "fat": old_f.fat_100g, "carbs": old_f.carbs_100g}
        new_dict = {"protein": new_f.protein_100g, "fat": new_f.fat_100g, "carbs": new_f.carbs_100g}

        # 3. 链式调用算法
        gaps = algorithm.calculate_nutrient_gaps(old_dict, req.old_weight, new_dict, req.new_weight)
        plans = algorithm.get_smart_fix_plan(gaps, all_f)

        return {
            "gaps": gaps,
            "smart_plans": plans
        }