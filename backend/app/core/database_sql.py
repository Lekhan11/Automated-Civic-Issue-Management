from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

_engine = None
_session_maker = None


def get_sql_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.supabase_db_url,
            echo=False,
            pool_pre_ping=True,
        )
    return _engine


def get_sql_session_maker():
    global _session_maker
    if _session_maker is None:
        engine = get_sql_engine()
        _session_maker = async_sessionmaker(
            engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_maker


async def get_sql_session():
    session_maker = get_sql_session_maker()
    async with session_maker() as session:
        yield session


async def close_sql_engine():
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
