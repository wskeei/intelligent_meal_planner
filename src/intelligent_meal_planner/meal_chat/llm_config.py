# src/intelligent_meal_planner/meal_chat/llm_config.py
import os
from functools import lru_cache

from crewai import LLM


@lru_cache
def get_deepseek_llm(temperature: float = 0.7) -> LLM:
    """
    获取配置好的 DeepSeek LLM 实例。

    使用 lru_cache 确保同一温度配置只创建一个实例。

    Args:
        temperature: 生成温度，对话建议 0.7，信息提取建议 0.0

    Returns:
        CrewAI LLM 实例
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "DEEPSEEK_API_KEY 环境变量未设置。"
            "请在 .env 文件中配置: DEEPSEEK_API_KEY=sk-xxx"
        )

    return LLM(
        model="openai/deepseek-v4-flash",
        base_url=os.getenv(
            "DEEPSEEK_API_BASE",
            "https://api.deepseek.com/v1",
        ),
        api_key=api_key,
        temperature=temperature,
    )


def get_extraction_llm() -> LLM:
    """获取用于信息提取的 LLM（低温度，更确定）"""
    return get_deepseek_llm(temperature=0.0)


def get_conversation_llm() -> LLM:
    """获取用于对话生成的 LLM（中等温度，更自然）"""
    return get_deepseek_llm(temperature=0.7)


def get_planning_llm() -> LLM:
    """获取用于规划任务的 LLM（低温度，更精确）"""
    return get_deepseek_llm(temperature=0.3)
