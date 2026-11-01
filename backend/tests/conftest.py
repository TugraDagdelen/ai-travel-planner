import pytest


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch):
    """Keep every test process isolated from the developer's persistent SQLite file."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
