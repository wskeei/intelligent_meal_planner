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
        goal="引导用户提供饮食需求信息，当信息齐全后明确告知可以生成配餐方案",
        backstory=(
            "你是一位经验丰富的营养师，你的核心任务有两个：\n"
            "1. 通过自然对话收集用户的个人信息（性别、年龄、身高、体重、活动量）和饮食偏好（健康目标、预算）\n"
            "2. 当所有必要信息齐全后，明确告知用户可以生成个性化配餐方案\n"
            "你的风格是：专业但不死板，友好但不敷衍。"
            "你会像朋友聊天一样自然地引导用户提供信息，而不是机械地逐项询问。"
            "每次只问 1-2 个问题，让对话流畅自然。"
            "当信息齐全时，你会总结已收集的信息，并清晰地引导用户进入下一步。"
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
    missing_fields: list[str] | None = None,
    info_complete: bool = False,
    today_requirements: dict | None = None,
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

    # 构建缺失字段指导
    missing_fields = missing_fields or []
    today_requirements = today_requirements or {}

    # 从当前消息中提取到的信息（明确告知 agent）
    just_extracted_profile = intent_result.profile_updates or {}
    just_extracted_prefs = intent_result.preference_updates or {}
    just_extracted = {**just_extracted_profile, **just_extracted_prefs}

    field_labels = {
        "gender": "性别", "age": "年龄", "height_cm": "身高",
        "weight_kg": "体重", "activity_level": "活动量",
        "health_goal": "健康目标", "budget": "预算",
        "disliked_foods": "忌口", "mood": "今日状态",
        "specific_requests": "今日要求", "avoid_today": "今日忌口",
    }

    if just_extracted:
        extracted_items = []
        for k, v in just_extracted.items():
            label = field_labels.get(k, k)
            extracted_items.append(f"{label}={v}")
        just_extracted_str = "、".join(extracted_items)
    else:
        just_extracted_str = "无"

    if missing_fields:
        missing_str = "、".join(missing_fields)
        collection_guidance = f"""
## 当前阶段：收集基础信息
**当前消息提取到的信息**: {just_extracted_str}
**还需要收集的信息**: {missing_str}

### 重要规则
1. 如果当前消息提取到了新信息（见上方"当前消息提取到的信息"），**必须先确认收到**，再问下一个问题
2. **绝对不要重复询问用户已经提供的信息**（包括用户画像中已有的信息和本次提取到的信息）
3. 每次只问 1-2 个缺失信息
4. 优先询问顺序：性别 → 年龄 → 身高体重 → 活动量 → 健康目标 → 预算
5. 如果提取到了信息但还有缺失，确认后自然地问下一个缺失项

### 回复模式
- 如果提取到了信息："好的，[确认信息]。[然后问下一个缺失项]"
- 如果没有提取到信息且用户说的是其他内容：先回应用户，再引导回缺失信息
"""
        plan_guidance = """
### 生成方案指导
基础信息尚未齐全，**不要**将 should_generate_plan 设置为 true。
继续收集缺失信息，直到所有必填字段都已获取。
"""
    elif not today_requirements:
        collection_guidance = """
## 当前阶段：了解今天的配餐需求
用户的基础信息已经齐全（性别、年龄、身高、体重、活动量、健康目标、预算）。
**现在你需要了解用户今天对配餐的具体想法和要求。**

### 今天需要了解的内容
- 今天的状态/心情（不太饿、很饿、精力不足等）
- 今天想吃什么类型的食物（清淡、重口味、特定菜系等）
- 今天有没有特别想吃或不想吃的东西
- 今天有没有时间限制（赶时间、可以慢慢做等）
- 今天有没有特殊场合（聚餐、加班、运动后等）

### 提问方式
自然地询问，例如：
- "你今天感觉怎么样？有什么特别想吃的吗？"
- "今天有没有什么特别想吃或者不想吃的东西？"
- "今天的用餐有什么特别的要求吗？"

**注意：不要一次问完所有问题，根据用户的回复自然跟进。**
"""
        plan_guidance = """
### 生成方案指导
正在了解用户今天的具体需求，**不要**将 should_generate_plan 设置为 true。
先了解用户今天的想法和要求，再生成方案。
"""
    else:
        today_str = "、".join(f"{k}={v}" for k, v in today_requirements.items() if v)
        collection_guidance = f"""
## 当前阶段：准备生成方案
用户的基础信息和今天的需求已了解。
**今天的需求**: {today_str}
"""
        plan_guidance = """
### 生成方案指导
信息已齐全，你应该：
1. 简要总结用户今天的需求
2. 明确告知用户"我了解了，这就为你生成今天的配餐方案"
3. **必须将 should_generate_plan 设置为 true**
"""

    return Task(
        description=f"""
你是一位专业营养师，正在与用户对话以了解其饮食需求，最终为用户生成个性化配餐方案。

## 用户已提供的信息
{profile_summary}

## 当前消息新提取到的信息
{just_extracted_str}

## 还需要收集的信息
{"、".join(missing_fields) if missing_fields else "无（信息齐全）"}

## 对话历史
{history_str if history_str else "(新对话)"}

## 当前阶段
{current_phase}

## 当前意图
{intent_result.intent}（置信度: {intent_result.confidence}）
{intent_guidance.get(intent_result.intent, "")}

## 对话指导
{intent_guidance.get(intent_result.intent, "")}
{collection_guidance}
{plan_guidance}

## 今日需求
{f"已了解的今日需求: {today_requirements}" if today_requirements else "尚未了解今日具体需求"}

## 回复要求
1. 回复要自然、友好、专业，像朋友聊天
2. 根据信息收集状态，主动引导用户提供缺失信息
3. 如果用户提问，简洁明了地回答
4. 避免机械的模板式回复
5. 每次只问 1-2 个问题
6. 控制回复长度，简洁有力
7. 如果信息齐全，明确告知用户可以生成方案，并将 should_generate_plan 设为 true

## 输出
- assistant_message: 回复内容
- needs_clarification: 是否需要澄清
- clarification_questions: 需要澄清的问题列表
- suggested_phase: 建议的下一阶段
- should_generate_plan: 是否应该生成方案（仅当所有必填信息齐全时设为 true）
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
        missing_fields: list[str] | None = None,
        info_complete: bool = False,
        today_requirements: dict | None = None,
    ) -> ConversationResult:
        """
        执行对话生成。

        Args:
            intent_result: 意图分析结果
            recent_messages: 最近对话历史
            profile_summary: 用户画像摘要
            current_phase: 当前阶段
            missing_fields: 尚未收集的必填字段列表
            info_complete: 所有必填信息是否已齐全
            today_requirements: 本次配餐的具体需求

        Returns:
            ConversationResult
        """
        task = create_conversation_task(
            agent=self.nutritionist,
            intent_result=intent_result,
            recent_messages=recent_messages,
            profile_summary=profile_summary,
            current_phase=current_phase,
            missing_fields=missing_fields,
            info_complete=info_complete,
            today_requirements=today_requirements,
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
