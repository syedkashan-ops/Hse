# HSE ProGen AI Assistant V7

## V7 fix
This version fixes the Gemini/Pydantic error:

`Extra inputs are not permitted`

The previous V6 code passed the completed blank data dictionary directly as
`response_schema`. That dictionary is an example data object, not a Gemini
response schema. V7 converts the exact field structure into an explicit Gemini
`OBJECT` schema with nested properties and required fields.

It also normalizes the returned JSON against the same master schema before
displaying it in Streamlit.

## Deploy
1. Replace `app.py` in the GitHub repository with the V7 `app.py`.
2. Keep `requirements.txt` as provided.
3. In Streamlit Cloud Secrets add:
   `GEMINI_API_KEY = "your_key"`
4. Optional:
   `GEMINI_MODEL = "gemini-2.5-flash"`
5. Reboot/redeploy the Streamlit app.

## Important
This app does not directly control or autofill the separate ProGen site.
Use Copy Mode to transfer reviewed content to ProGen.
