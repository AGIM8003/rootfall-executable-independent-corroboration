"""ROOTFALL validators."""
from __future__ import annotations


def require_nonempty(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def require_roots(root_ids: list[str]) -> list[str]:
    if not isinstance(root_ids, list) or not root_ids:
        raise ValueError("root_ids must be a non-empty list")
    for r in root_ids:
        require_nonempty("root_id", r)
    return list(root_ids)
