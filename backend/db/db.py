# Smartii DB: SQLAlchemy models and helpers for audit logging
from __future__ import annotations
import os
import uuid
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import (
    create_engine, Column, String, DateTime, Boolean, Text, Integer
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import JSON

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/smartii")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class ActionLog(Base):
    __tablename__ = "action_logs"
    id = Column(String, primary_key=True, default=_uuid)
    action_id = Column(String, nullable=True)
    action_type = Column(String, nullable=False)
    params = Column(JSON)
    confirm = Column(Boolean, default=False)
    is_async = Column(Boolean, default=False)
    meta = Column(JSON)
    status = Column(String, default="accepted")  # accepted|completed|error
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class JobLog(Base):
    __tablename__ = "job_logs"
    id = Column(String, primary_key=True, default=_uuid)
    job_id = Column(String, nullable=False, index=True)
    action_type = Column(String, nullable=True)
    status = Column(String, default="queued")  # queued|running|succeeded|failed
    result = Column(JSON)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventLog(Base):
    __tablename__ = "event_logs"
    id = Column(String, primary_key=True, default=_uuid)
    type = Column(String, nullable=False)
    source = Column(String, nullable=True)
    payload = Column(JSON)
    ts = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def log_action(action_type: str, status: str, *, action_id: Optional[str] = None, params: Any = None,
               confirm: bool = False, is_async: bool = False, meta: Any = None, error: Optional[str] = None):
    session = SessionLocal()
    try:
        entry = ActionLog(
            action_id=action_id,
            action_type=action_type,
            params=params,
            confirm=confirm,
            is_async=is_async,
            meta=meta,
            status=status,
            error=error,
        )
        session.add(entry)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def log_job(job_id: str, status: str, *, action_type: Optional[str] = None, result: Any = None, error: Optional[str] = None):
    session = SessionLocal()
    try:
        entry = JobLog(
            job_id=job_id,
            action_type=action_type,
            status=status,
            result=result,
            error=error,
        )
        session.add(entry)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def log_event(event_type: str, source: Optional[str], payload: Any):
    session = SessionLocal()
    try:
        entry = EventLog(
            type=event_type,
            source=source,
            payload=payload,
        )
        session.add(entry)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
