from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
import hashlib
import html
import re
from xml.etree import ElementTree as ET

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository
from app.schemas.immigration import (
    ImmigrationBriefRequest,
    ImmigrationBriefResponse,
    ImmigrationRefreshResponse,
    ImmigrationSearchRequest,
    ImmigrationSearchResponse,
    ImmigrationUpdateResponse,
)


@dataclass(frozen=True)
class ImmigrationSource:
    name: str
    source_type: str
    url: str


IMMIGRATION_CATEGORIES = ["H1B", "F1", "OPT", "STEM OPT", "Visa Bulletin", "Green Card", "General"]


class ImmigrationService:
    _cache_items: list[ImmigrationUpdateResponse] = []
    _cache_refreshed_at: datetime | None = None
    _cache_ttl_minutes = 45

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_repo = AuditRepository(session)
        self.sources = [
            ImmigrationSource(
                name="USCIS Alerts",
                source_type="html_uscis",
                url="https://www.uscis.gov/newsroom/alerts",
            ),
            ImmigrationSource(
                name="USCIS News Releases",
                source_type="html_uscis",
                url="https://www.uscis.gov/newsroom/news-releases",
            ),
            ImmigrationSource(
                name="DOS Visa Bulletin",
                source_type="html_visa_bulletin",
                url="https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html",
            ),
            ImmigrationSource(
                name="Study in the States (DHS)",
                source_type="rss",
                url="https://studyinthestates.dhs.gov/rss.xml",
            ),
        ]

    async def refresh(self, *, force: bool = False) -> ImmigrationRefreshResponse:
        now = datetime.now(UTC)
        if (
            not force
            and self.__class__._cache_refreshed_at is not None
            and now - self.__class__._cache_refreshed_at < timedelta(minutes=self.__class__._cache_ttl_minutes)
        ):
            return ImmigrationRefreshResponse(
                refreshed=False,
                fetched_count=len(self.__class__._cache_items),
                message="Immigration feed cache is still fresh.",
                last_refreshed_at=self.__class__._cache_refreshed_at,
            )

        rows: list[dict[str, Any]] = []
        for source in self.sources:
            text = await self._fetch_text(source.url)
            if not text:
                continue
            if source.source_type == "rss":
                rows.extend(self._parse_rss(source_name=source.name, source_url=source.url, payload=text))
            elif source.source_type == "html_uscis":
                rows.extend(self._parse_uscis_html(source_name=source.name, source_url=source.url, payload=text))
            else:
                rows.extend(
                    self._parse_visa_bulletin_html(source_name=source.name, source_url=source.url, payload=text)
                )

        deduped: list[ImmigrationUpdateResponse] = []
        seen_links: set[str] = set()
        for item in rows:
            title = self._clean(item.get("title", ""))
            link = self._clean(item.get("link", ""))
            if not title or not link:
                continue
            if link in seen_links:
                continue
            seen_links.add(link)
            category, tags = self._categorize(item)
            summary = self._summarize(title=title, raw_text=self._clean(item.get("summary", "")), category=category)
            published_date = self._parse_dt(item.get("published_date")) or now
            source_name = self._clean(item.get("source", "")) or "Unknown Source"
            source_url = self._clean(item.get("source_url", "")) or None
            digest = hashlib.sha256(f"{title}|{link}|{source_name}".encode("utf-8")).hexdigest()[:18]
            deduped.append(
                ImmigrationUpdateResponse(
                    id=digest,
                    title=title,
                    summary=summary,
                    source=source_name,
                    source_url=source_url,
                    link=link,
                    visa_category=category,
                    published_date=published_date,
                    tags=tags[:8],
                )
            )

        deduped.sort(key=lambda item: item.published_date or datetime(1970, 1, 1, tzinfo=UTC), reverse=True)
        self.__class__._cache_items = deduped
        self.__class__._cache_refreshed_at = now
        return ImmigrationRefreshResponse(
            refreshed=True,
            fetched_count=len(deduped),
            message="Immigration feeds refreshed successfully.",
            last_refreshed_at=now,
        )

    async def search(self, *, user_id, payload: ImmigrationSearchRequest) -> ImmigrationSearchResponse:
        if payload.force_refresh or not self.__class__._cache_items:
            await self.refresh(force=payload.force_refresh)
        updates = self.__class__._cache_items

        clean_query = self._clean(payload.query).lower()
        categories = [item for item in payload.visa_categories if item in IMMIGRATION_CATEGORIES]
        if clean_query:
            filtered = [
                item
                for item in updates
                if clean_query
                in " ".join(
                    [
                        item.title,
                        item.summary,
                        item.source,
                        item.visa_category,
                        " ".join(item.tags),
                    ]
                ).lower()
            ]
        else:
            filtered = list(updates)

        if categories:
            filtered = [item for item in filtered if item.visa_category in categories]

        response = ImmigrationSearchResponse(
            updates=filtered[: payload.limit],
            categories=list(IMMIGRATION_CATEGORIES),
            live_note=(
                "Results are aggregated from official/public immigration sources and summarized for quick review."
            ),
            last_refreshed_at=self.__class__._cache_refreshed_at,
        )

        await self.audit_repo.create(
            AuditLog(
                entity_type="immigration_search",
                entity_id=str(user_id),
                event_type="immigration_query_executed",
                payload={
                    "query": clean_query,
                    "categories": categories,
                    "limit": payload.limit,
                    "results_count": len(response.updates),
                },
            )
        )
        await self.session.commit()
        return response

    async def build_brief(self, *, user_id, payload: ImmigrationBriefRequest) -> ImmigrationBriefResponse:
        search_response = await self.search(
            user_id=user_id,
            payload=ImmigrationSearchRequest(
                query=payload.query,
                visa_categories=payload.visa_categories,
                limit=payload.limit,
                force_refresh=False,
            ),
        )
        top = search_response.updates[: payload.limit]
        if not top:
            return ImmigrationBriefResponse(
                brief=(
                    "No matching immigration updates were found for the current filter. "
                    "Try terms like H1B registration, STEM OPT, or visa bulletin."
                ),
                generated_at=datetime.now(UTC),
            )

        summary_line = (
            f'Latest immigration signal for "{self._clean(payload.query) or "all updates"}": '
            f"{top[0].title} ({top[0].source})."
        )
        bullets = []
        for row in top[:3]:
            date_label = row.published_date.date().isoformat() if row.published_date else "unknown date"
            bullets.append(f"- {row.title} [{row.visa_category}] ({date_label})")
        brief = (
            summary_line
            + "\n\nKey updates:\n"
            + "\n".join(bullets)
            + "\n\nNext step: validate date-sensitive guidance from the source link before acting."
        )
        return ImmigrationBriefResponse(brief=brief, generated_at=datetime.now(UTC))

    async def _fetch_text(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url)
            if response.status_code >= 400:
                return ""
            return response.text
        except Exception:
            return ""

    def _parse_rss(self, *, source_name: str, source_url: str, payload: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        try:
            root = ET.fromstring(payload)
        except Exception:
            return rows

        for item in root.findall(".//item"):
            title = self._clean(self._node_text(item, "title"))
            link = self._clean(self._node_text(item, "link"))
            summary = self._clean(self._node_text(item, "description"))
            published = self._clean(self._node_text(item, "pubDate")) or self._clean(self._node_text(item, "updated"))
            if not title or not link:
                continue
            rows.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published_date": published,
                    "source": source_name,
                    "source_url": source_url,
                }
            )
            if len(rows) >= 80:
                break
        return rows

    def _parse_uscis_html(self, *, source_name: str, source_url: str, payload: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        pattern = re.compile(
            r'<a[^>]+href="(?P<href>/newsroom/(?:alerts|news-releases)/[^"#?]+)"[^>]*>(?P<title>.*?)</a>',
            flags=re.IGNORECASE,
        )
        for match in pattern.finditer(payload):
            link = self._resolve_link(source_url, match.group("href"))
            title = self._strip_html(match.group("title"))
            if not title or not link:
                continue
            rows.append(
                {
                    "title": title,
                    "link": link,
                    "summary": title,
                    "published_date": datetime.now(UTC).isoformat(),
                    "source": source_name,
                    "source_url": source_url,
                }
            )
            if len(rows) >= 120:
                break
        return rows

    def _parse_visa_bulletin_html(
        self,
        *,
        source_name: str,
        source_url: str,
        payload: str,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        pattern = re.compile(
            r'<a[^>]+href="(?P<href>/content/travel/en/legal/visa-law0/visa-bulletin/[^"#?]+\.html)"[^>]*>'
            r"(?P<title>.*?)</a>",
            flags=re.IGNORECASE,
        )
        for match in pattern.finditer(payload):
            link = self._resolve_link(source_url, match.group("href"))
            title = self._strip_html(match.group("title"))
            if not title or not link:
                continue
            rows.append(
                {
                    "title": title,
                    "link": link,
                    "summary": title,
                    "published_date": datetime.now(UTC).isoformat(),
                    "source": source_name,
                    "source_url": source_url,
                }
            )
            if len(rows) >= 60:
                break
        return rows

    def _categorize(self, item: dict[str, Any]) -> tuple[str, list[str]]:
        corpus = " ".join(
            [
                self._clean(item.get("title", "")).lower(),
                self._clean(item.get("summary", "")).lower(),
                self._clean(item.get("link", "")).lower(),
                self._clean(item.get("source", "")).lower(),
            ]
        )
        patterns: list[tuple[str, tuple[str, ...]]] = [
            ("H1B", ("h1b", "h-1b", "cap registration", "lottery")),
            ("STEM OPT", ("stem opt", "i-983", "24-month extension")),
            ("OPT", ("opt", "optional practical training")),
            ("F1", ("f1", "f-1", "sevis", "international student")),
            ("Visa Bulletin", ("visa bulletin", "priority date", "dates for filing")),
            ("Green Card", ("green card", "i-485", "adjustment of status", "permanent resident")),
        ]
        category = "General"
        matched_tags: list[str] = []
        for candidate, keywords in patterns:
            if any(keyword in corpus for keyword in keywords):
                if category == "General":
                    category = candidate
                matched_tags.extend(keywords[:2])
        tags = [category, "US-immigration", self._clean(item.get("source", ""))]
        tags.extend(tag for tag in matched_tags if tag)
        deduped: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            clean = self._clean(tag)
            if not clean:
                continue
            key = clean.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(clean)
        return category, deduped[:8]

    @staticmethod
    def _summarize(*, title: str, raw_text: str, category: str) -> str:
        cleaned = re.sub(r"\s+", " ", raw_text).strip()
        if not cleaned:
            cleaned = title
        sentence_match = re.match(r"(.{40,260}?[.!?])(\s|$)", cleaned)
        snippet = sentence_match.group(1).strip() if sentence_match else cleaned[:220].strip()
        if category and category != "General":
            return f"{snippet} ({category})"
        return snippet

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except Exception:
            pass
        try:
            parsed_email = parsedate_to_datetime(raw)
            if parsed_email.tzinfo is None:
                parsed_email = parsed_email.replace(tzinfo=UTC)
            return parsed_email.astimezone(UTC)
        except Exception:
            return None

    @staticmethod
    def _clean(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip())

    @staticmethod
    def _node_text(node: ET.Element, name: str) -> str:
        direct = node.find(name)
        if direct is not None and str(direct.text or "").strip():
            return str(direct.text or "").strip()
        atom = node.find(f"{{http://www.w3.org/2005/Atom}}{name}")
        if atom is not None and str(atom.text or "").strip():
            return str(atom.text or "").strip()
        return ""

    @staticmethod
    def _strip_html(raw_html: str) -> str:
        cleaned = re.sub(r"<script[\s\S]*?</script>", " ", str(raw_html or ""), flags=re.IGNORECASE)
        cleaned = re.sub(r"<style[\s\S]*?</style>", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = html.unescape(cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def _resolve_link(base_url: str, href: str) -> str:
        raw = str(href or "").strip()
        if not raw:
            return ""
        if raw.lower().startswith(("http://", "https://")):
            return raw
        base = str(base_url or "").strip().rstrip("/")
        if raw.startswith("/"):
            match = re.match(r"^(https?://[^/]+)", base, flags=re.IGNORECASE)
            if match:
                return f"{match.group(1)}{raw}"
            return f"{base}{raw}"
        return f"{base}/{raw}"

