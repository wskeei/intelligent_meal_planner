# src/intelligent_meal_planner/meal_chat/crews/memory_crew.py
"""MemoryUpdateCrew - 认知文件更新 Crew"""

from crewai import Agent, Crew, Task, Process

from ..llm_config import get_extraction_llm
from ..models.memory import MemoryUpdateResult
from ..models.intent import IntentResult
from ..profile.manager import UserProfileManager
from ..profile.schema import FeedbackRecord
from datetime import date


def create_memory_evaluator_agent() -> Agent:
    """创建记忆评估员 Agent"""
    return Agent(
        role="记忆评估员",
        goal="判断对话中是否有值得长期记住的信息",
        backstory=(
            "你负责评估用户消息的价值。"
            "只有明确、有价值的信息才应该被记录到用户认知文件中。"
            "例如：明确的口味偏好、对某道菜的反馈、纠正之前的信息等。"
            "普通闲聊或临时问题不需要记录。"
        ),
        llm=get_extraction_llm(),
        verbose=True,
    )


def create_archivist_agent() -> Agent:
    """创建档案管理员 Agent"""
    return Agent(
        role="档案管理员",
        goal="将评估通过的信息更新到用户认知文件",
        backstory="你负责精确地更新用户档案，确保数据的准确性和一致性。",
        llm=get_extraction_llm(),
        verbose=True,
    )


def create_evaluation_task(
    agent: Agent,
    user_message: str,
    assistant_message: str,
    intent_result: IntentResult,
    current_profile_summary: str,
) -> Task:
    """创建记忆评估任务"""
    return Task(
        description=f"""
评估对话是否包含值得记录的信息。

## 用户消息
{user_message}

## 助手回复
{assistant_message}

## 意图分析
- 意图: {intent_result.intent}
- 提取的信息: {intent_result.profile_updates}, {intent_result.preference_updates}

## 用户当前画像
{current_profile_summary}

## 判断标准
应该记录的情况：
1. 用户明确表达口味偏好（如"我喜欢清淡的"）
2. 用户明确表达不喜欢某种食物（如"我不吃香菜"）
3. 用户纠正之前的信息（如"我其实是减脂不是增肌"）
4. 用户对方案给出明确反馈（如"这道菜太辣了"）
5. 用户表达饮食行为模式（如"我经常点外卖"）

不应记录的情况：
1. 普通闲聊
2. 临时性问题（如"今天吃什么"）
3. 信息已经存在于画像中
4. 模糊或不确定的表达

## 任务
判断是否需要更新，以及更新什么内容。
""",
        expected_output="评估结果，包含 should_update, update_reason, 和建议的更新内容",
        agent=agent,
    )


def create_update_task(
    agent: Agent,
    evaluation_result: str,
) -> Task:
    """创建更新任务"""
    return Task(
        description=f"""
根据评估结果生成具体的更新内容。

## 评估结果
{evaluation_result}

## 输出格式
生成 MemoryUpdateResult，包含：
- should_update: 是否更新
- update_reason: 更新原因
- profile_updates: 档案更新内容
- preference_updates: 偏好更新内容
- taste_profile_updates: 口味画像更新内容
- feedback_to_add: 反馈记录（如果有）
- confidence: 对更新内容的置信度
""",
        expected_output="MemoryUpdateResult 结构化输出",
        agent=agent,
        output_pydantic=MemoryUpdateResult,
    )


class MemoryUpdateCrew:
    """认知文件更新 Crew"""

    def __init__(self, profile_manager: UserProfileManager | None = None):
        self.evaluator = create_memory_evaluator_agent()
        self.archivist = create_archivist_agent()
        self.profile_manager = profile_manager or UserProfileManager()

    def run(
        self,
        user_id: str,
        user_message: str,
        assistant_message: str,
        intent_result: IntentResult,
    ) -> MemoryUpdateResult:
        """
        执行记忆更新评估。

        Args:
            user_id: 用户 ID
            user_message: 用户消息
            assistant_message: 助手回复
            intent_result: 意图分析结果

        Returns:
            MemoryUpdateResult
        """
        # 获取当前用户画像
        profile = self.profile_manager.get_profile(user_id)
        profile_summary = profile.get_summary_for_context()

        # 评估任务
        eval_task = create_evaluation_task(
            agent=self.evaluator,
            user_message=user_message,
            assistant_message=assistant_message,
            intent_result=intent_result,
            current_profile_summary=profile_summary,
        )

        # 执行 Crew
        crew = Crew(
            agents=[self.evaluator],
            tasks=[eval_task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        # 解析结果
        update_result = self._parse_result(result)

        # 如果需要更新，执行更新
        if update_result.should_update:
            self._apply_update(user_id, update_result)

        return update_result

    def _parse_result(self, result) -> MemoryUpdateResult:
        """解析 Crew 结果"""
        if hasattr(result, 'pydantic') and result.pydantic:
            return result.pydantic

        # 默认不更新
        return MemoryUpdateResult(should_update=False)

    def _apply_update(
        self,
        user_id: str,
        update_result: MemoryUpdateResult,
    ) -> None:
        """应用更新到用户认知文件"""
        feedback = None
        if update_result.feedback_to_add:
            feedback = FeedbackRecord(
                feedback_date=date.today(),
                **update_result.feedback_to_add,
            )

        self.profile_manager.update_profile(
            user_id=user_id,
            profile_updates=update_result.profile_updates or None,
            preference_updates=update_result.preference_updates or None,
            taste_profile_updates=update_result.taste_profile_updates or None,
            feedback=feedback,
        )
