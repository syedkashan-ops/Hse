import os
import json
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from progen_browser import ProgenBrowser
from ai_engine import HSEAI

st.set_page_config(
    page_title="HSE ProGen AI Assistant",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ HSE ProGen AI Assistant")
st.caption("AI-assisted review and investigation preparation for the existing HSE ProGen workflow")

if "browser" not in st.session_state:
    st.session_state.browser = None
if "incident_snapshot" not in st.session_state:
    st.session_state.incident_snapshot = None
if "ai_review" not in st.session_state:
    st.session_state.ai_review = None
if "ai_fields" not in st.session_state:
    st.session_state.ai_fields = None

with st.sidebar:
    st.header("Connection")
    progen_url = st.text_input(
        "ProGen URL",
        value="https://formhand.psopk.com/ords/r/apps/hse-progen",
    )
    headless = st.checkbox(
        "Run browser headless",
        value=False,
        help="Keep this OFF so you can see the browser and log in yourself.",
    )
    st.divider()
    st.header("AI")
    api_key = st.text_input(
        "OpenAI API key",
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
        help="Used only for the current session unless you place it in .env.",
    )
    model = st.text_input(
        "Model",
        value=os.getenv("OPENAI_MODEL", "gpt-5.6"),
    )
    st.divider()
    st.warning(
        "Do not give the app your ProGen password. The V1 browser opens normally and "
        "you log in manually."
    )

browser = st.session_state.browser

st.subheader("1. Open ProGen and log in")
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("🚀 Open ProGen Browser", use_container_width=True):
        try:
            if browser is None:
                browser = ProgenBrowser(headless=headless)
                st.session_state.browser = browser
            browser.open(progen_url)
            st.success("Browser opened. Log in to ProGen manually.")
        except Exception as e:
            st.error(f"Could not start browser: {e}")

with c2:
    if st.button("🔄 Refresh Current Page", use_container_width=True):
        try:
            if browser:
                browser.refresh()
                st.success("Page refreshed.")
            else:
                st.warning("Open the ProGen browser first.")
        except Exception as e:
            st.error(str(e))

with c3:
    if st.button("🧪 Inspect Current Page", use_container_width=True):
        try:
            if browser:
                data = browser.inspect_page()
                st.session_state.incident_snapshot = data
                st.success(
                    f"Captured {len(data.get('fields', []))} form controls and "
                    f"{len(data.get('buttons', []))} buttons."
                )
            else:
                st.warning("Open the ProGen browser first.")
        except Exception as e:
            st.error(str(e))

if browser:
    try:
        st.info(f"Browser status: {browser.current_url()}")
    except Exception:
        pass

st.divider()
st.subheader("2. Review the forwarded incident")

st.write(
    "Navigate in ProGen to **Pending Acknowledgement → the incident forwarded to you → "
    "First Incident Report**. Then click **Inspect Current Page** above."
)

snapshot = st.session_state.incident_snapshot
if snapshot:
    st.markdown("### Captured ProGen page")
    st.write(f"**Page title:** {snapshot.get('title','')}")
    st.write(f"**URL:** {snapshot.get('url','')}")
    st.write(f"**Fields found:** {len(snapshot.get('fields', []))}")

    with st.expander("Show captured fields"):
        st.dataframe(snapshot.get("fields", []), use_container_width=True)

    if st.button("🤖 Analyze Incident With AI", type="primary"):
        if not api_key:
            st.error("Enter an OpenAI API key in the sidebar.")
        else:
            try:
                ai = HSEAI(api_key=api_key, model=model)
                with st.spinner("AI is reviewing the incident and preparing suggestions..."):
                    result = ai.review_incident(snapshot)
                st.session_state.ai_review = result
                st.session_state.ai_fields = result.get("field_suggestions", [])
                st.success("AI review completed.")
            except Exception as e:
                st.error(f"AI analysis failed: {e}")

review = st.session_state.ai_review
if review:
    st.divider()
    st.subheader("3. AI Review — human approval required")

    st.info(
        "The AI must not invent facts. Suggestions marked as requiring confirmation "
        "should be verified from CCTV, witnesses, photographs, documents or the actual site."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Confirmed / reported information")
        for item in review.get("known_facts", []):
            st.write("• " + item)

        st.markdown("#### Missing information")
        for item in review.get("missing_information", []):
            st.write("• " + item)

    with col2:
        st.markdown("#### AI review observations")
        for item in review.get("review_observations", []):
            st.write("• " + item)

        st.markdown("#### Classification suggestion")
        st.write(review.get("classification_suggestion", "Not determined"))
        if review.get("classification_reason"):
            st.caption(review["classification_reason"])

    st.markdown("#### Field-by-field suggestions")
    suggestions = review.get("field_suggestions", [])
    if suggestions:
        for i, s in enumerate(suggestions):
            with st.container(border=True):
                a, b = st.columns([1, 2])
                with a:
                    st.markdown(f"**{s.get('label','Field')}**")
                    st.caption(s.get("control_type", ""))
                with b:
                    st.text_area(
                        "Suggested value",
                        value=str(s.get("suggested_value", "")),
                        key=f"suggestion_{i}",
                    )
                    st.caption(
                        f"Status: {s.get('status','VERIFY')} | "
                        f"Reason: {s.get('reason','')}"
                    )

        st.warning(
            "V1 intentionally does not press Submit. After reviewing the suggestions, "
            "use Apply Approved Suggestions only for fields that are safe to populate."
        )

        if st.button("✍️ Apply Approved Suggestions to Current ProGen Page"):
            try:
                approved = []
                for i, s in enumerate(suggestions):
                    approved.append({
                        **s,
                        "suggested_value": st.session_state.get(
                            f"suggestion_{i}", s.get("suggested_value", "")
                        ),
                    })
                result = browser.apply_suggestions(approved)
                st.success(
                    f"Applied {result['applied']} fields. "
                    f"Skipped {result['skipped']} fields."
                )
                if result["warnings"]:
                    for w in result["warnings"]:
                        st.warning(w)
            except Exception as e:
                st.error(f"Could not apply suggestions: {e}")

st.divider()
st.subheader("4. Investigation stage — V1 foundation")

st.write(
    "After you review the First Incident Report in ProGen and move the incident to "
    "Investigation Report, use **Inspect Current Page** again. The same engine will "
    "capture the investigation controls so the next version can map Consequence Details, "
    "Finding Summary, Chronology, CLC, Why-Why, Causes, Actions & Recommendations, "
    "Lesson Learned, Risk Assessment and Executive Summary."
)

st.caption(
    "V1 is deliberately conservative: it assists, reviews and fills; it does not "
    "submit or independently advance an official HSE record."
)
