"""
HomeGuard Database Connection Module
Async SQLAlchemy engine with connection pooling.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event


def get_database_url() -> str:
    """Construct async DATABASE_URL from environment."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://homeguard:homeguard@db:5432/homeguard"
    )


# Create async engine with connection pooling
engine = create_async_engine(
    get_database_url(),
    pool_size=int(os.environ.get("DB_POOL_SIZE", "10")),
    max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "20")),
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.environ.get("DB_ECHO", "false").lower() == "true",
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base model for all SQLAlchemy models."""
    # metadata.schema is set per-model to support multi-schema
    pass


async def get_db():
    """Dependency for FastAPI: yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (development only - use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database engine."""
    await engine.dispose()