import os
import json
from groq import Groq
from dotenv import load_dotenv
from app.models import PatientReferral
import json as json_lib

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ─────────────────────────────────────────────
# PRIMARY: Tool calling (structured output)
# ─────────────────────────────────────────────

def _extract_via_tool_calling(raw_text: str) -> PatientReferral:
    """
    Uses Groq's tool/function calling to force the LLM to return
    a structured JSON object matching the PatientReferral schema.
    Most reliable when the model supports it well.
    """
    tool_definition = {
        "type": "function",
        "function": {
            "name": "save_referral",
            "description": "Extract and save structured patient referral data from clinical notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "Anonymised patient ID. If not present, generate one like PAT-001."
                    },
                    "care_type_required": {
                        "type": "string",
                        "description": "Type of care needed: Residential, Nursing, Supported Living, or Mental Health."
                    },
                    "clinical_complexity": {
                        "type": "string",
                        "enum": ["Low", "Medium", "High"],
                        "description": "Clinical complexity level."
                    },
                    "primary_conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of diagnosed conditions mentioned."
                    },
                    "location_preference": {
                        "type": "string",
                        "description": "Preferred location for placement."
                    },
                    "max_weekly_budget": {
                        "type": "number",
                        "description": "Maximum weekly budget in GBP. Default to 1500 if not stated."
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["Routine", "Urgent", "Emergency"],
                        "description": "Urgency level. Default to Routine if not stated."
                    }
                },
                "required": [
                    "patient_id",
                    "care_type_required",
                    "clinical_complexity",
                    "location_preference"
                ]
            }
        }
    }

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert NHS clinical data extractor. "
                    "Extract structured referral data from the clinical notes provided. "
                    "Be conservative: only extract what is clearly stated."
                )
            },
            {"role": "user", "content": raw_text}
        ],
        tools=[tool_definition],
        tool_choice={"type": "function", "function": {"name": "save_referral"}}
    )

    args = response.choices[0].message.tool_calls[0].function.arguments
    return PatientReferral.model_validate_json(args)


# ─────────────────────────────────────────────
# FALLBACK: JSON-mode prompt
# ─────────────────────────────────────────────

def _extract_via_json_prompt(raw_text: str) -> PatientReferral:
    """
    Fallback approach: asks the LLM to return a raw JSON string.
    Used when tool calling fails or returns malformed output.
    """
    system_prompt = """
You are an expert NHS clinical data extractor.
Extract the following fields from the clinical notes and return ONLY a valid JSON object.
Do not include any explanation or markdown. Return raw JSON only.

Required fields:
- patient_id (string): Anonymised ID. Generate PAT-001 if not present.
- care_type_required (string): One of: Residential, Nursing, Supported Living, Mental Health
- clinical_complexity (string): One of: Low, Medium, High
- primary_conditions (array of strings): Diagnosed conditions mentioned
- location_preference (string): Preferred location
- max_weekly_budget (number): Weekly budget in GBP. Default 1500 if not stated.
- urgency (string): One of: Routine, Urgent, Emergency. Default Routine.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text}
        ],
        response_format={"type": "json_object"}
    )

    raw_json = response.choices[0].message.content
    data = json_lib.loads(raw_json)

    # Apply defaults defensively — LLMs sometimes return null for optional fields
    if not data.get("primary_conditions"):
        data["primary_conditions"] = []
    if not data.get("max_weekly_budget"):
        data["max_weekly_budget"] = 1500.0
    if not data.get("urgency"):
        data["urgency"] = "Routine"

    return PatientReferral.model_validate(data)



# ─────────────────────────────────────────────
# PUBLIC INTERFACE: Try primary, fall back
# ─────────────────────────────────────────────

def extract_referral_data(raw_text: str) -> PatientReferral:
    """
    Main entry point. Tries tool calling first.
    Falls back to JSON-mode prompt if tool calling fails.
    """
    try:
        return _extract_via_tool_calling(raw_text)
    except Exception as primary_error:
        print(f"[Extractor] Tool calling failed: {primary_error}. Trying JSON fallback...")
        try:
            return _extract_via_json_prompt(raw_text)
        except Exception as fallback_error:
            raise RuntimeError(
                f"Both extraction methods failed.\n"
                f"Primary: {primary_error}\n"
                f"Fallback: {fallback_error}"
            )
