from __future__ import annotations

from .feasibility_negotiator import build_negotiation_result
from .session_schema import ConversationMemory, TargetRanges
from .target_ranges import build_target_ranges
from .types import CrewTurnResult


class CrewMealChatRuntime:
    def __init__(self, planning_tool):
        self.planning_tool = planning_tool

    def run_turn(self, user_message: str, memory: ConversationMemory) -> CrewTurnResult:
        intent = self.intent_agent(user_message=user_message, memory=memory)
        profile_delta = self.profile_agent(
            user_message=user_message,
            memory=memory,
            intent=intent,
        )
        merged_memory = self._merge_memory(memory, profile_delta)

        strategy = self.strategy_agent(memory=merged_memory)
        if strategy.get("target_ranges"):
            merged_memory.target_ranges = TargetRanges.model_validate(
                strategy["target_ranges"]
            )

        negotiation = self.negotiator_agent(
            user_message=user_message,
            memory=merged_memory,
            intent=intent,
        )
        merged_memory.phase = negotiation["phase"]
        merged_memory.negotiation_options = negotiation.get("options", [])

        if not intent.get("needs_plan"):
            return CrewTurnResult(
                phase=merged_memory.phase,
                assistant_message=negotiation["assistant_message"],
                memory=merged_memory,
                negotiation_options=merged_memory.negotiation_options,
            )

        plan = self.planning_agent(memory=merged_memory, user_message=user_message)
        return CrewTurnResult(
            phase=plan["phase"],
            assistant_message=plan["assistant_message"],
            memory=merged_memory,
            negotiation_options=merged_memory.negotiation_options,
            meal_plan=plan["meal_plan"],
        )

    def intent_agent(self, user_message: str, memory: ConversationMemory) -> dict:
        text = user_message.lower()
        asks_budget = "预算" in user_message and any(
            token in user_message for token in ("多少", "最低", "至少", "?")
        )
        needs_plan = any(
            token in text
            for token in ("方案", "计划", "meal plan", "plan")
        )
        if asks_budget:
            return {"intent": "budget_question", "needs_plan": False}
        if needs_plan or memory.phase == "planning":
            return {"intent": "plan_request", "needs_plan": True}
        return {"intent": "general_chat", "needs_plan": False}

    def profile_agent(
        self, user_message: str, memory: ConversationMemory, intent: dict
    ) -> dict:
        return {
            "profile_updates": {},
            "preference_updates": {},
        }

    def strategy_agent(self, memory: ConversationMemory) -> dict:
        profile = memory.profile
        goal = memory.preferences.get("health_goal", "healthy")
        if not profile:
            return {"target_ranges": memory.target_ranges}
        return {
            "target_ranges": build_target_ranges(profile=profile, goal=goal),
        }

    def negotiator_agent(
        self, user_message: str, memory: ConversationMemory, intent: dict
    ) -> dict:
        budget = memory.preferences.get("budget")
        if budget is None or memory.target_ranges is None:
            return {
                "phase": memory.phase,
                "assistant_message": "我还需要你的预算和目标信息，才能继续判断。",
                "options": [],
            }

        negotiation = build_negotiation_result(
            budget=float(budget),
            target_ranges=memory.target_ranges,
        )
        return {
            "phase": negotiation.phase,
            "assistant_message": negotiation.explanation,
            "options": negotiation.options,
        }

    def planning_agent(self, memory: ConversationMemory, user_message: str) -> dict:
        if self.planning_tool is None:
            return {
                "phase": "planning",
                "assistant_message": "我已经准备好开始配餐。",
                "meal_plan": None,
            }
        return {
            "phase": "finalized",
            "assistant_message": "我给你整理好了一份方案。",
            "meal_plan": self.planning_tool.generate(),
        }

    def _merge_memory(self, memory: ConversationMemory, profile_delta: dict) -> ConversationMemory:
        merged = memory.model_copy(deep=True)
        merged.profile.update(profile_delta.get("profile_updates", {}))
        merged.preferences.update(profile_delta.get("preference_updates", {}))
        return merged
