"""Shared type aliases and TypedDicts."""

from __future__ import annotations

from typing import Any, TypeAlias

# Primitive aliases
JsonDict: TypeAlias = dict[str, Any]
EncryptedBytes: TypeAlias = bytes
PlainText: TypeAlias = str

# Status alias (string literal from Status class)
StatusStr: TypeAlias = str

# Broker adapter result
FindingDict: TypeAlias = dict[str, Any]
