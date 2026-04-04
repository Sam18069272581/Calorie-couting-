# test_logic.py
from sqlmodel import Session, select
from models import User, Food, engine
from algorithm import get_final_calories

def init_user_and_calc():
    # 1. 模拟用户输入（你可以改成你自己的数据）
    user_data = {
        "name": "Gemini_User",
        "age": 21,
        "gender": "男",
        "height": 180.0,
        "weight": 80.0,
        "activity": "轻度运动",
        "goal": "温和减脂"
    }

    # 2. 调用算法获取热量
    results = get_final_calories(
        user_data["weight"], 
        user_data["height"], 
        user_data["age"], 
        user_data["gender"], 
        user_data["activity"], 
        user_data["goal"]
    )
    
    target_cal = results["Target"]

    # 3. 将用户信息存入数据库
    with Session(engine) as session:
        new_user = User(
            name=user_data["name"],
            age=user_data["age"],
            gender=user_data["gender"],
            height=user_data["height"],
            weight=user_data["weight"],
            activity_factor=1.375, # 对应轻度运动
            target_calories=target_cal
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        print(f"用户 {new_user.name} 已存档，每日目标热量: {new_user.target_calories} kcal")

if __name__ == "__main__":
    init_user_and_calc()