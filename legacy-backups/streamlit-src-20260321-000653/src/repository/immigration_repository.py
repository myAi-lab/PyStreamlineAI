from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from src.dto.immigration_dto import ImmigrationArticleDTO, ImmigrationSearchInputDTO


class ImmigrationRepository:
    """Persistence layer for immigration updates and fetch metadata."""

    def __init__(self, db_connect: Callable[[], Any]) -> None:
        self._db_connect = db_connect

    def get_setting(self, setting_key: str) -> str:
        cleaned_key = str(setting_key or "").strip()
        if not cleaned_key:
            return ""
        conn = self._db_connect()
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                """
                SELECT setting_value
                FROM app_settings
                WHERE setting_key = ?
                LIMIT 1
                """,
                (cleaned_key,),
            ).fetchone()
            if row is None:
                return ""
            if isinstance(row, dict):
                return str(row.get("setting_value", "") or "").strip()
            return str(row[0] or "").strip()
        finally:
            conn.close()

    def set_setting(self, setting_key: str, setting_value: str) -> None:
        cleaned_key = str(setting_key or "").strip()
        if not cleaned_key:
            return
        cleaned_value = str(setting_value or "").strip()
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = self._db_connect()
        try:
            conn.execute(
                """
                INSERT INTO app_settings (setting_key, setting_value, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET
                    setting_value = excluded.setting_value,
                    updated_at = excluded.updated_at
                """,
                (cleaned_key, cleaned_value, now_iso, now_iso),
            )
            conn.commit()
        finally:
            conn.close()

    def upsert_articles(self, articles: list[ImmigrationArticleDTO]) -> tuple[int, int, int]:
        if not articles:
            return 0, 0, 0
        now_iso = datetime.now(timezone.utc).isoformat()
        inserted = 0
        updated = 0
        skipped = 0
        conn = self._db_connect()
        conn.row_factory = sqlite3.Row
        try:
            for article in articles:
                link = str(article.link or "").strip()
                title = str(article.title or "").strip()
                if not link or not title:
                    skipped += 1
                    continue

                existing = conn.execute(
                    """
                    SELECT id, content_hash, title, summary, visa_category, tags
                    FROM immigration_updates
                    WHERE link = ?
                    LIMIT 1
                    """,
                    (link,),
                ).fetchone()
                tags_csv = ",".join(self._normalize_tags(article.tags))
                summary = str(article.summary or "").strip()
                visa_category = str(article.visa_category or "").strip() or "General"
                published_date = str(article.published_date or "").strip() or now_iso
                original_text = str(article.original_text or "").strip()
                content_hash = str(article.content_hash or "").strip()
                source = str(article.source or "").strip() or "Unknown Source"

                if existing is None:
                    conn.execute(
                        """
                        INSERT INTO immigration_updates (
                            title, summary, source, link, visa_category, published_date, tags,
                            original_text, content_hash, created_at, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            title,
                            summary,
                            source,
                            link,
                            visa_category,
                            published_date,
                            tags_csv,
                            original_text,
                            content_hash,
                            now_iso,
                            now_iso,
                        ),
                    )
                    inserted += 1
                    continue

                existing_hash = str(self._row_value(existing, "content_hash", "") or "").strip()
                existing_summary = str(self._row_value(existing, "summary", "") or "").strip()
                existing_title = str(self._row_value(existing, "title", "") or "").strip()
                existing_category = str(self._row_value(existing, "visa_category", "") or "").strip()
                existing_tags = str(self._row_value(existing, "tags", "") or "").strip()
                needs_update = any(
                    [
                        content_hash and existing_hash != content_hash,
                        summary and summary != existing_summary,
                        title != existing_title,
                        visa_category != existing_category,
                        tags_csv != existing_tags,
                    ]
                )
                if not needs_update:
                    skipped += 1
                    continue

                conn.execute(
                    """
                    UPDATE immigration_updates
                    SET
                        title = ?,
                        summary = ?,
                        source = ?,
                        visa_category = ?,
                        published_date = ?,
                        tags = ?,
                        original_text = ?,
                        content_hash = ?,
                        updated_at = ?
                    WHERE link = ?
                    """,
                    (
                        title,
                        summary,
                        source,
                        visa_category,
                        published_date,
                        tags_csv,
                        original_text,
                        content_hash,
                        now_iso,
                        link,
                    ),
                )
                updated += 1
            conn.commit()
        finally:
            conn.close()
        return inserted, updated, skipped

    def search_updates(self, search_input: ImmigrationSearchInputDTO) -> list[dict[str, Any]]:
        limit = max(1, min(100, int(search_input.limit or 30)))
        offset = max(0, int(search_input.offset or 0))
        query = re.sub(r"\s+", " ", str(search_input.query or "").strip())
        visa_categories = [str(item).strip() for item in search_input.visa_categories if str(item).strip()]

        conn = self._db_connect()
        conn.row_factory = sqlite3.Row
        try:
            where_parts = ["1=1"]
            params: list[Any] = []

            if visa_categories:
                placeholders = ", ".join(["?"] * len(visa_categories))
                where_parts.append(f"visa_category IN ({placeholders})")
                params.extend(visa_categories)

            if query:
                if str(getattr(conn, "backend", "")).lower() == "postgres":
                    where_parts.append(
                        "to_tsvector('english', coalesce(title,'') || ' ' || coalesce(summary,'') || ' ' || coalesce(tags,'')) "
                        "@@ plainto_tsquery('english', ?)"
                    )
                    params.append(query)
                else:
                    pattern = f"%{query}%"
                    where_parts.append("(title LIKE ? OR summary LIKE ? OR tags LIKE ?)")
                    params.extend([pattern, pattern, pattern])

            sql = (
                """
                SELECT id, title, summary, source, link, visa_category, published_date, tags, created_at, updated_at
                FROM immigration_updates
                WHERE """
                + " AND ".join(where_parts)
                + """
                ORDER BY published_date DESC, created_at DESC
                LIMIT ? OFFSET ?
                """
            )
            params.extend([limit, offset])
            rows = conn.execute(sql, tuple(params)).fetchall()
            return [self._normalize_row(row) for row in rows]
        finally:
            conn.close()

    def list_recent_alerts(self, lookback_hours: int = 72, limit: int = 8) -> list[dict[str, Any]]:
        safe_hours = max(1, min(24 * 14, int(lookback_hours or 72)))
        threshold = datetime.now(timezone.utc) - timedelta(hours=safe_hours)
        threshold_iso = threshold.isoformat()
        conn = self._db_connect()
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT id, title, summary, source, link, visa_category, published_date, tags, created_at, updated_at
                FROM immigration_updates
                WHERE published_date >= ?
                ORDER BY published_date DESC
                LIMIT ?
                """,
                (threshold_iso, max(1, min(50, int(limit or 8)))),
            ).fetchall()
            return [self._normalize_row(row) for row in rows]
        finally:
            conn.close()

    def cleanup_noise_entries(self) -> int:
        conn = self._db_connect()
        try:
            cursor = conn.execute(
                """
                DELETE FROM immigration_updates
                WHERE source = ?
                  AND (
                    title = ?
                    OR title = ?
                    OR title = ?
                  )
                """,
                (
                    "US Department of State Visa Bulletin",
                    "Skip to main content",
                    "The Visa Bulletin",
                    "Visa Bulletin Update",
                ),
            )
            conn.commit()
            return int(getattr(cursor, "rowcount", 0) or 0)
        finally:
            conn.close()

    @staticmethod
    def _row_value(row: Any, key: str, default: Any = None) -> Any:
        if isinstance(row, dict):
            return row.get(key, default)
        if hasattr(row, "__getitem__"):
            try:
                return row[key]
            except Exception:
                return default
        return default

    @staticmethod
    def _normalize_tags(tags: tuple[str, ...] | list[str] | str) -> list[str]:
        if isinstance(tags, str):
            raw_items = [item.strip() for item in tags.split(",")]
        else:
            raw_items = [str(item).strip() for item in list(tags)]
        deduped: list[str] = []
        seen: set[str] = set()
        for item in raw_items:
            if not item:
                continue
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item[:60])
        return deduped[:12]

    def _normalize_row(self, row: Any) -> dict[str, Any]:
        tags_raw = str(self._row_value(row, "tags", "") or "").strip()
        return {
            "id": int(self._row_value(row, "id", 0) or 0),
            "title": str(self._row_value(row, "title", "") or "").strip(),
            "summary": str(self._row_value(row, "summary", "") or "").strip(),
            "source": str(self._row_value(row, "source", "") or "").strip(),
            "link": str(self._row_value(row, "link", "") or "").strip(),
            "visa_category": str(self._row_value(row, "visa_category", "") or "").strip(),
            "published_date": str(self._row_value(row, "published_date", "") or "").strip(),
            "tags": self._normalize_tags(tags_raw),
            "created_at": str(self._row_value(row, "created_at", "") or "").strip(),
            "updated_at": str(self._row_value(row, "updated_at", "") or "").strip(),
        }
