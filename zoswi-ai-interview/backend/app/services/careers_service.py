from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote_plus
import re

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.audit_log import AuditLog
from app.models.resume_analysis import ResumeAnalysis
from app.repositories.audit_repository import AuditRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.careers import (
    CareersMatchFilters,
    CareersMatchRequest,
    CareersMatchResponse,
    CareersMatchResult,
    CareersTopCompanyLink,
)


POSITION_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "full-time": ("full-time", "full time", "permanent"),
    "contract": ("contract", "freelance", "consultant"),
    "w2": ("w2",),
    "c2c": ("c2c", "corp-to-corp", "corp to corp"),
    "part-time": ("part-time", "part time"),
}

PUBLIC_COMPANY_LINKS: tuple[str, ...] = (
    "Google",
    "Apple",
    "Microsoft",
    "Amazon",
    "Meta",
    "NVIDIA",
    "Adobe",
    "Salesforce",
)


class CareersService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.resume_repo = ResumeRepository(session)
        self.candidate_repo = CandidateRepository(session)
        self.audit_repo = AuditRepository(session)

    async def match_jobs(
        self,
        *,
        user_id,
        payload: CareersMatchRequest,
    ) -> CareersMatchResponse:
        role_query = self._clean_text(payload.role_query)
        if len(role_query) < 2:
            raise ValidationError("Role query must be at least 2 characters")

        trace: list[str] = []
        resume_text, analysis = await self._resolve_resume_context(user_id=user_id, resume_id=payload.resume_id)
        if resume_text:
            trace.append("Loaded resume context for ranking.")
        else:
            trace.append("Resume context not found; ranking uses role and job metadata only.")

        raw_jobs, fetch_note = await self._fetch_jobs(role_query=role_query, max_results=max(20, payload.max_results * 7))
        trace.append(f"Fetched {len(raw_jobs)} jobs from Remotive provider.")
        if fetch_note:
            trace.append(fetch_note)

        filtered = self._filter_jobs(
            raw_jobs=raw_jobs,
            preferred_location=self._clean_text(payload.preferred_location),
            selected_position_types=payload.selected_position_types,
            posted_within_days=payload.posted_within_days,
        )
        trace.append(f"{len(filtered)} jobs remained after location/date/type filters.")

        scored = self._score_jobs(
            jobs=filtered,
            role_query=role_query,
            resume_text=resume_text,
            analysis=analysis,
            sponsorship_required=payload.sponsorship_required,
        )
        results = scored[: payload.max_results]

        await self.audit_repo.create(
            AuditLog(
                entity_type="careers_search",
                entity_id=str(user_id),
                event_type="careers_match_executed",
                payload={
                    "role_query": role_query,
                    "preferred_location": self._clean_text(payload.preferred_location),
                    "visa_status": self._clean_text(payload.visa_status),
                    "sponsorship_required": payload.sponsorship_required,
                    "selected_position_types": payload.selected_position_types,
                    "posted_within_days": payload.posted_within_days,
                    "max_results": payload.max_results,
                    "results_count": len(results),
                },
            )
        )
        await self.session.commit()

        return CareersMatchResponse(
            filters=CareersMatchFilters(
                role_query=role_query,
                preferred_location=self._clean_text(payload.preferred_location),
                visa_status=self._clean_text(payload.visa_status),
                sponsorship_required=payload.sponsorship_required,
                selected_position_types=self._normalize_position_types(payload.selected_position_types),
                posted_within_days=payload.posted_within_days,
                max_results=payload.max_results,
            ),
            results=results,
            trace=trace,
            info_message=fetch_note or None,
            top_company_links=self._build_company_links(
                role_query=role_query,
                preferred_location=self._clean_text(payload.preferred_location),
            ),
        )

    async def _resolve_resume_context(self, *, user_id, resume_id) -> tuple[str, ResumeAnalysis | None]:
        resume_text = ""
        analysis: ResumeAnalysis | None = None

        if resume_id is not None:
            resume = await self.resume_repo.get_for_user(user_id=user_id, resume_id=resume_id)
            if resume is not None:
                resume_text = str(resume.raw_text or "").strip()
                analysis = await self.resume_repo.get_analysis(resume.id)
                return resume_text, analysis

        resumes = await self.resume_repo.list_for_user(user_id)
        if resumes:
            resume_text = str(resumes[0].raw_text or "").strip()
            analysis = await self.resume_repo.get_analysis(resumes[0].id)
        if analysis is None:
            analysis = await self.resume_repo.get_latest_analysis_for_user(user_id)

        return resume_text, analysis

    async def _fetch_jobs(self, *, role_query: str, max_results: int) -> tuple[list[dict[str, Any]], str]:
        query = self._clean_text(role_query)
        if not query:
            return [], "Missing role query for provider search."

        try:
            async with httpx.AsyncClient(timeout=18.0, follow_redirects=True) as client:
                response = await client.get(
                    "https://remotive.com/api/remote-jobs",
                    params={"search": query, "limit": str(max_results)},
                )
            if response.status_code >= 400:
                return [], f"Provider response status {response.status_code}."
            payload = response.json()
            jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
            if not isinstance(jobs, list):
                return [], "Provider returned malformed jobs payload."
            return jobs, ""
        except Exception:
            return [], "Provider lookup failed. Showing fallback company links only."

    def _filter_jobs(
        self,
        *,
        raw_jobs: list[dict[str, Any]],
        preferred_location: str,
        selected_position_types: list[str],
        posted_within_days: int,
    ) -> list[dict[str, Any]]:
        location_token = preferred_location.lower().strip()
        now = datetime.now(UTC)
        normalized_types = self._normalize_position_types(selected_position_types)
        type_keywords = self._position_keywords(normalized_types)

        filtered: list[dict[str, Any]] = []
        for job in raw_jobs:
            if not isinstance(job, dict):
                continue

            title = self._clean_text(job.get("title", ""))
            description = self._clean_text(job.get("description", ""))
            location = self._clean_text(job.get("candidate_required_location", ""))
            job_type = self._clean_text(job.get("job_type", ""))
            combined = " ".join([title, description, location, job_type]).lower()

            if location_token:
                if "remote" in location_token:
                    if "remote" not in combined and "anywhere" not in combined and "worldwide" not in combined:
                        continue
                elif location_token not in combined:
                    continue

            if posted_within_days > 0:
                posted = self._parse_datetime(job.get("publication_date"))
                if posted is None or (now - posted) > timedelta(days=posted_within_days):
                    continue

            if type_keywords and not any(keyword in combined for keyword in type_keywords):
                continue

            filtered.append(job)
        return filtered

    def _score_jobs(
        self,
        *,
        jobs: list[dict[str, Any]],
        role_query: str,
        resume_text: str,
        analysis: ResumeAnalysis | None,
        sponsorship_required: bool,
    ) -> list[CareersMatchResult]:
        role_tokens = self._tokenize(role_query)
        resume_tokens = self._resume_tokens(resume_text=resume_text, analysis=analysis)
        missing_points = self._missing_points(analysis)

        results: list[CareersMatchResult] = []
        for job in jobs:
            title = self._clean_text(job.get("title", "Untitled role"))
            company = self._clean_text(job.get("company_name", "Unknown company"))
            location = self._clean_text(job.get("candidate_required_location", "Location not listed"))
            apply_url = self._clean_text(job.get("url", "")) or None
            description = self._clean_text(job.get("description", ""))
            job_type = self._clean_text(job.get("job_type", ""))
            category = self._clean_text(job.get("category", ""))
            tags = [self._clean_text(item) for item in job.get("tags", []) if self._clean_text(item)]
            posted_at = self._parse_datetime(job.get("publication_date"))
            text_blob = " ".join([title, description, location, category, job_type, " ".join(tags)])
            job_tokens = self._tokenize(text_blob)

            role_relevance = self._role_relevance(role_tokens=role_tokens, title=title, job_tokens=job_tokens)
            resume_match = self._resume_match(resume_tokens=resume_tokens, job_tokens=job_tokens)
            sponsorship_status, sponsorship_confidence = self._sponsorship_signal(text_blob=text_blob)

            sponsorship_component = 100
            if sponsorship_required:
                if sponsorship_status == "Not Available":
                    sponsorship_component = 0
                elif sponsorship_status == "Unknown":
                    sponsorship_component = 45
                elif sponsorship_status == "Possible":
                    sponsorship_component = 68
                else:
                    sponsorship_component = 88

            overall_score = round((resume_match * 0.42) + (role_relevance * 0.38) + (sponsorship_component * 0.20))
            if sponsorship_required and sponsorship_status == "Not Available":
                overall_score -= 25
            if sponsorship_required and sponsorship_status == "Unknown":
                overall_score -= 10
            overall_score = max(0, min(100, int(overall_score)))

            reason = (
                f"Role relevance {role_relevance}%, resume alignment {resume_match}%, "
                f"sponsorship signal {sponsorship_status.lower()}."
            )
            position_tags = [item for item in [job_type, category, *tags[:3]] if item]

            results.append(
                CareersMatchResult(
                    external_id=str(job.get("id")) if job.get("id") is not None else None,
                    title=title,
                    company=company,
                    location=location,
                    posted_at=posted_at,
                    overall_score=overall_score,
                    resume_match_score=resume_match,
                    role_relevance=role_relevance,
                    sponsorship_status=sponsorship_status,
                    sponsorship_confidence=sponsorship_confidence,
                    reason=reason,
                    missing_points=missing_points,
                    apply_url=apply_url,
                    position_tags=position_tags,
                    source_provider="remotive",
                )
            )

        results.sort(key=lambda item: item.overall_score, reverse=True)
        return results

    def _build_company_links(self, *, role_query: str, preferred_location: str) -> list[CareersTopCompanyLink]:
        role_token = quote_plus(role_query or "software engineer")
        location_token = quote_plus(preferred_location or "")
        has_location = bool(preferred_location.strip())

        links: list[CareersTopCompanyLink] = []
        for company in PUBLIC_COMPANY_LINKS:
            if company == "Google":
                url = f"https://careers.google.com/jobs/results/?q={role_token}"
                if has_location:
                    url = f"{url}&location={location_token}"
            elif company == "Apple":
                url = f"https://jobs.apple.com/en-us/search?search={role_token}"
                if has_location:
                    url = f"{url}&location={location_token}"
            elif company == "Microsoft":
                url = f"https://jobs.careers.microsoft.com/global/en/search?q={role_token}"
                if has_location:
                    url = f"{url}&l={location_token}"
            elif company == "Amazon":
                url = f"https://www.amazon.jobs/en/search?base_query={role_token}"
                if has_location:
                    url = f"{url}&loc_query={location_token}"
            elif company == "Meta":
                url = f"https://www.metacareers.com/jobs/?q={role_token}"
            elif company == "NVIDIA":
                url = f"https://www.nvidia.com/en-us/about-nvidia/careers/?keyword={role_token}"
            elif company == "Adobe":
                url = f"https://careers.adobe.com/us/en/search-results?keywords={role_token}"
            else:
                url = f"https://careers.salesforce.com/en/jobs/?keywords={role_token}"
            links.append(CareersTopCompanyLink(name=company, url=url))
        return links

    def _resume_tokens(self, *, resume_text: str, analysis: ResumeAnalysis | None) -> set[str]:
        tokens = set(self._tokenize(resume_text)[:500])
        if analysis is not None:
            for skill in analysis.extracted_skills or []:
                for token in self._tokenize(str(skill)):
                    tokens.add(token)
        return tokens

    @staticmethod
    def _normalize_position_types(position_types: list[str]) -> list[str]:
        normalized: list[str] = []
        for item in position_types:
            clean = re.sub(r"[^a-z0-9\-\s]+", "", str(item or "").strip().lower())
            clean = clean.replace(" ", "-")
            if clean in POSITION_TYPE_KEYWORDS and clean not in normalized:
                normalized.append(clean)
        return normalized

    @staticmethod
    def _position_keywords(position_types: list[str]) -> set[str]:
        result: set[str] = set()
        for position_type in position_types:
            result.update(POSITION_TYPE_KEYWORDS.get(position_type, ()))
        return result

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except Exception:
            return None

    @staticmethod
    def _clean_text(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip())

    @staticmethod
    def _tokenize(value: str) -> list[str]:
        return re.findall(r"[a-z0-9]{2,}", str(value or "").lower())

    @staticmethod
    def _role_relevance(*, role_tokens: list[str], title: str, job_tokens: list[str]) -> int:
        if not role_tokens:
            return 0
        role_set = set(role_tokens)
        job_set = set(job_tokens)
        overlap = len(role_set.intersection(job_set))
        ratio = overlap / max(1, len(role_set))
        base = int(min(100, 25 + (ratio * 75)))
        title_lower = title.lower()
        if any(token in title_lower for token in role_tokens):
            base = min(100, base + 12)
        return max(0, min(100, base))

    @staticmethod
    def _resume_match(*, resume_tokens: set[str], job_tokens: list[str]) -> int:
        if not resume_tokens:
            return 48
        job_set = set(job_tokens)
        overlap = len(resume_tokens.intersection(job_set))
        ratio = overlap / max(1, min(len(resume_tokens), 180))
        return max(0, min(100, int(30 + (ratio * 260))))

    @staticmethod
    def _sponsorship_signal(*, text_blob: str) -> tuple[str, int]:
        lowered = text_blob.lower()
        negative_patterns = (
            "no sponsorship",
            "without sponsorship",
            "cannot sponsor",
            "not sponsor",
            "no visa",
        )
        positive_patterns = (
            "visa sponsorship",
            "sponsorship available",
            "sponsor h1b",
            "h-1b sponsorship",
            "immigration support",
        )
        possible_patterns = ("h1b", "h-1b", "visa", "work authorization")

        if any(pattern in lowered for pattern in negative_patterns):
            return "Not Available", 88
        if any(pattern in lowered for pattern in positive_patterns):
            return "Likely Available", 82
        if any(pattern in lowered for pattern in possible_patterns):
            return "Possible", 61
        return "Unknown", 35

    @staticmethod
    def _missing_points(analysis: ResumeAnalysis | None) -> list[str]:
        if analysis is not None:
            points = [str(item).strip() for item in (analysis.weaknesses or []) if str(item).strip()]
            points.extend(str(item).strip() for item in (analysis.suggestions or []) if str(item).strip())
            deduped: list[str] = []
            seen: set[str] = set()
            for point in points:
                key = point.lower()
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(point)
            if deduped:
                return deduped[:3]
        return [
            "Quantify impact with measurable outcomes in experience bullets.",
            "Align top skills with target-role keywords.",
            "Highlight production ownership and collaboration outcomes.",
        ]

