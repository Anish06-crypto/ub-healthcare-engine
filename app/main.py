import logging
import os
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.models import PatientReferral, MatchResult
from app.services.extractor import extract_referral_data
from app.services.matcher import score_providers, CareProvider
from app.database import PlacementLog, create_tables, get_db

load_dotenv()

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# LIFESPAN — schema init on startup
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    logger.info("Audit log database initialised.")
    yield


# ─────────────────────────────────────────────
# APP INITIALISATION
# ─────────────────────────────────────────────

app = FastAPI(
    title="UB Healthcare — Care Placement Intelligence Engine",
    description=(
        "An AI-enabled API that structures unstructured NHS patient referrals "
        "and matches them to care providers using a deterministic scoring engine "
        "with LLM-generated audit trails for clinical governance compliance."
    ),
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "Anish Ravikiran",
        "url": "https://github.com/Anish06-crypto/ub-healthcare-engine",
    },
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ─────────────────────────────────────────────
# HELPER: Load provider database
# ─────────────────────────────────────────────

def load_providers() -> List[CareProvider]:
    """Loads the mock provider database from JSON."""
    data_path = os.path.join(
        os.path.dirname(__file__), "data", "mock_providers.json"
    )
    with open(data_path, "r") as f:
        data = json.load(f)
    return [CareProvider(**p) for p in data]


# ─────────────────────────────────────────────
# HELPER: Write audit log entry (non-blocking)
# Database failure never propagates to the caller.
# ─────────────────────────────────────────────

def _write_audit_log(
    db: Session,
    referral: PatientReferral,
    results: List[MatchResult],
) -> None:
    """
    Persists a PlacementLog row for the given referral + results.
    Swallows all exceptions — audit failure must never break a placement call.
    """
    try:
        top = results[0] if results else None
        entry = PlacementLog(
            timestamp=datetime.now(timezone.utc),
            patient_id=referral.patient_id,
            care_type_required=referral.care_type_required,
            clinical_complexity=referral.clinical_complexity,
            location_preference=referral.location_preference,
            max_weekly_budget=referral.max_weekly_budget,
            urgency=referral.urgency,
            top_match_provider_id=top.provider_id if top else None,
            top_match_provider_name=top.provider_name if top else None,
            top_match_score=top.match_score if top else None,
            top_match_reasoning=top.reasoning_trace if top else None,
            total_matches_returned=len(results),
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Audit log write failed (non-fatal): %s", exc)


# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────

class RawReferralRequest(BaseModel):
    text: str

    class Config:
        json_schema_extra = {
            "example": {
                "text": (
                    "Referral for a 78-year-old female patient with advanced dementia "
                    "and Type 2 diabetes. Requires nursing home placement in the "
                    "Birmingham area. High clinical complexity. Budget up to £1,400 "
                    "per week. Urgent placement needed."
                )
            }
        }


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/health", tags=["System"])
@limiter.limit("20/minute")
async def health_check(request: Request):
    """Confirms the API is running."""
    return {"status": "healthy", "service": "UB Healthcare Placement Engine"}


@app.post(
    "/api/v1/extract-referral",
    response_model=PatientReferral,
    tags=["Referral Intelligence"],
    summary="Extract structured data from a raw NHS referral",
    description=(
        "Accepts unstructured clinical referral text and uses an LLM "
        "(with deterministic fallback) to extract a structured PatientReferral object. "
        "Primary method uses tool calling; falls back to JSON-mode prompt if needed."
    ),
)
@limiter.limit("10/minute")
async def extract_referral(request: Request, payload: RawReferralRequest):
    try:
        return extract_referral_data(payload.text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}",
        )


@app.post(
    "/api/v1/match-providers",
    response_model=List[MatchResult],
    tags=["Provider Matching"],
    summary="Match a structured referral to available care providers",
    description=(
        "Accepts a structured PatientReferral and scores it against the provider database. "
        "Hard filters exclude providers with no beds, wrong care type, or unsupported complexity. "
        "Soft scores are applied for budget and location. Each result includes a "
        "reasoning_trace for NHS clinical governance audit requirements."
    ),
)
@limiter.limit("10/minute")
async def match_providers(
    request: Request,
    referral: PatientReferral,
    db: Session = Depends(get_db),
):
    try:
        providers = load_providers()
        results = score_providers(referral, providers)
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No suitable providers found for this referral.",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Matching failed: {str(e)}",
        )

    _write_audit_log(db, referral, results)
    return results


@app.post(
    "/api/v1/full-pipeline",
    response_model=List[MatchResult],
    tags=["Full Pipeline"],
    summary="Extract referral and match providers in one call",
    description=(
        "Convenience endpoint that combines extraction and matching. "
        "Accepts raw referral text and returns ranked provider matches in a single request."
    ),
)
@limiter.limit("10/minute")
async def full_pipeline(
    request: Request,
    payload: RawReferralRequest,
    db: Session = Depends(get_db),
):
    try:
        referral = extract_referral_data(payload.text)
        providers = load_providers()
        results = score_providers(referral, providers)
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No suitable providers found for this referral.",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline failed: {str(e)}",
        )

    _write_audit_log(db, referral, results)
    return results


@app.get(
    "/api/v1/audit-log",
    tags=["Audit"],
    summary="Retrieve the last 50 placement log entries",
    description=(
        "Returns the most recent 50 PlacementLog records ordered by timestamp descending. "
        "Provides a queryable audit trail for NHS clinical governance purposes."
    ),
)
@limiter.limit("30/minute")
async def get_audit_log(request: Request, db: Session = Depends(get_db)):
    try:
        entries = (
            db.query(PlacementLog)
            .order_by(PlacementLog.timestamp.desc())
            .limit(50)
            .all()
        )
        return [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "patient_id": e.patient_id,
                "care_type_required": e.care_type_required,
                "clinical_complexity": e.clinical_complexity,
                "location_preference": e.location_preference,
                "max_weekly_budget": e.max_weekly_budget,
                "urgency": e.urgency,
                "top_match_provider_id": e.top_match_provider_id,
                "top_match_provider_name": e.top_match_provider_name,
                "top_match_score": e.top_match_score,
                "top_match_reasoning": e.top_match_reasoning,
                "total_matches_returned": e.total_matches_returned,
            }
            for e in entries
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audit log: {str(e)}",
        )
