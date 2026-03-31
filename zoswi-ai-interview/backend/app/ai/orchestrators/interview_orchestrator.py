from app.ai.gateway import AIGateway
from app.ai.prompts.final_summary import build_final_summary_messages
from app.ai.prompts.interview_question import build_next_question_messages
from app.ai.prompts.turn_evaluation import build_turn_evaluation_messages
from app.ai.schemas import FinalSummaryAIOutput, InterviewQuestionAIOutput, TurnEvaluationAIOutput


class InterviewOrchestrator:
    def __init__(self, gateway: AIGateway) -> None:
        self.gateway = gateway

    async def generate_next_question(
        self,
        *,
        role_target: str,
        session_mode: str,
        experience_level: str,
        turn_index: int,
        profile_context: str,
        prior_turns_summary: str,
        score_trend: str,
    ) -> InterviewQuestionAIOutput:
        messages = build_next_question_messages(
            role_target=role_target,
            session_mode=session_mode,
            experience_level=experience_level,
            turn_index=turn_index,
            profile_context=profile_context,
            prior_turns_summary=prior_turns_summary,
            score_trend=score_trend,
        )
        return await self.gateway.run_structured(
            workflow="interview_next_question",
            messages=messages,
            response_model=InterviewQuestionAIOutput,
        )

    async def evaluate_turn(
        self,
        *,
        role_target: str,
        experience_level: str,
        question: str,
        answer: str,
        recent_context: str,
    ) -> TurnEvaluationAIOutput:
        messages = build_turn_evaluation_messages(
            role_target=role_target,
            experience_level=experience_level,
            question=question,
            answer=answer,
            recent_context=recent_context,
        )
        return await self.gateway.run_structured(
            workflow="turn_evaluation",
            messages=messages,
            response_model=TurnEvaluationAIOutput,
        )

    async def summarize_interview(self, *, role_target: str, transcript: str) -> FinalSummaryAIOutput:
        messages = build_final_summary_messages(role_target=role_target, transcript=transcript)
        return await self.gateway.run_structured(
            workflow="interview_final_summary",
            messages=messages,
            response_model=FinalSummaryAIOutput,
        )
