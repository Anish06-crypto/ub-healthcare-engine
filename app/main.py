import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

from app.models import PatientReferral, MatchResult
from app.services.extractor import extract_referral_data
from app.services.matcher import score_providers, CareProvider

load_dotenv( )

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
    contact={
        "name": "Anish Ravikiran",
        "url": "https://github.com/Anish06-crypto/ub-healthcare-engine"
    }
 )


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
async def health_check():
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
    )
)
async def extract_referral(request: RawReferralRequest):
    try:
        return extract_referral_data(request.text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
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
    )
)
async def match_providers(referral: PatientReferral):
    try:
        providers = load_providers()
        results = score_providers(referral, providers)
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No suitable providers found for this referral."
            )
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Matching failed: {str(e)}"
        )


@app.post(
    "/api/v1/full-pipeline",
    response_model=List[MatchResult],
    tags=["Full Pipeline"],
    summary="Extract referral and match providers in one call",
    description=(
        "Convenience endpoint that combines extraction and matching. "
        "Accepts raw referral text and returns ranked provider matches in a single request."
    )
)
async def full_pipeline(request: RawReferralRequest):
    try:
        referral = extract_referral_data(request.text)
        providers = load_providers()
        results = score_providers(referral, providers)
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No suitable providers found for this referral."
            )
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline failed: {str(e)}"
        )
