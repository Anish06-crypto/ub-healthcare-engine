"""
UB Healthcare — Care Placement Intelligence Engine
Streamlit Demo Dashboard
"""

import streamlit as st
import requests
import json
import time
import pandas as pd

# ─────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="UB Healthcare | Care Placement Engine",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Clinical, high-contrast, compact
# ─────────────────────────────────────────────

st.markdown("""
<style>
  /* Google Font */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  /* Dark clinical background */
  .stApp {
    background-color: #0d1117;
    color: #e6edf3;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
  }

  /* Metric cards */
  .metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
  }
  .metric-card h4 {
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0 0 4px 0;
  }
  .metric-card .value {
    font-size: 28px;
    font-weight: 700;
    color: #e6edf3;
  }

  /* Provider result card */
  .provider-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 18px 22px;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
  }
  .provider-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    border-radius: 8px 0 0 8px;
    background: var(--accent, #238636);
  }
  .provider-card h3 {
    margin: 0 0 4px 0;
    color: #e6edf3;
    font-size: 15px;
    font-weight: 600;
  }
  .provider-card .provider-id {
    font-family: 'Courier New', monospace;
    font-size: 11px;
    color: #58a6ff;
    letter-spacing: 0.04em;
  }
  .score-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
    color: white;
  }
  .cqc-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.03em;
  }
  .reasoning-box {
    background: #0d1117;
    border: 1px solid #21262d;
    border-left: 3px solid #388bfd;
    border-radius: 4px;
    padding: 10px 14px;
    margin-top: 12px;
    font-size: 13px;
    color: #8b949e;
    font-style: italic;
    line-height: 1.6;
  }
  .reasoning-box strong {
    color: #58a6ff;
    font-style: normal;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    display: block;
    margin-bottom: 4px;
  }

  /* Section headers */
  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid #21262d;
  }
  .section-header h2 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  /* Status dot */
  .status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
  }
  .status-dot.green { background: #3fb950; box-shadow: 0 0 6px #3fb950; }
  .status-dot.red   { background: #f85149; box-shadow: 0 0 6px #f85149; }

  /* Streamlit widget overrides */
  .stTextArea textarea {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    border-radius: 6px !important;
  }
  .stSelectbox > div > div {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
  }
  .stNumberInput input {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
  }
  div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #238636, #2ea043) !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 20px !important;
    transition: opacity 0.2s !important;
  }
  div[data-testid="stButton"] button:hover {
    opacity: 0.85 !important;
  }

  /* Pill tags */
  .tag {
    display: inline-block;
    background: #21262d;
    border: 1px solid #30363d;
    color: #8b949e;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 11px;
    margin: 2px;
  }
  .tag.blue { border-color: #388bfd40; background: #388bfd15; color: #58a6ff; }

  /* Info/warning callouts */
  .callout {
    background: #161b22;
    border-left: 3px solid #d29922;
    border-radius: 4px;
    padding: 10px 14px;
    font-size: 12px;
    color: #8b949e;
    margin-bottom: 16px;
  }

  /* Hide default Streamlit branding */
  #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

API_BASE = "http://localhost:8000"

EXAMPLE_REFERRALS = {
    "High Complexity — Dementia + Diabetes": (
        "Referral for a 78-year-old female patient with advanced dementia and Type 2 diabetes. "
        "Requires nursing home placement in the Birmingham area. High clinical complexity. "
        "Budget up to £1,400 per week. Urgent placement needed."
    ),
    "Mental Health — Bipolar Disorder": (
        "74-year-old male with a long-standing history of bipolar disorder and recent hospital discharge. "
        "Requires supported living or mental health unit in Birmingham or West Midlands. "
        "Low-medium clinical complexity. Budget ceiling: £1,200/week. Routine urgency."
    ),
    "Acquired Brain Injury — Complex Needs": (
        "45-year-old male with acquired brain injury following road traffic accident. "
        "High clinical complexity, requires specialist nursing and occupational therapy input. "
        "Location preference: West Midlands. Budget up to £2,500/week. Urgent referral."
    ),
    "Elderly Residential — Stroke Recovery": (
        "82-year-old female post-stroke, requiring residential care with stroke recovery support. "
        "Low clinical complexity. Birmingham or Solihull preferred. Budget: £1,100/week. Routine."
    ),
}

CQC_COLORS = {
    "Outstanding": "#3fb950",
    "Good": "#388bfd",
    "Requires Improvement": "#d29922",
    "Inadequate": "#f85149",
}

SCORE_COLORS = {
    (90, 101): ("#3fb950", "#0d1117"),
    (70, 90):  ("#388bfd", "#0d1117"),
    (50, 70):  ("#d29922", "#0d1117"),
    (0, 50):   ("#f85149", "#0d1117"),
}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def get_score_color(score: float) -> str:
    for (lo, hi), (color, _) in SCORE_COLORS.items():
        if lo <= score < hi:
            return color
    return "#e6edf3"


def check_api_health() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def call_full_pipeline(text: str) -> tuple[list | None, float, str | None]:
    start = time.time()
    try:
        r = requests.post(
            f"{API_BASE}/api/v1/full-pipeline",
            json={"text": text},
            timeout=30,
        )
        elapsed = time.time() - start
        if r.status_code == 200:
            return r.json(), elapsed, None
        else:
            detail = r.json().get("detail", r.text)
            return None, elapsed, detail
    except requests.exceptions.ConnectionError:
        return None, 0, "Cannot connect to API. Is `uvicorn app.main:app --reload` running?"
    except Exception as e:
        return None, 0, str(e)


def call_extract_only(text: str) -> tuple[dict | None, str | None]:
    try:
        r = requests.post(
            f"{API_BASE}/api/v1/extract-referral",
            json={"text": text},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json(), None
        return None, r.json().get("detail", r.text)
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API."
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 0 0 20px 0;">
      <div style="font-size:22px; font-weight:700; color:#e6edf3;">🏥 UB Healthcare</div>
      <div style="font-size:11px; color:#8b949e; letter-spacing:0.08em; text-transform:uppercase; margin-top:2px;">
        Care Placement Intelligence Engine
      </div>
    </div>
    """, unsafe_allow_html=True)

    # API health check
    api_ok = check_api_health()
    dot_class = "green" if api_ok else "red"
    status_text = "API Online" if api_ok else "API Offline"
    st.markdown(
        f'<span class="status-dot {dot_class}"></span>'
        f'<span style="font-size:12px; color:#8b949e;">{status_text}</span>',
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='border-color:#21262d; margin:16px 0;'>", unsafe_allow_html=True)

    # Navigation
    page = st.radio(
        "Navigate",
        ["🚀 Full Pipeline", "🔬 Extract Only", "📋 Provider Browser", "ℹ️ Architecture"],
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border-color:#21262d; margin:16px 0;'>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:11px; color:#8b949e; line-height:1.7;">
      <div style="font-weight:600; color:#58a6ff; margin-bottom:6px;">DESIGN PRINCIPLES</div>
      <div>• LLM extracts &amp; narrates</div>
      <div>• Deterministic scoring only</div>
      <div>• NHS governance audit trail</div>
      <div>• Hard + soft filter cascade</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#21262d; margin:16px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:11px; color:#8b949e;">
      <a href="http://localhost:8000/docs" target="_blank"
         style="color:#58a6ff; text-decoration:none;">📖 Swagger UI →</a>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE: FULL PIPELINE
# ─────────────────────────────────────────────

if "🚀 Full Pipeline" in page:

    st.markdown("""
    <div class="section-header">
      <h2>Full Pipeline — Extract &amp; Match</h2>
    </div>
    <div class="callout">
      Paste or type an unstructured NHS referral note. The API will extract structured fields using
      <strong>Groq LLaMA 3.1 8b</strong>, then score it against the provider database using
      <strong>deterministic logic</strong> — no LLM in the scoring loop.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 1], gap="large")

    with col1:
        st.markdown('<div style="font-size:12px; font-weight:600; color:#8b949e; margin-bottom:6px;">REFERRAL TEXT</div>', unsafe_allow_html=True)

        # Example selector
        example_choice = st.selectbox(
            "Load example",
            ["— paste your own —"] + list(EXAMPLE_REFERRALS.keys()),
            label_visibility="collapsed",
        )

        default_text = EXAMPLE_REFERRALS.get(example_choice, "") if example_choice != "— paste your own —" else ""

        referral_text = st.text_area(
            "Referral text",
            value=default_text,
            height=220,
            placeholder="Enter unstructured NHS referral text here…",
            label_visibility="collapsed",
        )

        run_btn = st.button("⚡ Run Full Pipeline", use_container_width=True)

    with col2:
        st.markdown('<div style="font-size:12px; font-weight:600; color:#8b949e; margin-bottom:6px;">SCORING WEIGHTS</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="metric-card">
          <h4>Care Type Match</h4>
          <div class="value" style="font-size:20px; color:#3fb950;">40 pts <span style="font-size:12px; color:#8b949e;">HARD filter</span></div>
        </div>
        <div class="metric-card">
          <h4>Clinical Complexity</h4>
          <div class="value" style="font-size:20px; color:#3fb950;">30 pts <span style="font-size:12px; color:#8b949e;">HARD filter</span></div>
        </div>
        <div class="metric-card">
          <h4>Budget Within Range</h4>
          <div class="value" style="font-size:20px; color:#388bfd;">20 pts <span style="font-size:12px; color:#8b949e;">soft score</span></div>
        </div>
        <div class="metric-card">
          <h4>Location Match</h4>
          <div class="value" style="font-size:20px; color:#388bfd;">10 pts <span style="font-size:12px; color:#8b949e;">soft score</span></div>
        </div>
        """, unsafe_allow_html=True)

    # Run pipeline
    if run_btn:
        if not referral_text.strip():
            st.warning("Please enter or select a referral text.")
        else:
            with st.spinner("Calling `/api/v1/full-pipeline` …"):
                results, elapsed, error = call_full_pipeline(referral_text)

            if error:
                st.error(f"**API Error:** {error}")
            elif results:
                st.markdown(f"""
                <div style="display:flex; gap:16px; margin: 20px 0 10px 0; flex-wrap:wrap;">
                  <div class="metric-card" style="flex:1; min-width:140px;">
                    <h4>Providers Matched</h4>
                    <div class="value">{len(results)}</div>
                  </div>
                  <div class="metric-card" style="flex:1; min-width:140px;">
                    <h4>Top Score</h4>
                    <div class="value" style="color:{get_score_color(results[0]['match_score'])};">
                      {results[0]['match_score']:.0f}<span style="font-size:14px;">/100</span>
                    </div>
                  </div>
                  <div class="metric-card" style="flex:1; min-width:140px;">
                    <h4>API Latency</h4>
                    <div class="value" style="font-size:22px;">{elapsed:.2f}<span style="font-size:14px;">s</span></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="section-header" style="margin-top:24px;">
                  <h2>Ranked Provider Matches</h2>
                </div>
                """, unsafe_allow_html=True)

                for i, r in enumerate(results):
                    score = r["match_score"]
                    accent = get_score_color(score)
                    cqc_color = CQC_COLORS.get(r["cqc_rating"], "#8b949e")
                    rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i] if i < 5 else f"#{i+1}"

                    st.markdown(f"""
                    <div class="provider-card" style="--accent:{accent};">
                      <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                        <div>
                          <div style="font-size:11px; color:#8b949e; margin-bottom:2px;">{rank_emoji} RANK {i+1}</div>
                          <h3>{r['provider_name']}</h3>
                          <span class="provider-id">{r['provider_id']}</span>
                        </div>
                        <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                          <span class="score-badge" style="background:{accent};">{score:.0f}/100</span>
                          <span class="cqc-badge" style="background:{cqc_color}22; color:{cqc_color}; border:1px solid {cqc_color}44;">
                            CQC: {r['cqc_rating']}
                          </span>
                          <span class="tag blue">£{r['weekly_cost']:,.0f}/wk</span>
                          <span class="tag">🛏 {r['available_beds']} beds</span>
                        </div>
                      </div>
                      <div class="reasoning-box">
                        <strong>🔍 NHS Audit Trace</strong>
                        {r['reasoning_trace']}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Score comparison chart
                st.markdown("""
                <div class="section-header" style="margin-top:28px;">
                  <h2>Score Comparison</h2>
                </div>
                """, unsafe_allow_html=True)

                chart_df = pd.DataFrame({
                    "Provider": [r["provider_name"] for r in results],
                    "Match Score": [r["match_score"] for r in results],
                    "Weekly Cost (£)": [r["weekly_cost"] for r in results],
                })
                st.bar_chart(chart_df.set_index("Provider")["Match Score"], color="#238636")

            else:
                st.info("No providers matched this referral criteria.")


# ─────────────────────────────────────────────
# PAGE: EXTRACT ONLY
# ─────────────────────────────────────────────

elif "🔬 Extract Only" in page:

    st.markdown("""
    <div class="section-header">
      <h2>LLM Extraction — Structured Referral Parser</h2>
    </div>
    <div class="callout">
      Calls <code>/api/v1/extract-referral</code> in isolation. Demonstrates the LLM extraction layer
      without triggering the matching engine.
    </div>
    """, unsafe_allow_html=True)

    example_choice = st.selectbox(
        "Load example",
        ["— paste your own —"] + list(EXAMPLE_REFERRALS.keys()),
    )
    default_text = EXAMPLE_REFERRALS.get(example_choice, "") if example_choice != "— paste your own —" else ""

    referral_text = st.text_area(
        "Referral text",
        value=default_text,
        height=200,
        placeholder="Enter unstructured NHS referral text…",
        label_visibility="collapsed",
    )

    if st.button("🔬 Extract Structured Fields", use_container_width=False):
        if not referral_text.strip():
            st.warning("Please enter a referral text.")
        else:
            with st.spinner("Calling LLM extractor…"):
                result, error = call_extract_only(referral_text)

            if error:
                st.error(f"**Error:** {error}")
            elif result:
                st.markdown("""
                <div class="section-header" style="margin-top:24px;">
                  <h2>Extracted PatientReferral Object</h2>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2, gap="large")

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                      <h4>Patient ID</h4>
                      <div class="value" style="font-family:monospace; font-size:20px; color:#58a6ff;">{result.get('patient_id','—')}</div>
                    </div>
                    <div class="metric-card">
                      <h4>Care Type Required</h4>
                      <div class="value" style="font-size:20px;">{result.get('care_type_required','—')}</div>
                    </div>
                    <div class="metric-card">
                      <h4>Clinical Complexity</h4>
                      <div class="value" style="font-size:20px; color:{'#f85149' if result.get('clinical_complexity')=='High' else '#d29922' if result.get('clinical_complexity')=='Medium' else '#3fb950'};">
                        {result.get('clinical_complexity','—')}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                      <h4>Location Preference</h4>
                      <div class="value" style="font-size:20px;">📍 {result.get('location_preference','—')}</div>
                    </div>
                    <div class="metric-card">
                      <h4>Max Weekly Budget</h4>
                      <div class="value" style="font-size:20px; color:#3fb950;">£{result.get('max_weekly_budget',0):,.0f}</div>
                    </div>
                    <div class="metric-card">
                      <h4>Urgency</h4>
                      <div class="value" style="font-size:20px; color:{'#f85149' if result.get('urgency')=='Emergency' else '#d29922' if result.get('urgency')=='Urgent' else '#3fb950'};">
                        {result.get('urgency','Routine')}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Primary conditions tags
                conditions = result.get("primary_conditions", [])
                if conditions:
                    tags_html = "".join([f'<span class="tag blue">{c}</span>' for c in conditions])
                    st.markdown(f"""
                    <div class="metric-card">
                      <h4>Primary Conditions</h4>
                      <div style="margin-top:8px;">{tags_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Raw JSON toggle
                with st.expander("📄 Raw JSON response"):
                    st.json(result)


# ─────────────────────────────────────────────
# PAGE: PROVIDER BROWSER
# ─────────────────────────────────────────────

elif "📋 Provider Browser" in page:

    st.markdown("""
    <div class="section-header">
      <h2>Provider Database Browser</h2>
    </div>
    <div class="callout">
      The current mock provider database loaded by the matching engine. 4 of 5 providers are active
      (PRV-004 has 0 available beds and will be hard-filtered out of all matches).
    </div>
    """, unsafe_allow_html=True)

    # Load mock data directly for display (no API call needed)
    import os, json as _json
    data_path = os.path.join(
        os.path.dirname(__file__), "app", "data", "mock_providers.json"
    )
    try:
        with open(data_path) as f:
            providers = _json.load(f)

        # Summary metrics
        total = len(providers)
        active = sum(1 for p in providers if p["available_beds"] > 0)
        total_beds = sum(p["available_beds"] for p in providers)
        avg_cost = sum(p["weekly_cost"] for p in providers) / total

        st.markdown(f"""
        <div style="display:flex; gap:14px; margin-bottom:20px; flex-wrap:wrap;">
          <div class="metric-card" style="flex:1; min-width:120px;">
            <h4>Total Providers</h4>
            <div class="value">{total}</div>
          </div>
          <div class="metric-card" style="flex:1; min-width:120px;">
            <h4>Active (Beds Available)</h4>
            <div class="value" style="color:#3fb950;">{active}</div>
          </div>
          <div class="metric-card" style="flex:1; min-width:120px;">
            <h4>Available Beds</h4>
            <div class="value">{total_beds}</div>
          </div>
          <div class="metric-card" style="flex:1; min-width:120px;">
            <h4>Avg Weekly Cost</h4>
            <div class="value" style="font-size:22px;">£{avg_cost:,.0f}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        for p in providers:
            cqc_color = CQC_COLORS.get(p["cqc_rating"], "#8b949e")
            available = p["available_beds"] > 0
            accent = "#238636" if available else "#f85149"

            care_tags = "".join([f'<span class="tag blue">{c}</span>' for c in p["care_types_offered"]])
            complexity_tags = "".join([f'<span class="tag">{c}</span>' for c in p["supported_complexities"]])
            specialism_tags = "".join([f'<span class="tag">{s}</span>' for s in p["specialisms"]])

            st.markdown(f"""
            <div class="provider-card" style="--accent:{accent};">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                <div>
                  <div class="provider-id">{p['provider_id']}</div>
                  <h3>{p['name']}</h3>
                  <div style="font-size:12px; color:#8b949e; margin-top:2px;">📍 {p['location']}</div>
                </div>
                <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                  <span class="cqc-badge" style="background:{cqc_color}22; color:{cqc_color}; border:1px solid {cqc_color}44;">
                    CQC: {p['cqc_rating']}
                  </span>
                  <span class="tag blue">£{p['weekly_cost']:,.0f}/wk</span>
                  <span class="tag" style="{'border-color:#3fb95044; background:#3fb95015; color:#3fb950;' if available else 'border-color:#f8514944; background:#f8514915; color:#f85149;'}">
                    🛏 {p['available_beds']} beds {'✓' if available else '— FULL'}
                  </span>
                </div>
              </div>
              <div style="margin-top:12px; display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
                <span style="font-size:10px; color:#8b949e; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; margin-right:4px;">Care Types:</span>
                {care_tags}
              </div>
              <div style="margin-top:6px; display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
                <span style="font-size:10px; color:#8b949e; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; margin-right:4px;">Complexity:</span>
                {complexity_tags}
              </div>
              <div style="margin-top:6px; display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
                <span style="font-size:10px; color:#8b949e; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; margin-right:4px;">Specialisms:</span>
                {specialism_tags}
              </div>
            </div>
            """, unsafe_allow_html=True)

    except FileNotFoundError:
        st.error("Provider database not found. Ensure you are running from the project root.")


# ─────────────────────────────────────────────
# PAGE: ARCHITECTURE
# ─────────────────────────────────────────────

elif "ℹ️ Architecture" in page:

    st.markdown("""
    <div class="section-header">
      <h2>System Architecture</h2>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown("""
        <div class="metric-card">
          <h4>Key Design Principle</h4>
          <div style="font-size:14px; color:#e6edf3; margin-top:8px; line-height:1.7;">
            The <strong style="color:#58a6ff;">LLM extracts and narrates</strong> — it never scores or filters.
            All clinical placement decisions use <strong style="color:#3fb950;">deterministic logic</strong>
            to ensure reproducibility and NHS governance compliance.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:12px; font-weight:600; color:#8b949e; margin:20px 0 10px 0; text-transform:uppercase; letter-spacing:0.08em;">PIPELINE STAGES</div>
        """, unsafe_allow_html=True)

        stages = [
            ("1", "#58a6ff", "Raw Referral Text", "Unstructured clinical notes, GP letters, discharge summaries"),
            ("2", "#d29922", "LLM Extractor", "Groq LLaMA 3.1 8b instant — tool calling with JSON-mode fallback"),
            ("3", "#3fb950", "Deterministic Scorer", "Hard filters → soft scoring. No LLM in the loop. Reproducible."),
            ("4", "#58a6ff", "LLM Audit Narrator", "Converts matching reasons to NHS-grade audit sentences"),
            ("5", "#8b949e", "FastAPI Response", "Ranked JSON list with match_score, cqc_rating, and reasoning_trace"),
        ]

        for num, color, title, desc in stages:
            st.markdown(f"""
            <div style="display:flex; gap:14px; margin-bottom:10px;">
              <div style="
                width:28px; height:28px; border-radius:50%;
                background:{color}22; border:2px solid {color};
                display:flex; align-items:center; justify-content:center;
                font-size:12px; font-weight:700; color:{color};
                flex-shrink:0; margin-top:2px;
              ">{num}</div>
              <div>
                <div style="font-size:13px; font-weight:600; color:#e6edf3;">{title}</div>
                <div style="font-size:11px; color:#8b949e; margin-top:2px;">{desc}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="font-size:12px; font-weight:600; color:#8b949e; margin-bottom:10px; text-transform:uppercase; letter-spacing:0.08em;">API ENDPOINTS</div>
        """, unsafe_allow_html=True)

        endpoints = [
            ("GET", "/health", "#3fb950", "System health check"),
            ("POST", "/api/v1/extract-referral", "#388bfd", "LLM extraction only"),
            ("POST", "/api/v1/match-providers", "#388bfd", "Matching only (structured input)"),
            ("POST", "/api/v1/full-pipeline", "#d29922", "Extract + match in one call"),
        ]

        for method, path, color, desc in endpoints:
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom:8px;">
              <div style="display:flex; gap:8px; align-items:center;">
                <span style="
                  font-size:10px; font-weight:700; font-family:monospace;
                  background:{color}22; color:{color}; border:1px solid {color}44;
                  padding:2px 7px; border-radius:4px;
                ">{method}</span>
                <span style="font-family:monospace; font-size:12px; color:#58a6ff;">{path}</span>
              </div>
              <div style="font-size:11px; color:#8b949e; margin-top:6px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:12px; font-weight:600; color:#8b949e; margin:20px 0 10px 0; text-transform:uppercase; letter-spacing:0.08em;">PROVIDER SWITCHING</div>
        <div class="metric-card">
          <div style="font-size:12px; color:#8b949e; line-height:1.8;">
            Uses the standard <span style="color:#58a6ff; font-family:monospace;">openai</span> SDK with a
            custom <code>base_url</code>.<br>
            Switching providers = updating <code>.env</code> only.
          </div>
          <div style="margin-top:10px; display:flex; flex-wrap:wrap; gap:6px;">
            <span class="cqc-badge" style="background:#3fb95022; color:#3fb950; border:1px solid #3fb95044;">✓ Groq (default)</span>
            <span class="tag">OpenAI</span>
            <span class="tag">Gemini</span>
            <span class="tag">Ollama</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:24px; padding:14px 18px; background:#161b22; border:1px solid #30363d; border-radius:8px; font-size:12px; color:#8b949e;">
      <strong style="color:#d29922;">⚠ Prototype Disclaimer</strong><br>
      This system uses mock provider data. It is a portfolio prototype and must not be used for
      real clinical placements without NHS information governance review, CQC integration, and
      appropriate clinical oversight. See <code>GOVERNANCE.md</code> for full details.
    </div>
    """, unsafe_allow_html=True)
