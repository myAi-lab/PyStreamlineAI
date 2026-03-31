from typing import TypeVar

from pydantic import BaseModel

from app.ai.providers.base import AIProvider
from app.ai.schemas import (
    FinalSummaryAIOutput,
    InterviewQuestionAIOutput,
    ResumeAnalysisAIOutput,
    TurnEvaluationAIOutput,
    WorkspaceReplyAIOutput,
)

T = TypeVar("T", bound=BaseModel)


class MockProvider(AIProvider):
    async def generate_structured(
        self,
        *,
        messages: list[dict[str, str]],
        response_model: type[T],
        model_name: str,
        timeout_seconds: float,
    ) -> T:
        if response_model is ResumeAnalysisAIOutput:
            payload = ResumeAnalysisAIOutput(
                extracted_skills=["Python", "SQL", "System Design"],
                strengths=["Strong technical breadth", "Clear project ownership evidence"],
                weaknesses=["Limited quantified impact examples"],
                suggestions=[
                    "Add measurable outcomes for recent projects",
                    "Clarify leadership scope in team initiatives",
                ],
                summary="Candidate shows strong engineering foundations with room to improve impact framing.",
            )
            return payload  # type: ignore[return-value]

        if response_model is InterviewQuestionAIOutput:
            payload = InterviewQuestionAIOutput(
                interviewer_message=(
                    "Got it. Walk me through a recent project where you improved system reliability under load."
                ),
                tone="professional",
                next_action="next_question",
            )
            return payload  # type: ignore[return-value]

        if response_model is TurnEvaluationAIOutput:
            payload = TurnEvaluationAIOutput(
                score_overall=7.0,
                score_communication=7.5,
                score_technical=7.0,
                score_confidence=6.8,
                strengths=[
                    "Explains the core approach clearly.",
                    "Shows reasonable understanding of backend tradeoffs.",
                ],
                weaknesses=[
                    "Impact was not quantified with concrete metrics.",
                    "Edge-case handling was mentioned but not detailed.",
                ],
                feedback=(
                    "Good structure and technical direction for this role.\n"
                    "Add one production metric and explain the key tradeoff decision.\n"
                    "Cover failure handling depth to match stronger expectations."
                ),
            )
            return payload  # type: ignore[return-value]

        if response_model is FinalSummaryAIOutput:
            payload = FinalSummaryAIOutput(
                final_score=7.2,
                recommendation="hold",
                strengths=["Clear communication", "Good fundamentals"],
                improvement_areas=["Deeper system design tradeoff articulation"],
                summary="Candidate demonstrates strong potential with moderate gaps for immediate senior ownership.",
            )
            return payload  # type: ignore[return-value]

        if response_model is WorkspaceReplyAIOutput:
            payload = WorkspaceReplyAIOutput(
                response=(
                    "Here is a focused improvement path: tighten your impact bullets, align resume keywords "
                    "to target role requirements, and run one mock interview session this week."
                ),
                key_points=[
                    "Quantify outcomes in your latest project bullets.",
                    "Align 8-12 role-specific keywords with your resume and LinkedIn profile.",
                    "Practice two STAR behavioral answers tied to measurable impact.",
                ],
                suggested_next_step="Choose one target role and I can generate a tailored 7-day plan.",
            )
            return payload  # type: ignore[return-value]

        return response_model.model_validate({})
