# src/intelligent_meal_planner/meal_chat/crews/planning_crew.py
"""PlanningCrew - 配餐方案生成 Crew"""

from crewai import Agent, Crew, Task, Process

from ..llm_config import get_planning_llm
from ..models.planning import PlanningResult
from ..tools.rl_planning_tool import create_meal_plan_dict
from ..profile.schema import UserProfile


def calculate_target_ranges(
    profile: dict,
    health_goal: str,
) -> dict:
    """
    根据用户档案和目标计算营养目标范围。

    简化版本：使用基础代谢率和活动系数估算。
    """
    # 获取基础数据，提供默认值
    weight = profile.get("weight_kg") or 70
    height = profile.get("height_cm") or 170
    age = profile.get("age") or 30
    gender = profile.get("gender") or "male"

    # 确保是数值类型
    weight = float(weight) if weight else 70.0
    height = float(height) if height else 170.0
    age = int(age) if age else 30

    # 计算基础代谢率 (BMR) - 使用 Mifflin-St Jeor 公式
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # 活动系数
    activity_multiplier = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    activity_level = profile.get("activity_level", "moderate")
    tdee = bmr * activity_multiplier.get(activity_level, 1.55)

    # 根据目标调整
    if health_goal == "lose_weight":
        calories_target = tdee * 0.85  # 15% 缺口
        protein_per_kg = 1.8  # 高蛋白保肌肉
    elif health_goal == "gain_muscle":
        calories_target = tdee * 1.1  # 10% 盈余
        protein_per_kg = 2.0
    else:  # maintain / healthy
        calories_target = tdee
        protein_per_kg = 1.5

    # 计算宏量营养素
    target_protein = weight * protein_per_kg
    target_fat = calories_target * 0.25 / 9  # 25% 来自脂肪
    target_carbs = (calories_target - target_protein * 4 - target_fat * 9) / 4

    return {
        "calories_min": int(calories_target * 0.95),
        "calories_max": int(calories_target * 1.05),
        "protein_min": int(target_protein * 0.9),
        "protein_max": int(target_protein * 1.1),
        "carbs_min": int(target_carbs * 0.9),
        "carbs_max": int(target_carbs * 1.1),
        "fat_min": int(target_fat * 0.9),
        "fat_max": int(target_fat * 1.1),
        "tdee": int(tdee),
        "bmr": int(bmr),
    }


def create_requirements_reviewer_agent() -> Agent:
    """创建需求审核员 Agent"""
    return Agent(
        role="需求审核员",
        goal="确认用户需求完整性和一致性",
        backstory="你负责检查用户提供的所有信息是否完整、合理。",
        llm=get_planning_llm(),
        verbose=True,
    )


def create_nutrition_planner_agent() -> Agent:
    """创建营养规划师 Agent"""
    return Agent(
        role="营养规划师",
        goal="根据用户目标计算精确的营养目标范围",
        backstory=(
            "你是营养学专家，擅长根据用户的身体状况和目标"
            "计算精确的宏量营养素配比。"
        ),
        llm=get_planning_llm(),
        verbose=True,
    )


def create_meal_generator_agent() -> Agent:
    """创建 RL 配餐器 Agent"""
    return Agent(
        role="RL配餐器",
        goal="调用强化学习模型生成最优配餐方案",
        backstory="你使用训练好的 RL 模型生成符合营养目标和预算的配餐方案。",
        llm=get_planning_llm(),
        verbose=True,
    )


def create_requirements_task(
    agent: Agent,
    profile: dict,
    preferences: dict,
) -> Task:
    """创建需求审核任务"""
    return Task(
        description=f"""
审核用户需求是否完整。

## 用户档案
{profile}

## 用户偏好
{preferences}

## 必需字段
档案：gender, age, height_cm, weight_kg, activity_level
偏好：health_goal, budget

## 任务
检查所有必需字段是否存在，返回审核摘要。
""",
        expected_output="需求完整性摘要",
        agent=agent,
    )


def create_nutrition_task(
    agent: Agent,
    profile: dict,
    health_goal: str,
) -> Task:
    """创建营养规划任务"""
    target_ranges = calculate_target_ranges(profile, health_goal)

    return Task(
        description=f"""
根据用户档案计算营养目标。

## 用户档案
{profile}

## 目标
{health_goal}

## 计算结果
{target_ranges}

## 任务
验证计算结果是否合理，并生成营养规划摘要。
""",
        expected_output="营养目标范围摘要",
        agent=agent,
    )


def create_generation_task(
    agent: Agent,
    preferences: dict,
    target_ranges: dict,
) -> Task:
    """创建配餐生成任务"""
    return Task(
        description=f"""
使用 RL 工具生成配餐方案。

## 用户偏好
- 目标: {preferences.get('health_goal')}
- 预算: {preferences.get('budget')} 元
- 忌口: {preferences.get('disliked_foods', [])}
- 口味偏好: {preferences.get('preferred_tags', [])}

## 营养目标
- 热量: {target_ranges.get('calories_min')}-{target_ranges.get('calories_max')} kcal
- 蛋白质: {target_ranges.get('protein_min')}-{target_ranges.get('protein_max')} g
- 碳水: {target_ranges.get('carbs_min')}-{target_ranges.get('carbs_max')} g
- 脂肪: {target_ranges.get('fat_min')}-{target_ranges.get('fat_max')} g

## 任务
调用 DQN配餐工具 生成方案。
""",
        expected_output="配餐方案 JSON",
        agent=agent,
    )


class PlanningCrew:
    """配餐方案生成 Crew"""

    def __init__(self):
        self.reviewer = create_requirements_reviewer_agent()
        self.planner = create_nutrition_planner_agent()
        self.generator = create_meal_generator_agent()

    def run(
        self,
        profile: dict,
        preferences: dict,
        user_profile: UserProfile | None = None,
    ) -> PlanningResult:
        """
        执行配餐方案生成。

        Args:
            profile: 收集到的档案信息
            preferences: 收集到的偏好信息
            user_profile: 用户认知文件（可选，用于更丰富的上下文）

        Returns:
            PlanningResult
        """
        health_goal = preferences.get("health_goal") or "healthy"
        budget = preferences.get("budget") or 80
        if budget is not None:
            budget = float(budget)
        else:
            budget = 80.0

        # 计算营养目标
        target_ranges = calculate_target_ranges(profile, health_goal)

        # 调用 RL 模型生成方案
        try:
            meal_plan_result = create_meal_plan_dict(
                health_goal=health_goal,
                budget=budget,
                disliked_foods=preferences.get("disliked_foods", []),
                preferred_tags=preferences.get("preferred_tags", []),
                target_calories=int((target_ranges["calories_min"] + target_ranges["calories_max"]) / 2),
                target_protein=int((target_ranges["protein_min"] + target_ranges["protein_max"]) / 2),
                target_carbs=int((target_ranges["carbs_min"] + target_ranges["carbs_max"]) / 2),
                target_fat=int((target_ranges["fat_min"] + target_ranges["fat_max"]) / 2),
            )
        except Exception as e:
            return PlanningResult(
                meal_plan={},
                target_ranges=target_ranges,
                explanation=f"生成方案时出错: {str(e)}",
                status="error",
            )

        # 构建结果
        metrics = meal_plan_result.get("metrics", {})
        return PlanningResult(
            meal_plan=meal_plan_result.get("meal_plan", {}),
            target_ranges=target_ranges,
            explanation=self._generate_explanation(
                meal_plan_result,
                target_ranges,
                health_goal,
                budget,
            ),
            highlights=self._extract_highlights(meal_plan_result, target_ranges),
            total_cost=metrics.get("total_cost", 0),
            total_calories=metrics.get("total_calories", 0),
            total_protein=metrics.get("total_protein", 0),
            total_carbs=metrics.get("total_carbs", 0),
            total_fat=metrics.get("total_fat", 0),
            calories_achievement=metrics.get("calories_achievement", 0),
            protein_achievement=metrics.get("protein_achievement", 0),
            budget_usage=metrics.get("budget_usage", 0),
            status=meal_plan_result.get("status", "ok"),
        )

    def _generate_explanation(
        self,
        meal_plan_result: dict,
        target_ranges: dict,
        health_goal: str,
        budget: float,
    ) -> str:
        """生成方案解释"""
        metrics = meal_plan_result.get("metrics", {})
        status = meal_plan_result.get("status", "ok")

        if status == "budget_infeasible":
            return f"在 {budget} 元预算内无法生成满足营养目标的方案，建议增加预算。"

        goal_text = {
            "lose_weight": "减脂",
            "gain_muscle": "增肌",
            "maintain": "维持",
            "healthy": "健康饮食",
        }.get(health_goal, health_goal)

        calories = metrics.get("total_calories", 0)
        protein = metrics.get("total_protein", 0)
        cost = metrics.get("total_cost", 0)

        return (
            f"方案已生成，围绕{goal_text}目标。"
            f"总热量约 {calories} kcal，蛋白质 {protein} g，"
            f"总花费 {cost:.1f} 元。"
        )

    def _extract_highlights(
        self,
        meal_plan_result: dict,
        target_ranges: dict,
    ) -> list[str]:
        """提取方案亮点"""
        highlights = []
        metrics = meal_plan_result.get("metrics", {})

        # 检查热量达标情况
        calories_pct = metrics.get("calories_achievement", 0)
        if 90 <= calories_pct <= 110:
            highlights.append("热量目标精准达成")

        # 检查蛋白质达标
        protein_pct = metrics.get("protein_achievement", 0)
        if protein_pct >= 90:
            highlights.append("蛋白质摄入充足")

        # 检查预算使用
        budget_pct = metrics.get("budget_usage", 0)
        if budget_pct <= 80:
            highlights.append("预算使用高效，有余量")

        return highlights
