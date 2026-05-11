"""HTML parsing helpers used by broker adapters."""

from __future__ import annotations

import re
from typing import Optional

try:
    from selectolax.parser import HTMLParser as _HTMLParser  # fast path

    def _parse(html: str) -> object:
        return _HTMLParser(html)

    def _css(tree: object, selector: str) -> list[object]:
        return tree.css(selector)  # type: ignore[union-attr]

    def _text(node: object) -> str:
        return node.text(strip=True)  # type: ignore[union-attr]

except ImportError:
    from bs4 import BeautifulSoup

    def _parse(html: str) -> object:  # type: ignore[misc]
        return BeautifulSoup(html, "html.parser")

    def _css(tree: object, selector: str) -> list[object]:
        return tree.select(selector)  # type: ignore[union-attr]

    def _text(node: object) -> str:
        return node.get_text(strip=True)  # type: ignore[union-attr]


def extract_text_blocks(html: str, css_selector: str = "p,h1,h2,h3,li") -> list[str]:
    """Return non-empty text blocks matching *css_selector*."""
    tree = _parse(html)
    return [_text(n) for n in _css(tree, css_selector) if _text(n)]


def find_name_presence(html: str, full_name: str) -> bool:
    """Return ``True`` if *full_name* appears verbatim in *html* (case-insensitive)."""
    return full_name.lower() in html.lower()


def extract_opt_out_form_fields(html: str) -> dict[str, str]:
    """Extract ``<input>`` names and default values from a form."""
    tree = _parse(html)
    inputs = _css(tree, "input[name]")
    result: dict[str, str] = {}
    for inp in inputs:
        try:
            name = inp.attributes.get("name", "")  # type: ignore[union-attr]
            value = inp.attributes.get("value", "") or ""  # type: ignore[union-attr]
            if name:
                result[name] = value
        except AttributeError:
            pass
    return result


def detect_captcha_presence(html: str) -> bool:
    """Heuristic check for CAPTCHA indicators in HTML."""
    patterns = [
        r"recaptcha",
        r"hcaptcha",
        r"captcha",
        r"g-recaptcha",
        r"cf-turnstile",
    ]
    lower = html.lower()
    return any(re.search(p, lower) for p in patterns)
