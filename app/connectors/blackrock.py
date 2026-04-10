"""BlackRock connectors backed by a single local SpreadsheetML XML workbook."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from app.connectors.base import BaseConnector


SS_NS = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
SS_NAME = "{urn:schemas-microsoft-com:office:spreadsheet}Name"
SS_INDEX = "{urn:schemas-microsoft-com:office:spreadsheet}Index"
SS_MERGE_ACROSS = "{urn:schemas-microsoft-com:office:spreadsheet}MergeAcross"


def _read_spreadsheetml_worksheet(path: Path, worksheet_name: str) -> list[list[str | None]]:
    root = ElementTree.parse(path).getroot()
    worksheet = None
    for candidate in root.findall("ss:Worksheet", SS_NS):
        if candidate.attrib.get(SS_NAME) == worksheet_name:
            worksheet = candidate
            break
    if worksheet is None:
        available = [node.attrib.get(SS_NAME, "") for node in root.findall("ss:Worksheet", SS_NS)]
        raise ValueError(f"Worksheet '{worksheet_name}' not found in {path.name}. Available sheets: {available}")

    table = worksheet.find("ss:Table", SS_NS)
    if table is None:
        return []

    parsed_rows: list[list[str | None]] = []
    for row in table.findall("ss:Row", SS_NS):
        current: list[str | None] = []
        current_index = 1
        for cell in row.findall("ss:Cell", SS_NS):
            explicit_index = cell.attrib.get(SS_INDEX)
            if explicit_index:
                target_index = int(explicit_index)
                while current_index < target_index:
                    current.append(None)
                    current_index += 1
            data = cell.find("ss:Data", SS_NS)
            current.append(data.text.strip() if data is not None and data.text is not None else None)
            current_index += 1
            merge_across = cell.attrib.get(SS_MERGE_ACROSS)
            if merge_across:
                for _ in range(int(merge_across)):
                    current.append(None)
                    current_index += 1
        parsed_rows.append(current)
    return parsed_rows


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped or stripped == "-":
        return None
    return stripped


def _parse_float(value: str | None) -> float | None:
    cleaned = _clean_text(value)
    if cleaned is None:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_blackrock_funds_xml(path: Path) -> list[dict[str, Any]]:
    rows = _read_spreadsheetml_worksheet(path, "All Funds")
    if len(rows) < 3:
        return []

    header = rows[0]
    records: list[dict[str, Any]] = []
    for row in rows[2:]:
        padded = row + [None] * (len(header) - len(row))
        values = {str(header[idx]).strip(): padded[idx] for idx in range(len(header)) if header[idx]}
        fund_name = _clean_text(values.get("Name"))
        if not fund_name:
            continue
        snapshot_date = _clean_text(values.get("As of"))
        records.append(
            {
                "fund_id": _clean_text(values.get("ISIN")) or _clean_text(values.get("SEDOL")) or fund_name,
                "fund_name": fund_name,
                "share_class": _clean_text(values.get("Share Class")),
                "isin": _clean_text(values.get("ISIN")),
                "sedol": _clean_text(values.get("SEDOL")),
                "fund_type": "Fund",
                "domicile": "United Kingdom",
                "asset_class": _clean_text(values.get("Asset Class")),
                "currency": _clean_text(values.get("Share Class Currency")) or _clean_text(values.get("Base Currency")),
                "blackrock_url": None,
                "snapshot_date": snapshot_date,
                "ticker": _clean_text(values.get("Ticker")),
                "cusip": _clean_text(values.get("CUSIP")),
                "sub_asset_class": _clean_text(values.get("Sub Asset Class")),
                "region": _clean_text(values.get("Region")),
                "strategy": _clean_text(values.get("Strategy")),
                "market": _clean_text(values.get("Market")),
                "inception_date": _clean_text(values.get("Inception Date")),
                "aum_m": _parse_float(values.get("AUM (M)")),
                "nav": _parse_float(values.get("NAV")),
                "distribution_rate": _parse_float(values.get("Distribution Rate")),
                "source_url": str(path),
            }
        )
    return records


class BlackRockFundConnector(BaseConnector):
    """Connector for BlackRock fund metadata from a local workbook."""

    source_system = "BLACKROCK"
    dataset_name = "funds"

    def __init__(self, settings=None) -> None:
        super().__init__(settings)
        self.source_url = str(self.settings.blackrock_source_file)

    def load_sample_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        path = self.settings.blackrock_source_file
        records = _parse_blackrock_funds_xml(path)
        return records, None, {"source_file": str(path), "worksheet": "All Funds", "format": "SpreadsheetML XML"}

    def fetch_live_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        path = self.settings.blackrock_source_file
        records = _parse_blackrock_funds_xml(path)
        return records, None, {"source_file": str(path), "worksheet": "All Funds", "format": "SpreadsheetML XML"}


class BlackRockHoldingsConnector(BaseConnector):
    """Connector for BlackRock holdings from the same local workbook."""

    source_system = "BLACKROCK"
    dataset_name = "holdings"

    def __init__(self, settings=None) -> None:
        super().__init__(settings)
        self.source_url = str(self.settings.blackrock_source_file)

    def load_sample_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        path = self.settings.blackrock_source_file
        return [], None, {
            "source_file": str(path),
            "worksheet": "All Funds",
            "note": "The provided workbook only contains fund metadata and no holdings worksheet.",
        }

    def fetch_live_records(self) -> tuple[list[dict[str, Any]], datetime | None, dict[str, Any]]:
        path = self.settings.blackrock_source_file
        return [], None, {
            "source_file": str(path),
            "worksheet": "All Funds",
            "note": "The provided workbook only contains fund metadata and no holdings worksheet.",
        }
