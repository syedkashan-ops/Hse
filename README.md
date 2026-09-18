# HSE ProGen AI Assistant — V1

This is a local Streamlit + Playwright prototype for the workflow discussed:

1. Someone else initiates an incident in PSO HSE ProGen.
2. The incident is forwarded to you.
3. You open ProGen and log in manually.
4. You navigate to Pending Acknowledgement and open the incident.
5. The assistant inspects the visible First Incident Report page.
6. AI reviews the existing information, identifies missing information and proposes field-level edits.
7. You review the suggestions.
8. Approved suggestions can be applied to the current ProGen page.
9. The assistant does NOT submit the official record.

## Why this is a local app

A normal Streamlit Cloud deployment cannot directly control the Chrome browser on your laptop.
V1 therefore runs Streamlit locally and launches a visible Chromium browser with Playwright.

The architecture can later be changed to a Chrome extension or a local browser agent if desired.

## Installation

### Easiest on Windows

1. Install Python 3.11 or newer.
2. Extract this ZIP.
3. Double-click `run_local.bat`.
4. The browser will open.
5. Enter your ProGen credentials directly into ProGen.
6. Do not enter your ProGen password into Streamlit.

If Windows blocks the batch file, run:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m streamlit run app.py
```

## OpenAI key

Either enter the key in the Streamlit sidebar for the current session, or copy
`.env.example` to `.env` and set `OPENAI_API_KEY`.

Do not commit `.env` to GitHub.

## V1 limitations

The screenshots supplied for this project show the ProGen workflow and investigation
sections, but they do not expose the application's HTML/DOM selectors. Therefore V1 uses
a DOM inspection layer that captures actual controls from the live page.

The first live test is intentionally diagnostic. Once the real logged-in page is inspected,
the field mappings can be made more precise.

V1 does not:
- store your ProGen password
- automatically submit an incident
- independently move an incident into investigation
- invent missing facts
- automatically select a root cause without evidence

## Planned next versions

V2:
- dedicated First Incident Report field map
- stronger dropdown/radio handling
- review/edit workflow
- automatic navigation to the investigation stage

V3:
- Consequence Details
- Finding Summary
- Chronology
- Contributing Factors / CLC

V4:
- Why-Why Analysis
- Causes
- Actions & Recommendations

V5:
- Lesson Learned
- Risk Assessment
- Executive Summary

V6:
- CCTV/photo/document evidence analysis
- investigation evidence matrix
- end-to-end assisted workflow

## Security

Use only an authorized ProGen account and follow your organization's access and
data-handling rules. Treat incident records, names, photographs, CCTV and investigation
documents as confidential organizational information.
