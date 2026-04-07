import streamlit as st
from sqlmodel import Session, select
from external_api import search_german_food
import pandas as pd
import plotly.express as px
import algorithm
from models import engine, Food, create_db_and_tables

# 确保数据库表在云端启动时自动创建
try:
    create_db_and_tables()
except Exception as e:
    st.error(f"数据库初始化失败: {e}")

# 1. 页面配置
st.set_page_config(page_title="硬核营养战术面板", layout="wide")

# 2. 核心数据读取 (解决 Undefined 报错的关键)
def load_food_data():
    with Session(engine) as session:
        foods = session.exec(select(Food)).all()
       
        if not foods:
            from init_db import add_initial_foods
            add_initial_foods()
            foods = session.exec(select(Food)).all() 
        options = {f.name: {"p": f.protein_100g, "f": f.fat_100g, "c": f.carbs_100g} for f in foods}
        names = list(options.keys())
        return foods, options, names

# 这一步确保了变量在全局可用
all_foods_db, food_options, food_names = load_food_data()

# --- UI 界面开始 ---
st.title("💪 硬核多维营养战术面板 (PRO)")

with st.sidebar:
    st.header("👤 档案")
    gender = st.radio("性别", ["男", "女"])
    weight = st.number_input("体重(kg)", 80.0)
    height = st.number_input("身高(cm)", 180.0)
    age = st.number_input("年龄", 21)
    activity = st.selectbox("运动频率", list(algorithm.ACTIVITY_LEVELS.keys()))
    goal = st.selectbox("目标", list(algorithm.GOAL_FACTORS.keys()))

# 3. 计算与图表
base_res = algorithm.get_final_calories(weight, height, age, gender, activity, goal)
macros = algorithm.calculate_macros_pro(base_res["Target"], weight, gender, goal)

# 雷达图
fig = px.line_polar(
    r=[macros["protein_g"], macros["carbs_g"], macros["fat_g"]],
    theta=['蛋白质', '碳水', '脂肪'], 
    line_close=True
)
fig.update_traces(fill='toself', fillcolor='rgba(255, 75, 75, 0.3)')
st.plotly_chart(fig, use_container_width=True)

# app.py 核心交互区重构
# --- 2. 🍱 全天食谱战术分配 (替代原有的简单计算器) ---
st.divider()
st.header("🍱 全天食谱战术分配 (3:4:3 模式)")

# 1. 自动获取三餐热量目标 (调用 algorithm 里的分配逻辑)
# 假设你的 algorithm.py 里有 distribute_meals，如果没有，可以直接用下面的比例
meal_ratios = [0.3, 0.4, 0.3]
meal_names = ["早餐", "午餐", "晚餐"]

# 创建三餐选项卡
tabs = st.tabs(["🌅 早餐 (30%)", "🌞 午餐 (40%)", "🌙 晚餐 (30%)"])

for i, tab in enumerate(tabs):
    name = meal_names[i]
    ratio = meal_ratios[i]
    
    # 计算该餐的理想目标
    t_cal = base_res["Target"] * ratio
    t_p = macros["protein_g"] * ratio
    t_c = macros["carbs_g"] * ratio
    t_f = macros["fat_g"] * ratio

    with tab:
        col_input, col_fix = st.columns([2, 1])
        
        with col_input:
            st.markdown(f"**目标：{round(t_cal)} kcal** | 蛋白:{round(t_p)}g | 碳水:{round(t_c)}g | 脂肪:{round(t_f)}g")
            
            # 用户自由选择该餐想吃的食物
            user_choice = st.multiselect(f"你想往{name}里加点什么？", food_names, key=f"multi_{i}")
            
            current_meal_foods = []
            for fname in user_choice:
                # 动态生成每种食物的重量输入框
                amt = st.number_input(f"调整 {fname} 重量(g)", value=100, step=10, key=f"weight_{fname}_{i}")
                f_info = food_options[fname]
                current_meal_foods.append({
                    "name": fname,
                    "p_total": (f_info['p']/100) * amt,
                    "f_total": (f_info['f']/100) * amt,
                    "c_total": (f_info['c']/100) * amt,
                    "p_100": f_info['p'], # 👈 新增：传给算法用于计算补齐克数
                    "f_100": f_info['f']
                })

        with col_fix:
            st.markdown("🚀 **实时平衡指挥部**")
            # app.py 修复版逻辑
            if user_choice:
                result = algorithm.balance_meal_plan(t_cal, t_p, t_f, t_c, current_meal_foods, all_foods_db)
    
            # 1. 处理蛋白质补齐
                p_item = result.get('remedy_p') # 使用 .get 更安全
                if p_item: # 只有不为 None 时才执行
                    st.success(f"🥩 **补齐蛋白：{p_item['amount']}g {p_item['name']}**")
                else:
                    st.write("✅ 蛋白质已达标")

                # 2. 处理脂肪补齐
                f_item = result.get('remedy_f')
                if f_item: # 只有不为 None 时才执行
                    st.success(f"🍾 **补齐脂肪：{f_item['amount']}g {f_item['name']}**")
                else:
                    st.write("✅ 脂肪已达标")
        
                # 3. 处理碳水缺口
                c_gap = result['gaps']['c']
                if c_gap > 5:
                    st.warning(f"💡 还差 {round(c_gap, 1)}g 碳水，建议加点主食")
                elif c_gap < -10:
                    st.error(f"⚠️ 碳水超标了 {round(abs(c_gap), 1)}g")
                
            
st.header("🔍 扩充弹药库 (从全欧数据库导入)")

search_query = st.text_input("输入食物名称 (支持德文/英文，如: Quark, Haferflocken)")

if st.button("搜索外部数据库"):
    with st.spinner("正在连接欧洲食品数据库..."):
        results = search_german_food(search_query)
        
        if results:
            st.session_state.api_results = results # 存入 session state 供后续选择
        else:
            st.warning("没找到相关食物，换个词试试？")

# 显示搜索结果并提供导入按钮
if "api_results" in st.session_state:
    for idx, item in enumerate(st.session_state.api_results):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{item['name']}** ({item['brand']})")
            st.caption(f"C: {item['carbs_100g']}g | P: {item['protein_100g']}g | F: {item['fat_100g']}g")
        with col2:
            # 动态生成导入按钮
            if st.button("📥 导入我的数据库", key=f"import_{idx}"):
                with Session(engine) as session:
                    new_food = Food(
                        name=item['name'],
                        protein_100g=item['protein_100g'],
                        fat_100g=item['fat_100g'],
                        carbs_100g=item['carbs_100g']
                    )
                    session.add(new_food)
                    session.commit()
                    st.success(f"✅ {item['name']} 已成功加入你的战术面板！刷新页面即可使用。")

def load_food_data():
    with Session(engine) as session:
        foods = session.exec(select(Food)).all()
        
        # --- 重点：如果没数据，自动跑一遍初始化 ---
        if not foods:
            from init_db import add_initial_foods
            add_initial_foods() # 确保你这个函数能正常运行
            foods = session.exec(select(Food)).all() # 重新抓取
        # ---------------------------------------
        
        options = {f.name: {"p": f.protein_100g, "f": f.fat_100g, "c": f.carbs_100g} for f in foods}
        names = list(options.keys())
        return foods, options, names
    
# app.py 改进建议

# 使用 Session State 存储个人档案
if 'user_weight' not in st.session_state:
    st.session_state.user_weight = 80.0

# 侧边栏改为绑定模式
with st.sidebar:
    weight = st.number_input("体重 (kg)", value=st.session_state.user_weight, key="weight_input")
    st.session_state.user_weight = weight # 实时保存