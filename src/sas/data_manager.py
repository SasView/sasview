"""Bookkeeping of all the data loaded into SasView, and of which objects use
which.

Objects are tracked with `shared_ptr`-like semantics. An object (the holder)
using another tracked object (the target) does so through a `DataReference`,
obtained from `NewDataManager.reference` and kept as one of the holder's
fields. The data explorer itself holds a reference to every top-level item. An
object stays tracked as long as anything references it. Once nothing does, it
is destroyed, releasing its own references in turn. Callers only deal with
their own objects and references, never with how the data manager stores them.

Values owned by a single object, which are never shared or shown in the
explorer, are kept as plain fields rather than references.

This module must not depend on Qt. The GUI integrates with the data manager by
connecting callbacks to its hooks (see `NewDataManager`).

The data manager is not thread safe. It must only be modified from one thread
(in practice the GUI thread), since the hooks run synchronously on the thread
that modified it.
"""
import logging
from collections.abc import Callable
from typing import TypeVar

from sasdata.data import SasData, SasMeasurement
from sasdata.trend import Trend

from sas.refactored_plotting.PlotModifiers import PlotModifier
from sas.tracked_objects import TrackedFit, TrackedPlot

logger = logging.getLogger(__name__)

# The data types known to the data manager. The GUI may track further objects
# (e.g. perspectives), which the data manager treats as opaque.
TrackedData = SasData | SasMeasurement | Trend | TrackedFit | TrackedPlot | PlotModifier

T = TypeVar('T')


class Hook[*Args]:
    """A minimal observer list, used in place of Qt signals.

    Callbacks run synchronously, in the order they were connected. An exception
    raised by a callback is logged, and does not prevent the remaining callbacks
    from running.
    """

    def __init__(self) -> None:
        self._callbacks: list[Callable[[*Args], object]] = []

    def connect(self, callback: Callable[[*Args], object]) -> None:
        self._callbacks.append(callback)

    def disconnect(self, callback: Callable[[*Args], object]) -> None:
        self._callbacks.remove(callback)

    def emit(self, *args: *Args) -> None:
        for callback in list(self._callbacks):
            try:
                callback(*args)
            except Exception:
                logger.exception("Error in data manager hook callback %r", callback)


class _Node:
    """Internal wrapper around a tracked object, recording the references from
    and to it. Only modified through `NewDataManager._link` and `_unlink`, which
    keep both sides consistent."""
    __slots__ = ("data", "references", "dependents")

    def __init__(self, data: object):
        self.data = data
        # The references this node holds, in the order they were made.
        self.references: list[DataReference] = []
        # The references to this node.
        self.dependents: list[DataReference] = []


class DataReference[T]:
    """A handle through which a holder uses a tracked object (the target),
    keeping it alive. Obtained from `NewDataManager.reference`. Release it once
    the holder no longer needs the target; all of a holder's references are
    released automatically when the holder itself is destroyed."""
    __slots__ = ("_manager", "_holder", "_target", "_released")

    def __init__(self, manager: "NewDataManager", holder: _Node, target: _Node):
        self._manager = manager
        self._holder = holder
        self._target = target
        self._released = False

    def get(self) -> T:
        if self._released:
            raise ValueError("This reference has been released.")
        return self._target.data

    @property
    def released(self) -> bool:
        return self._released

    def __bool__(self) -> bool:
        """False once released, so `if ref:` checks whether it can be used."""
        return not self._released

    def release(self):
        if not self._released:
            self._manager._release(self)


class NewDataManager:
    """Tracks data, and the references between them.

    Hooks:
        data_added(datum): datum was added to the top level of the explorer.
        data_removed(datum): datum was removed from the top level of the
            explorer. It stays tracked as long as anything references it.
        reference_added(holder, target): holder now references target.
        reference_removed(holder, target): holder no longer references target.
        data_destroyed(datum): nothing references datum any more, so it is no
            longer tracked. Anything showing it should be closed.
        data_changed(datum): a tracked datum changed, and anything displaying it
            should be updated. Triggered by `notify_changed`.
    """

    def __init__(self):
        # The root's references are the top-level items of the explorer.
        self._root = _Node(None)
        # Keyed by id, since tracked objects aren't necessarily hashable. The
        # nodes keep the objects alive, so ids can't be reused while tracked.
        self._nodes: dict[int, _Node] = {}

        self.data_added = Hook[object]()
        self.data_removed = Hook[object]()
        self.reference_added = Hook[object, object]()
        self.reference_removed = Hook[object, object]()
        self.data_destroyed = Hook[object]()
        self.data_changed = Hook[object]()

    # Internals

    def _node(self, data: object) -> _Node:
        node = self._nodes.get(id(data))
        if node is None:
            raise ValueError(f"{data!r} is not tracked by the data manager.")
        return node

    def _link(self, holder: _Node, target: _Node) -> DataReference:
        ref = DataReference(self, holder, target)
        holder.references.append(ref)
        target.dependents.append(ref)
        return ref

    @staticmethod
    def _unlink(ref: DataReference):
        ref._holder.references.remove(ref)
        ref._target.dependents.remove(ref)
        ref._released = True

    @staticmethod
    def _reaches(start: _Node, goal: _Node) -> bool:
        """Whether goal can be reached from start by following references."""
        to_visit = [start]
        visited: set[int] = set()
        while to_visit:
            node = to_visit.pop()
            if node is goal:
                return True
            if id(node) not in visited:
                visited.add(id(node))
                to_visit.extend(ref._target for ref in node.references)
        return False

    def _root_reference(self, node: _Node) -> DataReference | None:
        return next((ref for ref in node.dependents if ref._holder is self._root), None)

    def _release(self, ref: DataReference):
        self._unlink(ref)
        if ref._holder is self._root:
            self.data_removed.emit(ref._target.data)
        else:
            self.reference_removed.emit(ref._holder.data, ref._target.data)
        self._destroy_if_unused(ref._target)

    def _destroy_if_unused(self, node: _Node):
        if node.dependents:
            return
        for ref in list(node.references):
            self._release(ref)
        del self._nodes[id(node.data)]
        self.data_destroyed.emit(node.data)

    # Modification

    def add_data(self, data: object):
        """Add data to the top level of the explorer, tracking it if it isn't
        already."""
        node = self._nodes.get(id(data))
        if node is None:
            node = self._nodes[id(data)] = _Node(data)
        elif self._root_reference(node) is not None:
            return
        self._link(self._root, node)
        self.data_added.emit(data)

    def remove_data(self, data: object):
        """Remove data from the top level of the explorer. It is destroyed once
        nothing else references it."""
        node = self._node(data)
        root_reference = self._root_reference(node)
        if root_reference is not None:
            self._release(root_reference)
        else:
            self._destroy_if_unused(node)

    def reference[U](self, holder: object, target: U) -> DataReference[U]:
        """A new reference through which holder uses target. Both must already
        be tracked."""
        holder_node = self._node(holder)
        target_node = self._node(target)
        # A cycle would keep its members alive forever.
        if self._reaches(target_node, holder_node):
            raise ValueError(f"{target!r} already depends on {holder!r}.")
        ref = self._link(holder_node, target_node)
        self.reference_added.emit(holder, target)
        return ref

    def notify_changed(self, data: object):
        """Tell everything displaying data that it should be updated."""
        self.data_changed.emit(data)

    def register_trend(self, trend: Trend):
        # Trends come from sasdata, so they can't hold references themselves.
        # Their references are only kept here, and released when the trend is
        # destroyed.
        self.add_data(trend)
        for datum in trend.data:
            self.reference(trend, datum)

    # Queries. These treat untracked objects as having no references.

    def is_tracked(self, data: object) -> bool:
        return id(data) in self._nodes

    def references_of(self, holder: object, of_type: type[T] = object) -> list[T]:
        """The objects of type of_type which holder references."""
        node = self._nodes.get(id(holder))
        if node is None:
            return []
        return [ref._target.data for ref in node.references if isinstance(ref._target.data, of_type)]

    def dependents_of(self, target: object, of_type: type[T] = object) -> list[T]:
        """The objects of type of_type which reference target."""
        node = self._nodes.get(id(target))
        if node is None:
            return []
        return [ref._holder.data for ref in node.dependents
                if ref._holder is not self._root and isinstance(ref._holder.data, of_type)]

    @property
    def all_data(self) -> list[object]:
        """The top-level items of the explorer."""
        return [ref._target.data for ref in self._root.references]

    def data_of_type(self, data_type: type[T]) -> list[T]:
        """The top-level items of the explorer of type data_type."""
        return [ref._target.data for ref in self._root.references if isinstance(ref._target.data, data_type)]

    @property
    def default_new_trend_name(self) -> str:
        trend_number = len(self.data_of_type(Trend)) + 1
        return f"Trend #{trend_number}"
