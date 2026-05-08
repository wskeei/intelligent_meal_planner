# src/intelligent_meal_planner/meal_chat/flow.py
"""MealChatFlow - 对话流程编排"""

from crewai.flow.flow import Flow, listen, start

from .state import ConversationState
from .models.intent import IntentResult
from .models.conversation import ConversationResult
from .models.planning import PlanningResult
from .models.memory import MemoryUpdateResult
from .crews.intent_crew import IntentCrew
from .crews.conversation_crew import ConversationCrew
from .crews.planning_crew import PlanningCrew
from .crews.memory_crew import MemoryUpdateCrew
from .profile.manager import UserProfileManager


class MealChatFlow(Flow[ConversationState]):
    """主对话流程"""

    def __init__(
        self,
        profile_manager: UserProfileManager | None = None,
    ):
        super().__init__()
        self.profile_manager = profile_manager or UserProfileManager()
        self.intent_crew = IntentCrew()
        self.conversation_crew = ConversationCrew()
        self.planning_crew = PlanningCrew()
        self.memory_crew = MemoryUpdateCrew(profile_manager=self.profile_manager)

    @start()
    def receive_message(self) -> IntentResult:
        """接收用户消息，进行意图理解"""
        # Get user message from inputs (passed via kickoff)
        user_message = getattr(self.state, 'user_message', '')
        user_id = getattr(self.state, 'user_id', 'default-user')
        session_id = getattr(self.state, 'session_id', 'default-session')

        # 记录用户消息
        self.state.add_message("user", user_message)

        # 获取用户画像摘要
        user_profile = self.profile_manager.get_profile(user_id)
        profile_summary = user_profile.get_summary_for_context()

        # 获取对话上下文
        recent_messages = self.state.get_context_for_llm()

        # 执行意图理解
        intent_result = self.intent_crew.run(
            user_message=user_message,
            recent_messages=recent_messages,
            profile_summary=profile_summary,
            expected_slot=self._get_expected_slot(),
        )

        # 更新状态
        self.state.last_intent = intent_result.intent
        self.state.last_confidence = intent_result.confidence
        self.state.merge_updates(
            intent_result.profile_updates,
            intent_result.preference_updates,
        )

        return intent_result

    @listen(receive_message)
    def generate_response(self, intent_result: IntentResult) -> ConversationResult:
        """生成对话回复"""
        user_id = getattr(self.state, 'user_id', 'default-user')

        # 获取用户画像摘要
        user_profile = self.profile_manager.get_profile(user_id)
        profile_summary = user_profile.get_summary_for_context()

        # 获取对话上下文
        recent_messages = self.state.get_context_for_llm()

        # 检查是否需要生成方案
        should_plan = (
            intent_result.intent == "request_plan"
            or intent_result.ready_for_planning
            or self.state.is_ready_for_planning()
        )

        # 如果需要生成方案
        if should_plan and self.state.current_meal_plan is None:
            planning_result = self._generate_plan()
            self.state.current_meal_plan = planning_result.meal_plan

            # 存储元数据用于构建 API 响应
            self.state.current_meal_plan_metadata = {
                "total_cost": planning_result.total_cost,
                "total_calories": planning_result.total_calories,
                "total_protein": planning_result.total_protein,
                "total_carbs": planning_result.total_carbs,
                "total_fat": planning_result.total_fat,
                "calories_achievement": planning_result.calories_achievement,
                "protein_achievement": planning_result.protein_achievement,
                "budget_usage": planning_result.budget_usage,
                "status": planning_result.status,
                "highlights": planning_result.highlights,
            }

            # 使用方案生成带解读的回复
            conversation_result = self.conversation_crew.run(
                intent_result=intent_result,
                recent_messages=recent_messages,
                profile_summary=profile_summary,
                current_phase="planning",
            )

            # 添加方案解读
            conversation_result.assistant_message = self._build_plan_response(
                planning_result,
                conversation_result.assistant_message,
            )
            conversation_result.should_generate_plan = True
            self.state.current_phase = "explaining"
        else:
            # 普通对话
            conversation_result = self.conversation_crew.run(
                intent_result=intent_result,
                recent_messages=recent_messages,
                profile_summary=profile_summary,
                current_phase=self.state.current_phase,
            )

            # 检查阶段转换
            if conversation_result.should_generate_plan:
                self.state.current_phase = "planning_ready"

        # 记录助手回复
        self.state.add_message("assistant", conversation_result.assistant_message)

        return conversation_result

    @listen(generate_response)
    def update_memory(self, conversation_result: ConversationResult) -> MemoryUpdateResult:
        """更新用户认知文件"""
        user_id = getattr(self.state, 'user_id', 'default-user')

        # 获取最后一条用户消息
        if not self.state.recent_messages:
            return MemoryUpdateResult(should_update=False)

        # 找到最近一条用户消息
        user_message = ""
        for msg in reversed(self.state.recent_messages):
            if msg.role == "user":
                user_message = msg.content
                break

        # 创建意图结果（简化版）
        intent_result = IntentResult(
            intent=self.state.last_intent,
            confidence=self.state.last_confidence,
            profile_updates=self.state.collected_profile,
            preference_updates=self.state.collected_preferences,
        )

        # 执行记忆更新评估
        memory_result = self.memory_crew.run(
            user_id=user_id,
            user_message=user_message,
            assistant_message=conversation_result.assistant_message,
            intent_result=intent_result,
        )

        return memory_result

    def _get_expected_slot(self) -> str | None:
        """获取预期的信息字段"""
        # 根据当前状态判断用户可能在回答什么
        if not self.state.collected_profile.get("height_cm"):
            return "height_weight"
        if not self.state.collected_preferences.get("health_goal"):
            return "health_goal"
        if not self.state.collected_preferences.get("budget"):
            return "budget"
        return None

    def _generate_plan(self) -> PlanningResult:
        """生成配餐方案"""
        return self.planning_crew.run(
            profile=self.state.collected_profile,
            preferences=self.state.collected_preferences,
        )

    def _build_plan_response(
        self,
        planning_result: PlanningResult,
        base_message: str,
    ) -> str:
        """构建方案回复"""
        if planning_result.status == "budget_infeasible":
            return planning_result.explanation

        # 获取助手的基础回复
        explanation = self.conversation_crew.explain_plan(
            meal_plan=planning_result.meal_plan,
            target_ranges=planning_result.target_ranges,
            user_goal=self.state.collected_preferences.get("health_goal", "healthy"),
        )

        return explanation


def create_meal_chat_flow(
    user_id: str,
    session_id: str,
    profile_manager: UserProfileManager | None = None,
) -> MealChatFlow:
    """创建对话流程实例"""
    flow = MealChatFlow(profile_manager=profile_manager)

    # Set initial state values via inputs
    flow.state.user_id = user_id
    flow.state.session_id = session_id

    return flow
