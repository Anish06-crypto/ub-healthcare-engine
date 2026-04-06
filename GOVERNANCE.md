# Clinical Governance & Data Compliance Notes

**Project:** UB Healthcare — Care Placement Intelligence Engine  
**Version:** 1.0.0  
**Author:** Anish Ravikiran  

---

## Purpose

This document outlines the clinical governance principles applied in the design
of this system. It is intended to demonstrate that AI-assisted care placement
decisions remain auditable, safe, and compliant with NHS data standards.

---

## 1. Data Minimisation

The LLM extraction layer (`extractor.py`) processes only the clinical text
provided in the referral. No patient data is stored, logged, or persisted
beyond the lifetime of a single API request. The system does not maintain
a patient database.

Patient identifiers are treated as anonymised references (e.g., `PAT-001`).
The system is not designed to process, store, or transmit personally
identifiable information (PII) and should not be used with real patient data
without a full Data Protection Impact Assessment (DPIA) under UK GDPR.

---

## 2. Deterministic Guardrails

The matching algorithm (`matcher.py`) applies hard filters before any scoring
occurs. These filters are deterministic — they do not rely on LLM output:

| Hard Filter | Clinical Rationale |
|---|---|
| `available_beds == 0` | A provider with no capacity cannot accept a placement |
| Care type mismatch | Placing a Nursing patient in Supported Living is a clinical risk |
| Complexity mismatch | A Low complexity provider cannot safely manage a High complexity patient |

No probabilistic or LLM-based logic is used to override these filters.
A provider that fails a hard filter will never appear in results, regardless
of any other matching criteria.

---

## 3. Auditability — The Reasoning Trace

Every `MatchResult` object contains a `reasoning_trace` field. This field:

- Is populated for every result, without exception
- Contains a human-readable summary of why the provider was recommended
- Is generated from a pre-built list of deterministic reasons (not LLM hallucination)
- Has a plain-text fallback if the LLM call fails

This trace is designed to satisfy the requirement that every NHS placement
decision can be reviewed and justified by a human clinician or governance board.

---

## 4. CQC Rating Transparency

Every `MatchResult` surfaces the provider's CQC (Care Quality Commission)
rating. The system does not filter or rank by CQC rating automatically —
this is a deliberate decision. A case manager may have legitimate reasons
to select a "Requires Improvement" provider (e.g., it is the only available
option for a complex patient in a specific location). The rating is surfaced
for human review, not used as an automated gate.

---

## 5. Human-in-the-Loop

This system is designed as a **decision support tool**, not a decision-making
system. All placement decisions must be reviewed and confirmed by a qualified
case manager. The API returns ranked recommendations — it does not place
patients automatically.

---

## 6. Limitations & Future Work

- The current system uses a mock provider database. Production use would
  require integration with a live, regularly audited provider registry.
- The LLM extraction layer should be validated against a labelled dataset
  of real (anonymised) referrals before clinical use.
- A full DPIA and Information Governance review would be required before
  processing real patient data.
- Rate limiting and authentication (e.g., NHS login / OAuth2) are not
  implemented in this prototype and would be required for production.
