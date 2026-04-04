from typing import Optional
from sqlmodel import Field, SQLModel, create_engine

# --- 数据库表模型 ---

class Food(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index = True)             # 食物名称：如 "生燕麦", "熟米饭"
    category: str           # 分类：主食, 肉类, 油脂
    calories_100g: float    # 每100g热量
    protein_100g: float     # 每100g蛋白质
    carbs_100g: float       # 每100g碳水
    fat_100g: float         # 每100g脂肪

# --- 数据库连接配置 ---
# 这里使用 SQLite，数据库文件会直接生成在你的项目根目录下，名字叫 database.db
sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False}) # echo=True 会在终端显示 SQL 语句，方便调试

def create_db_and_tables():
    """初始化数据库，创建上面定义的表"""
    SQLModel.metadata.create_all(engine)