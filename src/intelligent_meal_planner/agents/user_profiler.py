"""
用户需求分析师 Agent

负责与用户对话，收集配餐需求，输出结构化的 JSON 报告
"""

from crewai import Agent


class UserProfilerAgent:
    """用户需求分析师 - 收集和分析用户的配餐需求"""
    
    @staticmethod
    def create(llm=None) -> Agent:
        """
        创建用户需求分析师 Agent
        
        Args:
            llm: 语言模型实例（可选）
        
        Returns:
            配置好的 Agent 实例
        """
        return Agent(
            role="用户需求分析师",
            goal="全面理解用户的饮食需求，包括健康目标、预算、口味偏好和忌口，并整理成结构化报告",
            backstory="""你是一位经验丰富的营养咨询师，擅长通过对话了解用户的真实需求。
你善于引导用户表达他们的健康目标（如减脂、增肌、维持体重），
了解他们的预算限制，以及任何饮食禁忌或偏好。
你的任务是将这些信息整理成一份清晰的 JSON 格式报告，供配餐师使用。""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )