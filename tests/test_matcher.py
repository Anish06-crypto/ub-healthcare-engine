import pytest
from app.models import PatientReferral, CareProvider
from app.services.matcher import score_providers


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture
def standard_referral():
    return PatientReferral(
        patient_id="PAT-TEST-001",
        care_type_required="Nursing",
        clinical_complexity="High",
        primary_conditions=["Dementia", "Diabetes"],
        location_preference="Birmingham",
        max_weekly_budget=1400.0,
        urgency="Urgent"
    )


@pytest.fixture
def all_providers():
    return [
        CareProvider(
            provider_id="PRV-001",
            name="Oakwood Nursing Home",
            care_types_offered=["Nursing", "Residential"],
            supported_complexities=["Medium", "High"],
            specialisms=["Dementia", "Parkinson's"],
            location="Birmingham, West Midlands",
            weekly_cost=1350.00,
            cqc_rating="Good",
            available_beds=3
        ),
        CareProvider(
            provider_id="PRV-002",
            name="Meadowbrook Supported Living",
            care_types_offered=["Supported Living"],
            supported_complexities=["Low", "Medium"],
            specialisms=["Learning Disabilities"],
            location="Coventry, West Midlands",
            weekly_cost=980.00,
            cqc_rating="Outstanding",
            available_beds=1
        ),
        CareProvider(
            provider_id="PRV-003",
            name="Riverside Mental Health Unit",
            care_types_offered=["Mental Health", "Supported Living"],
            supported_complexities=["High"],
            specialisms=["Schizophrenia"],
            location="Birmingham, West Midlands",
            weekly_cost=1800.00,
            cqc_rating="Good",
            available_beds=2
        ),
        CareProvider(
            provider_id="PRV-004",
            name="Hillcrest Residential Care",
            care_types_offered=["Residential"],
            supported_complexities=["Low", "Medium"],
            specialisms=["Elderly Care"],
            location="Solihull, West Midlands",
            weekly_cost=1100.00,
            cqc_rating="Good",
            available_beds=0  # Full — must be excluded
        ),
        CareProvider(
            provider_id="PRV-005",
            name="Northgate Complex Care",
            care_types_offered=["Nursing", "Mental Health"],
            supported_complexities=["High"],
            specialisms=["Acquired Brain Injury"],
            location="Wolverhampton, West Midlands",
            weekly_cost=2200.00,
            cqc_rating="Outstanding",
            available_beds=1
        ),
    ]


# ─────────────────────────────────────────────
# HARD FILTER TESTS
# ─────────────────────────────────────────────

def test_provider_with_no_beds_is_excluded(standard_referral, all_providers):
    """PRV-004 has 0 available beds and must never appear in results."""
    results = score_providers(standard_referral, all_providers)
    result_ids = [r.provider_id for r in results]
    assert "PRV-004" not in result_ids


def test_wrong_care_type_is_excluded(standard_referral, all_providers):
    """PRV-002 offers Supported Living only — must be excluded for a Nursing referral."""
    results = score_providers(standard_referral, all_providers)
    result_ids = [r.provider_id for r in results]
    assert "PRV-002" not in result_ids


def test_wrong_complexity_is_excluded(standard_referral, all_providers):
    """PRV-003 is Mental Health / Supported Living — wrong care type for Nursing referral."""
    results = score_providers(standard_referral, all_providers)
    result_ids = [r.provider_id for r in results]
    assert "PRV-003" not in result_ids


# ─────────────────────────────────────────────
# SCORING TESTS
# ─────────────────────────────────────────────

def test_best_match_ranks_first(standard_referral, all_providers):
    """PRV-001 matches care type, complexity, budget, and location — must rank first."""
    results = score_providers(standard_referral, all_providers)
    assert results[0].provider_id == "PRV-001"


def test_best_match_has_maximum_score(standard_referral, all_providers):
    """PRV-001 satisfies all four scoring criteria — must score 100."""
    results = score_providers(standard_referral, all_providers)
    top = next(r for r in results if r.provider_id == "PRV-001")
    assert top.match_score == 100.0


def test_over_budget_provider_scores_lower(standard_referral, all_providers):
    """PRV-005 is over budget — must score lower than PRV-001."""
    results = score_providers(standard_referral, all_providers)
    prv001 = next(r for r in results if r.provider_id == "PRV-001")
    prv005 = next(r for r in results if r.provider_id == "PRV-005")
    assert prv001.match_score > prv005.match_score


def test_results_are_sorted_descending(standard_referral, all_providers):
    """Results must always be returned highest score first."""
    results = score_providers(standard_referral, all_providers)
    scores = [r.match_score for r in results]
    assert scores == sorted(scores, reverse=True)


# ─────────────────────────────────────────────
# EDGE CASE TESTS
# ─────────────────────────────────────────────

def test_no_providers_returns_empty_list(standard_referral):
    """If the provider database is empty, return an empty list gracefully."""
    results = score_providers(standard_referral, [])
    assert results == []


def test_all_providers_full_returns_empty_list(standard_referral, all_providers):
    """If every provider has 0 beds, return an empty list."""
    for p in all_providers:
        p.available_beds = 0
    results = score_providers(standard_referral, all_providers)
    assert results == []


def test_reasoning_trace_is_populated(standard_referral, all_providers):
    """Every result must have a non-empty reasoning trace for audit compliance."""
    results = score_providers(standard_referral, all_providers)
    for result in results:
        assert result.reasoning_trace is not None
        assert len(result.reasoning_trace) > 0
