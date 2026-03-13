from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Callable

from src.repository.auth_repository import AuthRepository


def _make_db_connect(tmp_path: Path) -> Callable[[], sqlite3.Connection]:
    db_path = tmp_path / "auth_repo_test.db"

    def _connect() -> sqlite3.Connection:
        return sqlite3.connect(str(db_path))

    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                email TEXT UNIQUE,
                role TEXT,
                years_experience TEXT,
                created_at TEXT,
                email_verified_at TEXT,
                password_hash TEXT,
                updated_at TEXT,
                last_login_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE auth_sessions (
                user_id INTEGER,
                token_hash TEXT,
                created_at TEXT,
                expires_at TEXT,
                last_seen_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE user_login_events (
                user_id INTEGER,
                login_method TEXT,
                login_provider TEXT,
                login_at TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    return _connect


def _insert_user(
    db_connect: Callable[[], sqlite3.Connection],
    *,
    full_name: str = "Test User",
    email: str = "user@example.com",
    role: str = "candidate",
    years_experience: str = "5",
    created_at: str = "2026-01-01T00:00:00+00:00",
    email_verified_at: str = "2026-01-01T00:00:00+00:00",
    password_hash: str = "stored_hash",
) -> int:
    conn = db_connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO users (
                full_name, email, role, years_experience, created_at, email_verified_at, password_hash, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                full_name,
                email,
                role,
                years_experience,
                created_at,
                email_verified_at,
                password_hash,
                created_at,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def test_authenticate_user_returns_none_for_unknown_user(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    repo = AuthRepository(db_connect)

    result = repo.authenticate_user(
        "missing@example.com",
        "pw",
        verify_password=lambda raw, stored: raw == stored,
        is_modern_password_hash=lambda _: True,
        hash_password=lambda raw: f"hash:{raw}",
    )

    assert result is None


def test_authenticate_user_returns_none_for_bad_password(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    _insert_user(db_connect, password_hash="expected_hash")
    repo = AuthRepository(db_connect)

    result = repo.authenticate_user(
        "user@example.com",
        "wrong_pw",
        verify_password=lambda raw, stored: raw == stored,
        is_modern_password_hash=lambda _: True,
        hash_password=lambda raw: f"hash:{raw}",
    )

    assert result is None


def test_authenticate_user_returns_pending_verification_payload(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    _insert_user(db_connect, email_verified_at="")
    repo = AuthRepository(db_connect)

    result = repo.authenticate_user(
        "user@example.com",
        "stored_hash",
        verify_password=lambda raw, stored: raw == stored,
        is_modern_password_hash=lambda _: True,
        hash_password=lambda raw: f"hash:{raw}",
    )

    assert result is not None
    assert result["pending_verification"] is True
    assert result["email"] == "user@example.com"
    assert "role" not in result


def test_authenticate_user_returns_verified_user_payload(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    _insert_user(db_connect, role="Recruiter", years_experience="9")
    repo = AuthRepository(db_connect)

    result = repo.authenticate_user(
        "user@example.com",
        "stored_hash",
        verify_password=lambda raw, stored: raw == stored,
        is_modern_password_hash=lambda _: True,
        hash_password=lambda raw: f"hash:{raw}",
    )

    assert result is not None
    assert result["pending_verification"] if "pending_verification" in result else False is False
    assert result["role"] == "Recruiter"
    assert result["years_experience"] == "9"


def test_authenticate_user_upgrades_legacy_hash(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    user_id = _insert_user(db_connect, password_hash="legacy_hash")
    repo = AuthRepository(db_connect)

    _ = repo.authenticate_user(
        "user@example.com",
        "plain_pw",
        verify_password=lambda raw, stored: raw == "plain_pw" and stored == "legacy_hash",
        is_modern_password_hash=lambda _: False,
        hash_password=lambda raw: f"modern:{raw}",
    )

    conn = db_connect()
    try:
        row = conn.execute("SELECT password_hash, updated_at FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row[0] == "modern:plain_pw"
    assert str(row[1]).strip() != ""


def test_get_user_by_email_handles_empty_and_returns_normalized_email(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    _insert_user(db_connect, email="user@example.com")
    repo = AuthRepository(db_connect)

    assert repo.get_user_by_email("") is None
    assert repo.get_user_by_email("missing@example.com") is None
    result = repo.get_user_by_email("  USER@EXAMPLE.COM ")

    assert result is not None
    assert result["email"] == "user@example.com"
    assert result["full_name"] == "Test User"


def test_update_password_and_revoke_sessions_updates_user_and_clears_sessions(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    user_id = _insert_user(db_connect, password_hash="old_hash")
    repo = AuthRepository(db_connect)
    conn = db_connect()
    try:
        conn.execute(
            "INSERT INTO auth_sessions (user_id, token_hash, created_at, expires_at, last_seen_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, "abc", "2026-01-01T00:00:00+00:00", "2999-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        )
        conn.commit()
    finally:
        conn.close()

    repo.update_password_and_revoke_sessions(user_id, "new_hash")

    conn = db_connect()
    try:
        user_row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
        session_rows = conn.execute("SELECT COUNT(*) FROM auth_sessions WHERE user_id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    assert user_row is not None
    assert user_row[0] == "new_hash"
    assert session_rows is not None
    assert int(session_rows[0]) == 0


def test_update_password_and_revoke_sessions_noop_for_invalid_user(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    repo = AuthRepository(db_connect)

    repo.update_password_and_revoke_sessions(0, "ignored")

    conn = db_connect()
    try:
        rows = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    finally:
        conn.close()
    assert rows is not None
    assert int(rows[0]) == 0


def test_record_user_login_event_inserts_event_and_updates_user(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    user_id = _insert_user(db_connect)
    repo = AuthRepository(db_connect)

    repo.record_user_login_event(user_id, "PASSWORD", "LOCAL")

    conn = db_connect()
    try:
        event = conn.execute(
            "SELECT login_method, login_provider, login_at FROM user_login_events WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        user_row = conn.execute("SELECT last_login_at FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    assert event is not None
    assert event[0] == "password"
    assert event[1] == "local"
    assert str(event[2]).strip() != ""
    assert user_row is not None
    assert str(user_row[0]).strip() != ""


def test_create_auth_session_persists_hash_and_revoke_by_raw_token(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    user_id = _insert_user(db_connect)
    repo = AuthRepository(db_connect)
    conn = db_connect()
    try:
        conn.execute(
            "INSERT INTO auth_sessions (user_id, token_hash, created_at, expires_at, last_seen_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, "expired", "2020-01-01T00:00:00+00:00", "2020-01-02T00:00:00+00:00", "2020-01-01T00:00:00+00:00"),
        )
        conn.commit()
    finally:
        conn.close()

    raw_token = repo.create_auth_session(user_id, ttl_days=3)

    assert raw_token
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    conn = db_connect()
    try:
        row = conn.execute(
            "SELECT token_hash FROM auth_sessions WHERE token_hash = ?",
            (expected_hash,),
        ).fetchone()
        expired_left = conn.execute(
            "SELECT COUNT(*) FROM auth_sessions WHERE token_hash = 'expired'",
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert expired_left is not None
    assert int(expired_left[0]) == 0

    repo.revoke_auth_session(raw_token)
    conn = db_connect()
    try:
        after = conn.execute(
            "SELECT COUNT(*) FROM auth_sessions WHERE token_hash = ?",
            (expected_hash,),
        ).fetchone()
    finally:
        conn.close()
    assert after is not None
    assert int(after[0]) == 0


def test_create_auth_session_invalid_user_returns_empty(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    repo = AuthRepository(db_connect)

    assert repo.create_auth_session(0) == ""


def test_record_login_and_revoke_noop_paths_for_invalid_inputs(tmp_path: Path) -> None:
    db_connect = _make_db_connect(tmp_path)
    repo = AuthRepository(db_connect)

    repo.record_user_login_event(0, "password")
    repo.revoke_auth_session("")

    conn = db_connect()
    try:
        events = conn.execute("SELECT COUNT(*) FROM user_login_events").fetchone()
        sessions = conn.execute("SELECT COUNT(*) FROM auth_sessions").fetchone()
    finally:
        conn.close()
    assert events is not None and int(events[0]) == 0
    assert sessions is not None and int(sessions[0]) == 0
