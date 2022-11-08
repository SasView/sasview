from sas.qtgui.GL.WireModel import WireModel
from sas.qtgui.GL.SolidModel import SolidModel


class Cube(WireModel, SolidModel):
    """ Unit cube centred at 0,0,0"""

    vertices = [

    ]

    def __init__(self, face_colors=None, edge_colors=None):
        self.wireframe_render_enabled = edge_colors is not None
        self.solid_render_enabled = face_colors is not None




