# init_db.py
from sqlmodel import Session, select
from models import Food, engine, create_db_and_tables

def add_initial_foods():
    new_foods = [
        # 补丁类 (高蛋白/高脂肪)
        Food(name="去皮鸡腿", category="肉类", calories_100g=121, protein_100g=20.2, fat_100g=4.0, carbs_100g=0),
        Food(name="金枪鱼罐头", category="肉类", calories_100g=90, protein_100g=20, fat_100g=0.8, carbs_100g=0),
        Food(name="牛肉", category="肉类", calories_100g=160, protein_100g=20, fat_100g=8.7, carbs_100g=0.5),
        Food(name="牛油果", category="油脂", calories_100g=160, protein_100g=2, fat_100g=14.7, carbs_100g=8.5),
        Food(name="橄榄油", category="油脂", calories_100g=884, protein_100g=0, fat_100g=100, carbs_100g=0),
        Food(name="黄油", category="油脂", calories_100g=888, protein_100g=1.4, fat_100g=98, carb_100g=0),
        Food(name="鸡蛋", category="蛋", calories_100g=139, protein_100g=13.1, fat_100g=8.6, carb_100g=2.4),
        
        # 基础类 (乳制品/主食)
        Food(name="纯牛奶", category="乳制品", calories_100g=64, protein_100g=3.3, fat_100g=3.6, carbs_100g=4.8),
        Food(name="Speisequark", category="乳制品", calories_100g=70, protein_100g=12.2, fat_100g=0.3, carbs_100g=3.9),
        Food(name="大米", category="主食", calories_100g=346, protein_100g=7.9, fat_100g=0.9, carbs_100g=77.2),
        Food(name="熟米饭", category="主食", calories_100g=116, protein_100g=2.6, fat_100g=0.3, carbs_100g=25.9),
        Food(name="全麦面包", category="主食", calories_100g=246, protein_100g=9.1, fat_100g=3.3, carbs_100g=45),
        Food(name="燕麦", category="主食", calories_100g=367, protein_100g=12.1, fat_100g=6.7, carbs_100g=61.4),
        Food(name="意大利面", category="主食", calories_100g=365.2, protein_100g=12.9, fat_100g=1.8, carbs_100g=75.3),
        
        # 蔬菜类
        Food(name="洋葱", category="蔬菜", calories_100g=40, protein_100g=1.1, fat_100g=0.1, carbs_100g=9.3),
        Food(name="胡萝卜", category="蔬菜", calories_100g=41, protein_100g=0.9, fat_100g=0.2, carbs_100g=9.6),
        Food(name="彩椒", category="蔬菜", calories_100g=26, protein_100g=1.3, fat_100g=0.2, carbs_100g=6.4),
    ]

    with Session(engine) as session:
        for food in new_foods:
            # 查重逻辑：防止重复运行脚本导致数据堆积
            statement = select(Food).where(Food.name == food.name)
            results = session.exec(statement)
            if not results.first():
                session.add(food)
        session.commit()
    print("✅ 战术库初始化完成！")

if __name__ == "__main__":
    create_db_and_tables() # 这一步会自动根据 models.py 创建表
    add_initial_foods()