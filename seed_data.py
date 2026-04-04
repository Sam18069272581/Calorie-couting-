# seed_data.py
from sqlmodel import Session
from models import Food, engine

def seed_foods():
    with Session(engine) as session:
        foods = [
            Food(name="生燕麦", category="主食", calories_100g=367, protein_100g=12, carbs_100g=60, fat_100g=7),
            Food(name="白米饭", category="主食", calories_100g=130, protein_100g=2.6, carbs_100g=28, fat_100g=0.3),
            Food(name="橄榄油", category="油脂", calories_100g=884, protein_100g=0, carbs_100g=0, fat_100g=100),
            Food(name="鸡胸肉", category="肉类", calories_100g=133, protein_100g=30, carbs_100g=0, fat_100g=1.5),
        ]
        for f in foods:
            session.add(f)
        session.commit()

if __name__ == "__main__":
    seed_foods()
    print("种子食物数据已存入数据库！")