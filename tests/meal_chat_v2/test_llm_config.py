# tests/meal_chat_v2/test_llm_config.py
import os
import pytest
from unittest.mock import patch

from intelligent_meal_planner.meal_chat.llm_config import (
    get_deepseek_llm,
    get_extraction_llm,
    get_conversation_llm,
)


class TestLLMConfig:
    def test_get_deepseek_llm_requires_api_key(self):
        """测试没有 API Key 时抛出异常"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
                get_deepseek_llm.cache_clear()
                get_deepseek_llm()

    def test_get_deepseek_llm_with_api_key(self):
        """测试有 API Key 时正常创建"""
        with patch.dict(
            os.environ,
            {"DEEPSEEK_API_KEY": "test-key"},
        ):
            get_deepseek_llm.cache_clear()
            llm = get_deepseek_llm()
            assert llm is not None
            # 验证模型配置
            assert "deepseek" in llm.model.lower()

    def test_get_extraction_llm_temperature(self):
        """测试提取 LLM 的温度为 0"""
        with patch.dict(
            os.environ,
            {"DEEPSEEK_API_KEY": "test-key"},
        ):
            get_deepseek_llm.cache_clear()
            llm = get_extraction_llm()
            assert llm.temperature == 0.0

    def test_get_conversation_llm_temperature(self):
        """测试对话 LLM 的温度为 0.7"""
        with patch.dict(
            os.environ,
            {"DEEPSEEK_API_KEY": "test-key"},
        ):
            get_deepseek_llm.cache_clear()
            llm = get_conversation_llm()
            assert llm.temperature == 0.7

    def test_llm_caching(self):
        """测试 LLM 实例缓存"""
        with patch.dict(
            os.environ,
            {"DEEPSEEK_API_KEY": "test-key"},
        ):
            get_deepseek_llm.cache_clear()
            llm1 = get_deepseek_llm(temperature=0.5)
            llm2 = get_deepseek_llm(temperature=0.5)
            # 相同温度应返回同一实例
            assert llm1 is llm2
