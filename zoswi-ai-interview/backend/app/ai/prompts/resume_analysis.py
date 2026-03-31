from textwrap import dedent


def build_resume_analysis_messages(raw_text: str) -> list[dict[str, str]]:
    system = dedent(
        """
        You are ZoSwi Resume Intelligence.
        Analyze a candidate resume and return strict JSON with keys:
        extracted_skills (array of strings),
        strengths (array of strings),
        weaknesses (array of strings),
        suggestions (array of strings),
        summary (string).
        Keep each list concise and action-oriented. Avoid exposing sensitive PII.
        """
    ).strip()

    user = dedent(
        f"""
        Resume text:
        ---
        {raw_text}
        ---
        Return only JSON.
        """
    ).strip()

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]

