# src/intelligent_meal_planner/meal_chat/profile/manager.py
import json
from pathlib import Path
from typing import Optional

from .schema import UserProfile, FeedbackRecord


class UserProfileManager:
    """用户认知文件管理器"""

    def __init__(self, profiles_dir: str | Path | None = None):
        """
        初始化管理器。

        Args:
            profiles_dir: 认知文件存储目录，默认为 data/user_profiles/
        """
        if profiles_dir is None:
            # 默认路径：项目根目录/data/user_profiles/
            project_root = Path(__file__).parent.parent.parent.parent
            profiles_dir = project_root / "data" / "user_profiles"

        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self._cache: dict[str, UserProfile] = {}

    def get_profile(self, user_id: str) -> UserProfile:
        """
        获取用户认知文件。

        如果文件不存在，返回新的空 Profile。

        Args:
            user_id: 用户 ID

        Returns:
            UserProfile 实例
        """
        # 检查缓存
        if user_id in self._cache:
            return self._cache[user_id]

        # 检查文件
        profile_path = self.profiles_dir / f"{user_id}.json"
        if profile_path.exists():
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                profile = UserProfile.model_validate(data)
        else:
            # 创建新 Profile
            profile = UserProfile(user_id=user_id)

        # 缓存
        self._cache[user_id] = profile
        return profile

    def save_profile(self, profile: UserProfile) -> None:
        """
        保存用户认知文件。

        Args:
            profile: UserProfile 实例
        """
        profile_path = self.profiles_dir / f"{profile.user_id}.json"

        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(
                profile.model_dump(mode="json"),
                f,
                ensure_ascii=False,
                indent=2,
            )

        # 更新缓存
        self._cache[profile.user_id] = profile

    def update_profile(
        self,
        user_id: str,
        profile_updates: Optional[dict] = None,
        preference_updates: Optional[dict] = None,
        taste_profile_updates: Optional[dict] = None,
        feedback: Optional[FeedbackRecord] = None,
    ) -> UserProfile:
        """
        更新用户认知文件。

        Args:
            user_id: 用户 ID
            profile_updates: 档案更新
            preference_updates: 偏好更新
            taste_profile_updates: 口味画像更新
            feedback: 反馈记录

        Returns:
            更新后的 UserProfile
        """
        profile = self.get_profile(user_id)

        if profile_updates:
            profile.update_profile(profile_updates)

        if preference_updates:
            profile.update_preferences(preference_updates)

        if taste_profile_updates:
            profile.update_taste_profile(taste_profile_updates)

        if feedback:
            profile.add_feedback(feedback)

        self.save_profile(profile)
        return profile

    def clear_cache(self, user_id: Optional[str] = None) -> None:
        """
        清除缓存。

        Args:
            user_id: 指定用户，None 表示清除所有
        """
        if user_id is None:
            self._cache.clear()
        elif user_id in self._cache:
            del self._cache[user_id]
