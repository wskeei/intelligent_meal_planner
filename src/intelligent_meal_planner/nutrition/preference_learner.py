"""Learn user taste preferences from ratings, selections, and skips."""

from datetime import date

from sqlalchemy.orm import Session

from ..db import models


RATING_DELTAS = {1: -0.3, 2: -0.1, 3: 0.0, 4: 0.1, 5: 0.3}
SELECTION_DELTA = 0.02
SKIP_DELTA = -0.05


class PreferenceLearner:
    def __init__(self, db: Session):
        self.db = db

    def _get_or_create(self, user_id: int, recipe_id: int) -> models.UserPreference:
        pref = (
            self.db.query(models.UserPreference)
            .filter_by(user_id=user_id, recipe_id=recipe_id)
            .first()
        )
        if not pref:
            pref = models.UserPreference(
                user_id=user_id, recipe_id=recipe_id, preference_score=0.5,
            )
            self.db.add(pref)
        return pref

    def _clamp_score(self, score: float) -> float:
        return max(0.0, min(1.0, score))

    def update_from_rating(self, user_id: int, recipe_id: int, rating: int) -> None:
        pref = self._get_or_create(user_id, recipe_id)
        delta = RATING_DELTAS.get(rating, 0.0)
        pref.preference_score = self._clamp_score(pref.preference_score + delta)

        if pref.avg_rating is None:
            pref.avg_rating = float(rating)
        else:
            count = pref.times_eaten + 1
            pref.avg_rating = ((pref.avg_rating * (count - 1)) + rating) / count

        pref.updated_at = date.today()
        self.db.commit()

    def update_from_selection(self, user_id: int, recipe_id: int) -> None:
        pref = self._get_or_create(user_id, recipe_id)
        pref.times_eaten += 1
        pref.preference_score = self._clamp_score(pref.preference_score + SELECTION_DELTA)
        pref.last_eaten = date.today()
        pref.updated_at = date.today()
        self.db.commit()

    def update_from_skip(self, user_id: int, recipe_id: int) -> None:
        pref = self._get_or_create(user_id, recipe_id)
        pref.times_skipped += 1
        pref.preference_score = self._clamp_score(pref.preference_score + SKIP_DELTA)
        pref.updated_at = date.today()
        self.db.commit()

    def get_user_taste_profile(self, user_id: int) -> dict:
        prefs = (
            self.db.query(models.UserPreference)
            .filter_by(user_id=user_id)
            .all()
        )

        category_scores: dict[str, list[float]] = {}
        disliked = []
        for pref in prefs:
            recipe = self.db.get(models.Recipe, pref.recipe_id)
            if recipe:
                cat = recipe.category
                category_scores.setdefault(cat, []).append(pref.preference_score)
                if pref.avg_rating is not None and pref.avg_rating < 2:
                    disliked.append(recipe.name)

        preferred_cats = sorted(
            category_scores.keys(),
            key=lambda c: sum(category_scores[c]) / len(category_scores[c]),
            reverse=True,
        )

        return {
            "preferred_categories": preferred_cats,
            "disliked_recipes": disliked,
            "total_tracked": len(prefs),
        }

    def get_preference_map(self, user_id: int) -> dict[int, float]:
        """Return recipe_id -> preference_score mapping for RL integration."""
        prefs = (
            self.db.query(models.UserPreference)
            .filter_by(user_id=user_id)
            .all()
        )
        return {p.recipe_id: p.preference_score for p in prefs}
