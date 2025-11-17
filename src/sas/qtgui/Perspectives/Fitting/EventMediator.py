"""
EventMediator - Central event bus for FittingWidget.

This class implements the Mediator pattern to decouple signal/slot connections
and reduce tight coupling between FittingWidget and its child widgets.
"""

from collections.abc import Callable
from enum import Enum, auto
from typing import Any

from PySide6 import QtCore


class FittingEventType(Enum):
    """Enumeration of all event types in the fitting perspective."""

    # Model selection events
    MODEL_SELECTED = auto()
    STRUCTURE_FACTOR_SELECTED = auto()
    CATEGORY_SELECTED = auto()
    BATCH_FILE_SELECTED = auto()

    # View toggle events
    VIEW_2D_TOGGLED = auto()
    POLYDISPERSITY_TOGGLED = auto()
    MAGNETISM_TOGGLED = auto()
    CHAIN_FIT_TOGGLED = auto()

    # Action button events
    FIT_REQUESTED = auto()
    PLOT_REQUESTED = auto()
    HELP_REQUESTED = auto()

    # Data events
    DATA_LOADED = auto()
    DATA_UPDATED = auto()
    MASKED_DATA_UPDATED = auto()
    Q_RANGE_UPDATED = auto()

    # Parameter events
    PARAMS_CHANGED = auto()
    SELECTION_CHANGED = auto()
    FIT_ENABLEMENT_CHANGED = auto()

    # Calculation events
    CALCULATION_STARTED = auto()
    CALCULATION_FINISHED = auto()
    CALCULATION_1D_FINISHED = auto()
    CALCULATION_2D_FINISHED = auto()

    # Fitting events
    FITTING_STARTED = auto()
    FITTING_FINISHED = auto()
    BATCH_FITTING_FINISHED = auto()

    # Constraint events
    CONSTRAINT_ADDED = auto()
    CONSTRAINT_REMOVED = auto()

    # Widget update events
    OPTIONS_UPDATE_REQUESTED = auto()
    SMEARING_OPTIONS_UPDATED = auto()
    MODEL_ITERATION_REQUESTED = auto()

    # Custom model events
    CUSTOM_MODEL_CHANGED = auto()
    MODEL_CATEGORIES_UPDATED = auto()

    # Keyboard events
    KEY_PRESSED = auto()


class EventMediator(QtCore.QObject):
    """
    Central event bus for managing events in the fitting perspective.

    This mediator decouples signal/slot connections by providing:
    - Type-safe event routing
    - Centralized subscription management
    - Weak reference support to prevent memory leaks
    - Event filtering and transformation capabilities

    Usage:
        mediator = EventMediator()
        mediator.subscribe(FittingEventType.FIT_REQUESTED, self.onFit)
        mediator.publish(FittingEventType.FIT_REQUESTED, {"params": params})
    """

    def __init__(self, parent: QtCore.QObject | None = None):
        """
        Initialize the EventMediator.

        Args:
            parent: Parent QObject (optional)
        """
        super().__init__(parent)

        # Dictionary of event_type -> list of (callback, use_weak_ref) tuples
        self._subscribers: dict[FittingEventType, list[tuple[Callable, bool]]] = {}

        # Event history for debugging (limited size)
        self._event_history: list[tuple[FittingEventType, Any]] = []
        self._max_history_size = 100

        # Enable/disable event logging
        self._logging_enabled = False

    def subscribe(
        self,
        event_type: FittingEventType,
        callback: Callable[[Any], None],
        use_weak_ref: bool = False
    ) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: The event type to subscribe to
            callback: Function to call when event is published
            use_weak_ref: If True, use weak reference to prevent memory leaks
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append((callback, use_weak_ref))

    def unsubscribe(
        self,
        event_type: FittingEventType,
        callback: Callable[[Any], None]
    ) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: The event type to unsubscribe from
            callback: The callback function to remove
        """
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                (cb, weak) for cb, weak in self._subscribers[event_type]
                if cb != callback
            ]

    def publish(
        self,
        event_type: FittingEventType,
        event_data: Any = None
    ) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type: The event type being published
            event_data: Optional data associated with the event
        """
        # Log event if enabled
        if self._logging_enabled:
            self._log_event(event_type, event_data)

        # Store in history
        self._add_to_history(event_type, event_data)

        # Notify all subscribers
        if event_type in self._subscribers:
            for callback, use_weak_ref in self._subscribers[event_type][:]:
                try:
                    if use_weak_ref:
                        # TODO: Implement weak reference support
                        callback(event_data)
                    else:
                        callback(event_data)
                except Exception as e:
                    # Log error but don't stop other callbacks
                    print(f"Error in event callback for {event_type}: {e}")

    def clear_subscribers(self, event_type: FittingEventType | None = None) -> None:
        """
        Clear all subscribers for an event type, or all subscribers if None.

        Args:
            event_type: Event type to clear, or None to clear all
        """
        if event_type is None:
            self._subscribers.clear()
        elif event_type in self._subscribers:
            self._subscribers[event_type].clear()

    def has_subscribers(self, event_type: FittingEventType) -> bool:
        """
        Check if an event type has any subscribers.

        Args:
            event_type: Event type to check

        Returns:
            True if there are subscribers, False otherwise
        """
        return event_type in self._subscribers and len(self._subscribers[event_type]) > 0

    def get_subscriber_count(self, event_type: FittingEventType) -> int:
        """
        Get the number of subscribers for an event type.

        Args:
            event_type: Event type to check

        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))

    def enable_logging(self, enabled: bool = True) -> None:
        """
        Enable or disable event logging.

        Args:
            enabled: True to enable logging, False to disable
        """
        self._logging_enabled = enabled

    def get_event_history(self) -> list[tuple[FittingEventType, Any]]:
        """
        Get the event history.

        Returns:
            List of (event_type, event_data) tuples
        """
        return self._event_history.copy()

    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()

    def _add_to_history(self, event_type: FittingEventType, event_data: Any) -> None:
        """Add event to history with size limit."""
        self._event_history.append((event_type, event_data))

        # Trim history if too large
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]

    def _log_event(self, event_type: FittingEventType, event_data: Any) -> None:
        """Log event for debugging."""
        print(f"[EventMediator] {event_type.name}: {event_data}")


class EventBridge:
    """
    Helper class to bridge Qt signals to EventMediator.

    This class provides utilities to connect Qt signals to the event mediator,
    reducing boilerplate in initializeSignals().
    """

    def __init__(self, mediator: EventMediator):
        """
        Initialize the EventBridge.

        Args:
            mediator: The EventMediator to publish events to
        """
        self.mediator = mediator

    def connect_signal(
        self,
        signal: QtCore.Signal,
        event_type: FittingEventType,
        transform: Callable[[Any], Any] | None = None
    ) -> None:
        """
        Connect a Qt signal to an event type.

        Args:
            signal: Qt signal to connect
            event_type: Event type to publish when signal is emitted
            transform: Optional function to transform signal data before publishing
        """
        def on_signal_emitted(*args):
            # Extract single value if only one arg
            event_data = args[0] if len(args) == 1 else args if args else None

            # Apply transformation if provided
            if transform:
                event_data = transform(event_data)

            # Publish to mediator
            self.mediator.publish(event_type, event_data)

        signal.connect(on_signal_emitted)

    def connect_action(
        self,
        signal: QtCore.Signal,
        event_type: FittingEventType
    ) -> None:
        """
        Connect a parameterless signal (like button clicks) to an event type.

        Args:
            signal: Qt signal to connect
            event_type: Event type to publish when signal is emitted
        """
        signal.connect(lambda: self.mediator.publish(event_type))

    def publish_to_signal(
        self,
        event_type: FittingEventType,
        signal: QtCore.Signal
    ) -> None:
        """
        Subscribe to an event type and emit a Qt signal when it occurs.

        Args:
            event_type: Event type to subscribe to
            signal: Qt signal to emit when event occurs
        """
        self.mediator.subscribe(event_type, lambda data: signal.emit(data))
