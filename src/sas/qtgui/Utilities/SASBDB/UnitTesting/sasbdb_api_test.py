"""Unit tests for SASBDB API helpers."""

import logging

from sas.qtgui.Utilities.SASBDB import sasbdb_api
from sas.qtgui.Utilities.SASBDB.sasbdb_api import (
    INVALID_DATASET_ID_MESSAGE,
    validateDatasetId,
)
from sas.qtgui.Utilities.SASBDB.sasbdb_display import metadata_summary
from sas.qtgui.Utilities.SASBDB.sasbdb_parse import (
    SASBDBDatasetInfo,
    parseMetadata,
)


class TestSASBDBApi:
    """Tests for SASBDB identifier validation and helpers."""

    def test_validate_dataset_id_accepts_mixed_alphanumeric(self):
        normalized, error = validateDatasetId("SASD2B2")
        assert error is None
        assert normalized == "SASD2B2"

        normalized, error = validateDatasetId("sasdn24")
        assert error is None
        assert normalized == "SASDN24"

    def test_validate_dataset_id_rejects_invalid(self):
        for bad_id in ("", "SAS", "SASD2B", "SASD2B22", "NOTASAS", "SAS!!22"):
            normalized, error = validateDatasetId(bad_id)
            assert normalized is None
            assert error == INVALID_DATASET_ID_MESSAGE

    def test_validate_dataset_id_does_not_log_warning(self, caplog):
        with caplog.at_level(logging.WARNING, logger=sasbdb_api.__name__):
            validateDatasetId("BADCODE")
        assert not any(
            "Invalid SASBDB dataset ID" in record.message
            for record in caplog.records
        )

    def test_guess_file_extension_from_metadata(self):
        assert sasbdb_api._guessFileExtension(
            "https://example.com/file", {"file_type": "CSV"}
        ) == ".csv"
        assert sasbdb_api._guessFileExtension(
            "https://example.com/file", {"format": "plain text"}
        ) == ".txt"
        assert sasbdb_api._guessFileExtension(
            "https://example.com/file", {"data_format": "intensity data"}
        ) == ".dat"
        assert sasbdb_api._guessFileExtension(
            "https://example.com/file.out", {}
        ) == ".out"
        assert sasbdb_api._guessFileExtension(
            "https://example.com/file", {}
        ) == ".dat"


class TestParseMetadata:
    """Field lookup order for SASBDB metadata."""

    def test_shallow_value_wins_over_a_deeper_alias(self):
        info = parseMetadata({
            "rg": 1.0,
            "experiment": {"guinier_rg": 9.0},
        })
        assert info.rg == 1.0

    def test_nested_alias_used_when_top_level_does_not_convert(self):
        info = parseMetadata({
            "rg": "bad",
            "experiment": {"radius_of_gyration": 4.0},
        })
        assert info.rg == 4.0

    def test_deep_value_and_sequence_found_outside_known_paths(self):
        info = parseMetadata({
            "title": "Top title",
            "sample": {"name": "Nested sample", "rg": "bad"},
            "analysis": {"guinier_rg": 12.5, "fasta": "ACDE"},
            "measurements": [{"buffer_ph": 7.2}],
            "molecules": [{"fasta_sequence": "SHOULD_NOT_WIN"}],
            "authors": ["A", "B"],
            "i0": 0.0,
        })
        assert info.title == "Top title"
        assert info.sample_name == "Nested sample"
        assert info.rg == 12.5
        assert info.ph == 7.2
        assert info.i0 == 0.0
        assert info.sequence == "ACDE"
        assert info.authors == ["A", "B"]

    def test_non_dict_metadata_is_empty(self):
        assert parseMetadata(None).title == ""
        assert parseMetadata([]).entry_id == ""


class TestSASBDBDisplay:
    """Tests for SASBDB display formatting helpers."""

    def test_metadata_summary_keeps_zero_numeric_values(self):
        info = SASBDBDatasetInfo(rg=0.0, rg_error=0.0, i0=0.0, i0_error=0.0)
        summary = metadata_summary(info)
        assert "Rg: 0.00 ± 0.00 Å" in summary
        assert "I(0): 0.0 ± 0.0" in summary
