import pandas as pd
import pytest

from upload_intelligence import read_dataset_upload, upload_preview


def test_csv_intake_reports_encoding_delimiter_shape_and_duplicates():
    frame, meta = read_dataset_upload(
        "orders.csv",
        "region;amount;amount\nNorth;12;12\nSouth;9;9\n".encode("utf-8"),
    )
    assert frame.shape == (2, 3)
    assert meta["delimiter"] == ";"
    assert meta["encoding"] == "utf-8-sig"
    assert meta["rows"] == 2
    assert any("Duplicate source headers" in warning for warning in meta["warnings"])


def test_tsv_intake_detects_tab_and_blank_headers():
    frame, meta = read_dataset_upload("export.tsv", "\tname\tvalue\n1\tA\t4\n".encode())
    assert frame.shape == (1, 3)
    assert meta["delimiter"] == "TAB"
    assert any("headers are blank" in warning for warning in meta["warnings"])


def test_non_utf8_csv_uses_windows_encoding_without_loss():
    frame, meta = read_dataset_upload("people.csv", "name,city\nAndré,Casablanca\n".encode("cp1252"))
    assert frame.loc[0, "name"] == "André"
    assert meta["encoding"] == "cp1252"


def test_malformed_csv_rows_are_rejected_instead_of_silently_skipped():
    with pytest.raises(ValueError, match="No rows were discarded"):
        read_dataset_upload("broken.csv", b"a,b\n1,2\n3,4,5\n")


def test_json_records_are_normalized_and_nested_values_are_disclosed():
    frame, meta = read_dataset_upload(
        "records.json",
        b'{"records":[{"name":"A","profile":{"city":"Rabat"}},{"name":"B","profile":{"city":"Agadir"}}]}',
    )
    assert frame["profile.city"].tolist() == ["Rabat", "Agadir"]
    assert any("Nested JSON" in warning for warning in meta["warnings"])


def test_json_rejects_scalar_payloads_with_actionable_error():
    with pytest.raises(ValueError, match="array of records"):
        read_dataset_upload("scalar.json", b'42')


def test_unsupported_extension_is_rejected_explicitly():
    with pytest.raises(ValueError, match="Unsupported file type"):
        read_dataset_upload("data.parquet", b"ignored")


def test_preview_is_copy_and_respects_limit():
    frame = pd.DataFrame({"x": range(12)})
    preview = upload_preview(frame, 5)
    assert len(preview) == 5
    preview.loc[0, "x"] = 999
    assert frame.loc[0, "x"] == 0
