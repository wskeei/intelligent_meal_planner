from __future__ import annotations

from .session_schema import ConversationMemory


class MealChatOrchestrator:
    def __init__(self, intake_runtime, crew_runner):
        self.intake_runtime = intake_runtime
        self.crew_runner = crew_runner

    def advance(self, user, session, user_message: str):
        memory = ConversationMemory.model_validate(session.collected_slots or {})
        intake_result = self.intake_runtime.run_turn(
            user_message=user_message,
            memory=memory,
        )

        if not intake_result.ready_for_crew:
            session.collected_slots = intake_result.memory.model_dump(mode="json")
            session.status = intake_result.phase
            return {
                "status": intake_result.phase,
                "assistant_message": intake_result.assistant_message,
                "hidden_targets": None,
                "meal_plan": None,
                "trace": {
                    "phase": intake_result.phase,
                    "memory": intake_result.memory.model_dump(mode="json"),
                    "crew_trace": intake_result.memory.crew_events,
                    "open_questions": intake_result.memory.open_questions,
                    "known_facts": intake_result.memory.known_facts,
                },
            }

        final_result = self.crew_runner.run(memory=intake_result.memory, user=user)
        intake_result.memory.phase = final_result["phase"]
        intake_result.memory.crew_events = list(final_result.get("events", []))
        intake_result.memory.crew_summary = {
            "assistant_message": final_result["assistant_message"],
            "phase": final_result["phase"],
        }
        session.collected_slots = intake_result.memory.model_dump(mode="json")
        session.status = final_result["phase"]
        if final_result["meal_plan"] is not None:
            session.final_plan = final_result["meal_plan"]

        return {
            "status": final_result["phase"],
            "assistant_message": final_result["assistant_message"],
            "hidden_targets": None,
            "meal_plan": final_result["meal_plan"],
            "trace": {
                "phase": final_result["phase"],
                "memory": intake_result.memory.model_dump(mode="json"),
                "crew_trace": final_result.get("events", []),
                "open_questions": intake_result.memory.open_questions,
                "known_facts": intake_result.memory.known_facts,
            },
        }
