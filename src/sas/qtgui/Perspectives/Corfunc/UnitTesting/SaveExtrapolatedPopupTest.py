import numpy as np

from sas.qtgui.Perspectives.Corfunc.SaveExtrapolatedPopup import SaveExtrapolatedPopup


def test_save_extrapolated_creates_uncorrected_and_corrected_files(qapp, mocker, tmp_path):
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
