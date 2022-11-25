from typing import List

import numpy as np
from pyqtgraph.Transform3D import Transform3D

from sasmodels.jitter import Rx, Ry, Rz


class OrientationViewerGraphics:

    @staticmethod
    def createCubeTransform(theta_deg: float, phi_deg: float, psi_deg: float, scaling: List[float]) -> Transform3D:

        # Get rotation matrix
        r_mat = Rz(phi_deg)@Ry(theta_deg)@Rz(psi_deg)@np.diag(scaling)

        # Get the 4x4 transformation matrix, by (1) padding by zeros (2) setting the corner element to 1
        trans_mat = np.pad(r_mat, ((0, 1), (0, 1)))
        trans_mat[-1, -1] = 1
        trans_mat[2, -1] = 2

        return Transform3D(trans_mat)