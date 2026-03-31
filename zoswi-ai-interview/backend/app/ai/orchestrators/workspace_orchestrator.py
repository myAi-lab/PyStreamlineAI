from app.ai.gateway import AIGateway
from app.ai.prompts.workspace_reply import build_workspace_reply_messages
from app.ai.schemas import WorkspaceReplyAIOutput


class WorkspaceOrchestrator:
    def __init__(self, gateway: AIGateway) -> None:
        self.gateway = gateway

    async def generate_reply(
        self,
        *,
        candidate_name: str,
        profile_context: str,
        conversation_summary: str,
        user_message: str,
    ) -> WorkspaceReplyAIOutput:
        messages = build_workspace_reply_messages(
            candidate_name=candidate_name,
            profile_context=profile_context,
            conversation_summary=conversation_summary,
            user_message=user_message,
        )
        return await self.gateway.run_structured(
            workflow="workspace_reply",
            messages=messages,
            response_model=WorkspaceReplyAIOutput,
        )
