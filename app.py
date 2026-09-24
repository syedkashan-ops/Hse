import json
import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types

PROGEN_URL = "https://formhand.psopk.com/ords/r/apps/hse-progen"

st.set_page_config(page_title="HSE ProGen AI Assistant V7", page_icon="🦺", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.block-container{padding-top:1rem;max-width:1200px}
.stButton>button,.stDownloadButton>button,a[data-testid="stLinkButton"]{width:100%;min-height:46px;border-radius:10px}
div[data-testid="stTextArea"] textarea{min-height:110px}
.copybox{border:1px solid #bbb;border-radius:12px;padding:10px;margin:8px 0}
@media(max-width:700px){
.block-container{padding-left:.7rem;padding-right:.7rem}
h1{font-size:1.6rem!important}
}
</style>
""", unsafe_allow_html=True)

def blank_schema():
    return {
      "ai_review":{
        "Confirmed / Reported Facts":"",
        "Missing Information":"",
        "Inconsistencies / Review Points":"",
        "Suggested Incident Classification":"",
        "Suggested Wording / Field Edits":"",
        "Review Notes":""
      },
      "first_incident_report":{
        "Reference No.":"",
        "Incident Type":"",
        "Reported Date/Time":"",
        "Incident Date/Time":"",
        "Location":"",
        "Incident Description":"",
        "Immediate Response":"",
        "Severity":"",
        "Probability":"",
        "Risk":"",
        "Other Fields":""
      },
      "consequence_details":{
        "Actual Consequence":"",
        "Potential Consequence":"",
        "Injury/Illness":"",
        "Property/Equipment Damage":"",
        "Environmental Impact":"",
        "Business/Operational Impact":"",
        "Consequence Details":""
      },
      "finding_summary":{
        "Finding Summary":"",
        "Key Findings":"",
        "Fact/Evidence Basis":"",
        "Items Requiring Verification":""
      },
      "chronology":{
        "Chronology":"",
        "Unverified Sequence/Missing Time":""
      },
      "contributing_factors":{
        "Procedures":"",
        "Tools / Plant / Equipment / Vehicles":"",
        "PPE":"",
        "Exposure":"",
        "Focus / Inattention":"",
        "Workplace Layout":"",
        "Physical / Mental Capabilities / Condition / Stress":"",
        "Skill / Competency":"",
        "Training / Knowledge Transfer":"",
        "Management / Supervision / Leadership":"",
        "Contractor Selection / Oversight":"",
        "Engineering / Design":"",
        "Standards / Practices / Procedures":"",
        "Communication":"",
        "Control of Work":""
      },
      "similar_past_incidents":{
        "Similar Past Incidents":"",
        "Similarity / Relevance":"",
        "Verification Required":""
      },
      "why_why":{
        "Problem / Event":"",
        "Why 1":"",
        "Why 2":"",
        "Why 3":"",
        "Why 4":"",
        "Why 5":"",
        "Evidence Supporting Analysis":"",
        "Analysis Stopping Point / Verification":""
      },
      "causes":{
        "Immediate Cause":"",
        "Contributing Cause(s)":"",
        "Underlying Cause":"",
        "Root Cause":"",
        "Evidence Basis":"",
        "Causes Requiring Verification":""
      },
      "actions":{
        "Actions & Recommendations":""
      },
      "lesson":{
        "Lesson Learned":"",
        "Communication / Sharing Required":""
      },
      "risk":{
        "Hazard Identified in RA":"",
        "Pre-Incident Likelihood":"",
        "Pre-Incident Consequence":"",
        "Pre-Incident Risk":"",
        "Revised Likelihood":"",
        "Revised Consequence":"",
        "Revised Risk":"",
        "RA Update Required":"",
        "Responsible Party":"",
        "Risk Assessment Notes":""
      },
      "regulatory":{
        "Notification Required":"",
        "Authority / Regulatory Body":"",
        "Notification Details":"",
        "Status / Date":"",
        "Verification":""
      },
      "evidence":{
        "Physical Inspection":"",
        "Document Review":"",
        "Interview":"",
        "Photographic Evidence":"",
        "Design Review":"",
        "Witness Statement":"",
        "CCTV Footage":""
      },
      "training":{
        "Corrective Training Required":"",
        "Training Topic":"",
        "Target Audience":"",
        "Training Method":"",
        "Responsible Party":"",
        "Target Date":""
      },
      "executive":{
        "Executive Summary":"",
        "Key Consequence":"",
        "Key Findings":"",
        "Key Causes":"",
        "Key Actions":"",
        "Verification / Limitations":""
      }
    }

SYSTEM = """You are an HSE incident review and investigation assistant for the PSO HSE-ProGen workflow.
The incident has already been initiated by another person and forwarded to the user.
Your task is to review the existing incident, identify gaps/inconsistencies, suggest wording, and prepare investigation content for human review.

Rules:
1. Never invent facts.
2. Missing information must be exactly: NOT PROVIDED — USER INPUT REQUIRED
3. Plausible but unconfirmed analysis must start with: VERIFY:
4. Do not fabricate chronology, dates, times, witnesses, documents, CCTV, injuries, damage, regulatory requirements, or risk ratings.
5. Do not assert root cause without supporting evidence.
6. Actions must be linked to supported findings/causes.
7. Preserve the exact JSON keys and HSE-ProGen terminology provided.
8. User remains responsible for Save, Submit, Acknowledge, and Move to Investigation.
"""

if "incident" not in st.session_state: st.session_state.incident = ""
if "notes" not in st.session_state: st.session_state.notes = ""
if "data" not in st.session_state: st.session_state.data = blank_schema()

def make_draft():
    key = st.secrets.get("GEMINI_API_KEY", "")
    if not key:
        st.error("GEMINI_API_KEY is missing from Streamlit Secrets.")
        return
    client = genai.Client(api_key=key)
    model = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")
    schema = blank_schema()
    prompt = f"""{SYSTEM}

EXISTING FORWARDED INCIDENT:
{st.session_state.incident}

ADDITIONAL CONFIRMED NOTES / EVIDENCE:
{st.session_state.notes}

Return one valid JSON object matching exactly:
{json.dumps(schema, indent=2)}
"""
    # IMPORTANT: response_schema must be a real Gemini JSON schema.
    # Passing the blank example dictionary directly as response_schema causes
    # the Google GenAI SDK to build an incompatible Pydantic schema and reject
    # valid generated fields with "Extra inputs are not permitted".
    def to_gemini_schema(obj):
        if isinstance(obj, dict):
            return types.Schema(
                type=types.Type.OBJECT,
                properties={k: to_gemini_schema(v) for k, v in obj.items()},
                required=list(obj.keys()),
                additional_properties=False,
            )
        return types.Schema(type=types.Type.STRING)

    response_schema = to_gemini_schema(schema)

    r = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.1,
        ),
    )

    # Parse and normalize the response so the Streamlit editor always has
    # exactly the fields defined by blank_schema().
    generated = json.loads(r.text)

    def normalize(template, value):
        if isinstance(template, dict):
            value = value if isinstance(value, dict) else {}
            return {
                key: normalize(child, value.get(key, ""))
                for key, child in template.items()
            }
        return "" if value is None else str(value)

    st.session_state.data = normalize(schema, generated)

def edit_section(key, title):
    st.subheader(title)
    section = st.session_state.data[key]
    for field in list(section.keys()):
        section[field] = st.text_area(field, value=section[field], key=f"{key}_{field}")

def copy_card(label, value, ident):
    text = str(value or "")
    safe_js = json.dumps(text)
    safe_html = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    h = 170 if len(text) < 180 else 240
    components.html(f"""
    <div class="copybox">
      <b>{label}</b>
      <div style="white-space:pre-wrap;margin:8px 0">{safe_html}</div>
      <button id="b{ident}" style="width:100%;min-height:42px">Copy</button>
      <script>
      document.getElementById("b{ident}").onclick=async()=>{{
        try {{
          await navigator.clipboard.writeText({safe_js});
          document.getElementById("b{ident}").innerText="Copied";
          setTimeout(()=>document.getElementById("b{ident}").innerText="Copy",1200);
        }} catch(e) {{
          document.getElementById("b{ident}").innerText="Copy failed";
        }}
      }};
      </script>
    </div>
    """, height=h, scrolling=True)

st.title("🦺 HSE ProGen AI Assistant — V7")
st.caption("Streamlit + GitHub | Mobile Chrome friendly | No extension | Gemini AI | Human review required | Schema-fixed V7")

tabs = st.tabs(["Incident","AI Review","FIR","Investigation","Copy Mode","ProGen","Export"])

with tabs[0]:
    st.session_state.incident = st.text_area("Paste existing forwarded incident from ProGen", value=st.session_state.incident, height=280)
    st.session_state.notes = st.text_area("Additional confirmed notes / evidence", value=st.session_state.notes, height=160)
    if st.button("Generate AI Review + Investigation Draft", type="primary"):
        if not st.session_state.incident.strip():
            st.warning("Paste the incident details first.")
        else:
            try:
                with st.spinner("Generating structured draft..."):
                    make_draft()
                st.success("Draft created. Review every field before using it in ProGen.")
            except Exception as e:
                st.error(f"Generation failed: {e}")

with tabs[1]:
    edit_section("ai_review","AI Review")

with tabs[2]:
    edit_section("first_incident_report","First Incident Report")

with tabs[3]:
    names = [
      ("consequence_details","Consequence Details"),
      ("finding_summary","Finding Summary"),
      ("chronology","Chronology"),
      ("contributing_factors","Contributing Factors (CLC)"),
      ("similar_past_incidents","Similar Past Incidents"),
      ("why_why","Why-Why Analysis Tree"),
      ("causes","Causes"),
      ("actions","Actions & Recommendations"),
      ("lesson","Lesson Learned"),
      ("risk","Risk Assessment"),
      ("regulatory","Regulatory & Statutory Notification"),
      ("evidence","Evidence & Attachments"),
      ("training","Corrective Training"),
      ("executive","Executive Summary")
    ]
    subs = st.tabs([x[1] for x in names])
    for tab,(key,title) in zip(subs,names):
        with tab:
            edit_section(key,title)

with tabs[4]:
    st.subheader("Mobile Copy Mode")
    st.write("Open ProGen in another Chrome tab. Copy a field here, switch to ProGen, paste it, then return for the next field.")
    labels = {
      "first_incident_report":"First Incident Report",
      "consequence_details":"Consequence Details",
      "finding_summary":"Finding Summary",
      "chronology":"Chronology",
      "contributing_factors":"Contributing Factors (CLC)",
      "similar_past_incidents":"Similar Past Incidents",
      "why_why":"Why-Why Analysis Tree",
      "causes":"Causes",
      "actions":"Actions & Recommendations",
      "lesson":"Lesson Learned",
      "risk":"Risk Assessment",
      "regulatory":"Regulatory & Statutory Notification",
      "evidence":"Evidence & Attachments",
      "training":"Corrective Training",
      "executive":"Executive Summary"
    }
    sel = st.selectbox("Select section", list(labels), format_func=lambda x: labels[x])
    mode = st.radio("Copy layout", ["One field at a time","Whole section"], horizontal=True)
    if mode == "One field at a time":
        for i,(k,v) in enumerate(st.session_state.data[sel].items()):
            copy_card(k,v,f"{sel}{i}")
    else:
        whole = "\n\n".join(f"{k}:\n{v}" for k,v in st.session_state.data[sel].items())
        copy_card(labels[sel],whole,f"{sel}whole")
    st.link_button("Open ProGen", PROGEN_URL)

with tabs[5]:
    st.subheader("ProGen")
    st.link_button("Open ProGen in new tab", PROGEN_URL)
    st.info("V6 cannot directly control or autofill a separate ProGen Chrome tab because of browser cross-origin security. Use Copy Mode.")
    st.markdown("#### Experimental embedded ProGen")
    st.caption("This will only work if the ProGen server permits iframe embedding.")
    if st.checkbox("Try embedded ProGen"):
        components.iframe(PROGEN_URL, height=720, scrolling=True)

with tabs[6]:
    data_json = json.dumps(st.session_state.data, indent=2, ensure_ascii=False)
    st.download_button("Download JSON", data_json, "progen_v7_review.json", "application/json")
    text_parts=[]
    for sec,content in st.session_state.data.items():
        text_parts += [sec.upper().replace("_"," "), "="*50]
        for k,v in content.items():
            text_parts += [k, str(v), ""]
    data_txt="\n".join(text_parts)
    st.download_button("Download TXT", data_txt, "progen_v7_review.txt", "text/plain")
