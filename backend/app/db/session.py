from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine = create_engine(
	str(settings.DATABASE_URL),
	pool_size=settings.DATABASE_POOL_SIZE,
	max_overflow=settings.DATABASE_POOL_OVERFLOW,
	pool_pre_ping=True,
	future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
