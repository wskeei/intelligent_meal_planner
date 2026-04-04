from __future__ import annotations

import json

from crewai import Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM

from .crew_models import (
    BudgetCoordination,
    CrewBundle,
    CrewEvent,
    CrewPlanningResult,
    DQNMealPlanArtifact,
    NutritionStrategy,
    RequirementReview,
)
from .crew_tools import build_dqn_planning_tool


class StructuredCrewRuntimeLLM(BaseLLM):
    def __init__(self, planning_tool=None):
        super().__init__(model="structured-crewai-runtime")
        self.planning_tool = planning_tool
        self.prepare({})

    def prepare(self, inputs: dict) -> None:
        self.inputs = dict(inputs)
        self.events: list[CrewEvent] = []
        self.task_outputs: dict[str, dict] = {}

    def call(
        self,
        messages,
        tools=None,
        callbacks=None,
        available_functions=None,
        from_task=None,
        from_agent=None,
        response_model=None,
    ):
        del tools
        del callbacks
        del available_functions
        del messages

        agent_role = getattr(from_agent, "role", None) or getattr(
            getattr(from_task, "agent", None), "role", "Agent"
        )
        payload = self._build_payload(agent_role=agent_role)

        if response_model is not None:
            return response_model.model_validate(payload)
        return json.dumps(payload, ensure_ascii=False)

    def _build_payload(self, agent_role: str) -> dict:
        if agent_role == "需求审查专员":
            payload = {
                "summary": self._requirements_summary(),
                "constraints": {
                    "profile": self.inputs.get("profile", {}),
                    "preferences": self.inputs.get("preferences", {}),
                },
            }
            self._record_event(agent_role, payload["summary"], payload["constraints"])
            self.task_outputs[agent_role] = payload
            return payload

        if agent_role == "营养规划师":
            payload = {
                "summary": self._nutrition_summary(),
                "target_ranges": self.inputs.get("hidden_targets", {}),
            }
            self._record_event(agent_role, payload["summary"], payload["target_ranges"])
            self.task_outputs[agent_role] = payload
            return payload

        if agent_role == "预算协调员":
            budget = float(self.inputs.get("budget", 0) or 0)
            payload = {
                "summary": f"预算已锁定在 {budget:.1f} 元，可按该上限规划。",
                "budget": budget,
                "assessment": "feasible" if budget > 0 else "missing_budget",
            }
            self._record_event(
                agent_role,
                payload["summary"],
                {"budget": payload["budget"], "assessment": payload["assessment"]},
            )
            self.task_outputs[agent_role] = payload
            return payload

        if agent_role == "DQN 配餐师":
            payload = self._build_dqn_payload()
            self._record_event(
                agent_role,
                payload["summary"],
                {
                    "tool_name": payload["tool_name"],
                    "meal_plan_id": payload["meal_plan"].get("id"),
                    "total_price": (
                        payload["meal_plan"].get("nutrition", {}) or {}
                    ).get("total_price"),
                },
            )
            self.task_outputs[agent_role] = payload
            return payload

        meal_plan = (
            self.task_outputs.get("DQN 配餐师", {}) or {}
        ).get("meal_plan", {})
        final_message = self._final_message(meal_plan)
        self._record_event(
            agent_role,
            "已汇总协作结果并生成用户说明。",
            {"final_message": final_message},
        )
        payload = {
            "final_message": final_message,
            "meal_plan": meal_plan,
            "events": [event.model_dump(mode="json") for event in self.events],
            "negotiation_summary": self.task_outputs.get("预算协调员"),
        }
        self.task_outputs[agent_role] = payload
        return payload

    def _requirements_summary(self) -> str:
        goal = self.inputs.get("health_goal", "healthy")
        budget = float(self.inputs.get("budget", 0) or 0)
        disliked = self.inputs.get("disliked_foods", [])
        preferred = self.inputs.get("preferred_tags", [])
        return (
            f"已确认目标为 {goal}，预算 {budget:.1f} 元，"
            f"忌口 {disliked or '无'}，偏好 {preferred or '无'}。"
        )

    def _nutrition_summary(self) -> str:
        targets = self.inputs.get("hidden_targets", {})
        return (
            "已整理营养目标，"
            f"热量 {targets.get('target_calories', 0)} kcal，"
            f"蛋白质 {targets.get('target_protein', 0)} g。"
        )

    def _build_dqn_payload(self) -> dict:
        if self.planning_tool is None:
            meal_plan = {}
        else:
            raw = self.planning_tool._run(
                health_goal=self.inputs.get("health_goal", "healthy"),
                budget=float(self.inputs.get("budget", 0) or 0),
                disliked_foods=self.inputs.get("disliked_foods", []),
                preferred_tags=self.inputs.get("preferred_tags", []),
                hidden_targets=self.inputs.get("hidden_targets", {}),
            )
            meal_plan = json.loads(raw)

        plan_id = meal_plan.get("id", "unknown")
        total_price = ((meal_plan.get("nutrition", {}) or {}).get("total_price"))
        summary = f"DQN 工具已生成方案 {plan_id}。"
        if total_price is not None:
            summary = f"{summary} 当前方案总花费 {total_price} 元。"
        return {
            "summary": summary,
            "meal_plan": meal_plan,
            "tool_name": getattr(self.planning_tool, "name", "dqn_meal_planning_tool"),
        }

    def _final_message(self, meal_plan: dict) -> str:
        goal = self.inputs.get("health_goal", "healthy")
        budget = float(self.inputs.get("budget", 0) or 0)
        plan_id = meal_plan.get("id")
        if plan_id:
            return (
                f"多智能体协作已完成。已围绕 {goal} 目标和 {budget:.1f} 元预算生成方案 {plan_id}。"
            )
        return f"多智能体协作已完成。已围绕 {goal} 目标和 {budget:.1f} 元预算整理方案。"

    def _record_event(self, agent: str, message: str, payload: dict | None = None) -> None:
        self.events.append(
            CrewEvent(agent=agent, status="completed", message=message, payload=payload)
        )


def build_meal_planning_crew(planning_tool) -> CrewBundle:
    dqn_tool = build_dqn_planning_tool(planning_tool)
    llm = StructuredCrewRuntimeLLM(planning_tool=dqn_tool)

    requirements_agent = Agent(
        role="需求审查专员",
        goal="核对用户资料是否完整，输出可执行约束。",
        backstory="擅长把自然语言偏好整理成结构化需求。",
        verbose=True,
        llm=llm,
    )
    nutrition_agent = Agent(
        role="营养规划师",
        goal="把用户目标映射到营养范围和执行策略。",
        backstory="专注于增肌、减脂和均衡饮食方案。",
        verbose=True,
        llm=llm,
    )
    budget_agent = Agent(
        role="预算协调员",
        goal="判断预算可行性并提出折中方向。",
        backstory="负责成本与营养目标的冲突协调。",
        verbose=True,
        llm=llm,
    )
    dqn_agent = Agent(
        role="DQN 配餐师",
        goal="调用 DQN 工具生成结构化配餐结果。",
        backstory="负责把营养约束映射为最终菜谱方案。",
        tools=[dqn_tool] if dqn_tool is not None else [],
        verbose=True,
        llm=llm,
    )
    explanation_agent = Agent(
        role="结果解读员",
        goal="向用户解释方案形成原因和执行建议。",
        backstory="负责把多智能体决策过程转成可信解释。",
        verbose=True,
        llm=llm,
    )

    agents = [
        requirements_agent,
        nutrition_agent,
        budget_agent,
        dqn_agent,
        explanation_agent,
    ]

    tasks = [
        Task(
            description="整理用户画像、预算、目标和饮食限制，输出执行约束。",
            expected_output="结构化需求摘要。",
            agent=requirements_agent,
            output_pydantic=RequirementReview,
        ),
        Task(
            description="根据用户画像与目标，整理营养策略与建议目标范围。",
            expected_output="营养策略摘要。",
            agent=nutrition_agent,
            output_pydantic=NutritionStrategy,
        ),
        Task(
            description="判断预算是否支持目标，并给出预算协同意见。",
            expected_output="预算分析摘要。",
            agent=budget_agent,
            output_pydantic=BudgetCoordination,
        ),
        Task(
            description="使用 DQN 配餐工具生成最终结构化配餐结果。",
            expected_output="结构化 meal_plan。",
            agent=dqn_agent,
            tools=[dqn_tool] if dqn_tool is not None else [],
            output_pydantic=DQNMealPlanArtifact,
        ),
        Task(
            description="汇总协作结论，向用户解释方案为何成立以及如何执行。",
            expected_output="包含最终说明、meal_plan 和协作事件的结构化结果。",
            agent=explanation_agent,
            output_pydantic=CrewPlanningResult,
        ),
    ]

    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return CrewBundle(
        crew=crew,
        agents=agents,
        tasks=tasks,
        runtime_llm=llm,
    )
