"""Database utilities for prediction analytics."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from prediction_analytics.config import settings


def get_engine():
    """Create a SQLAlchemy engine for Bentley_Bot."""
    url = (
        f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def get_session_factory():
    """Return a configured session factory."""
    return sessionmaker(bind=get_engine())
