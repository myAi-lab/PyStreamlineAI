from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MANDATORY_COMPETENCIES = (
    "practical_implementation",
    "debugging",
    "architecture",
    "tradeoff_reasoning",
)


@dataclass(frozen=True)
class InterviewPlanState:
    detected_domain: str
    items: list[dict[str, Any]]


class InterviewEngine:
    def detect_domain(self, role: str, resume_text: str = "") -> str:
        text = " ".join([str(role or ""), str(resume_text or "")]).lower()
        if any(token in text for token in ("frontend", "react", "ui", "typescript", "javascript")):
            return "frontend"
        if any(token in text for token in ("data", "machine learning", "ml", "ai", "pipeline")):
            return "data_ml"
        if any(token in text for token in ("devops", "infra", "kubernetes", "cloud", "platform")):
            return "devops"
        return "backend"

    def build_plan(self, role: str, resume_text: str = "") -> InterviewPlanState:
        domain = self.detect_domain(role=role, resume_text=resume_text)
        items = [
            {"competency_key": key, "target_turns": 1, "covered_turns": 0, "priority": idx + 1}
            for idx, key in enumerate(MANDATORY_COMPETENCIES)
        ]
        return InterviewPlanState(detected_domain=domain, items=items)

    def select_next_competency(self, plan_items: list[dict[str, Any]]) -> str:
        ordered = sorted(
            plan_items,
            key=lambda item: (int(item.get("covered_turns", 0) >= item.get("target_turns", 1)), int(item.get("priority", 99))),
        )
        for item in ordered:
            if int(item.get("covered_turns", 0)) < int(item.get("target_turns", 1)):
                return str(item.get("competency_key", "practical_implementation"))
        return str(ordered[0].get("competency_key", "practical_implementation")) if ordered else "practical_implementation"

    def assess_answer_quality(self, answer: str) -> tuple[bool, float]:
        cleaned = re.sub(r"\s+", " ", str(answer or "").strip())
        if not cleaned:
            return False, 0.0
        words = len(cleaned.split())
        vague_markers = ("not sure", "i don't know", "maybe", "kind of", "sort of")
        vague_hits = sum(1 for marker in vague_markers if marker in cleaned.lower())
        quality = max(0.0, min(1.0, (words / 60.0) - (vague_hits * 0.12)))
        return quality >= 0.35, round(quality, 3)

    def should_follow_up(self, answer_quality_ok: bool, answer_quality_score: float) -> bool:
        if not answer_quality_ok:
            return True
        return answer_quality_score < 0.5

    def semantic_similarity(self, left: str, right: str) -> float:
        left_tokens = set(re.findall(r"[a-z0-9]{3,}", str(left or "").lower()))
        right_tokens = set(re.findall(r"[a-z0-9]{3,}", str(right or "").lower()))
        if not left_tokens or not right_tokens:
            return 0.0
        overlap = len(left_tokens.intersection(right_tokens))
        union = len(left_tokens.union(right_tokens))
        if union == 0:
            return 0.0
        return round(overlap / union, 4)

    def is_repeated_question(self, question: str, previous_questions: list[str], threshold: float = 0.75) -> bool:
        for previous in previous_questions[-8:]:
            if self.semantic_similarity(question, previous) >= threshold:
                return True
        return False

    def coverage_reached(self, plan_items: list[dict[str, Any]]) -> bool:
        if not plan_items:
            return False
        return all(int(item.get("covered_turns", 0)) >= int(item.get("target_turns", 1)) for item in plan_items)

    def update_coverage(self, plan_items: list[dict[str, Any]], competency_key: str) -> list[dict[str, Any]]:
        updated: list[dict[str, Any]] = []
        for item in plan_items:
            candidate = dict(item)
            if str(candidate.get("competency_key")) == str(competency_key):
                candidate["covered_turns"] = int(candidate.get("covered_turns", 0)) + 1
            updated.append(candidate)
        return updated
