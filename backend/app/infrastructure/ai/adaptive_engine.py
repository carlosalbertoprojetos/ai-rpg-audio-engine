from app.domain.audio.entities import AIContext


class AdaptiveAmbienceEngine:
    async def generate(self, session_id: str, mood_hint: str) -> AIContext:
        mood = mood_hint.strip().lower() or "neutral"
        tags_by_mood = {
            "battle": ["combat", "drums", "tension"],
            "mystery": ["ambient", "dark", "echo"],
            "calm": ["soft", "nature", "wind"],
        }
        tags = tags_by_mood.get(mood, ["ambient"])
        return AIContext.create(session_id=session_id, mood=mood, recommended_track_tags=tags)

