from textwrap import dedent


def build_final_summary_messages(
    *,
    role_target: str,
    transcript: str,
) -> list[dict[str, str]]:
    system = dedent(
        """
        You are a hiring interview summarizer.
        Produce a final recommendation with balanced signal.
        Return strict JSON with keys:
        final_score (0-10),
        recommendation (hire, hold, no_hire),
        strengths (array),
        improvement_areas (array),
        summary (string).
        """
    ).strip()

    user = dedent(
        f"""
        Role target: {role_target}
        Transcript:
        {transcript}

        Return only JSON.
        """
    ).strip()

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]

