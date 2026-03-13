from __future__ import annotations

from unittest.mock import Mock

from src.dto.auth_dto import PasswordResetInputDTO
from src.service.auth_service import AuthService, AuthServiceDependencies


def _build_service() -> tuple[AuthService, AuthServiceDependencies]:
    deps = AuthServiceDependencies(
        email_code_name="Secure Code",
        is_valid_email_address=Mock(return_value=True),
        can_send_email_otp=Mock(return_value=(True, "")),
        get_user_by_email=Mock(return_value={"id": 7, "email": "user@example.com"}),
        get_password_reset_resend_seconds=Mock(return_value=30),
        send_email_verification_otp=Mock(return_value=(True, "sent")),
        validate_password_strength=Mock(return_value=(True, "")),
        verify_email_verification_otp=Mock(return_value=(True, "")),
        hash_password=Mock(return_value="hashed_pw"),
        update_password_and_revoke_sessions=Mock(),
    )
    return AuthService(deps), deps


def test_send_password_reset_code_rejects_invalid_email() -> None:
    service, deps = _build_service()
    deps.is_valid_email_address.return_value = False

    result = service.send_password_reset_code("bad-email")

    assert result.ok is False
    assert result.message == "Enter a valid email address."
    deps.can_send_email_otp.assert_not_called()


def test_send_password_reset_code_surfaces_email_config_error() -> None:
    service, deps = _build_service()
    deps.can_send_email_otp.return_value = (False, "SMTP missing")

    result = service.send_password_reset_code("User@Example.com")

    assert result.ok is False
    assert result.message == "SMTP missing"
    deps.get_user_by_email.assert_not_called()


def test_send_password_reset_code_rejects_unknown_user() -> None:
    service, deps = _build_service()
    deps.get_user_by_email.return_value = None

    result = service.send_password_reset_code("User@Example.com")

    assert result.ok is False
    assert result.message == "Not an active user. Please create an account first."
    deps.send_email_verification_otp.assert_not_called()


def test_send_password_reset_code_returns_success_message() -> None:
    service, deps = _build_service()

    result = service.send_password_reset_code("User@Example.com")

    assert result.ok is True
    assert result.message == "Reset Secure Code sent to your email."
    deps.send_email_verification_otp.assert_called_once_with(
        7,
        "user@example.com",
        resend_seconds_override=30,
    )


def test_send_password_reset_code_returns_sender_error_message() -> None:
    service, deps = _build_service()
    deps.send_email_verification_otp.return_value = (False, "Rate limited")

    result = service.send_password_reset_code("user@example.com")

    assert result.ok is False
    assert result.message == "Rate limited"


def test_reset_password_with_code_rejects_invalid_email() -> None:
    service, deps = _build_service()
    deps.is_valid_email_address.return_value = False

    result = service.reset_password_with_code(
        PasswordResetInputDTO(
            email="bad",
            otp_code="123456",
            new_password="Strong@123",
            confirm_password="Strong@123",
        )
    )

    assert result.ok is False
    assert result.message == "Enter a valid email address."


def test_reset_password_with_code_rejects_password_mismatch() -> None:
    service, _ = _build_service()

    result = service.reset_password_with_code(
        PasswordResetInputDTO(
            email="user@example.com",
            otp_code="123456",
            new_password="Strong@123",
            confirm_password="Strong@321",
        )
    )

    assert result.ok is False
    assert result.message == "Passwords do not match."


def test_reset_password_with_code_rejects_weak_password() -> None:
    service, deps = _build_service()
    deps.validate_password_strength.return_value = (False, "Too weak")

    result = service.reset_password_with_code(
        PasswordResetInputDTO(
            email="user@example.com",
            otp_code="123456",
            new_password="weak",
            confirm_password="weak",
        )
    )

    assert result.ok is False
    assert result.message == "Too weak"
    deps.get_user_by_email.assert_not_called()


def test_reset_password_with_code_rejects_unknown_user() -> None:
    service, deps = _build_service()
    deps.get_user_by_email.return_value = None

    result = service.reset_password_with_code(
        PasswordResetInputDTO(
            email="user@example.com",
            otp_code="123456",
            new_password="Strong@123",
            confirm_password="Strong@123",
        )
    )

    assert result.ok is False
    assert result.message == "Invalid reset request. Check your email and secure code."


def test_reset_password_with_code_returns_otp_error() -> None:
    service, deps = _build_service()
    deps.verify_email_verification_otp.return_value = (False, "OTP invalid")

    result = service.reset_password_with_code(
        PasswordResetInputDTO(
            email="user@example.com",
            otp_code="654321",
            new_password="Strong@123",
            confirm_password="Strong@123",
        )
    )

    assert result.ok is False
    assert result.message == "OTP invalid"
    deps.update_password_and_revoke_sessions.assert_not_called()


def test_reset_password_with_code_updates_password_on_success() -> None:
    service, deps = _build_service()

    result = service.reset_password_with_code(
        PasswordResetInputDTO(
            email="USER@EXAMPLE.COM",
            otp_code="111222",
            new_password="Strong@123",
            confirm_password="Strong@123",
        )
    )

    assert result.ok is True
    assert result.message == "Password reset successful. Please log in with your new password."
    deps.verify_email_verification_otp.assert_called_once_with(7, "user@example.com", "111222")
    deps.hash_password.assert_called_once_with("Strong@123")
    deps.update_password_and_revoke_sessions.assert_called_once_with(7, "hashed_pw")
