# src/intelligent_meal_planner/meal_chat/crews/intent_crew.py
"""IntentCrew - 意图理解 Crew"""

from crewai import Agent, Crew, Task, Process

from ..llm_config import get_extraction_llm
from ..models.intent import IntentResult


def create_intent_analyst_agent() -> Agent:
    """创建对话分析师 Agent"""
    return Agent(
        role="对话分析师",
        goal="分析用户消息，理解对话意图和上下文",
        backstory=(
            "你是一个专业的对话分析师，擅长理解用户的言外之意。"
            "你需要准确识别用户是想提供信息、提问、请求方案还是闲聊。"
            "同时要判断信息是否足够生成配餐方案。"
        ),
        llm=get_extraction_llm(),
        verbose=True,
    )


def create_info_extractor_agent() -> Agent:
    """创建信息提取员 Agent"""
    return Agent(
        role="信息提取员",
        goal="从用户消息中提取结构化信息",
        backstory=(
            "你擅长从自然语言中提取关键数据。"
            "需要提取的信息包括：性别、年龄、身高、体重、活动量、"
            "健康目标、预算、忌口食材、口味偏好等。"
        ),
        llm=get_extraction_llm(),
        verbose=True,
    )


def create_intent_analysis_task(
    agent: Agent,
    user_message: str,
    recent_messages: list[dict],
    profile_summary: str,
) -> Task:
    """创建意图分析任务"""
    context_str = ""
    if recent_messages:
        context_str = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in recent_messages[-4:]  # 最近 2 轮
        ])

    return Task(
        description=f"""
分析用户的最新消息，识别其意图。

## 已知用户信息
{profile_summary}

## 对话历史
{context_str if context_str else "(无历史对话)"}

## 用户最新消息
{user_message}

## 任务
1. 判断用户意图类型（provide_info/ask_question/request_plan/adjust_plan/chat/complaint）
2. 评估意图识别的置信度（0.0-1.0）
3. 生成简短的上下文摘要
4. 判断信息是否足够生成配餐方案（需要：性别、年龄、身高、体重、活动量、目标、预算）
""",
        expected_output="意图分析结果，包含 intent, confidence, context_summary, ready_for_planning",
        agent=agent,
    )


def create_info_extraction_task(
    agent: Agent,
    user_message: str,
    expected_slot: str | None = None,
) -> Task:
    """创建信息提取任务"""
    slot_hint = f"\n预期用户在回答: {expected_slot}" if expected_slot else ""

    return Task(
        description=f"""
从用户消息中提取结构化信息。

## 用户消息
{user_message}
{slot_hint}

## 需要提取的字段
档案字段：
- gender: 性别 (male/female)
- age: 年龄（整数）
- height_cm: 身高（厘米，整数）
- weight_kg: 体重（公斤，整数或浮点）
- activity_level: 活动量 (sedentary/light/moderate/active/very_active)

偏好字段：
- health_goal: 健康目标 (lose_weight/gain_muscle/maintain/healthy)
- budget: 每日预算（元，浮点数）
- disliked_foods: 忌口食材列表
- preferred_tags: 口味偏好标签列表

今日配餐需求字段（用户对本次配餐的具体要求）：
- mood: 今天的状态（如"不太饿"、"很饿"、"精力不足"）
- specific_requests: 今天的具体要求（如"少吃一点"、"想吃清淡的"、"想吃辣的"）
- avoid_today: 今天不想吃的东西（如"不想吃米饭"、"不想吃肉"）
- time_constraint: 时间限制（如"赶时间"、"需要快手菜"）

## 提取规则
1. 只提取用户明确提及的信息
2. 没有提及的字段留空
3. 数值要转换成正确的类型
4. 如果用户在纠正之前的信息，提取正确的值
""",
        expected_output="提取结果，包含 profile_updates 和 preference_updates",
        agent=agent,
    )


def create_intent_result_task(
    agent: Agent,
    analysis_task: Task,
    extraction_task: Task,
) -> Task:
    """创建结果整合任务"""
    return Task(
        description="""
整合分析结果，生成结构化输出。

## 意图分析
{analysis_output}

## 信息提取
{extraction_output}

## 输出格式
按照 IntentResult 格式输出，包含：
- intent: 意图类型
- confidence: 置信度
- context_summary: 上下文摘要
- profile_updates: 档案更新
- preference_updates: 偏好更新
- question_topic: 如果是提问，问题主题
- adjustment_request: 如果是调整，调整内容
- ready_for_planning: 是否可以生成方案
""",
        expected_output="IntentResult 结构化输出",
        agent=agent,
        context=[analysis_task, extraction_task],  # 使用 context 建立依赖
        output_pydantic=IntentResult,
    )


class IntentCrew:
    """意图理解 Crew"""

    def __init__(self):
        self.analyst = create_intent_analyst_agent()
        self.extractor = create_info_extractor_agent()

    def run(
        self,
        user_message: str,
        recent_messages: list[dict],
        profile_summary: str,
        expected_slot: str | None = None,
    ) -> IntentResult:
        """
        执行意图理解。

        Args:
            user_message: 用户消息
            recent_messages: 最近对话历史
            profile_summary: 用户画像摘要
            expected_slot: 预期用户正在回答的字段

        Returns:
            IntentResult
        """
        # 创建任务
        analysis_task = create_intent_analysis_task(
            agent=self.analyst,
            user_message=user_message,
            recent_messages=recent_messages,
            profile_summary=profile_summary,
        )

        extraction_task = create_info_extraction_task(
            agent=self.extractor,
            user_message=user_message,
            expected_slot=expected_slot,
        )

        result_task = create_intent_result_task(
            agent=self.analyst,
            analysis_task=analysis_task,
            extraction_task=extraction_task,
        )

        # 创建 Crew
        crew = Crew(
            agents=[self.analyst, self.extractor],
            tasks=[analysis_task, extraction_task, result_task],
            process=Process.sequential,
            verbose=True,
        )

        # 执行
        result = crew.kickoff()

        # 从结果中获取 IntentResult
        if hasattr(result, 'pydantic') and result.pydantic:
            return result.pydantic

        # 备选：从最后一个任务获取
        if result_task.output and result_task.output.pydantic:
            return result_task.output.pydantic

        # 默认返回
        return IntentResult(
            intent="chat",
            confidence=0.5,
            context_summary="无法解析意图",
        )
