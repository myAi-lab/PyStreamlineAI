from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RecommendationLabel(StrEnum):
    strong_hire = "Strong Hire"
    hire = "Hire"
    leaning_no = "Leaning No"
    no_hire = "No Hire"


@dataclass(frozen=True)
class TurnScorePayload:
    technical_correctness: float
    problem_solving_debugging: float
    architecture_design: float
    communication_clarity: float
    tradeoff_reasoning: float
    professional_integrity: float
    confidence_score: float
    weighted_score: float
    evidence_snippet: str
    coverage_update: dict[str, Any]


class ScoringEngine:
    # Percent weights
    technical_weight = 0.30
    problem_solving_weight = 0.20
    architecture_weight = 0.20
    communication_weight = 0.15
    tradeoff_weight = 0.10
    integrity_weight = 0.05

    def score_turn(
        self,
        *,
        transcript_text: str,
        evaluation_signals: dict[str, Any],
        answer_quality_score: float,
        integrity_signal_count: int,
        competency_key: str,
    ) -> TurnScorePayload:
        technical = self._clamp(evaluation_signals.get("technical_accuracy", 0.0))
        communication = self._clamp(evaluation_signals.get("communication_clarity", 0.0))
        confidence = self._clamp(evaluation_signals.get("confidence", 0.0))

        problem_solving = self._clamp((technical * 0.7) + (answer_quality_score * 10 * 0.3))
        architecture = self._clamp((technical * 0.6) + (confidence * 0.4))
        tradeoff = self._clamp((technical * 0.5) + (communication * 0.5))
        integrity = self._clamp(max(0.0, 10.0 - (float(integrity_signal_count) * 1.5)))

        weighted = (
            technical * self.technical_weight
            + problem_solving * self.problem_solving_weight
            + architecture * self.architecture_weight
            + communication * self.communication_weight
            + tradeoff * self.tradeoff_weight
            + integrity * self.integrity_weight
        )
        snippet = self._build_evidence_snippet(transcript_text)
        coverage_update = {"competency_key": competency_key, "score_bucket": round(weighted, 2)}

        return TurnScorePayload(
            technical_correctness=technical,
            problem_solving_debugging=problem_solving,
            architecture_design=architecture,
            communication_clarity=communication,
            tradeoff_reasoning=tradeoff,
            professional_integrity=integrity,
            confidence_score=confidence,
            weighted_score=round(weighted, 2),
            evidence_snippet=snippet,
            coverage_update=coverage_update,
        )

    def summarize_final_assessment(self, turn_scores: list[TurnScorePayload]) -> dict[str, Any]:
        if not turn_scores:
            return {
                "overall_score": 0.0,
                "competency_coverage": 0.0,
                "strengths": [],
                "weaknesses": ["No candidate responses captured."],
                "recommendation": RecommendationLabel.no_hire.value,
            }

        overall = round(sum(item.weighted_score for item in turn_scores) / len(turn_scores), 2)
        coverage = round(min(100.0, len(turn_scores) * 25.0), 2)

        strengths: list[str] = []
        weaknesses: list[str] = []
        if overall >= 8.0:
            strengths.append("Strong technical depth across the interview.")
        if overall >= 7.0:
            strengths.append("Consistent communication and structured responses.")
        if overall < 6.0:
            weaknesses.append("Insufficient depth in multiple technical responses.")
        if coverage < 100:
            weaknesses.append("Incomplete competency coverage due to limited turns.")

        if overall >= 8.5:
            recommendation = RecommendationLabel.strong_hire.value
        elif overall >= 7.0:
            recommendation = RecommendationLabel.hire.value
        elif overall >= 5.5:
            recommendation = RecommendationLabel.leaning_no.value
        else:
            recommendation = RecommendationLabel.no_hire.value

        return {
            "overall_score": overall,
            "competency_coverage": coverage,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendation": recommendation,
        }

    @staticmethod
    def _clamp(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        return max(0.0, min(10.0, round(numeric, 2)))

    @staticmethod
    def _build_evidence_snippet(text: str, max_len: int = 220) -> str:
        cleaned = " ".join(str(text or "").split()).strip()
        if len(cleaned) <= max_len:
            return cleaned
        return f"{cleaned[: max_len - 3]}..."
