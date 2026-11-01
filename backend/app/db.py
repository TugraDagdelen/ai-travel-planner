from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def create_database(url: str):
    options = {"check_same_thread": False} if url.startswith("sqlite") else {}
    kwargs = {"connect_args": options}
    if url.endswith(":memory:"):
        kwargs["poolclass"] = StaticPool
    elif url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, **kwargs)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)
