from __future__ import annotations

from crewai import Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM

from .crew_models import CrewBundle
from .crew_tools import build_dqn_planning_tool


class PlaceholderCrewLLM(BaseLLM):
    def __init__(self):
        super().__init__(model="placeholder-crewai-model")

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
        del messages
        del tools
        del callbacks
        del available_functions
        del from_task
        del from_agent
        if response_model is not None:
            return response_model.model_validate(
                {
                    "final_message": "多智能体协作已完成，我给你整理好了方案。",
                    "meal_plan": {},
                    "events": [],
                }
            )
        return "多智能体协作已完成。"


def build_meal_planning_crew(planning_tool) -> CrewBundle:
    dqn_tool = build_dqn_planning_tool(planning_tool)
    llm = PlaceholderCrewLLM()

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
        ),
        Task(
            description="根据用户画像与目标，整理营养策略与建议目标范围。",
            expected_output="营养策略摘要。",
            agent=nutrition_agent,
        ),
        Task(
            description="判断预算是否支持目标，并给出预算协同意见。",
            expected_output="预算分析摘要。",
            agent=budget_agent,
        ),
        Task(
            description="使用 DQN 配餐工具生成最终结构化配餐结果。",
            expected_output="结构化 meal_plan。",
            agent=dqn_agent,
            tools=[dqn_tool] if dqn_tool is not None else [],
        ),
        Task(
            description="汇总协作结论，向用户解释方案为何成立以及如何执行。",
            expected_output="最终用户说明。",
            agent=explanation_agent,
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
        event_messages={
            "需求审查专员": "已确认用户需求",
            "营养规划师": "已整理营养策略",
            "预算协调员": "已完成预算协调",
            "DQN 配餐师": "已调用 DQN 生成方案",
            "结果解读员": "已汇总最终说明",
        },
    )
