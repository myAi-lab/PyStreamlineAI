from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ImmigrationArticleDTO:
    title: str
    summary: str
    source: str
    link: str
    visa_category: str
    published_date: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    original_text: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class ImmigrationSearchInputDTO:
    query: str = ""
    visa_categories: tuple[str, ...] = field(default_factory=tuple)
    limit: int = 30
    offset: int = 0


@dataclass(frozen=True)
class ImmigrationRefreshResultDTO:
    refreshed: bool
    message: str
    fetched_count: int = 0
    inserted_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0

