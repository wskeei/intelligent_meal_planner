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

        session.collected_slots = intake_result.memory.model_dump(mode="json")
        session.status = intake_result.phase

        if intake_result.ready_for_crew:
            return self._build_response(
                memory=intake_result.memory,
                status="planning_ready",
                assistant_message=intake_result.assistant_message,
                meal_plan=None,
            )

        return self._build_response(
            memory=intake_result.memory,
            status=intake_result.phase,
            assistant_message=intake_result.assistant_message,
            meal_plan=None,
        )

    def generate(self, user, session):
        memory = ConversationMemory.model_validate(session.collected_slots or {})
        final_result = self.crew_runner.run(memory=memory, user=user)

        memory.phase = final_result["phase"]
        memory.crew_events = list(final_result.get("events", []))
        memory.crew_summary = {
            "assistant_message": final_result["assistant_message"],
            "phase": final_result["phase"],
        }

        session.collected_slots = memory.model_dump(mode="json")
        session.status = final_result["phase"]
        if final_result["meal_plan"] is not None:
            session.final_plan = final_result["meal_plan"]

        return self._build_response(
            memory=memory,
            status=final_result["phase"],
            assistant_message=final_result["assistant_message"],
            meal_plan=final_result["meal_plan"],
        )

    def _build_response(self, memory, status: str, assistant_message: str, meal_plan):
        return {
            "status": status,
            "assistant_message": assistant_message,
            "hidden_targets": None,
            "meal_plan": meal_plan,
            "presentation": {
                "phase": memory.phase,
                "overlay_state": memory.overlay_state,
            },
            "trace": {
                "phase": status,
                "memory": memory.model_dump(mode="json"),
                "crew_trace": memory.crew_events,
                "open_questions": memory.open_questions,
                "known_facts": memory.known_facts,
            },
        }
