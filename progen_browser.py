from __future__ import annotations

import re
from typing import Any, Dict, List

from playwright.sync_api import sync_playwright


class ProgenBrowser:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.pw = None
        self.browser = None
        self.context = None
        self.page = None

    def _ensure(self):
        if self.page is None:
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch(
                headless=self.headless,
                args=["--start-maximized"],
            )
            self.context = self.browser.new_context(
                viewport={"width": 1440, "height": 900},
                ignore_https_errors=False,
            )
            self.page = self.context.new_page()

    def open(self, url: str):
        self._ensure()
        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)

    def refresh(self):
        self.page.reload(wait_until="domcontentloaded", timeout=60000)

    def current_url(self):
        return self.page.url if self.page else ""

    def inspect_page(self) -> Dict[str, Any]:
        if not self.page:
            raise RuntimeError("Browser is not open.")

        # Capture visible controls using DOM properties rather than relying on
        # screenshots. This makes the diagnostic useful even before exact selectors
        # are known.
        fields = self.page.locator(
            "input, textarea, select, [role='combobox'], [role='textbox'], "
            "button, [role='checkbox'], [role='radio']"
        )

        rows: List[Dict[str, Any]] = []
        count = min(fields.count(), 500)

        for i in range(count):
            el = fields.nth(i)
            try:
                if not el.is_visible():
                    continue

                tag = el.evaluate("(e) => e.tagName")
                typ = el.get_attribute("type") or ""
                name = el.get_attribute("name") or ""
                el_id = el.get_attribute("id") or ""
                aria = el.get_attribute("aria-label") or ""
                placeholder = el.get_attribute("placeholder") or ""
                value = ""
                try:
                    value = el.input_value()
                except Exception:
                    value = el.inner_text(timeout=500)

                # Try to find nearby label text.
                label = ""
                try:
                    label = el.evaluate(
                        """e => {
                          if (e.labels && e.labels.length) return e.labels[0].innerText;
                          const p = e.closest('div,td,li');
                          return p ? p.innerText.slice(0,180) : '';
                        }"""
                    )
                except Exception:
                    pass

                rows.append({
                    "index": i,
                    "tag": tag,
                    "type": typ,
                    "id": el_id,
                    "name": name,
                    "aria_label": aria,
                    "placeholder": placeholder,
                    "label_context": (label or "").strip(),
                    "value": value,
                })
            except Exception:
                continue

        buttons = []
        btns = self.page.locator("button, a, [role='button']")
        for i in range(min(btns.count(), 250)):
            b = btns.nth(i)
            try:
                if b.is_visible():
                    txt = (b.inner_text(timeout=300) or "").strip()
                    if txt:
                        buttons.append({
                            "index": i,
                            "text": re.sub(r"\s+", " ", txt)[:180],
                        })
            except Exception:
                pass

        return {
            "title": self.page.title(),
            "url": self.page.url,
            "fields": rows,
            "buttons": buttons,
        }

    def _locator_for(self, suggestion: Dict[str, Any]):
        s = suggestion
        idx = s.get("index")
        if idx is not None:
            loc = self.page.locator(
                "input, textarea, select, [role='combobox'], [role='textbox'], "
                "[role='checkbox'], [role='radio']"
            ).nth(int(idx))
            if loc.is_visible():
                return loc

        el_id = s.get("id")
        if el_id:
            loc = self.page.locator(f"#{el_id}")
            if loc.count() and loc.first.is_visible():
                return loc.first

        name = s.get("name")
        if name:
            loc = self.page.locator(f"[name='{name}']")
            if loc.count() and loc.first.is_visible():
                return loc.first

        return None

    def apply_suggestions(self, suggestions: List[Dict[str, Any]]):
        if not self.page:
            raise RuntimeError("Browser is not open.")

        applied = 0
        skipped = 0
        warnings = []

        for s in suggestions:
            status = str(s.get("status", "")).upper()
            if status in {"DO NOT FILL", "VERIFY", "REQUIRES CONFIRMATION"}:
                skipped += 1
                continue

            value = s.get("suggested_value", "")
            if value is None or str(value).strip() == "":
                skipped += 1
                continue

            loc = self._locator_for(s)
            if loc is None:
                skipped += 1
                warnings.append(
                    f"Could not locate field: {s.get('label') or s.get('id') or s.get('name')}"
                )
                continue

            try:
                tag = loc.evaluate("(e) => e.tagName.toLowerCase()")
                typ = (loc.get_attribute("type") or "").lower()

                if typ in {"checkbox", "radio"}:
                    desired = str(value).strip().lower() in {
                        "yes", "true", "1", "checked", "selected"
                    }
                    if desired:
                        loc.check()
                    else:
                        loc.uncheck()
                elif tag == "select":
                    # First try exact label/value; then fall back to visible text.
                    try:
                        loc.select_option(label=str(value))
                    except Exception:
                        loc.select_option(value=str(value))
                else:
                    loc.fill(str(value))

                applied += 1
            except Exception as e:
                skipped += 1
                warnings.append(
                    f"Could not fill {s.get('label','field')}: {str(e)[:180]}"
                )

        return {"applied": applied, "skipped": skipped, "warnings": warnings}
