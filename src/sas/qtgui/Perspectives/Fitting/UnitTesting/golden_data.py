"""
Qt-free data fixtures shared by the golden-file cases and the document tests.

Fixed values and ids, so that the legacy outputs are reproducible.
"""
import json
from pathlib import Path

import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D, Data2D

GOLDEN_DIR = Path(__file__).parent / "goldens"


def golden_path(name: str) -> Path:
    return GOLDEN_DIR / f"{name}.json"


def load_golden(name: str) -> list[dict]:
    with open(golden_path(name), encoding="utf-8") as f:
        return json.load(f)


def make_data1d(data_id: str, name: str, sesans: bool = False) -> Data1D:
    x = np.linspace(0.005, 0.4, 40)
    y = 1.0 / (1.0 + (x * 50.0) ** 2) + 0.01
    data = Data1D(x=x, y=y, dy=0.05 * y)
    data.id = data_id
    data.name = name
    data.filename = name + ".txt"
    if sesans:
        data.isSesans = True
        data.x = np.linspace(100.0, 10000.0, 40)
        data._xunit = "A"
        data.source.wavelength = np.full(40, 2.0)
        data.sample.zacceptance = (0.02, "radians")
    return data


def make_data2d(data_id: str, name: str) -> Data2D:
    n = 10
    qx, qy = np.meshgrid(np.linspace(-0.1, 0.1, n), np.linspace(-0.1, 0.1, n))
    qx, qy = qx.flatten(), qy.flatten()
    image = 1.0 / (1.0 + (np.hypot(qx, qy) * 50.0) ** 2) + 0.01
    data = Data2D(image=image, err_image=0.05 * image, qx_data=qx, qy_data=qy,
                  q_data=np.hypot(qx, qy), mask=np.ones(n * n, dtype=bool))
    data.xmin, data.xmax, data.ymin, data.ymax = -0.1, 0.1, -0.1, 0.1
    data.id = data_id
    data.name = name
    data.filename = name + ".dat"
    return data
