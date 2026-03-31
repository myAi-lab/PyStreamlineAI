from statistics import mean

from app.ai.gateway import AIGateway
from app.ai.orchestrators.interview_orchestrator import InterviewOrchestrator
from app.ai.schemas import InterviewQuestionAIOutput
from app.core.config import get_settings
from app.models.candidate_profile import CandidateProfile
from app.models.interview import InterviewSession, InterviewTurn


class InterviewEngineService:
    def __init__(self) -> None:
        settings = get_settings()
        self.orchestrator = InterviewOrchestrator(AIGateway(settings))

    async def generate_next_question(
        self,
        *,
        session: InterviewSession,
        turns: list[InterviewTurn],
        profile: CandidateProfile | None,
    ) -> InterviewQuestionAIOutput:
        profile_context = self._format_profile(profile)
        prior_turns_summary = self._format_turn_history(turns)
        score_trend = self._score_trend(turns)
        experience_level = self._infer_experience_level(profile)
        return await self.orchestrator.generate_next_question(
            role_target=session.role_target,
            session_mode=session.session_mode.value,
            experience_level=experience_level,
            turn_index=len(turns) + 1,
            profile_context=profile_context,
            prior_turns_summary=prior_turns_summary,
            score_trend=score_trend,
        )

    @staticmethod
    def _format_profile(profile: CandidateProfile | None) -> str:
        if profile is None:
            return "No additional profile context available."
        return (
            f"Headline: {profile.headline or 'N/A'}\n"
            f"Years experience: {profile.years_experience or 'N/A'}\n"
            f"Target roles: {', '.join(profile.target_roles) if profile.target_roles else 'N/A'}\n"
            f"Location: {profile.location or 'N/A'}"
        )

    @staticmethod
    def _format_turn_history(turns: list[InterviewTurn]) -> str:
        if not turns:
            return "No turns yet."

        lines: list[str] = []
        for turn in turns[-6:]:
            answer_preview = (turn.candidate_message or "[no answer]")[:240]
            lines.append(
                f"Turn {turn.turn_index}: Q={turn.interviewer_message[:180]} | "
                f"A={answer_preview} | score={turn.score_overall or 'N/A'}"
            )
        return "\n".join(lines)

    @staticmethod
    def _score_trend(turns: list[InterviewTurn]) -> str:
        scored = [turn.score_overall for turn in turns if turn.score_overall is not None]
        if not scored:
            return "No scores yet."
        recent = scored[-3:]
        return f"Recent average: {mean(recent):.2f}/10 across {len(recent)} scored turns"

    @staticmethod
    def _infer_experience_level(profile: CandidateProfile | None) -> str:
        years = profile.years_experience if profile and profile.years_experience is not None else None
        if years is None:
            return "mid"
        if years <= 2:
            return "junior"
        if years <= 6:
            return "mid"
        return "senior"
