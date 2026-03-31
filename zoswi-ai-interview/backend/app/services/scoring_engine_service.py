from statistics import mean

from app.ai.gateway import AIGateway
from app.ai.orchestrators.interview_orchestrator import InterviewOrchestrator
from app.ai.schemas import FinalSummaryAIOutput, TurnEvaluationAIOutput
from app.core.config import get_settings
from app.models.interview import InterviewSession, InterviewTurn


class ScoringEngineService:
    def __init__(self) -> None:
        settings = get_settings()
        self.orchestrator = InterviewOrchestrator(AIGateway(settings))

    async def evaluate_turn(
        self,
        *,
        session: InterviewSession,
        question: str,
        answer: str,
        prior_turns: list[InterviewTurn],
        experience_level: str = "mid",
    ) -> TurnEvaluationAIOutput:
        clean_answer = answer.strip()
        if len(clean_answer) < 15:
            return TurnEvaluationAIOutput(
                score_overall=2.5,
                score_communication=3.0,
                score_technical=2.0,
                score_confidence=2.5,
                strengths=[],
                weaknesses=["Answer is too brief and lacks role-relevant evidence."],
                feedback=(
                    "Your response is too short to assess depth for this role.\n"
                    "Use a clear structure: context, decision, and measurable outcome.\n"
                    "Add one concrete technical tradeoff you handled."
                ),
            )

        recent_context = self._format_recent_context(prior_turns)
        return await self.orchestrator.evaluate_turn(
            role_target=session.role_target,
            experience_level=experience_level,
            question=question,
            answer=clean_answer,
            recent_context=recent_context,
        )

    async def summarize_session(
        self,
        *,
        session: InterviewSession,
        turns: list[InterviewTurn],
    ) -> FinalSummaryAIOutput:
        transcript = self._build_transcript(turns)
        if not transcript.strip():
            return FinalSummaryAIOutput(
                final_score=0.0,
                recommendation="no_hire",
                strengths=[],
                improvement_areas=["Insufficient interview evidence."],
                summary="Interview did not capture enough candidate responses to evaluate.",
            )

        summary = await self.orchestrator.summarize_interview(
            role_target=session.role_target,
            transcript=transcript,
        )
        if summary.final_score == 0 and turns:
            scored = [turn.score_overall for turn in turns if turn.score_overall is not None]
            if scored:
                summary.final_score = round(mean(scored), 2)
        return summary

    @staticmethod
    def _format_recent_context(turns: list[InterviewTurn]) -> str:
        lines: list[str] = []
        for turn in turns[-4:]:
            lines.append(
                f"Q: {turn.interviewer_message[:220]}\n"
                f"A: {(turn.candidate_message or '[no answer]')[:220]}\n"
                f"Score: {turn.score_overall if turn.score_overall is not None else 'N/A'}"
            )
        return "\n\n".join(lines)

    @staticmethod
    def _build_transcript(turns: list[InterviewTurn]) -> str:
        chunks: list[str] = []
        for turn in turns:
            if turn.candidate_message is None:
                continue
            chunks.append(
                f"Turn {turn.turn_index}\n"
                f"Interviewer: {turn.interviewer_message}\n"
                f"Candidate: {turn.candidate_message}\n"
                f"Scores: overall={turn.score_overall}, communication={turn.score_communication}, "
                f"technical={turn.score_technical}, confidence={turn.score_confidence}\n"
            )
        return "\n".join(chunks)
