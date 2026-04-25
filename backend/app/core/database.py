from app.core.config import settings


async def get_db():
    """FastAPI dependency that returns the appropriate database object.
    Supabase (SQLAlchemy session) or MongoDB (Motor database).
    """
    if settings.use_supabase:
        from app.core.database_sql import get_sql_session
        async for session in get_sql_session():
            yield session
    else:
        from app.core.database_mongo import get_mongo_db
        db = await get_mongo_db()
        yield db


async def connect_to_database():
    if settings.use_supabase:
        from app.core.database_sql import get_sql_engine
        engine = get_sql_engine()
        async with engine.connect() as conn:
            await conn.run_sync(lambda: None)
        print("Connected to Supabase PostgreSQL")
    else:
        from app.core.database_mongo import connect_to_mongo
        await connect_to_mongo()


async def close_database():
    if settings.use_supabase:
        from app.core.database_sql import close_sql_engine
        await close_sql_engine()
        print("Disconnected from Supabase")
    else:
        from app.core.database_mongo import close_mongo_connection
        await close_mongo_connection()
