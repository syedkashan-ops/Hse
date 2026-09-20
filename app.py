import json
import os
import re
from datetime import datetime

import streamlit as st
from google import genai

APP_TITLE = "HSE Progen AI Assistant – V4"
DEFAULT_MODEL = "gemini-2.5-flash"

SECTIONS = [
    "Consequence Details",
    "Finding Summary",
    "Chronology",
    "Contributing Factors (CLC)",
    "Similar Past Incidents",
    "Why-Why Analysis Tree",
    "Causes",
    "Actions & Recommendations",
    "Lesson Learned",
    "Risk Assessment",
    "Regulatory & Statutory Notification",
    "Evidence & Attachments",
    "Corrective Training",
    "Executive Summary",
]

SYSTEM = """
You are an HSE incident review and investigation drafting assistant.
The incident already exists in ProGen and was initiated by someone else.

RULES:
- Never invent facts, dates, times, names, measurements, witnesses, evidence, injuries, losses,
  classifications, causes, risk ratings, legal requirements, or actions.
- Separate confirmed/reported facts from missing information and suggestions.
- Mark unsupported information as VERIFY or NOT PROVIDED — USER INPUT REQUIRED.
- Never state a root cause as fact without supporting evidence.
- Classification, severity, probability, risk, causes and contributing factors are suggestions
  for human review only unless directly supported by the supplied information.
- Do not fabricate chronology.
- If regulatory notification is uncertain, write VERIFY AGAINST APPLICABLE REQUIREMENTS.
- Keep wording professional, concise, neutral and evidence-based.
- Human review is required before Save/Submit/Move to Investigation.
"""

REVIEW_PROMPT = """
Review the following existing incident.

Use exactly these headings:
## 1. Reported / Confirmed Facts
## 2. Missing or Unclear Information
## 3. Inconsistencies / Items Requiring Review
## 4. Suggested Incident Classification
## 5. Suggested Improvements to Incident Description
## 6. Suggested Immediate Response / Controls Wording
## 7. Information Needed Before Investigation
## 8. Reviewer Checklist

Mark uncertain items VERIFY.

INCIDENT:
---
{incident}
---
"""

INV_PROMPT = """
Prepare a draft HSE investigation from the incident and reviewed notes below.

Use exactly these headings in this order:
## Consequence Details
## Finding Summary
## Chronology
## Contributing Factors (CLC)
## Similar Past Incidents
## Why-Why Analysis Tree
## Causes
## Actions & Recommendations
## Lesson Learned
## Risk Assessment
## Regulatory & Statutory Notification
## Evidence & Attachments
## Corrective Training
## Executive Summary

Requirements:
- Use NOT PROVIDED — USER INPUT REQUIRED for absent facts.
- Use VERIFY where analysis needs confirmation.
- Chronology must contain only supplied events/times.
- For CLC, consider only evidence-supported categories such as procedures; tools/plant/equipment/
  vehicles; PPE; exposure; focus/inattention; workplace layout; physical/mental capabilities/
  condition/stress; skill/competency; training/knowledge transfer; management/supervision/
  leadership; contractor selection/oversight; engineering/design; standards/practices/procedures;
  communication; and control of work.
- Why-Why must stop where evidence is insufficient and identify what must be verified.
- Causes should distinguish immediate, contributing, underlying and root causes only where supported.
- Actions must link to supported findings/causes; do not invent owners or dates.
- Risk Assessment should cover hazard, pre-incident likelihood/consequence/risk, revised
  likelihood/consequence/risk, RA update requirement, and responsible party only when supplied.
- Regulatory notification should say VERIFY AGAINST APPLICABLE REQUIREMENTS unless established.
- Evidence may include physical inspection, document review, interview, photographic evidence,
  design review, witness statement or CCTV footage, but never claim it exists unless supplied.

INCIDENT:
---
{incident}
---

REVIEWED NOTES:
---
{review}
---
"""

def secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)

def ai_call(key, model, prompt):
    client = genai.Client(api_key=key)
    r = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"system_instruction": SYSTEM, "temperature": 0.2},
    )
    if not getattr(r, "text", None):
        raise RuntimeError("Gemini returned no text.")
    return r.text.strip()

def friendly_error(exc):
    s = str(exc)
    low = s.lower()
    if "429" in low or "quota" in low or "resource_exhausted" in low:
        return ("Gemini free-tier quota/rate limit was reached. No payment is required for this V4. "
                "Wait for the free quota window to reset or select another free-tier model available "
                "to your Google AI Studio project.")
    if "403" in low or "permission" in low or "api key" in low or "unauth" in low:
        return ("Gemini authentication failed. Check GEMINI_API_KEY in Streamlit Secrets and confirm "
                "the key is active in Google AI Studio.")
    return "Gemini API error: " + s

def parse_sections(text):
    out = {}
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text or "", re.MULTILINE))
    for i, m in enumerate(matches):
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        out[m.group(1).strip()] = text[m.end():end].strip()
    return out

st.set_page_config(page_title=APP_TITLE, page_icon="🦺", layout="wide")
st.title("🦺 HSE Progen AI Assistant – V4")
st.caption("Gemini free-tier edition • Copy/Paste workflow • Human approval required")

with st.sidebar:
    st.header("AI Settings")
    typed_key = st.text_input("Gemini API Key", type="password",
                              placeholder="Leave blank to use Streamlit Secret")
    key = typed_key.strip() or secret("GEMINI_API_KEY", "")
    model = st.text_input("Gemini model", value=secret("GEMINI_MODEL", DEFAULT_MODEL))
    if key:
        st.success("Gemini API key detected.")
    else:
        st.warning("Gemini API key not detected.")
    st.info("V4 never submits or saves anything in ProGen automatically.")

for k in ["incident", "review", "approved", "investigation"]:
    st.session_state.setdefault(k, "")

t1, t2, t3, t4, t5 = st.tabs([
    "1️⃣ Incident Input", "2️⃣ AI Review", "3️⃣ Investigation Builder",
    "4️⃣ ProGen Copy Mode", "5️⃣ Export"
])

with t1:
    st.subheader("Paste the existing incident from ProGen")
    st.write("Paste all information already entered by the initiator. Do not add assumptions.")
    st.session_state.incident = st.text_area(
        "Existing incident information",
        value=st.session_state.incident,
        height=430,
        placeholder=("Reference No: ...\nIncident Type: ...\nReported Date/Time: ...\n"
                     "Incident Date/Time: ...\nLocation: ...\nIncident Description: ...\n"
                     "Immediate Response: ...\nSeverity/Probability/Risk: ...")
    )

with t2:
    st.subheader("AI Review")
    if st.button("🔎 Generate AI Review", type="primary", use_container_width=True):
        if not st.session_state.incident.strip():
            st.error("Paste the incident information first.")
        elif not key:
            st.error("Add GEMINI_API_KEY in Streamlit Secrets or enter it in the sidebar.")
        else:
            try:
                with st.spinner("Reviewing incident..."):
                    st.session_state.review = ai_call(
                        key, model.strip(), REVIEW_PROMPT.format(incident=st.session_state.incident)
                    )
                    st.session_state.approved = st.session_state.review
                st.success("Review generated. Edit it before continuing.")
            except Exception as e:
                st.error(friendly_error(e))
    st.text_area("AI review reference", value=st.session_state.review, height=350, disabled=True)
    st.session_state.approved = st.text_area(
        "Your reviewed / edited version", value=st.session_state.approved, height=430
    )

with t3:
    st.subheader("Investigation Builder")
    if st.button("🧭 Build Investigation Draft", type="primary", use_container_width=True):
        if not st.session_state.incident.strip():
            st.error("Incident information is required.")
        elif not st.session_state.approved.strip():
            st.error("Generate and review the AI Review first.")
        elif not key:
            st.error("Gemini API key is missing.")
        else:
            try:
                with st.spinner("Building investigation sections..."):
                    st.session_state.investigation = ai_call(
                        key, model.strip(),
                        INV_PROMPT.format(
                            incident=st.session_state.incident,
                            review=st.session_state.approved
                        )
                    )
                st.success("Investigation draft generated.")
            except Exception as e:
                st.error(friendly_error(e))
    st.session_state.investigation = st.text_area(
        "Editable investigation draft", value=st.session_state.investigation, height=760
    )

with t4:
    st.subheader("ProGen Copy Mode")
    st.write("Review each section, then copy the approved wording into the matching ProGen tab.")
    parsed = parse_sections(st.session_state.investigation)
    if not st.session_state.investigation.strip():
        st.info("Build the investigation draft first.")
    else:
        for i, name in enumerate(SECTIONS, 1):
            with st.expander(f"{i}. {name}", expanded=i <= 2):
                value = parsed.get(name, "")
                if value:
                    st.text_area(f"{name} — copy after review", value=value,
                                 height=190, key=f"copy_{i}")
                else:
                    st.warning("Section not detected. Complete it manually from the full draft.")

with t5:
    st.subheader("Export working record")
    record = {
        "app": APP_TITLE,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "incident_input": st.session_state.incident,
        "approved_review": st.session_state.approved,
        "investigation_draft": st.session_state.investigation,
        "notice": "Human review required. Not an official ProGen submission."
    }
    st.download_button(
        "⬇️ Download JSON",
        json.dumps(record, indent=2, ensure_ascii=False),
        file_name="HSE_Progen_V4_working_record.json",
        mime="application/json",
        use_container_width=True
    )
    txt = f"""HSE PROGEN AI ASSISTANT – V4
Generated: {record['exported_at']}
Model: {model}

===== INCIDENT INPUT =====
{st.session_state.incident}

===== APPROVED REVIEW =====
{st.session_state.approved}

===== INVESTIGATION DRAFT =====
{st.session_state.investigation}

NOTICE: Human review required. Not an official ProGen submission.
"""
    st.download_button(
        "⬇️ Download TXT", txt,
        file_name="HSE_Progen_V4_working_record.txt",
        mime="text/plain",
        use_container_width=True
    )

st.divider()
st.caption("Verify all facts, classifications, causes, risk ratings, statutory requirements and actions before official submission.")
