"""Sanctions source connectors."""

from __future__ import annotations

import json
from ast import literal_eval
from datetime import UTC, datetime
from typing import Any
from xml.etree import ElementTree

import pandas as pd

from app.connectors.base import BaseConnector


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _children(element: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in list(element) if _local_name(child.tag) == name]


def _first_child(element: ElementTree.Element, name: str) -> ElementTree.Element | None:
    matches = _children(element, name)
    return matches[0] if matches else None


def _text(element: ElementTree.Element | None, name: str | None = None) -> str | None:
    target = _first_child(element, name) if element is not None and name is not None else element
    if target is None or target.text is None:
        return None
    value = target.text.strip()
    return value or None


def _texts(element: ElementTree.Element | None, path: list[str]) -> list[str]:
    if element is None:
        return []
    nodes = [element]
    for name in path:
        next_nodes: list[ElementTree.Element] = []
        for node in nodes:
            next_nodes.extend(_children(node, name))
        nodes = next_nodes
    results: list[str] = []
    for node in nodes:
        value = _text(node)
        if value:
            results.append(value)
    return results


def _first_non_empty(values: list[str | None]) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _parse_alias_list(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        try:
            parsed_json = json.loads(value)
            if isinstance(parsed_json, list):
                return [str(item) for item in parsed_json if str(item).strip()]
        except json.JSONDecodeError:
            pass
        try:
            parsed_literal = literal_eval(value)
            if isinstance(parsed_literal, list):
                return [str(item) for item in parsed_literal if str(item).strip()]
        except (ValueError, SyntaxError):
            pass
        return [value] if value.strip() else []
    return [str(value)]


def _clean_scalar(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


def _load_sanctions_sample_csv(path: str) -> list[dict[str, Any]]:
    frame = pd.read_csv(path, keep_default_na=False)
    records: list[dict[str, Any]] = []
    for row in frame.to_dict(orient="records"):
        aliases = _parse_alias_list(row.get("aliases_json") or row.get("alternate_names"))
        records.append(
            {
                "source_record_id": _clean_scalar(row.get("source_record_id")),
                "primary_name": _clean_scalar(row.get("primary_name")),
                "alternate_names": aliases,
                "entity_type": _clean_scalar(row.get("entity_type")) or "Entity",
                "program": _clean_scalar(row.get("program")),
                "country": _clean_scalar(row.get("country")),
                "nationality": _clean_scalar(row.get("nationality")),
                "date_of_birth": _clean_scalar(row.get("date_of_birth")),
                "place_of_birth": _clean_scalar(row.get("place_of_birth")),
                "remarks": _clean_scalar(row.get("remarks")),
                "aliases_json": aliases,
                "source_url": _clean_scalar(row.get("source_url")),
                "source_last_updated": _clean_scalar(row.get("source_last_updated")),
                "isin": _clean_scalar(row.get("isin")),
                "cusip": _clean_scalar(row.get("cusip")),
                "sedol": _clean_scalar(row.get("sedol")),
                "ticker": _clean_scalar(row.get("ticker")),
            }
        )
    return records


class UNSanctionsConnector(BaseConnector):
    """Connector for the UN consolidated sanctions list."""

    source_system = "UN"
    dataset_name = "consolidated_sanctions"
    source_url = "https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list"
    data_url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"

    def load_sample_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        path = self.settings.sample_data_dir / "un_sanctions.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload["records"], _parse_datetime(payload["source_last_updated"]), {"sample_path": str(path)}

    def fetch_live_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        root = ElementTree.fromstring(self._download_bytes(self.data_url))
        records: list[dict[str, Any]] = []
        for node in root.findall(".//INDIVIDUAL") + root.findall(".//ENTITY"):
            reference = node.findtext("DATAID") or node.findtext("REFERENCE_NUMBER") or ""
            name_parts = [
                node.findtext("FIRST_NAME"),
                node.findtext("SECOND_NAME"),
                node.findtext("THIRD_NAME"),
                node.findtext("FOURTH_NAME"),
                node.findtext("NAME_ORIGINAL_SCRIPT"),
            ]
            primary_name = " ".join(part.strip() for part in name_parts if part and part.strip())
            aliases = [
                alias.findtext("ALIAS_NAME")
                for alias in node.findall(".//INDIVIDUAL_ALIAS") + node.findall(".//ENTITY_ALIAS")
                if alias.findtext("ALIAS_NAME")
            ]
            records.append(
                {
                    "source_record_id": reference,
                    "primary_name": primary_name,
                    "alternate_names": aliases,
                    "entity_type": node.tag.title(),
                    "program": node.findtext("UN_LIST_TYPE"),
                    "country": node.findtext("NATIONALITY/VALUE") or node.findtext("COUNTRY/VALUE"),
                    "nationality": node.findtext("NATIONALITY/VALUE"),
                    "date_of_birth": node.findtext(".//INDIVIDUAL_DATE_OF_BIRTH/DATE"),
                    "place_of_birth": node.findtext(".//INDIVIDUAL_PLACE_OF_BIRTH/CITY"),
                    "remarks": node.findtext("COMMENTS1"),
                    "aliases_json": aliases,
                    "source_last_updated": None,
                    "source_url": self.source_url,
                    "raw_payload": ElementTree.tostring(node, encoding="unicode"),
                }
            )
        return records, None, {"source_url": self.source_url, "data_url": self.data_url, "format": "XML"}


class EUSanctionsConnector(BaseConnector):
    """Connector for the EU financial sanctions file."""

    source_system = "EU"
    dataset_name = "financial_sanctions"
    source_url = "https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions?locale=en"
    data_url = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content"

    def load_sample_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        path = self.settings.sample_data_dir / "eu_sanctions.csv"
        records = _load_sanctions_sample_csv(str(path))
        return records, _parse_datetime("2026-04-05T00:00:00Z"), {"sample_path": str(path)}

    def fetch_live_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        root = ElementTree.fromstring(self._download_bytes(self.data_url))
        records: list[dict[str, Any]] = []
        for node in root.findall(".//sanctionEntity"):
            aliases = [
                alias.get("wholeName")
                for alias in node.findall(".//nameAlias")
                if alias.get("wholeName")
            ]
            country = next(
                (
                    citizenship.get("countryDescription")
                    for citizenship in node.findall(".//citizenship")
                    if citizenship.get("countryDescription")
                ),
                None,
            )
            primary_name = aliases[0] if aliases else node.get("euReferenceNumber", "")
            records.append(
                {
                    "source_record_id": node.get("euReferenceNumber", ""),
                    "primary_name": primary_name,
                    "alternate_names": aliases[1:],
                    "entity_type": node.get("subjectType", "Entity"),
                    "program": node.get("regulationType"),
                    "country": country,
                    "nationality": None,
                    "date_of_birth": None,
                    "place_of_birth": None,
                    "remarks": node.get("remark"),
                    "aliases_json": aliases,
                    "source_last_updated": None,
                    "source_url": self.source_url,
                    "raw_payload": ElementTree.tostring(node, encoding="unicode"),
                }
            )
        return records, None, {"source_url": self.source_url, "data_url": self.data_url, "format": "XML"}


class OFACSanctionsConnector(BaseConnector):
    """Connector for the OFAC SDN list."""

    source_system = "OFAC"
    dataset_name = "sdn"
    source_url = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML"

    def load_sample_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        path = self.settings.sample_data_dir / "ofac_sdn.csv"
        records = _load_sanctions_sample_csv(str(path))
        return records, _parse_datetime("2026-04-06T00:00:00Z"), {"sample_path": str(path)}

    def fetch_live_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        root = ElementTree.fromstring(self._download_bytes(self.source_url))
        publish_information = _first_child(root, "publishInformation")
        source_last_updated = _parse_datetime(
            _first_non_empty(
                [
                    _text(publish_information, "PublishDate"),
                    _text(publish_information, "publishDate"),
                    _text(root, "publishDate"),
                ]
            )
        )

        records: list[dict[str, Any]] = []
        for node in root.iter():
            if _local_name(node.tag) != "sdnEntry":
                continue

            first_name = _text(node, "firstName")
            last_name = _text(node, "lastName")
            primary_name = " ".join(part for part in [first_name, last_name] if part) or _text(node, "lastName") or ""
            alias_names: list[str] = []
            for aka in _children(_first_child(node, "akaList") or node, "aka"):
                aka_first = _text(aka, "firstName")
                aka_last = _text(aka, "lastName")
                alias = " ".join(part for part in [aka_first, aka_last] if part) or aka_last or aka_first
                if alias:
                    alias_names.append(alias)

            programs = _texts(node, ["programList", "program"])
            nationalities = _texts(node, ["nationalityList", "nationality", "country"])
            citizenships = _texts(node, ["citizenshipList", "citizenship", "country"])
            countries = _texts(node, ["addressList", "address", "country"])
            date_of_birth = _first_non_empty(_texts(node, ["dateOfBirthList", "dateOfBirthItem", "dateOfBirth"]))
            place_of_birth = _first_non_empty(
                [
                    ", ".join(
                        part
                        for part in [
                            _text(place_of_birth_item, "placeOfBirth"),
                            _text(place_of_birth_item, "city"),
                            _text(place_of_birth_item, "country"),
                        ]
                        if part
                    )
                    for place_of_birth_item in _children(_first_child(node, "placeOfBirthList") or node, "placeOfBirthItem")
                ]
            )
            remarks = _text(node, "remarks")

            isin = None
            cusip = None
            sedol = None
            ticker = None
            id_list = _first_child(node, "idList")
            for identifier in _children(id_list or node, "id"):
                id_type = (_text(identifier, "idType") or "").upper()
                id_number = _text(identifier, "idNumber")
                if not id_number:
                    continue
                if "ISIN" in id_type:
                    isin = isin or id_number
                elif "CUSIP" in id_type:
                    cusip = cusip or id_number
                elif "SEDOL" in id_type:
                    sedol = sedol or id_number
                elif "TICKER" in id_type:
                    ticker = ticker or id_number

            records.append(
                {
                    "source_record_id": _text(node, "uid") or "",
                    "primary_name": primary_name,
                    "alternate_names": alias_names,
                    "entity_type": _text(node, "sdnType") or "Entity",
                    "program": "; ".join(programs) if programs else None,
                    "country": _first_non_empty(countries + citizenships + nationalities),
                    "nationality": _first_non_empty(nationalities + citizenships),
                    "date_of_birth": date_of_birth,
                    "place_of_birth": place_of_birth,
                    "remarks": remarks,
                    "aliases_json": alias_names,
                    "source_last_updated": source_last_updated.isoformat() if source_last_updated else None,
                    "source_url": self.source_url,
                    "isin": isin,
                    "cusip": cusip,
                    "sedol": sedol,
                    "ticker": ticker,
                    "raw_payload": ElementTree.tostring(node, encoding="unicode"),
                }
            )
        return records, source_last_updated, {"source_url": self.source_url, "format": "SDN.XML"}
