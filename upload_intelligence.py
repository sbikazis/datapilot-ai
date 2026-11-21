from __future__ import annotations

import csv
import json
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls", ".json"}


def _csv_structure(text: str, delimiter: str) -> tuple[list[str], int]:
    """Return the raw header and count rows whose field count differs."""
    try:
        reader = csv.reader(StringIO(text), delimiter=delimiter)
        rows = iter(reader)
        header = next(rows, [])
        width = len(header)
        irregular = sum(1 for row in rows if row and len(row) != width)
        return header, irregular
    except (csv.Error, StopIteration):
        return [], 0


def _choose_text_encoding(payload: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return payload.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("The text file encoding could not be identified.")


def _choose_delimiter(sample: str, extension: str) -> str:
    if extension == ".tsv":
        return "\t"
    try:
        return csv.Sniffer().sniff(sample[:8192], delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def read_dataset_upload(
    filename: str,
    payload: bytes,
    sheet_name: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read a supported upload and return explicit, non-destructive intake metadata."""
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension or 'no extension'}.")

    metadata: dict[str, Any] = {
        "filename": Path(filename).name,
        "format": extension.lstrip(".").upper(),
        "encoding": None,
        "delimiter": None,
        "sheets": [],
        "selected_sheet": None,
        "raw_headers": [],
        "irregular_rows": 0,
        "warnings": [],
    }

    if extension in {".xlsx", ".xls"}:
        book = pd.ExcelFile(BytesIO(payload))
        metadata["sheets"] = list(book.sheet_names)
        if not book.sheet_names:
            raise ValueError("The workbook does not contain any worksheets.")
        selected = sheet_name if sheet_name in book.sheet_names else book.sheet_names[0]
        frame = pd.read_excel(BytesIO(payload), sheet_name=selected)
        metadata["selected_sheet"] = selected
        metadata["raw_headers"] = [str(value) for value in frame.columns]
    elif extension == ".json":
        try:
            parsed = json.loads(payload.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid JSON file: {exc}") from exc
        if isinstance(parsed, dict):
            for key in ("data", "records", "results", "items"):
                if isinstance(parsed.get(key), list):
                    parsed = parsed[key]
                    break
        if not isinstance(parsed, (list, dict)):
            raise ValueError("JSON must contain an array of records or an object with a records/data/items array.")
        frame = pd.json_normalize(parsed)
        metadata["encoding"] = "utf-8-sig"
        metadata["raw_headers"] = [str(value) for value in frame.columns]
        if any(isinstance(value, (dict, list)) for value in parsed) if isinstance(parsed, list) else False:
            metadata["warnings"].append("Nested JSON values were flattened into columns; review the preview before analysis.")
    else:
        text, encoding = _choose_text_encoding(payload)
        delimiter = _choose_delimiter(text, extension)
        headers, irregular = _csv_structure(text, delimiter)
        if irregular:
            raise ValueError(
                f"{irregular:,} non-empty row(s) have a different number of fields from the header. "
                "No rows were discarded; correct the source file or export it again."
            )
        try:
            frame = pd.read_csv(StringIO(text), sep=delimiter)
        except pd.errors.ParserError as exc:
            raise ValueError(f"Rows do not have a consistent number of fields. Check the delimiter or malformed rows. Details: {exc}") from exc
        metadata.update({
            "encoding": encoding,
            "delimiter": "TAB" if delimiter == "\t" else delimiter,
            "raw_headers": headers,
            "irregular_rows": irregular,
        })

    if frame.empty:
        metadata["warnings"].append("No data rows were found after reading the header.")
    if frame.columns.astype(str).str.strip().eq("").any() or any(not str(value).strip() for value in metadata["raw_headers"]):
        metadata["warnings"].append("One or more column headers are blank; generated placeholder names may be used.")
    normalized_headers = [str(value).strip().casefold() for value in metadata["raw_headers"]]
    duplicates = sorted({value for value in normalized_headers if value and normalized_headers.count(value) > 1})
    if duplicates:
        metadata["warnings"].append("Duplicate source headers detected: " + ", ".join(duplicates[:8]) + ". Rename them to avoid ambiguous field references.")
    if len(frame.columns) == 1 and extension in {".csv", ".tsv"}:
        metadata["warnings"].append("Only one column was detected. Confirm that the file delimiter was interpreted correctly.")
    metadata["rows"] = int(len(frame))
    metadata["columns"] = int(len(frame.columns))
    metadata["duplicate_rows"] = int(frame.duplicated().sum()) if not frame.empty else 0
    metadata["empty_columns"] = [str(column) for column in frame.columns if frame[column].isna().all()]
    if metadata["empty_columns"]:
        metadata["warnings"].append("Entirely empty columns: " + ", ".join(metadata["empty_columns"][:8]) + ".")
    return frame, metadata


def upload_preview(frame: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    """Return a display-only preview; never mutates or repairs the source frame."""
    if limit < 1:
        raise ValueError("Preview limit must be positive.")
    return frame.head(limit).copy()
