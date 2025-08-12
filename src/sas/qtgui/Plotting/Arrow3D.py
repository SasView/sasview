"""
Module that draws multiple arrows in 3D coordinates
"""

import time

import numpy as np
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d


# from matplotlib.artist import allow_rasterization
class Arrow3D(FancyArrowPatch):
    """
    Draw 3D arrow
    """

    def __init__(self, base, xs, ys, zs, colors, *args, **kwargs):
        """
        Init
        :Params xs: [[x0, x0+dx0], [x1, x1+dx1], ...]
        :Params ys: [[y0, y0+dy0], [y1, y1+dy1], ...]
        :Params zs: [[z0, z0+dz0], [z1, z1+dz1], ...]
        :Params colors: [[R0, G0, B0], [R1, G1, B1], ...]
        where R, G, B ranges (0,1)
        """
        super().__init__((0, 0), (0, 0), *args, **kwargs)
        self.leftdown = False
        self.realtime = False
        self.t_click = 0
        self._verts3d = xs, ys, zs
        self.colors = colors
        self.base = base

        if base is not None:
            # To turn the updating off during dragging
            base.canvas.mpl_connect('button_press_event', self.on_left_down)
            base.canvas.mpl_connect('button_release_event', self.on_left_up)

    def set_realtime(self, realtime):
        """
            Bool specifying whether arrows should be shown rotating while dragging is in progress
            May be slow for large numbers of arrows
        """
        self.realtime = realtime

    def on_left_down(self, event):
        """
            Mouse left-down event
        """
        self.leftdown = True
        self.t_click = time.time()

    def on_left_up(self, event):
        """
            Mouse left up event
        """
        t_up = time.time() - self.t_click
        # Avoid just clicking
        if t_up > 0.1:
            self.leftdown = False
            self.base.canvas.draw()

    def update_data(self, xs, ys, zs):
        self._verts3d = xs, ys, zs
        self.base.canvas.draw()

    def do_3d_projection(self):
        """
        Drawing actually happens here
        """
        # Draws only when the dragging finished
        if self.leftdown and not self.realtime:
            return
        xs3d, ys3d, zs3d = self._verts3d
        zmins = []
        for i in range(len(xs3d)):
            xs, ys, zs = proj3d.proj_transform(xs3d[i], ys3d[i], zs3d[i], self.axes.M)
            self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
            self.set_color(self.colors[i])
            zmins.append(np.min(zs))

        self.leftdown = False
        return min(zmins)
