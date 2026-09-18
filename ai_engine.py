from __future__ import annotations

import json
from typing import Any, Dict

from openai import OpenAI


SYSTEM_PROMPT = """
You are an HSE incident-reporting and investigation assistant.

Your job is to review an EXISTING incident report that another person has already
initiated in an HSE system. Do not invent facts.

Rules:
1. Preserve the terminology and structure visible in the supplied ProGen page.
2. Separate confirmed/reported facts from assumptions and information that must be verified.
3. If a value cannot be established from the page, mark it VERIFY rather than guessing.
4. You may suggest wording improvements for descriptions, observations and actions.
5. You may suggest an incident classification, but explain the factual basis and flag it
   for human confirmation.
6. Do not make medical, legal or regulatory determinations beyond the supplied information.
7. Do not submit, approve or close an official incident.
8. When proposing a field value, reference the field index from the captured page so the
   browser can locate it.
9. Avoid adding a root cause unless the available evidence supports it.
10. The investigator remains responsible for the final official record.

Return valid JSON only with this structure:
{
  "known_facts": ["..."],
  "missing_information": ["..."],
  "review_observations": ["..."],
  "classification_suggestion": "...",
  "classification_reason": "...",
  "field_suggestions": [
    {
      "index": 0,
      "id": "",
      "name": "",
      "label": "",
      "control_type": "",
      "suggested_value": "",
      "status": "APPROVE|VERIFY|DO NOT FILL",
      "reason": ""
    }
  ]
}
"""


class HSEAI:
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def review_incident(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        user_prompt = (
            "Review the following currently visible HSE ProGen page. "
            "It is expected to be a First Incident Report or related incident page.\n\n"
            + json.dumps(snapshot, ensure_ascii=False, indent=2)
        )

        response = self.client.responses.create(
            model=self.model,
            instructions=SYSTEM_PROMPT,
            input=user_prompt,
        )

        text = response.output_text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extracting a JSON object if the model wrapped it in markdown.
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start:end + 1])
            raise ValueError("AI returned invalid JSON.")
