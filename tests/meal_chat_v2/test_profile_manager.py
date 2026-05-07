# tests/meal_chat_v2/test_profile_manager.py
import json
import pytest
import tempfile
from pathlib import Path
from datetime import date

from intelligent_meal_planner.meal_chat.profile.schema import (
    UserProfile,
    FeedbackRecord,
    GoalHistory,
)
from intelligent_meal_planner.meal_chat.profile.manager import UserProfileManager


class TestUserProfile:
    def test_create_new_profile(self):
        profile = UserProfile(user_id="test-user")
        assert profile.user_id == "test-user"
        assert profile.profile["gender"] is None
        assert profile.preferences["health_goal"] is None

    def test_update_profile(self):
        profile = UserProfile(user_id="test-user")
        profile.update_profile({
            "age": 28,
            "height_cm": 175,
            "weight_kg": 72,
        })
        assert profile.profile["age"] == 28
        assert profile.profile["height_cm"] == 175
        assert profile.updated_at == date.today()

    def test_update_preferences(self):
        profile = UserProfile(user_id="test-user")
        profile.update_preferences({
            "health_goal": "lose_weight",
            "budget_daily": 80,
        })
        assert profile.preferences["health_goal"] == "lose_weight"
        assert len(profile.goal_history) == 1

    def test_update_taste_profile(self):
        profile = UserProfile(user_id="test-user")
        profile.update_taste_profile({
            "preferred_styles": ["家常", "清淡"],
            "avoid_ingredients": ["香菜"],
        })
        assert "家常" in profile.taste_profile["preferred_styles"]
        assert "香菜" in profile.taste_profile["avoid_ingredients"]

    def test_add_feedback(self):
        profile = UserProfile(user_id="test-user")
        feedback = FeedbackRecord(
            feedback_date=date.today(),
            meal_plan_id="plan-001",
            liked_dishes=["宫保鸡丁"],
            disliked_dishes=["麻婆豆腐"],
            comment="豆腐太辣了",
        )
        profile.add_feedback(feedback)
        assert len(profile.feedback_history) == 1
        assert profile.feedback_history[0].liked_dishes[0] == "宫保鸡丁"

    def test_get_summary_for_context(self):
        profile = UserProfile(
            user_id="test-user",
            profile={"age": 28, "height_cm": 175, "weight_kg": 72},
            preferences={"health_goal": "lose_weight", "budget_daily": 80},
        )
        summary = profile.get_summary_for_context()
        assert "28岁" in summary
        assert "175cm" in summary
        assert "减脂" in summary
        assert "80元" in summary


class TestUserProfileManager:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_get_new_profile(self, temp_dir):
        manager = UserProfileManager(profiles_dir=temp_dir)
        profile = manager.get_profile("new-user")
        assert profile.user_id == "new-user"
        assert profile.profile["age"] is None

    def test_save_and_load_profile(self, temp_dir):
        manager = UserProfileManager(profiles_dir=temp_dir)

        # 创建并保存
        profile = UserProfile(user_id="test-user")
        profile.update_profile({"age": 28})
        manager.save_profile(profile)

        # 清除缓存后重新加载
        manager.clear_cache()
        loaded = manager.get_profile("test-user")
        assert loaded.profile["age"] == 28

    def test_update_profile_convenience(self, temp_dir):
        manager = UserProfileManager(profiles_dir=temp_dir)

        profile = manager.update_profile(
            user_id="test-user",
            profile_updates={"age": 28, "height_cm": 175},
            preference_updates={"health_goal": "lose_weight"},
        )

        assert profile.profile["age"] == 28
        assert profile.preferences["health_goal"] == "lose_weight"

        # 验证持久化
        manager.clear_cache()
        loaded = manager.get_profile("test-user")
        assert loaded.profile["age"] == 28

    def test_profile_caching(self, temp_dir):
        manager = UserProfileManager(profiles_dir=temp_dir)

        profile1 = manager.get_profile("test-user")
        profile2 = manager.get_profile("test-user")

        # 应该是同一个实例（缓存命中）
        assert profile1 is profile2

    def test_profile_file_format(self, temp_dir):
        manager = UserProfileManager(profiles_dir=temp_dir)

        manager.update_profile(
            user_id="test-user",
            profile_updates={"age": 28},
        )

        # 直接读取文件验证格式
        profile_path = temp_dir / "test-user.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["user_id"] == "test-user"
        assert data["profile"]["age"] == 28
