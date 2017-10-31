interface_color = 'black'
disable_color = 'gray'
active_color = 'red'
rho_color = 'black'
mu_color = 'green'
P_color = 'blue'
theta_color = 'orange'
profile_colors = [rho_color, mu_color, P_color, theta_color]

class BaseInteractor(object):
    """
    Share some functions between the interface interactor and various layer
    interactors.

    Individual interactors need the following functions:

        save(ev)  - save the current state for later restore
        restore() - restore the old state
        move(x,y,ev) - move the interactor to position x,y
        moveend(ev) - end the drag event
        update() - draw the interactors

    The following are provided by the base class:

        connect_markers(markers) - register callbacks for all markers
        clear_markers() - remove all items in self.markers
        onHilite(ev) - enter/leave event processing
        onLeave(ev) - enter/leave event processing
        onClick(ev) - mouse click: calls save()
        onRelease(ev) - mouse click ends: calls moveend()
        onDrag(ev) - mouse move: calls move() or restore()
        onKey(ev) - keyboard move: calls move() or restore()

    Interactor attributes:

        base  - model we are operating on
        axes  - axes holding the interactor
        color - color of the interactor in non-active state
        markers - list of handles for the interactor

    """
    def __init__(self, base, axes, color='black'):
        """
        """
        self.base = base
        self.axes = axes
        self.color = color
        self.clickx = None
        self.clicky = None
        self.markers = []

    def clear_markers(self):
        """
        Clear old markers and interfaces.
        """
        for h in self.markers: h.remove()
        if self.markers:
            self.base.connect.clear(*self.markers)
        self.markers = []

    def save(self, ev):
        """
        """
        pass

    def restore(self, ev):
        """
        """
        pass

    def move(self, x, y, ev):
        """
        """
        pass

    def moveend(self, ev):
        """
        """
        pass

    def connect_markers(self, markers):
        """
        Connect markers to callbacks
        """

        for h in markers:
            connect = self.base.connect
            connect('enter', h, self.onHilite)
            connect('leave', h, self.onLeave)
            connect('click', h, self.onClick)
            connect('release', h, self.onRelease)
            connect('drag', h, self.onDrag)
            connect('key', h, self.onKey)

    def onHilite(self, ev):
        """
        Hilite the artist reporting the event, indicating that it is
        ready to receive a click.
        """
        ev.artist.set_color(active_color)
        self.base.draw()
        return True

    def onLeave(self, ev):
        """
        Restore the artist to the original colour when the cursor leaves.
        """
        ev.artist.set_color(self.color)
        self.base.draw()
        return True

    def onClick(self, ev):
        """
        Prepare to move the artist.  Calls save() to preserve the state for
        later restore().
        """
        self.clickx, self.clicky = ev.xdata, ev.ydata
        self.save(ev)
        return True

    def onRelease(self, ev):
        """
        """
        self.moveend(ev)
        return True

    def onDrag(self, ev):
        """
        Move the artist.  Calls move() to update the state, or restore() if
        the mouse leaves the window.
        """
        inside, _ = self.axes.contains(ev)
        if inside:
            self.clickx, self.clicky = ev.xdata, ev.ydata
            self.move(ev.xdata, ev.ydata, ev)
        else:
            self.restore()
        self.base.update()
        return True

    def onKey(self, ev):
        """
        Respond to keyboard events.  Arrow keys move the widget.  Escape
        restores it to the position before the last click.

        Calls move() to update the state.  Calls restore() on escape.
        """
        if ev.key == 'escape':
            self.restore()
        elif ev.key in ['up', 'down', 'right', 'left']:
            dx, dy = self.dpixel(self.clickx, self.clicky, nudge=ev.control)
            if ev.key == 'up':
                self.clicky += dy
            elif ev.key == 'down':
                self.clicky -= dy
            elif ev.key == 'right':
                self.clickx += dx
            else: self.clickx -= dx
            self.move(self.clickx, self.clicky, ev)
        else:
            return False
        self.base.update()
        return True

    def dpixel(self, x, y, nudge=False):
        """
        Return the step size in data coordinates for a small
        step in screen coordinates.  If nudge is False (default)
        the step size is one pixel.  If nudge is True, the step
        size is 0.2 pixels.
        """
        ax = self.axes
        px, py = ax.transData.inverse_xy_tup((x, y))
        if nudge:
            nx, ny = ax.transData.xy_tup((px + 0.2, py + 0.2))
        else:
            nx, ny = ax.transData.xy_tup((px + 1.0, py + 1.0))
        dx, dy = nx - x, ny - y
        return dx, dy

