"""Entity normalization utilities."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

LEGAL_SUFFIXES = {
    "LIMITED",
    "LTD",
    "PLC",
    "INC",
    "INCORPORATED",
    "SA",
    "NV",
    "LLC",
    "CO",
    "COMPANY",
    "CORP",
    "CORPORATION",
    "HOLDINGS",
    "HLDGS",
    "AG",
    "BV",
    "GROUP",
}
STOPWORDS = {"THE", "AND", "OF", "INTERNATIONAL", "GLOBAL", "CLASS", "SHARE"}
PUNCTUATION_RE = re.compile(r"[^A-Z0-9\s]")
WHITESPACE_RE = re.compile(r"\s+")


def transliterate(value: str) -> str:
    """Convert accented characters into ASCII equivalents."""

    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def normalize_whitespace(value: str) -> str:
    """Collapse consecutive spaces."""

    return WHITESPACE_RE.sub(" ", value).strip()


def strip_legal_suffixes(tokens: list[str]) -> list[str]:
    """Remove common corporate suffixes from a token list."""

    return [token for token in tokens if token not in LEGAL_SUFFIXES]


def strip_stopwords(tokens: list[str]) -> list[str]:
    """Remove broad corporate stopwords after suffix stripping."""

    return [token for token in tokens if token not in STOPWORDS]


def normalize_name(value: str | None) -> str:
    """Generate a canonical normalized entity name."""

    if not value:
        return ""
    candidate = transliterate(value.upper())
    candidate = PUNCTUATION_RE.sub(" ", candidate)
    tokens = normalize_whitespace(candidate).split(" ")
    tokens = strip_stopwords(strip_legal_suffixes(tokens))
    return normalize_whitespace(" ".join(tokens))


def normalize_identifier(value: str | None) -> str | None:
    """Normalize a security or entity identifier for comparisons."""

    if not value:
        return None
    normalized = re.sub(r"[^A-Z0-9]", "", value.upper())
    return normalized or None


def canonical_name(value: str | None) -> str:
    """Return a deterministic canonical name alias."""

    return normalize_name(value)


def expand_aliases(primary_name: str | None, aliases: Iterable[str] | None) -> list[str]:
    """Normalize aliases and preserve unique values."""

    values = {canonical_name(primary_name)} if primary_name else set()
    for alias in aliases or []:
        alias_value = canonical_name(alias)
        if alias_value:
            values.add(alias_value)
    return sorted(value for value in values if value)

