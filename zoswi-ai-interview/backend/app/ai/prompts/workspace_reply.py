from textwrap import dedent


def build_workspace_reply_messages(
    *,
    candidate_name: str,
    profile_context: str,
    conversation_summary: str,
    user_message: str,
) -> list[dict[str, str]]:
    system = dedent(
        """
        You are ZoSwi Live Workspace, an AI assistant for career intelligence and interview prep.
        Behavior:
        - Stay professional, concise, and action-oriented.
        - Focus on resume improvement, interview preparation, role targeting, and recruiter readiness.
        - Avoid legal, medical, or harmful content.
        Return strict JSON only with keys:
        response (string),
        key_points (array of strings),
        suggested_next_step (string or null).
        """
    ).strip()

    user = dedent(
        f"""
        Candidate name: {candidate_name}
        Candidate profile context:
        {profile_context}

        Recent conversation context:
        {conversation_summary}

        Latest user message:
        {user_message}

        Return only JSON.
        """
    ).strip()

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
