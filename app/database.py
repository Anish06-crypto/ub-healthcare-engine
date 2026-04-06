import os
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ─────────────────────────────────────────────
# DATABASE SETUP
# Resolves to <project_root>/audit.db regardless
# of which directory uvicorn is started from.
# ─────────────────────────────────────────────

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.path.join(_PROJECT_ROOT, "audit.db")
DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ─────────────────────────────────────────────
# DECLARATIVE BASE
# ─────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────
# TABLE: PlacementLog
# One row per /match-providers or /full-pipeline call.
# ─────────────────────────────────────────────

class PlacementLog(Base):
    __tablename__ = "placement_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Referral fields ───────────────────────────────────────────────────────
    patient_id = Column(String, nullable=False)
    care_type_required = Column(String, nullable=False)
    clinical_complexity = Column(String, nullable=False)
    location_preference = Column(String, nullable=False)
    max_weekly_budget = Column(Float, nullable=False)
    urgency = Column(String, nullable=True)

    # ── Top match fields (nullable — no match is a valid outcome) ─────────────
    top_match_provider_id = Column(String, nullable=True)
    top_match_provider_name = Column(String, nullable=True)
    top_match_score = Column(Float, nullable=True)
    top_match_reasoning = Column(Text, nullable=True)

    # ── Summary ───────────────────────────────────────────────────────────────
    total_matches_returned = Column(Integer, nullable=False, default=0)


# ─────────────────────────────────────────────
# SCHEMA INITIALISATION
# Called once on application startup.
# ─────────────────────────────────────────────

def create_tables() -> None:
    """Creates all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


# ─────────────────────────────────────────────
# FASTAPI DEPENDENCY
# Yields a DB session and guarantees it is closed
# after the request completes, even on exceptions.
# ─────────────────────────────────────────────

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
