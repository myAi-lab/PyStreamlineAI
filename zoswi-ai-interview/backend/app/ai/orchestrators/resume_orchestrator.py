from app.ai.gateway import AIGateway
from app.ai.prompts.resume_analysis import build_resume_analysis_messages
from app.ai.schemas import ResumeAnalysisAIOutput


class ResumeOrchestrator:
    def __init__(self, gateway: AIGateway) -> None:
        self.gateway = gateway

    async def analyze_resume(self, raw_text: str) -> ResumeAnalysisAIOutput:
        messages = build_resume_analysis_messages(raw_text=raw_text)
        return await self.gateway.run_structured(
            workflow="resume_analysis",
            messages=messages,
            response_model=ResumeAnalysisAIOutput,
        )

