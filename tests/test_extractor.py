import pytest
from app.services.extractor import extract_referral_data
from app.models import PatientReferral


SAMPLE_REFERRAL = """
Referral for a 78-year-old female patient with advanced dementia and Type 2 diabetes.
Requires nursing home placement in the Birmingham area.
High clinical complexity due to behavioural symptoms and insulin dependency.
Budget up to £1,400 per week. Urgent placement needed.
Patient ID: PAT-078-F.
"""

MINIMAL_REFERRAL = """
Patient needs residential care in Manchester. Low complexity. No budget stated.
"""


def test_extraction_returns_patient_referral():
    """Extractor must return a valid PatientReferral object."""
    result = extract_referral_data(SAMPLE_REFERRAL)
    assert isinstance(result, PatientReferral)


def test_extraction_identifies_care_type():
    """Extractor must identify 'Nursing' as the care type."""
    result = extract_referral_data(SAMPLE_REFERRAL)
    assert result.care_type_required == "Nursing"


def test_extraction_identifies_high_complexity():
    """Extractor must identify 'High' clinical complexity."""
    result = extract_referral_data(SAMPLE_REFERRAL)
    assert result.clinical_complexity == "High"


def test_extraction_identifies_conditions():
    """Extractor must identify at least one condition from the referral."""
    result = extract_referral_data(SAMPLE_REFERRAL)
    assert len(result.primary_conditions) > 0


def test_extraction_applies_budget_default_when_missing():
    """When no budget is stated, extractor must default to 1500.0."""
    result = extract_referral_data(MINIMAL_REFERRAL)
    assert result.max_weekly_budget == 1500.0


def test_extraction_applies_urgency_default_when_missing():
    """When no urgency is stated, extractor must default to 'Routine'."""
    result = extract_referral_data(MINIMAL_REFERRAL)
    assert result.urgency == "Routine"
