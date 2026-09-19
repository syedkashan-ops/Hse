# HSE ProGen AI Assistant — V3

A Streamlit Cloud app for reviewing a forwarded HSE incident and preparing investigation content for manual copy/paste into PSO HSE ProGen.

## Why V3 does not use a Chrome extension

Company-managed laptops may block extensions and browser automation. V3 therefore uses a browser-only workflow:

1. Open ProGen normally in Chrome and log in.
2. Open the incident forwarded to you.
3. Copy the relevant ProGen information.
4. Paste it into the Streamlit app.
5. Ask AI to review the existing incident.
6. Review/edit the AI suggestions.
7. Generate the investigation sections.
8. Approve/edit every section.
9. Use the Copy icon in each ProGen Copy Mode box and paste into ProGen.
10. You remain responsible for official Save/Submit/Move-to-Investigation actions.

## Deploy on Streamlit Community Cloud

1. Create a new GitHub repository.
2. Upload `app.py`, `requirements.txt`, `.gitignore`, `.streamlit/secrets.toml.example` and this README.
3. In Streamlit Community Cloud, create a new app and select `app.py`.
4. Open the app's Settings / Secrets and add:

```toml
OPENAI_API_KEY = "YOUR_API_KEY"
OPENAI_MODEL = "gpt-5.6"
```

Do NOT commit your real API key to GitHub.

If your API account uses another model, change `OPENAI_MODEL` in Secrets.

## V3 workflow

### Existing Incident Report
Paste the forwarded incident report text from ProGen.

### AI Review
The app identifies:
- confirmed/reported facts
- missing information
- observations/inconsistencies
- suggested classification
- field wording suggestions

### Investigation
The app drafts:
- Consequence Details
- Finding Summary
- Chronology
- Contributing Factors (CLC)
- Similar Past Incidents
- Why Why Analysis Tree
- Causes
- Actions & Recommendations
- Lesson Learned
- Risk Assessment
- Regulatory & Statutory Notification
- Evidence & Attachments
- Corrective Training
- Executive Summary

### ProGen Copy Mode
Each section is shown separately in a copy-friendly code box.

## Safety / quality controls

The prompts explicitly instruct the AI not to invent facts, not to fabricate similar incidents, not to invent risk scores, and not to declare unsupported root causes. Missing facts are marked `VERIFY — NOT PROVIDED`.

The app does not automatically submit or advance a ProGen record.
