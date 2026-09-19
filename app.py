import json
import os
import re
from datetime import datetime

import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="HSE ProGen AI Assistant V3", page_icon="⛑️", layout="wide")

SECTIONS = [
    ("consequence_details", "Consequence Details"),
    ("finding_summary", "Finding Summary"),
    ("chronology", "Chronology"),
    ("contributing_factors", "Contributing Factors (CLC)"),
    ("similar_past_incidents", "Similar Past Incidents"),
    ("why_why_analysis", "Why Why Analysis Tree"),
    ("causes", "Causes"),
    ("actions_recommendations", "Actions & Recommendations"),
    ("lesson_learned", "Lesson Learned"),
    ("risk_assessment", "Risk Assessment"),
    ("regulatory_notification", "Regulatory & Statutory Notification"),
    ("evidence_attachments", "Evidence & Attachments"),
    ("corrective_training", "Corrective Training"),
    ("executive_summary", "Executive Summary"),
]

DEFAULTS = {k: "" for k, _ in SECTIONS}

SYSTEM_REVIEW = """You are an HSE incident-reporting and investigation assistant for an industrial/retail oil-marketing environment.

The user is reviewing an incident that was initiated by another person and forwarded to the user. Do NOT behave as if you are creating a new incident from scratch.

Your rules:
1. Use only facts contained in the user's supplied incident/report text.
2. Never invent people, dates, times, causes, equipment failures, injuries, witnesses, CCTV findings, legal requirements, or other facts.
3. Clearly separate confirmed/reported facts, missing information, inconsistencies, and suggestions.
4. If information is absent, write "VERIFY — NOT PROVIDED" rather than guessing.
5. Do not declare a root cause unless the evidence in the supplied text supports it.
6. Suggested classifications must be presented as suggestions, with reasons tied to the supplied facts.
7. Preserve uncertainty where the original report is uncertain.
8. Use professional HSE investigation language suitable for an internal investigation record.
9. Do not fabricate similar incidents. If none are supplied, say that a historical database check is required.
10. For regulatory/statutory notification, do not assert that notification is legally required unless the supplied material establishes it; instead identify what should be verified.
11. Return valid JSON only, matching the requested schema.
"""

SYSTEM_INVESTIGATION = """You are preparing draft content for an HSE investigation in a ProGen-style incident investigation workflow.

Use ONLY the supplied incident information and the AI review. Do not invent facts.

For every investigation section:
- Write concise, professional, evidence-based text.
- If evidence is missing, explicitly use "VERIFY — NOT PROVIDED".
- Do not turn assumptions into facts.
- Do not create a root cause without supporting evidence.
- For chronology, include only known events and mark missing times as VERIFY.
- For CLC/contributing factors, select factors only when supported; otherwise identify them as factors to verify.
- For similar past incidents, do not invent examples; state that database/history review is required when no examples are provided.
- For Why-Why, show the chain only to the depth supported by evidence and flag unsupported links for verification.
- For actions, distinguish immediate/corrective/preventive actions and include responsible party or due date only if supplied; otherwise VERIFY.
- For risk assessment, do not invent likelihood/consequence scores. Use VERIFY — NOT PROVIDED when scores are absent.
- For regulatory notification, distinguish reported actions from items requiring legal/regulatory verification.
- For evidence, list evidence explicitly mentioned and identify useful evidence that still needs collection as VERIFY.
- For corrective training, do not claim training occurred unless stated.
- Executive summary must reflect only supported facts.

Return valid JSON only with exactly these keys:
consequence_details, finding_summary, chronology, contributing_factors, similar_past_incidents, why_why_analysis, causes, actions_recommendations, lesson_learned, risk_assessment, regulatory_notification, evidence_attachments, corrective_training, executive_summary.
"""


def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


def get_client():
    key = get_secret("OPENAI_API_KEY")
    if not key:
        key = st.session_state.get("manual_api_key", "")
    if not key:
        return None
    return OpenAI(api_key=key)


def call_ai(system_prompt, user_prompt, model):
    client = get_client()
    if client is None:
        raise RuntimeError("OpenAI API key is not configured. Add OPENAI_API_KEY in Streamlit Secrets or enter it in the sidebar.")
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = response.output_text.strip()
    # Remove accidental markdown fences around JSON.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise ValueError("The AI response was not valid JSON. Please try again.")


def safe_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def reset_all():
    for k in ["review", "investigation", "incident_text", "review_notes"] + list(DEFAULTS):
        st.session_state.pop(k, None)


if "incident_text" not in st.session_state:
    st.session_state.incident_text = ""
if "review_notes" not in st.session_state:
    st.session_state.review_notes = ""

st.title("⛑️ HSE ProGen AI Assistant — V3")
st.caption("Copy from ProGen → AI review/investigation → approve/edit → copy approved content back into ProGen")

with st.sidebar:
    st.header("Settings")
    configured = bool(get_secret("OPENAI_API_KEY"))
    if not configured:
        st.session_state.manual_api_key = st.text_input("OpenAI API key", type="password", help="For company use, prefer adding OPENAI_API_KEY to Streamlit Cloud Secrets instead of entering it here.")
    model = st.text_input("AI model", value=get_secret("OPENAI_MODEL", "gpt-5.6"))
    st.divider()
    st.info("This version does not require a Chrome extension or software installation. ProGen remains open in your normal Chrome browser.")
    if st.button("Start New Incident", use_container_width=True):
        reset_all()
        st.rerun()

st.markdown("### 1. Existing Incident Report")
st.write("Open the forwarded incident in ProGen, select/copy the relevant information, then paste it below. You can paste the entire page text or only the fields you want the AI to review.")
incident = st.text_area(
    "Paste ProGen incident information",
    key="incident_text",
    height=360,
    placeholder="Example: Reference No., incident date/time, location, incident description, immediate response, reported severity, incident type, etc.",
)

with st.expander("Optional: add your own investigation notes", expanded=False):
    st.session_state.review_notes = st.text_area(
        "Investigator notes / additional facts",
        value=st.session_state.review_notes,
        height=180,
        placeholder="Add facts you have personally verified. Do not add assumptions.",
    )

col1, col2 = st.columns([1, 1])
with col1:
    review_btn = st.button("🔍 Review Existing Incident", type="primary", use_container_width=True, disabled=not incident.strip())
with col2:
    if st.session_state.get("review"):
        st.success("AI review available below.")
    else:
        st.info("Run the review before generating the investigation.")

if review_btn:
    prompt = f"""Review this existing incident report.

INCIDENT REPORT:
{incident}

INVESTIGATOR NOTES (only if supplied by the user):
{st.session_state.review_notes}

Return JSON with exactly these keys:
known_facts: array of concise factual statements
missing_information: array of information needed but not supplied
review_observations: array of inconsistencies, ambiguities, or items to verify
classification_suggestion: string
classification_reason: string
field_suggestions: object where keys are relevant ProGen fields and values are suggested wording; prefix uncertain suggestions with VERIFY —
"""
    try:
        with st.spinner("Reviewing the existing incident..."):
            st.session_state.review = call_ai(SYSTEM_REVIEW, prompt, model)
        st.session_state.investigation = None
        st.success("Review completed.")
    except Exception as e:
        st.error(str(e))

if st.session_state.get("review"):
    review = st.session_state.review
    st.markdown("## 2. AI Review")
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("#### Confirmed / reported facts")
        for x in review.get("known_facts", []):
            st.write("• " + safe_text(x))
        st.markdown("#### Missing information")
        for x in review.get("missing_information", []):
            st.warning(safe_text(x))
    with r2:
        st.markdown("#### Review observations")
        for x in review.get("review_observations", []):
            st.write("• " + safe_text(x))
        st.markdown("#### Suggested classification")
        st.info(safe_text(review.get("classification_suggestion", "VERIFY — NOT PROVIDED")))
        st.caption(safe_text(review.get("classification_reason", "")))

    st.markdown("#### Suggested field wording — edit before using")
    suggestions = review.get("field_suggestions", {}) or {}
    if suggestions:
        for key, value in suggestions.items():
            label = key.replace("_", " ").title()
            st.text_area(label, value=safe_text(value), key=f"suggest_{key}", height=100)
    else:
        st.info("No specific field suggestions were generated.")

    st.markdown("## 3. Generate Investigation")
    gen_btn = st.button("🧩 Generate ProGen Investigation", type="primary", use_container_width=True)
    if gen_btn:
        prompt = f"""Prepare the investigation draft from the following source material.

ORIGINAL INCIDENT REPORT:
{incident}

INVESTIGATOR NOTES:
{st.session_state.review_notes}

AI REVIEW:
{json.dumps(review, ensure_ascii=False, indent=2)}

Generate every requested ProGen investigation section. Do not omit a key. Where the source does not contain enough information, use VERIFY — NOT PROVIDED.
"""
        try:
            with st.spinner("Preparing the investigation sections..."):
                st.session_state.investigation = call_ai(SYSTEM_INVESTIGATION, prompt, model)
            st.success("Investigation draft generated. Review and edit every section before copying to ProGen.")
        except Exception as e:
            st.error(str(e))

if st.session_state.get("investigation"):
    st.markdown("## 4. Investigation — Review & Edit")
    st.warning("AI-generated content is a draft. Verify facts, causes, classifications, risk scores, regulatory requirements, and actions before entering/submitting them in ProGen.")

    inv = st.session_state.investigation
    for key, label in SECTIONS:
        initial = safe_text(inv.get(key, ""))
        if f"approved_{key}" not in st.session_state:
            st.session_state[f"approved_{key}"] = initial
        with st.expander(label, expanded=(key in ["finding_summary", "chronology", "causes", "actions_recommendations", "executive_summary"])):
            st.text_area(
                f"Approved/editable content — {label}",
                key=f"approved_{key}",
                height=180 if key not in ["why_why_analysis", "risk_assessment", "actions_recommendations"] else 230,
            )
            st.caption("Use VERIFY — NOT PROVIDED wherever you still need to establish the fact in ProGen/investigation.")

    st.markdown("## 5. ProGen Copy Mode")
    st.write("Use the copy icon in each code box, then switch to ProGen and paste into the matching field. This is intentionally manual so the app never submits or advances the official record for you.")

    for key, label in SECTIONS:
        value = st.session_state.get(f"approved_{key}", "")
        with st.expander(f"Copy → {label}", expanded=False):
            st.code(value or "VERIFY — NOT PROVIDED", language=None)

    export = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "incident_source": incident,
        "review": review,
        "approved_investigation": {key: st.session_state.get(f"approved_{key}", "") for key, _ in SECTIONS},
    }
    st.download_button(
        "⬇️ Download approved investigation as JSON",
        data=json.dumps(export, ensure_ascii=False, indent=2),
        file_name="progen_ai_investigation.json",
        mime="application/json",
        use_container_width=True,
    )

st.divider()
st.caption("HSE ProGen AI Assistant V3 • AI is an assistant only. The investigator remains responsible for verification, editing, Save/Submit, Move to Investigation, and final official record quality.")
