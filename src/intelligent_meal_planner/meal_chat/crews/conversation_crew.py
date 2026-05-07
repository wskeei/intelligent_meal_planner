# src/intelligent_meal_planner/meal_chat/crews/conversation_crew.py
"""ConversationCrew - 对话生成 Crew"""

from crewai import Agent, Crew, Task, Process

from ..llm_config import get_conversation_llm
from ..models.conversation import ConversationResult
from ..models.intent import IntentResult


def create_nutritionist_agent() -> Agent:
    """创建营养师 Agent - 主对话 Agent"""
    return Agent(
        role="营养师",
        goal="像专业营养师一样与用户自然对话，帮助用户达成饮食目标",
        backstory=(
            "你是一位经验丰富的营养师，擅长用亲切自然的方式与用户沟通。"
            "你的风格是：专业但不死板，友好但不敷衍。"
            "在收集信息时，你会像朋友聊天一样自然地提问，而不是机械地逐项询问。"
            "当用户有疑问时，你会用通俗易懂的语言解释专业知识。"
            "你的回答应该简洁有力，避免冗长。"
        ),
        llm=get_conversation_llm(),
        verbose=True,
    )


def create_explainer_agent() -> Agent:
    """创建方案解读员 Agent"""
    return Agent(
        role="方案解读员",
        goal="用专业但易懂的方式解释配餐方案的营养原理",
        backstory=(
            "你擅长把复杂的营养科学转化为用户能理解的内容。"
            "你会解释为什么选择某道菜、某个营养配比，"
            "以及这些选择如何帮助用户达成目标。"
        ),
        llm=get_conversation_llm(),
        verbose=True,
    )


def create_conversation_task(
    agent: Agent,
    intent_result: IntentResult,
    recent_messages: list[dict],
    profile_summary: str,
    current_phase: str,
) -> Task:
    """创建对话生成任务"""
    history_str = ""
    if recent_messages:
        history_str = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in recent_messages
        ])

    # 根据意图和阶段定制任务描述
    intent_guidance = {
        "provide_info": "用户正在提供信息，确认收到并决定下一步",
        "ask_question": "用户在提问，需要回答问题",
        "request_plan": "用户请求配餐方案",
        "adjust_plan": "用户想调整已有方案",
        "chat": "用户在闲聊，保持友好并引导回正题",
        "complaint": "用户有不满，需要理解并妥善处理",
    }

    return Task(
        description=f"""
生成自然的对话回复。

## 用户画像
{profile_summary}

## 对话历史
{history_str if history_str else "(新对话)"}

## 当前阶段
{current_phase}

## 意图分析
- 意图: {intent_result.intent}
- 置信度: {intent_result.confidence}
- 提取的信息: 档案={intent_result.profile_updates}, 偏好={intent_result.preference_updates}

## 指导
{intent_guidance.get(intent_result.intent, "")}

## 要求
1. 回复要自然、友好、专业
2. 如果信息不足，自然地询问缺失的信息（不要一次问太多）
3. 如果用户提问，简洁明了地回答
4. 避免机械的模板式回复
5. 每次只问 1-2 个问题，不要列出一堆
6. 控制回复长度，不要过于冗长

## 输出
- assistant_message: 回复内容
- needs_clarification: 是否需要澄清
- clarification_questions: 需要澄清的问题列表
- suggested_phase: 建议的下一阶段
- should_generate_plan: 是否应该生成方案
""",
        expected_output="ConversationResult 结构化输出",
        agent=agent,
        output_pydantic=ConversationResult,
    )


def create_explanation_task(
    agent: Agent,
    meal_plan: dict,
    target_ranges: dict,
    user_goal: str,
) -> Task:
    """创建方案解读任务"""
    return Task(
        description=f"""
解读配餐方案，帮助用户理解为什么这样配餐。

## 用户目标
{user_goal}

## 营养目标范围
- 热量: {target_ranges.get('calories_min', 0)}-{target_ranges.get('calories_max', 0)} kcal
- 蛋白质: {target_ranges.get('protein_min', 0)}-{target_ranges.get('protein_max', 0)} g

## 配餐方案
{meal_plan}

## 任务
1. 解释方案的整体思路
2. 说明为什么选择这些菜品
3. 分析营养结构如何支持用户目标
4. 指出方案的亮点

## 要求
- 用通俗易懂的语言
- 突出 2-3 个关键点即可，不要面面俱到
- 如果有预算考虑，也要提及
""",
        expected_output="方案解读文本",
        agent=agent,
    )


class ConversationCrew:
    """对话生成 Crew"""

    def __init__(self):
        self.nutritionist = create_nutritionist_agent()
        self.explainer = create_explainer_agent()

    def run(
        self,
        intent_result: IntentResult,
        recent_messages: list[dict],
        profile_summary: str,
        current_phase: str,
    ) -> ConversationResult:
        """
        执行对话生成。

        Args:
            intent_result: 意图分析结果
            recent_messages: 最近对话历史
            profile_summary: 用户画像摘要
            current_phase: 当前阶段

        Returns:
            ConversationResult
        """
        task = create_conversation_task(
            agent=self.nutritionist,
            intent_result=intent_result,
            recent_messages=recent_messages,
            profile_summary=profile_summary,
            current_phase=current_phase,
        )

        crew = Crew(
            agents=[self.nutritionist],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        # 获取结构化输出
        if hasattr(result, 'pydantic') and result.pydantic:
            return result.pydantic

        if task.output and task.output.pydantic:
            return task.output.pydantic

        # 默认回复
        return ConversationResult(
            assistant_message="抱歉，我需要再确认一下你的需求。",
            suggested_phase=current_phase,
        )

    def explain_plan(
        self,
        meal_plan: dict,
        target_ranges: dict,
        user_goal: str,
    ) -> str:
        """
        生成方案解读。

        Args:
            meal_plan: 配餐方案
            target_ranges: 营养目标范围
            user_goal: 用户目标

        Returns:
            解读文本
        """
        task = create_explanation_task(
            agent=self.explainer,
            meal_plan=meal_plan,
            target_ranges=target_ranges,
            user_goal=user_goal,
        )

        crew = Crew(
            agents=[self.explainer],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()
        return result.raw if hasattr(result, 'raw') else str(result)
