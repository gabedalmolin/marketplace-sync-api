import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_loads_valid_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = "postgresql+asyncpg://user:password@localhost:5432/test_database"

    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings(_env_file=None)

    assert settings.app_env == "test"
    assert str(settings.database_url) == database_url


def test_settings_rejects_invalid_app_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost:5432/test_database",
    )

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_requires_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_sewttings_rejects_invalid_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "not-a-database-url")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
