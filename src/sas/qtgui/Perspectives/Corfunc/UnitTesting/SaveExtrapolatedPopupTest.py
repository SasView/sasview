import numpy as np
import pytest
from PySide6.QtWidgets import QMessageBox

import sas.qtgui.Perspectives.Corfunc.SaveExtrapolatedPopup as save_extrapolated_popup_module
from sas.qtgui.Perspectives.Corfunc.SaveExtrapolatedPopup import SaveExtrapolatedPopup, SaveOutputPathExhausted


def test_save_extrapolated_creates_uncorrected_and_corrected_files(qapp, mocker, tmp_path):
    """Test that the _do_save method creates both uncorrected and background-corrected CSV files with the expected content."""
    q = np.array([0.1, 0.2, 0.3])
    intensity = np.array([10.0, 20.0, 30.0])
    background = 1.5

    popup = SaveExtrapolatedPopup(q, lambda qs: qs, background=background)

    output_path = tmp_path / "extrapolated.csv"
    mocker.patch(
        "sas.qtgui.Perspectives.Corfunc.SaveExtrapolatedPopup.QFileDialog.getSaveFileName",
        return_value=(str(output_path), ""))

    popup._do_save(q, intensity)

    uncorrected_lines = (tmp_path / "extrapolated_uncorrected.csv").read_text().splitlines()
    assert uncorrected_lines[0] == "Q, I(q)"
    assert uncorrected_lines[1] == "0.1, 10"
    assert uncorrected_lines[2] == "0.2, 20"
    assert uncorrected_lines[3] == "0.3, 30"

    corrected_lines = (tmp_path / "extrapolated_corrected.csv").read_text().splitlines()
    assert corrected_lines[0] == "Q, I(q)-Background"
    assert corrected_lines[1] == "0.1, 8.5"
    assert corrected_lines[2] == "0.2, 18.5"
    assert corrected_lines[3] == "0.3, 28.5"

@pytest.mark.parametrize(
    "user_choice, expect_suffix_files",
    [
        (QMessageBox.No, True),
        (QMessageBox.Yes, False),
    ],
    ids=["decline-overwrite", "confirm-overwrite"],
)
def test_save_extrapolated_does_not_overwrite(qapp, mocker, tmp_path, user_choice, expect_suffix_files):
    """
    Test that the _do_save method follows the user's choice regarding overwriting existing files:
        - if the user declines to overwrite, new files with incremented suffixes are created,
        - if the user confirms overwriting, the original files are overwritten and no new suffixed files are created.
    """
    q = np.array([0.2, 0.4, 0.6])
    intensity = np.array([20.0, 40.0, 60.0])
    background = 2

    popup = SaveExtrapolatedPopup(q, lambda qs: qs, background=background)

    output_path = tmp_path / "extrapolated.csv"
    mocker.patch(
        "sas.qtgui.Perspectives.Corfunc.SaveExtrapolatedPopup.QFileDialog.getSaveFileName",
        return_value=(str(output_path), "")
    )
    mocker.patch(
        "sas.qtgui.Perspectives.Corfunc.SaveExtrapolatedPopup.QMessageBox.question",
        return_value=user_choice
    )

    original_uncorrected = tmp_path / "extrapolated_uncorrected.csv"
    original_corrected = tmp_path / "extrapolated_corrected.csv"
    original_uncorrected.write_text("existing uncorrected\n")
    original_corrected.write_text("existing corrected\n")

    popup._do_save(q, intensity)

    suffixed_uncorrected = tmp_path / "extrapolated_uncorrected_1.csv"
    suffixed_corrected = tmp_path / "extrapolated_corrected_1.csv"

    if expect_suffix_files:
        # Verify that original files were not overwritten
        assert original_uncorrected.read_text() == "existing uncorrected\n"
        assert original_corrected.read_text() == "existing corrected\n"

        new_uncorrected_lines = suffixed_uncorrected.read_text().splitlines()
        assert new_uncorrected_lines[0] == "Q, I(q)"
        assert new_uncorrected_lines[1] == "0.2, 20"
        assert new_uncorrected_lines[2] == "0.4, 40"
        assert new_uncorrected_lines[3] == "0.6, 60"

        new_corrected_lines = suffixed_corrected.read_text().splitlines()
        assert new_corrected_lines[0] == "Q, I(q)-Background"
        assert new_corrected_lines[1] == "0.2, 18"
        assert new_corrected_lines[2] == "0.4, 38"
        assert new_corrected_lines[3] == "0.6, 58"
    else:
        # Verify that original files were overwritten
        new_uncorrected_lines = original_uncorrected.read_text().splitlines()
        assert new_uncorrected_lines[0] == "Q, I(q)"
        assert new_uncorrected_lines[1] == "0.2, 20"
        assert new_uncorrected_lines[2] == "0.4, 40"
        assert new_uncorrected_lines[3] == "0.6, 60"

        new_corrected_lines = original_corrected.read_text().splitlines()
        assert new_corrected_lines[0] == "Q, I(q)-Background"
        assert new_corrected_lines[1] == "0.2, 18"
        assert new_corrected_lines[2] == "0.4, 38"
        assert new_corrected_lines[3] == "0.6, 58"

        # Verify that no new files with incremented suffixes were created
        assert not suffixed_uncorrected.exists()
        assert not suffixed_corrected.exists()

def test_next_available_output_paths_raises_when_suffix_limit_reached(tmp_path, monkeypatch):
    """
    Test that _next_available_output_paths raises SaveOutputPathExhausted
    when the maximum number of suffix attempts is exceeded.
    """
    base_path = tmp_path / "extrapolated"
    (tmp_path / "extrapolated_uncorrected_1.csv").write_text("x\n")
    (tmp_path / "extrapolated_corrected_1.csv").write_text("x\n")

    monkeypatch.setattr(save_extrapolated_popup_module, "MAX_SUFFIX_ATTEMPTS", 1)

    with pytest.raises(SaveOutputPathExhausted):
        SaveExtrapolatedPopup._next_available_output_paths(base_path)
