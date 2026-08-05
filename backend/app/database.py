from collections.abc import AsyncGenerator
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _to_asyncpg_url(raw_url: str) -> str:
    """Neon gives a libpq-style DSN (postgresql://...?sslmode=require&channel_binding=require).
    asyncpg doesn't understand those query params, so we strip them and enforce TLS via connect_args instead.
    """
    parts = urlsplit(raw_url)
    scheme = "postgresql+asyncpg"
    return urlunsplit((scheme, parts.netloc, parts.path, "", ""))


engine = create_async_engine(
    _to_asyncpg_url(settings.database_url),
    connect_args={"ssl": True},
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
