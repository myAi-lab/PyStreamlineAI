from textwrap import dedent


def build_turn_evaluation_messages(
    *,
    role_target: str,
    experience_level: str,
    question: str,
    answer: str,
    recent_context: str,
) -> list[dict[str, str]]:
    system = dedent(
        """
        You are an AI Interview Evaluator.
        Evaluate the candidate response in a structured and objective way.

        RULES:
        - Be strict but fair.
        - No generic feedback.
        - Tie evaluation to role expectations.
        - Keep feedback concise.
        - No extra text outside JSON.

        OUTPUT FORMAT (STRICT JSON):
        {
          "score_overall": 0-10,
          "score_technical": 0-10,
          "score_communication": 0-10,
          "score_confidence": 0-10,
          "strengths": ["..."],
          "weaknesses": ["..."],
          "feedback": "short actionable feedback (2-3 lines)"
        }

        Return only valid JSON and no code fences.
        """
    ).strip()

    user = dedent(
        f"""
        Question: {question}
        Candidate answer: {answer}
        Role: {role_target}
        Experience level: {experience_level}
        Recent interview context: {recent_context}

        Return only JSON.
        """
    ).strip()

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
