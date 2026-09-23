# HSE ProGen AI Assistant V6

This version is for GitHub + Streamlit Community Cloud and is designed for mobile Chrome.

## What V6 does
- Reviews an existing incident already initiated in ProGen
- Uses Gemini API
- Keeps ProGen-oriented FIR and investigation sections
- Provides editable field-by-field drafts
- Provides Mobile Copy Mode
- Opens ProGen in another browser tab
- Includes an experimental embedded ProGen iframe
- Exports JSON and TXT
- Uses VERIFY / NOT PROVIDED safeguards

## Deployment
1. Upload all files from this ZIP to a GitHub repository.
2. In Streamlit Community Cloud, create an app from that repository.
3. Main file: `app.py`
4. In Streamlit App > Settings > Secrets, add:

```toml
GEMINI_API_KEY = "YOUR_REAL_GEMINI_API_KEY"
GEMINI_MODEL = "gemini-2.5-flash"
```

Do not upload your real API key to GitHub.

## Recommended mobile workflow
1. Open V6 in mobile Chrome.
2. Open ProGen from the V6 ProGen or Copy Mode tab.
3. Log in normally.
4. Open the forwarded incident.
5. Copy the existing incident details.
6. Return to V6 and paste them.
7. Generate the draft.
8. Review/edit every field.
9. Use Copy Mode to copy one field at a time.
10. Switch to ProGen, paste, and continue.
11. Save/submit only after human verification.

## Limitation
A Streamlit website cannot directly control or autofill a separate Chrome tab from another domain. This is a browser security restriction. The iframe will work only if the ProGen server permits embedding.
