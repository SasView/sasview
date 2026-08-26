"""Unit tests for SASBDB API helpers."""

import logging

from sas.qtgui.Utilities.SASBDB import sasbdb_api
from sas.qtgui.Utilities.SASBDB.sasbdb_api import (
    INVALID_DATASET_ID_MESSAGE,
    validateDatasetId,
)
from sas.qtgui.Utilities.SASBDB.sasbdb_display import metadata_summary
from sas.qtgui.Utilities.SASBDB.sasbdb_parse import SASBDBDatasetInfo


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


class TestSASBDBDisplay:
    """Tests for SASBDB display formatting helpers."""

    def test_metadata_summary_keeps_zero_numeric_values(self):
        info = SASBDBDatasetInfo(rg=0.0, rg_error=0.0, i0=0.0, i0_error=0.0)
        summary = metadata_summary(info)
        assert "Rg: 0.00 ± 0.00 Å" in summary
        assert "I(0): 0.0 ± 0.0" in summary
