from pydantic import BaseModel, Field
from typing import List, Optional


# ─────────────────────────────────────────────
# INBOUND: What arrives from an NHS referral
# ─────────────────────────────────────────────

class PatientReferral(BaseModel):
    patient_id: str = Field(
        ...,
        description="Anonymised patient identifier, e.g. PAT-001"
    )
    care_type_required: str = Field(
        ...,
        description="e.g. Residential, Nursing, Supported Living, Mental Health"
    )
    clinical_complexity: str = Field(
        ...,
        description="Must be one of: Low, Medium, High"
    )
    primary_conditions: List[str] = Field(
        ...,
        description="List of diagnosed conditions, e.g. ['Dementia', 'Diabetes']"
    )
    location_preference: str = Field(
        ...,
        description="Preferred city or region, e.g. Birmingham, West Midlands"
    )
    max_weekly_budget: float = Field(
        default=1500.0,
        description="Maximum weekly budget in GBP. Defaults to 1500 if not stated."
    )
    urgency: Optional[str] = Field(
        default="Routine",
        description="Routine, Urgent, or Emergency"
    )


# ─────────────────────────────────────────────
# DATABASE: A care provider record
# ─────────────────────────────────────────────

class CareProvider(BaseModel):
    provider_id: str
    name: str
    care_types_offered: List[str] = Field(
        description="e.g. ['Residential', 'Nursing']"
    )
    supported_complexities: List[str] = Field(
        description="e.g. ['Low', 'Medium', 'High']"
    )
    specialisms: List[str] = Field(
        description="e.g. ['Dementia', 'Mental Health', 'Acquired Brain Injury']"
    )
    location: str
    weekly_cost: float
    cqc_rating: str = Field(
        description="Outstanding, Good, Requires Improvement, or Inadequate"
    )
    available_beds: int


# ─────────────────────────────────────────────
# OUTBOUND: What the API returns per match
# ─────────────────────────────────────────────

class MatchResult(BaseModel):
    provider_id: str
    provider_name: str
    match_score: float = Field(
        description="Score out of 100. Higher is better."
    )
    reasoning_trace: str = Field(
        description="Human-readable audit trail for NHS clinical governance."
    )
    cqc_rating: str
    weekly_cost: float
    available_beds: int
