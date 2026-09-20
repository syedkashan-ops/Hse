# HSE Progen AI Assistant – V4

## Workflow
ProGen -> copy existing incident -> V4 -> AI Review -> human edit -> Investigation Builder ->
ProGen Copy Mode -> paste approved wording back into ProGen.

## Deploy
1. Extract this ZIP.
2. Upload all files to a GitHub repository.
3. In Streamlit Community Cloud create an app from that repository.
4. Set Main file path to `app.py`.
5. Open App Settings -> Secrets and add:

```toml
GEMINI_API_KEY = "YOUR_REAL_GEMINI_API_KEY"
GEMINI_MODEL = "gemini-2.5-flash"
```

6. Save and reboot the Streamlit app if required.

## Important
Do not upload your real API key to GitHub.
V4 does not log into ProGen or automatically submit anything.
Gemini free-tier limits still apply.
Incident text is sent to the Gemini API when you generate AI output, so follow your employer's
information-security and confidentiality rules.
