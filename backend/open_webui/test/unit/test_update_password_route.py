import asyncio
from types import SimpleNamespace

from open_webui.models.auths import UpdatePasswordForm
from open_webui.routers import auths


def test_update_password_allows_reset_without_current_password(monkeypatch):
    calls = {
        "authenticate_user": 0,
        "validate_password": [],
        "update_user_password_by_id": [],
    }

    def fake_authenticate_user(*args, **kwargs):
        calls["authenticate_user"] += 1
        return None

    def fake_validate_password(password):
        calls["validate_password"].append(password)
        return True

    def fake_get_password_hash(password):
        return f"hashed::{password}"

    def fake_update_user_password_by_id(user_id, new_password, db=None):
        calls["update_user_password_by_id"].append((user_id, new_password))
        return True

    monkeypatch.setattr(auths, "WEBUI_AUTH_TRUSTED_EMAIL_HEADER", None)
    monkeypatch.setattr(auths.Auths, "authenticate_user", fake_authenticate_user)
    monkeypatch.setattr(auths, "validate_password", fake_validate_password)
    monkeypatch.setattr(auths, "get_password_hash", fake_get_password_hash)
    monkeypatch.setattr(
        auths.Auths, "update_user_password_by_id", fake_update_user_password_by_id
    )

    result = asyncio.run(
        auths.update_password(
            UpdatePasswordForm(new_password="new-password"),
            session_user=SimpleNamespace(id="user-1", email="boss@hujiao.cn"),
            db=None,
        )
    )

    assert result is True
    assert calls["authenticate_user"] == 0
    assert calls["validate_password"] == ["new-password"]
    assert calls["update_user_password_by_id"] == [("user-1", "hashed::new-password")]
