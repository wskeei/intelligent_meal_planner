from __future__ import annotations

from .session_schema import ConversationMemory


class MealChatOrchestrator:
    def __init__(self, runtime, planner):
        self.runtime = runtime
        self.planner = planner

    def advance(self, user, session, user_message: str):
        del user
        memory = ConversationMemory.model_validate(session.collected_slots or {})
        result = self.runtime.run_turn(user_message=user_message, memory=memory)

        session.collected_slots = result.memory.model_dump(mode="json")
        session.status = result.phase
        if result.meal_plan is not None:
            session.final_plan = result.meal_plan

        return {
            "status": result.phase,
            "assistant_message": result.assistant_message,
            "hidden_targets": None,
            "meal_plan": result.meal_plan,
            "trace": {
                "phase": result.phase,
                "memory": result.memory.model_dump(mode="json"),
                "negotiation_options": [
                    option.model_dump(mode="json")
                    for option in result.negotiation_options
                ],
            },
        }
