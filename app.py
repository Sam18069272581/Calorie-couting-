import streamlit as st
from sqlmodel import Session, select
from external_api import search_german_food
import pandas as pd
import plotly.express as px
import algorithm
from models import engine, Food, create_db_and_tables

# --- 1. 初始化与数据加载 ---
try:
    create_db_and_tables()
except Exception as e:
    st.error(f"数据库初始化失败: {e}")

@st.cache_data(show_spinner=False)
def load_food_data():
    with Session(engine) as session:
        foods = session.exec(select(Food)).all()
        if not foods:
            try:
                from init_db import add_initial_foods
                add_initial_foods()
                foods = session.exec(select(Food)).all()
            except ImportError:
                pass 
        options = {f.name: {"p": f.protein_100g, "f": f.fat_100g, "c": f.carbs_100g} for f in foods}
        return foods, options, list(options.keys())

all_foods_db, food_options, food_names = load_food_data()

# --- 2. 页面配置与全天汇总变量 ---
st.set_page_config(page_title="硬核营养战术面板", layout="wide")
# 关键：每次运行脚本时重置汇总，通过循环组件重新计算
total_intake = {"p": 0.0, "c": 0.0, "f": 0.0, "cal": 0.0}

# --- 3. 侧边栏：档案与战术目标计算 ---
with st.sidebar:
    st.header("👤 档案与目标")
    gender = st.radio("性别", ["男", "女"])
    weight = st.number_input("体重 (kg)", 80.0)
    height = st.number_input("身高 (cm)", 180.0)
    age = st.number_input("年龄", 21)
    activity = st.selectbox("运动频率", list(algorithm.ACTIVITY_LEVELS.keys()))
    goal = st.selectbox("目标", list(algorithm.GOAL_FACTORS.keys()))

    # 调用算法计算目标 (同步 algorithm.py 的逻辑)
    base_res = algorithm.get_final_calories(weight, height, age, gender, activity, goal)
    macros = algorithm.calculate_macros_pro(base_res["Target"], weight, gender, goal)
    
    target_p = macros["protein_g"]
    target_c = macros["carbs_g"]
    target_f = macros["fat_g"]
    target_cal = base_res["Target"]

    st.divider()
    st.success(f"🎯 每日目标: {round(target_cal)} kcal")
    st.info(f"P: {round(target_p)}g | C: {round(target_c)}g | F: {round(target_f)}g")

# --- 4. 实时状态监控 (雷达图) ---
st.title("💪 硬核多维营养战术面板 (PRO)")
fig = px.line_polar(
    r=[target_p, target_c, target_f],
    theta=['蛋白质', '碳水', '脂肪'], 
    line_close=True,
    title="战术目标模型"
)
fig.update_traces(fill='toself', fillcolor='rgba(255, 75, 75, 0.3)')
st.plotly_chart(fig, use_container_width=True)

# --- 5. 🍱 全天食谱战术分配 (核心计算区) ---
st.header("🍱 全天食谱战术分配 (3:4:3 模式)")
meal_ratios = [0.3, 0.4, 0.3]
meal_names = ["早餐", "午餐", "晚餐"]
tabs = st.tabs([f"🌅 {meal_names[0]}", f"🌞 {meal_names[1]}", f"🌙 {meal_names[2]}"])

for i, tab in enumerate(tabs):
    ratio = meal_ratios[i]
    t_cal, t_p, t_c, t_f = target_cal * ratio, target_p * ratio, target_c * ratio, target_f * ratio
    
    with tab:
        col_in, col_res = st.columns([2, 1])
        with col_in:
            st.markdown(f"**本餐建议目标：{round(t_cal)} kcal**")
            user_choice = st.multiselect(f"计划加入的食物", food_names, key=f"multi_{i}")
            
            current_meal_foods = []
            for fname in user_choice:
                amt = st.number_input(f"{fname} 重量 (g)", value=100, step=10, key=f"w_{fname}_{i}")
                f_info = food_options[fname]
                
                # 计算单项营养并累加到全天汇总
                p_val = (f_info['p']/100) * amt
                c_val = (f_info['c']/100) * amt
                f_val = (f_info['f']/100) * amt
                
                total_intake["p"] += p_val
                total_intake["c"] += c_val
                total_intake["f"] += f_val
                total_intake["cal"] += (p_val*4 + c_val*4 + f_val*9)
                
                current_meal_foods.append({
                    "name": fname, "p_total": p_val, "f_total": f_val, "c_total": c_val,
                    "p_100": f_info['p'], "f_100": f_info['f']
                })

        with col_res:
            st.markdown("🚀 **实时平衡建议**")
            if user_choice:
                res = algorithm.balance_meal_plan(t_cal, t_p, t_f, t_c, current_meal_foods, all_foods_db)
                if res.get('remedy_p'):
                    st.success(f"🥩 补齐蛋白：{res['remedy_p']['amount']}g {res['remedy_p']['name']}")
                if res.get('remedy_f'):
                    st.success(f"🍾 补齐脂肪：{res['remedy_f']['amount']}g {res['remedy_f']['name']}")
                if not res.get('remedy_p') and not res.get('remedy_f'):
                    st.write("✅ 本餐配比合理")

# --- 6. 📊 今日宏量营养达成率 (全天汇总) ---
st.divider()
st.subheader("📊 全天达成进度汇总")
c1, c2, c3 = st.columns(3)

with c1:
    p_gap = total_intake["p"] - target_p
    p_percent = min(total_intake["p"] / target_p, 1.0) if target_p > 0 else 0
    st.metric("总蛋白质", f"{total_intake['p']:.1f}g", f"{p_gap:.1f}g")
    st.progress(p_percent)

with c2:
    c_gap = total_intake["c"] - target_c
    c_percent = min(total_intake["c"] / target_c, 1.0) if target_c > 0 else 0
    st.metric("总碳水", f"{total_intake['c']:.1f}g", f"{c_gap:.1f}g")
    st.progress(c_percent)

with c3:
    f_gap = total_intake["f"] - target_f
    f_percent = min(total_intake["f"] / target_f, 1.0) if target_f > 0 else 0
    # 脂肪超标时使用红色警告 (inverse)
    st.metric("总脂肪", f"{total_intake['f']:.1f}g", f"{f_gap:.1f}g", delta_color="inverse" if f_gap > 0 else "normal")
    st.progress(f_percent)

# --- 7. 🔍 扩充弹药库 (API 搜索) ---
st.divider()
st.header("🔍 发现新食材 (Open Food Facts API)")
search_query = st.text_input("搜点别的？(如: Magerquark, Skyr, Chicken)")

if st.button("启动全球搜索"):
    with st.spinner("正在穿越服务器..."):
        api_results = search_german_food(search_query)
        if api_results:
            st.session_state.temp_results = api_results
        else:
            st.warning("没找到结果，换个词试试？")

if "temp_results" in st.session_state:
    for idx, item in enumerate(st.session_state.temp_results):
        col_name, col_btn = st.columns([4, 1])
        with col_name:
            st.write(f"**{item['name']}** | P:{item['protein_100g']} F:{item['fat_100g']} C:{item['carbs_100g']}")
        with col_btn:
            if st.button("📥 存入", key=f"save_{idx}"):
                with Session(engine) as sess:
                    new_food = Food(name=item['name'], protein_100g=item['protein_100g'], 
                                   fat_100g=item['fat_100g'], carbs_100g=item['carbs_100g'])
                    sess.add(new_food)
                    sess.commit()
                st.success(f"已加入！刷新后可用。")