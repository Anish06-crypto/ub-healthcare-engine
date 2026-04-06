import os
import json
from typing import List
from groq import Groq
from dotenv import load_dotenv
from app.models import PatientReferral, CareProvider, MatchResult

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# ─────────────────────────────────────────────
# SCORING WEIGHTS
# Adjust these to tune the matching behaviour
# ─────────────────────────────────────────────

WEIGHTS = {
    "care_type_match": 40,       # Hard requirement — no match means excluded
    "complexity_match": 30,      # Hard requirement — no match means excluded
    "budget_within_range": 20,   # Soft — scored down if over budget, not excluded
    "location_match": 10,        # Soft — preference, not a hard requirement
}


def _generate_reasoning_trace(
    provider_name: str,
    reasons: List[str],
    score: float
) -> str:
    """
    Uses the LLM to convert a list of raw matching reasons into a single
    professional sentence suitable for an NHS clinical governance audit trail.
    Falls back to a plain concatenation if the LLM call fails.
    """
    try:
        prompt = (
            f"You are writing a clinical governance audit note for an NHS care placement system.\n"
            f"Provider: {provider_name}\n"
            f"Match score: {score}/100\n"
            f"Matching reasons: {reasons}\n\n"
            f"Write a single, professional sentence (max 40 words) summarising why this provider "
            f"was recommended. Use formal clinical language. Do not use bullet points."
        )

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80
        )
        return response.choices[0].message.content.strip()

    except Exception:
        # Fallback: plain concatenation — always works, never fails
        return f"{provider_name} matched with score {score}/100. Reasons: {'; '.join(reasons)}."


def score_providers(
    referral: PatientReferral,
    providers: List[CareProvider]
) -> List[MatchResult]:
    """
    Scores each provider against the referral using deterministic logic.
    Returns a ranked list of MatchResult objects, highest score first.
    Providers with zero available beds or mismatched care type/complexity
    are excluded entirely (hard filters).
    """
    results = []

    for provider in providers:

        # ── HARD FILTER 1: Availability ──────────────────────────────────
        if provider.available_beds == 0:
            continue  # Cannot place a patient in a full home

        reasons = []
        score = 0.0

        # ── HARD FILTER 2: Care Type ──────────────────────────────────────
        if referral.care_type_required not in provider.care_types_offered:
            continue  # Wrong type of care entirely — not a candidate

        score += WEIGHTS["care_type_match"]
        reasons.append(
            f"Care type '{referral.care_type_required}' is offered by this provider."
        )

        # ── HARD FILTER 3: Clinical Complexity ───────────────────────────
        if referral.clinical_complexity not in provider.supported_complexities:
            continue  # Provider cannot safely manage this patient's complexity

        score += WEIGHTS["complexity_match"]
        reasons.append(
            f"Provider supports '{referral.clinical_complexity}' clinical complexity."
        )

        # ── SOFT SCORE: Budget ────────────────────────────────────────────
        if provider.weekly_cost <= referral.max_weekly_budget:
            score += WEIGHTS["budget_within_range"]
            reasons.append(
                f"Weekly cost (£{provider.weekly_cost:.0f}) is within the "
                f"budget ceiling of £{referral.max_weekly_budget:.0f}."
            )
        else:
            reasons.append(
                f"Weekly cost (£{provider.weekly_cost:.0f}) exceeds the "
                f"budget ceiling of £{referral.max_weekly_budget:.0f}."
            )

        # ── SOFT SCORE: Location ──────────────────────────────────────────
        if referral.location_preference.lower() in provider.location.lower():
            score += WEIGHTS["location_match"]
            reasons.append(
                f"Provider is located in the preferred area: {provider.location}."
            )
        else:
            reasons.append(
                f"Provider location ({provider.location}) does not match "
                f"preference ({referral.location_preference})."
            )

        # ── GENERATE AUDIT TRACE ──────────────────────────────────────────
        trace = _generate_reasoning_trace(provider.name, reasons, score)

        results.append(MatchResult(
            provider_id=provider.provider_id,
            provider_name=provider.name,
            match_score=score,
            reasoning_trace=trace,
            cqc_rating=provider.cqc_rating,
            weekly_cost=provider.weekly_cost,
            available_beds=provider.available_beds
        ))

    # Sort by score descending — best match first
    return sorted(results, key=lambda x: x.match_score, reverse=True)
