from __future__ import annotations

from typing import Any
import hashlib
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository
from app.schemas.coding_room import (
    CodingEvaluationRequest,
    CodingEvaluationResponse,
    CodingHiddenCheckRequest,
    CodingHiddenCheckResponse,
    CodingRoomStage,
    CodingRoomStagesResponse,
    CodingStarterCodeResponse,
)
from app.models.enums import InterviewMode


CODING_STAGE_COUNT = 3


class CodingRoomService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_repo = AuditRepository(session)

    def list_stages(self, *, role_target: str, interview_mode: InterviewMode) -> CodingRoomStagesResponse:
        clean_role = re.sub(r"\s+", " ", role_target).strip() or "Software Engineer"
        mode_label = interview_mode.value.replace("_", " ")

        stages = [
            CodingRoomStage(
                stage_index=1,
                title="Stage 1: Core Logic",
                skill_focus=f"{clean_role} fundamentals",
                challenge=(
                    f"Build a deterministic parser for a {clean_role} interview scenario and return a structured output."
                ),
                difficulty="foundational",
                time_limit_min=20,
                requirements=[
                    "Implement TODO sections in starter code.",
                    "Handle empty or malformed input safely.",
                    "Return a stable output schema.",
                ],
                hint_starters=[
                    "Start with input validation before core logic.",
                    "Use clear variable names and deterministic operations.",
                ],
            ),
            CodingRoomStage(
                stage_index=2,
                title="Stage 2: Edge Cases & Scale",
                skill_focus=f"{clean_role} optimization",
                challenge=(
                    f"Refactor the solution to handle larger inputs and cover edge paths expected in {mode_label} interviews."
                ),
                difficulty="intermediate",
                time_limit_min=25,
                requirements=[
                    "Improve complexity and explain tradeoffs.",
                    "Add robust edge-case handling.",
                    "Keep output contract unchanged.",
                ],
                hint_starters=[
                    "Separate transformation and aggregation steps.",
                    "Add guard clauses for invalid records.",
                ],
            ),
            CodingRoomStage(
                stage_index=3,
                title="Stage 3: Production Readiness",
                skill_focus=f"{clean_role} communication & reliability",
                challenge=(
                    f"Finalize a production-ready version with clear reasoning, reliability checks, and concise explanation."
                ),
                difficulty="advanced",
                time_limit_min=30,
                requirements=[
                    "Demonstrate defensive coding patterns.",
                    "Document complexity and assumptions.",
                    "Produce final response in interview-ready style.",
                ],
                hint_starters=[
                    "Prioritize correctness first, then optimization.",
                    "Explain what you would monitor in production.",
                ],
            ),
        ]

        return CodingRoomStagesResponse(
            role_target=clean_role,
            interview_mode=interview_mode,
            stages=stages,
        )

    def starter_code(self, *, stage_index: int, language: str, role_target: str) -> CodingStarterCodeResponse:
        stage = self._stage(stage_index, role_target=role_target)
        normalized_language = self._language(language)
        code = self._build_starter_code(stage=stage, language=normalized_language)
        return CodingStarterCodeResponse(stage_index=stage_index, language=normalized_language, code=code)

    async def hidden_check(
        self,
        *,
        user_id,
        stage_index: int,
        language: str,
        payload: CodingHiddenCheckRequest,
        role_target: str,
    ) -> CodingHiddenCheckResponse:
        stage = self._stage(stage_index, role_target=role_target)
        normalized_language = self._language(language or payload.language)
        starter = self._build_starter_code(stage=stage, language=normalized_language)
        code = str(payload.code or "").strip()

        if not code:
            result = CodingHiddenCheckResponse(
                ran=True,
                total=5,
                passed=0,
                failed_cases=["submission_missing", "todo_completion", "return_shape"],
                summary="No code submitted yet.",
                ready_for_evaluation=False,
            )
        elif self._is_starter_unchanged(code, starter):
            result = CodingHiddenCheckResponse(
                ran=True,
                total=5,
                passed=0,
                failed_cases=["todo_completion", "core_logic", "edge_case_guard"],
                summary="Starter template is unchanged. Complete TODO sections before evaluation.",
                ready_for_evaluation=False,
            )
        else:
            has_return = "return" in code.lower()
            has_branching = bool(re.search(r"\b(if|elif|else|switch|case)\b", code, flags=re.IGNORECASE))
            has_iteration = bool(re.search(r"\b(for|while|foreach)\b", code, flags=re.IGNORECASE))
            has_todo = bool(re.search(r"\bTODO\b", code, flags=re.IGNORECASE))
            has_data_structure = bool(
                re.search(r"\b(dict|map|set|list|array|object|hashmap)\b", code, flags=re.IGNORECASE)
            )
            passed = 1
            passed += 1 if has_return else 0
            passed += 1 if has_branching else 0
            passed += 1 if has_iteration else 0
            passed += 1 if has_data_structure and not has_todo else 0

            failed_cases: list[str] = []
            if has_todo:
                failed_cases.append("todo_completion")
            if not has_return:
                failed_cases.append("return_shape")
            if not has_branching:
                failed_cases.append("edge_case_branching")
            if not has_iteration:
                failed_cases.append("iteration_logic")
            if not has_data_structure:
                failed_cases.append("data_structure_usage")

            ready = passed >= 3 and not has_todo
            result = CodingHiddenCheckResponse(
                ran=True,
                total=5,
                passed=min(5, max(0, passed)),
                failed_cases=failed_cases[:5],
                summary=(
                    f"Hidden checks passed {min(5, max(0, passed))}/5. "
                    + ("Ready for evaluation." if ready else "Resolve failed checks before evaluation.")
                ),
                ready_for_evaluation=ready,
            )

        await self.audit_repo.create(
            AuditLog(
                entity_type="coding_room_stage",
                entity_id=f"{user_id}:{stage_index}",
                event_type="coding_hidden_check",
                payload={
                    "stage_index": stage_index,
                    "language": normalized_language,
                    "passed": result.passed,
                    "total": result.total,
                    "ready": result.ready_for_evaluation,
                },
            )
        )
        await self.session.commit()
        return result

    async def evaluate(
        self,
        *,
        user_id,
        stage_index: int,
        language: str,
        payload: CodingEvaluationRequest,
        role_target: str,
    ) -> CodingEvaluationResponse:
        stage = self._stage(stage_index, role_target=role_target)
        normalized_language = self._language(language or payload.language)
        starter = self._build_starter_code(stage=stage, language=normalized_language)
        code = str(payload.code or "").strip()

        if not code:
            result = CodingEvaluationResponse(
                score=0,
                verdict="No submission",
                strengths=[],
                improvements=["Add a solution before running stage evaluation."],
                next_step="Write the first working version and evaluate again.",
            )
        elif self._is_starter_unchanged(code, starter):
            result = CodingEvaluationResponse(
                score=0,
                verdict="No submission",
                strengths=[],
                improvements=["Starter template is unchanged. Complete the TODO sections first."],
                next_step="Implement TODO blocks and re-run evaluation.",
            )
        else:
            has_return = "return" in code.lower()
            has_branching = bool(re.search(r"\b(if|elif|else|switch|case)\b", code, flags=re.IGNORECASE))
            has_iteration = bool(re.search(r"\b(for|while|foreach)\b", code, flags=re.IGNORECASE))
            has_data_structure = bool(
                re.search(r"\b(dict|map|set|list|array|object|hashmap)\b", code, flags=re.IGNORECASE)
            )
            has_error_guard = bool(re.search(r"\b(try|except|catch|raise|throw)\b", code, flags=re.IGNORECASE))
            has_todo = bool(re.search(r"\bTODO\b", code, flags=re.IGNORECASE))

            score = 30
            score += 18 if has_return else 0
            score += 16 if has_branching else 0
            score += 14 if has_iteration else 0
            score += 12 if has_data_structure else 0
            score += 10 if has_error_guard else 0
            score += 8 if not has_todo else 0
            score = max(0, min(100, score))

            strengths: list[str] = []
            improvements: list[str] = []
            if has_return:
                strengths.append("Returns a structured output shape.")
            if has_branching:
                strengths.append("Includes decision logic for different input paths.")
            if has_iteration:
                strengths.append("Processes collections using iterative logic.")
            if has_data_structure:
                strengths.append("Uses data structures appropriate for aggregation.")
            if has_error_guard:
                strengths.append("Includes basic defensive/error handling.")

            if not has_todo:
                strengths.append("All TODO placeholders appear addressed.")
            else:
                improvements.append("Complete remaining TODO sections.")
            if not has_branching:
                improvements.append("Add explicit edge-case branching.")
            if not has_iteration:
                improvements.append("Iterate over records instead of single-item assumptions.")
            if not has_error_guard:
                improvements.append("Add defensive checks or exception handling.")
            if not has_data_structure:
                improvements.append("Use stable mapping/list structures for predictable outputs.")

            verdict = self._verdict(score)
            result = CodingEvaluationResponse(
                score=score,
                verdict=verdict,
                strengths=strengths[:4],
                improvements=improvements[:4] or ["Tighten complexity explanation and add tests."],
                next_step=(
                    "Explain complexity tradeoffs, then continue to the next stage."
                    if score >= 70
                    else "Refine logic for edge cases and rerun evaluation."
                ),
            )

        await self.audit_repo.create(
            AuditLog(
                entity_type="coding_room_stage",
                entity_id=f"{user_id}:{stage_index}",
                event_type="coding_stage_evaluated",
                payload={
                    "stage_index": stage_index,
                    "language": normalized_language,
                    "score": result.score,
                    "verdict": result.verdict,
                },
            )
        )
        await self.session.commit()
        return result

    def _stage(self, stage_index: int, *, role_target: str) -> dict[str, Any]:
        stages = self.list_stages(role_target=role_target, interview_mode=InterviewMode.MIXED).stages
        if stage_index < 1 or stage_index > len(stages):
            raise ValidationError("Stage index out of range")
        stage = stages[stage_index - 1]
        return stage.model_dump()

    @staticmethod
    def _language(value: str) -> str:
        cleaned = re.sub(r"[^a-z0-9\+\#]+", "", str(value or "python").strip().lower())
        aliases = {
            "py": "python",
            "python": "python",
            "java": "java",
            "javascript": "javascript",
            "js": "javascript",
            "typescript": "typescript",
            "ts": "typescript",
            "go": "go",
            "golang": "go",
            "c++": "c++",
            "cpp": "c++",
        }
        return aliases.get(cleaned, "python")

    @staticmethod
    def _build_starter_code(*, stage: dict[str, Any], language: str) -> str:
        requirements = stage.get("requirements", [])
        if not isinstance(requirements, list):
            requirements = []
        todo_lines = [f"TODO {idx + 1}: {item}" for idx, item in enumerate(requirements[:3])]
        title = str(stage.get("title", "Coding Stage"))
        challenge = str(stage.get("challenge", "Complete the exercise."))

        if language == "python":
            todo = "\n".join(f"    # {line}" for line in todo_lines)
            return (
                f"# {title}\n"
                f"# {challenge}\n"
                "def solve(records):\n"
                f"{todo}\n"
                "    result = {}\n"
                "    return result\n\n"
                "if __name__ == '__main__':\n"
                "    sample_records = []\n"
                "    print(solve(sample_records))\n"
            )
        if language == "java":
            todo = "\n".join(f"        // {line}" for line in todo_lines)
            return (
                f"// {title}\n"
                f"// {challenge}\n"
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static Map<String, Object> solve(List<Map<String, Object>> records) {\n"
                f"{todo}\n"
                "        Map<String, Object> result = new HashMap<>();\n"
                "        return result;\n"
                "    }\n"
                "}\n"
            )
        if language == "javascript":
            todo = "\n".join(f"  // {line}" for line in todo_lines)
            return (
                f"// {title}\n"
                f"// {challenge}\n"
                "function solve(records) {\n"
                f"{todo}\n"
                "  const result = {};\n"
                "  return result;\n"
                "}\n\n"
                "console.log(solve([]));\n"
            )
        if language == "typescript":
            todo = "\n".join(f"  // {line}" for line in todo_lines)
            return (
                f"// {title}\n"
                f"// {challenge}\n"
                "type RecordItem = Record<string, unknown>;\n\n"
                "function solve(records: RecordItem[]): Record<string, unknown> {\n"
                f"{todo}\n"
                "  const result: Record<string, unknown> = {};\n"
                "  return result;\n"
                "}\n\n"
                "console.log(solve([]));\n"
            )
        if language == "go":
            todo = "\n".join(f"\t// {line}" for line in todo_lines)
            return (
                f"// {title}\n"
                f"// {challenge}\n"
                "package main\n\n"
                "import \"fmt\"\n\n"
                "func solve(records []map[string]any) map[string]any {\n"
                f"{todo}\n"
                "\tresult := map[string]any{}\n"
                "\treturn result\n"
                "}\n\n"
                "func main() {\n"
                "\tfmt.Println(solve([]map[string]any{}))\n"
                "}\n"
            )

        todo = "\n".join(f"// {line}" for line in todo_lines)
        return (
            f"// {title}\n"
            f"// {challenge}\n"
            "#include <bits/stdc++.h>\n"
            "using namespace std;\n\n"
            "int main() {\n"
            f"{todo}\n"
            "    unordered_map<string, int> result;\n"
            "    cout << result.size() << endl;\n"
            "    return 0;\n"
            "}\n"
        )

    @staticmethod
    def _is_starter_unchanged(code: str, starter_code: str) -> bool:
        normalize = lambda value: re.sub(r"\s+", "", str(value or "")).lower()
        return normalize(code) == normalize(starter_code)

    @staticmethod
    def _verdict(score: int) -> str:
        if score >= 85:
            return "Strong"
        if score >= 70:
            return "Solid"
        if score >= 55:
            return "Developing"
        return "Needs Improvement"

