"""
Extension to MPL to support the binding of artists to key/mouse events.
"""


import sys
import logging

logger = logging.getLogger(__name__)

class Selection(object):
    """
    Store and compare selections.
    """
    # TODO: We need some way to check in prop matches, preferably
    # TODO: without imposing structure on prop.

    artist = None
    prop = {}

    def __init__(self, artist=None, prop={}):
        self.artist, self.prop = artist, self.prop

    def __eq__(self, other):
        return self.artist is other.artist

    def __ne__(self, other):
        return self.artist is not other.artist

    def __bool__(self):
        return self.artist is not None


class BindArtist(object):
    """
    """
    # Track keyboard modifiers for events.
    # TODO: Move keyboard modifier support into the backend.  We cannot
    # TODO: properly support it from outside the windowing system since there
    # TODO: is no way to recognized whether shift is held down when the mouse
    # TODO: first clicks on the the application window.
    control, shift, alt, meta = False, False, False, False

    # Track doubleclick
    dclick_threshhold = 0.25
    _last_button, _last_time = None, 0

    # Mouse/keyboard events we can bind to
    events = ['enter', 'leave', 'motion', 'click', 'dclick', 'drag', 'release',
              'scroll', 'key', 'keyup']
    # TODO: Need our own event structure

    def __init__(self, figure):
        canvas = figure.canvas

        # Link to keyboard/mouse
        try:
            self._connections = [
                canvas.mpl_connect('motion_notify_event', self._onMotion),
                canvas.mpl_connect('button_press_event', self._onClick),
                canvas.mpl_connect('button_release_event', self._onRelease),
                canvas.mpl_connect('key_press_event', self._onKey),
                canvas.mpl_connect('key_release_event', self._onKeyRelease),
                canvas.mpl_connect('scroll_event', self._onScroll)
            ]
        except:
            print("bypassing scroll_event: wrong matplotlib version")
            self._connections = [
                canvas.mpl_connect('motion_notify_event', self._onMotion),
                canvas.mpl_connect('button_press_event', self._onClick),
                canvas.mpl_connect('button_release_event', self._onRelease),
                canvas.mpl_connect('key_press_event', self._onKey),
                canvas.mpl_connect('key_release_event', self._onKeyRelease),
            ]

        self._current = None
        self._actions = {}
        self.canvas = canvas
        self.figure = figure
        self.clearall()

    def clear(self, *artists):
        """
        self.clear(h1,h2,...)
            Remove connections for artists h1, h2, ...

        Use clearall() to reset all connections.
        """

        for h in artists:
            for a in self.events:
                if h in self._actions[a]:
                    del self._actions[a][h]
            if h in self._artists:
                self._artists.remove(h)
        if self._current.artist in artists:
            self._current = Selection()
        if self._hasclick.artist in artists:
            self._hasclick = Selection()
        if self._haskey.artist in artists:
            self._haskey = Selection()

    def clearall(self):
        """
        Clear connections to all artists.

        Use clear(h1,h2,...) to reset specific artists.
        """
        # Don't monitor any actions
        self._actions = {}
        for action in self.events:
            self._actions[action] = {}

        # Need activity state
        self._artists = []
        self._current = Selection()
        self._hasclick = Selection()
        self._haskey = Selection()

    def disconnect(self):
        """
        In case we need to disconnect from the canvas...
        """
        try:
            for cid in self._connections: self.canvas.mpl_disconnect(cid)
        except:
            logger.error("Error disconnection canvas: %s" % sys.exc_info()[1])
        self._connections = []

    def __del__(self):
        self.disconnect()

    def __call__(self, trigger, artist, action):
        """Register a callback for an artist to a particular trigger event.

        usage:
            self.connect(eventname,artist,action)

        where:
            eventname is a string
            artist is the particular graph object to respond to the event
            action(event,**kw) is called when the event is triggered

        The action callback is associated with particular artists.
        Different artists will have different kwargs.  See documentation
        on the contains() method for each artist.  One common properties
        are ind for the index of the item under the cursor, which is
        returned by Line2D and by collections.

        The following events are supported:
            enter: mouse cursor moves into the artist or to a new index
            leave: mouse cursor leaves the artist
            click: mouse button pressed on the artist
            drag: mouse button pressed on the artist and cursor moves
            release: mouse button released for the artist
            key: key pressed when mouse is on the artist
            keyrelease: key released for the artist

        The event received by action has a number of attributes:
            name is the event name which was triggered
            artist is the object which triggered the event
            x,y are the screen coordinates of the mouse
            xdata,ydata are the graph coordinates of the mouse
            button is the mouse button being pressed/released
            key is the key being pressed/released
            shift,control,alt,meta are flags which are true if the
                corresponding key is pressed at the time of the event.
            details is a dictionary of artist specific details, such as the
                id(s) of the point that were clicked.

        When receiving an event, first check the modifier state to be
        sure it applies.  E.g., the callback for 'press' might be:
            if event.button == 1 and event.shift: process Shift-click

        TODO: Only receive events with the correct modifiers (e.g., S-click,
        TODO:   or *-click for any modifiers).
        TODO: Only receive button events for the correct button (e.g., click1
        TODO:   release3, or dclick* for any button)
        TODO: Support virtual artist, so that and artist can be flagged as
        TODO:   having a tag list and receive the correct events
        TODO: Support virtual events for binding to button-3 vs shift button-1
        TODO:   without changing callback code
        TODO: Attach multiple callbacks to the same event?
        TODO: Clean up interaction with toolbar modes
        TODO: push/pushclear/pop context so that binding changes for
             the duration
        TODO:   e.g., to support ? context sensitive help
        """
        # Check that the trigger is valid
        if trigger not in self._actions:
            raise ValueError("%s invalid --- valid triggers are %s"\
                 % (trigger, ", ".join(self.events)))

        # Register the trigger callback
        self._actions[trigger][artist] = action

        # Maintain a list of all artists
        if artist not in self._artists:
            self._artists.append(artist)

    def trigger(self, actor, action, ev):
        """
        Trigger a particular event for the artist.  Fallback to axes,
        to figure, and to 'all' if the event is not processed.
        """
        if action not in self.events:
            raise ValueError("Trigger expects " + ", ".join(self.events))

        # Tag the event with modifiers
        for mod in ('alt', 'control', 'shift', 'meta'):
            setattr(ev, mod, getattr(self, mod))
        setattr(ev, 'artist', None)
        setattr(ev, 'action', action)
        setattr(ev, 'prop', {})

        # Fallback scheme.  If the event does not return false, pass to parent.
        processed = False
        artist, prop = actor.artist, actor.prop
        if artist in self._actions[action]:
            ev.artist, ev.prop = artist, prop
            processed = self._actions[action][artist](ev)
        if not processed and ev.inaxes in self._actions[action]:
            ev.artist, ev.prop = ev.inaxes, {}
            processed = self._actions[action][ev.inaxes](ev)
        if not processed and self.figure in self._actions[action]:
            ev.artist, ev.prop = self.figure, {}
            processed = self._actions[action][self.figure](ev)
        if not processed and 'all' in self._actions[action]:
            ev.artist, ev.prop = None, {}
            processed = self._actions[action]['all'](ev)
        return processed

    def _find_current(self, event):
        """
        Find the artist who will receive the event.  Only search
        registered artists.  All others are invisible to the mouse.
        """
        # TODO: sort by zorder of axes then by zorder within axes
        self._artists.sort(cmp=lambda x, y: cmp(y.zorder, x.zorder))
        found = Selection()
        for artist in self._artists:
            # TODO: should contains() return false if invisible?
            if not artist.get_visible():
                continue
            # TODO: optimization - exclude artists not inaxes
            try:
                inside, prop = artist.contains(event)
            except:
                # Probably an old version of matplotlib
                inside = False
            if inside:
                found.artist, found.prop = artist, prop
                break

        # TODO: how to check if prop is equal?
        if found != self._current:
            self.trigger(self._current, 'leave', event)
            self.trigger(found, 'enter', event)
        self._current = found

        return found

    def _onMotion(self, event):
        """
        Track enter/leave/motion through registered artists; all
        other artists are invisible.
        """
        # # Can't kill double-click on motion since Windows produces
        # # spurious motion events.
        # self._last_button = None

        # Dibs on the motion event for the clicked artist
        if self._hasclick:
            # Make sure the x,y data use the coordinate system of the
            # artist rather than the default axes coordinates.

            transform = self._hasclick.artist.get_transform()
            # x,y = event.xdata,event.ydata
            x, y = event.x, event.y
            try:
                if transform.__class__.__name__ == "IdentityTransform":
                    x, y = transform.inverted().transform((x, y))
                else:
                    # # For interactive plottable apply transform is not working
                    # # don't know why maybe marker definition
                    # #transform ="CompositeGenericTransform" crash
                    pass
            except:
                # # CRUFT matplotlib-0.91 support
                # # exception for transform ="CompositeGenericTransform"
                # # crashes also here
                x, y = transform.inverse_xy_tup((x, y))

            # event.xdata, event.ydata = x, y
            self.trigger(self._hasclick, 'drag', event)
        else:
            found = self._find_current(event)
            self.trigger(found, 'motion', event)

    def _onClick(self, event):
        """
        Process button click
        """
        import time

        # Check for double-click
        event_time = time.time()
        if (event.button != self._last_button) or \
                (event_time > self._last_time + self.dclick_threshhold):
            action = 'click'
        else:
            action = 'dclick'
        self._last_button = event.button
        self._last_time = event_time

        # If an artist is already dragging, feed any additional button
        # presses to that artist.
        # TODO: do we want to force a single button model on the user?
        # TODO: that is, once a button is pressed, no other buttons
        # TODO: can come through?  I think this belongs in canvas, not here.
        if self._hasclick:
            found = self._hasclick
        else:
            found = self._find_current(event)
        # print "button %d pressed"%event.button
        # Note: it seems like if "click" returns False then hasclick should
        # not be set.  The problem is that there are two reasons it can
        # return false: because there is no click action for this artist
        # or because the click action returned false.  A related problem
        # is that click actions will go to the canvas if there is no click
        # action for the artist, even if the artist has a drag. I'll leave
        # it to future maintainers to sort out this problem.  For now the
        # recommendation is that users should define click if they have
        # drag or release on the artist.
        self.trigger(found, action, event)
        self._hasclick = found

    def _onDClick(self, event):
        """
        Process button double click
        """
        # If an artist is already dragging, feed any additional button
        # presses to that artist.
        # TODO: do we want to force a single button model on the user?
        # TODO: that is, once a button is pressed, no other buttons
        # TODO: can come through?  I think this belongs in canvas, not here.
        if self._hasclick:
            found = self._hasclick
        else:
            found = self._find_current(event)
        self.trigger(found, 'dclick', event)
        self._hasclick = found

    def _onRelease(self, event):
        """
        Process release release
        """
        self.trigger(self._hasclick, 'release', event)
        self._hasclick = Selection()

    def _onKey(self, event):
        """
        Process key click
        """
        # TODO: Do we really want keyboard focus separate from mouse focus?
        # TODO: Do we need an explicit focus command for keyboard?
        # TODO: Can we tab between items?
        # TODO: How do unhandled events get propogated to axes, figure and
        # TODO: finally to application?  Do we need to implement a full tags
        # TODO: architecture a la Tk?
        # TODO: Do modifiers cause a grab?  Does the artist see the modifiers?
        if event.key in ('alt', 'meta', 'control', 'shift'):
            setattr(self, event.key, True)
            return

        if self._haskey:
            found = self._haskey
        else:
            found = self._find_current(event)
        self.trigger(found, 'key', event)
        self._haskey = found

    def _onKeyRelease(self, event):
        """
        Process key release
        """
        if event.key in ('alt', 'meta', 'control', 'shift'):
            setattr(self, event.key, False)
            return

        if self._haskey:
            self.trigger(self._haskey, 'keyup', event)
        self._haskey = Selection()

    def _onScroll(self, event):
        """
        Process scroll event
        """
        found = self._find_current(event)
        self.trigger(found, 'scroll', event)
