"""Search query builders for name/phone/email variations."""

from __future__ import annotations

import re


def build_name_variants(full_name: str) -> list[str]:
    """Return common search-safe name variants.

    E.g. ``"John Michael Doe"`` → ``["John Doe", "John M Doe", "J Doe"]``
    """
    parts = full_name.strip().split()
    if len(parts) < 2:
        return [full_name]

    first, *middle, last = parts
    variants = [f"{first} {last}"]
    if middle:
        variants.append(f"{first} {middle[0][0]} {last}")
    variants.append(f"{first[0]} {last}")
    return list(dict.fromkeys(variants))  # dedupe, preserve order


def normalize_phone(phone: str) -> str:
    """Strip non-digits from a phone number."""
    return re.sub(r"\D", "", phone)


def build_address_variants(address: str, city: str, state: str) -> list[str]:
    """Return address search variants."""
    base = f"{address}, {city}, {state}".strip(", ")
    short = f"{city}, {state}".strip(", ")
    return list(dict.fromkeys([base, short]))
