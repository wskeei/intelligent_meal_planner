"""
智能配餐系统 - Streamlit 前端

提供用户友好的配餐界面
"""

import streamlit as st
import requests
import json

# 页面配置
st.set_page_config(
    page_title="智能配餐系统",
    page_icon="🍽️",
    layout="wide"
)

# API 地址
API_BASE = "http://localhost:8000"


def main():
    st.title("🍽️ 智能配餐系统")
    st.markdown("*基于强化学习与多Agent协作的个性化配餐推荐*")
    
    # 侧边栏 - 参数设置
    with st.sidebar:
        st.header("⚙️ 配餐参数")
        
        st.subheader("营养目标")
        target_calories = st.slider("目标卡路里 (kcal)", 1200, 3000, 2000, 100)
        target_protein = st.slider("目标蛋白质 (g)", 50, 200, 100, 10)
        target_carbs = st.slider("目标碳水化合物 (g)", 100, 400, 250, 25)
        target_fat = st.slider("目标脂肪 (g)", 30, 120, 60, 10)
        
        st.subheader("预算限制")
        max_budget = st.slider("最大预算 (元)", 20, 100, 50, 5)
        
        st.markdown("---")
        st.markdown("### 快捷预设")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏃 减脂模式"):
                st.session_state.preset = "减脂"
        with col2:
            if st.button("💪 增肌模式"):
                st.session_state.preset = "增肌"
    
    # 主内容区
    tab1, tab2 = st.tabs(["🎯 快速配餐", "💬 智能对话"])
    
    with tab1:
        st.subheader("快速生成配餐方案")
        st.markdown("根据左侧设置的营养目标和预算，一键生成今日配餐")
        
        if st.button("🚀 生成配餐方案", type="primary", use_container_width=True):
            with st.spinner("AI 正在为您规划最优配餐..."):
                try:
                    # 直接调用本地模块（避免需要启动 API 服务）
                    from tools.rl_model_tool import create_rl_model_tool
                    from tools.recipe_database_tool import recipe_db_tool
                    
                    tool = create_rl_model_tool()
                    result = tool._run(
                        target_calories=target_calories,
                        target_protein=target_protein,
                        target_carbs=target_carbs,
                        target_fat=target_fat,
                        max_budget=max_budget
                    )
                    data = json.loads(result)
                    display_meal_plan(data, recipe_db_tool)
                except FileNotFoundError:
                    st.error("❌ 模型文件未找到，请先训练模型")
                except Exception as e:
                    st.error(f"❌ 生成失败: {str(e)}")
    
    with tab2:
        st.subheader("智能对话配餐")
        st.markdown("用自然语言描述您的需求，AI 营养师为您定制方案")
        
        user_input = st.text_area(
            "请描述您的配餐需求：",
            placeholder="例如：我想减肥，预算40元，不吃辣，喜欢清淡口味...",
            height=100
        )
        
        if st.button("🤖 开始对话配餐", use_container_width=True):
            if user_input:
                st.info("💡 对话模式需要配置 LLM API Key（如 OpenAI）")
                st.markdown("请在环境变量中设置 `OPENAI_API_KEY`")
            else:
                st.warning("请输入您的配餐需求")


def display_meal_plan(data: dict, recipe_db_tool):
    """展示配餐方案"""
    st.success("✅ 配餐方案生成成功！")
    
    meal_plan = data.get('meal_plan', {})
    metrics = data.get('metrics', {})
    target = data.get('target', {})
    
    # 三餐展示
    st.markdown("### 📋 今日配餐")
    cols = st.columns(3)
    
    meal_names = {'breakfast': '🌅 早餐', 'lunch': '☀️ 午餐', 'dinner': '🌙 晚餐'}
    
    for i, (meal, recipe_id) in enumerate(meal_plan.items()):
        with cols[i]:
            st.markdown(f"#### {meal_names.get(meal, meal)}")
            # 获取菜品详情
            recipe_info = recipe_db_tool._run(recipe_ids=[recipe_id])
            st.text(recipe_info)
    
    # 营养汇总
    st.markdown("### 📊 营养达成情况")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cal_pct = metrics.get('calories_achievement', 0)
        st.metric("卡路里", f"{metrics.get('total_calories', 0):.0f} kcal", 
                  f"{cal_pct:.1f}% 达成")
    with col2:
        pro_pct = metrics.get('protein_achievement', 0)
        st.metric("蛋白质", f"{metrics.get('total_protein', 0):.1f} g",
                  f"{pro_pct:.1f}% 达成")
    with col3:
        st.metric("碳水化合物", f"{metrics.get('total_carbs', 0):.1f} g")
    with col4:
        st.metric("脂肪", f"{metrics.get('total_fat', 0):.1f} g")
    
    # 花费
    st.markdown("### 💰 费用统计")
    budget_pct = metrics.get('budget_usage', 0)
    st.progress(min(budget_pct / 100, 1.0))
    st.markdown(f"总花费: **¥{metrics.get('total_cost', 0):.1f}** / 预算 ¥{target.get('budget', 50)}")


if __name__ == "__main__":
    main()