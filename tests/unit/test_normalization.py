from app.services.normalization import (
    canonical_name,
    expand_aliases,
    normalize_identifier,
    normalize_name,
)


def test_normalize_name_strips_suffixes_and_punctuation() -> None:
    assert normalize_name("Orion Petrochemicals PLC.") == "ORION PETROCHEMICALS"


def test_normalize_name_transliterates_characters() -> None:
    assert canonical_name("Société Générale SA") == "SOCIETE GENERALE"


def test_normalize_identifier_standardizes_values() -> None:
    assert normalize_identifier("us-0000 000001") == "US0000000001"


def test_expand_aliases_deduplicates() -> None:
    aliases = expand_aliases(
        "Acme Defense Technology Ltd", ["ACME DEFENSE TECHNOLOGY", "Acme Defense Technology Ltd"]
    )
    assert aliases == ["ACME DEFENSE TECHNOLOGY"]
