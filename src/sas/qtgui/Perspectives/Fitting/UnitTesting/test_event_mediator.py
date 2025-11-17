"""
Unit tests for EventMediator and EventBridge classes.
"""

from unittest.mock import Mock

from sas.qtgui.Perspectives.Fitting.EventMediator import EventBridge, EventMediator, FittingEventType


class TestEventMediator:
    """Test cases for EventMediator class."""

    def test_init(self):
        """Test EventMediator initialization."""
        mediator = EventMediator()
        assert mediator._subscribers == {}
        assert mediator._event_history == []
        assert mediator._max_history_size == 100
        assert not mediator._logging_enabled

    def test_subscribe(self):
        """Test subscribing to events."""
        mediator = EventMediator()
        callback = Mock()

        # Subscribe to an event
        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback)

        assert FittingEventType.FIT_REQUESTED in mediator._subscribers
        assert len(mediator._subscribers[FittingEventType.FIT_REQUESTED]) == 1
        assert mediator._subscribers[FittingEventType.FIT_REQUESTED][0] == (callback, False)

    def test_subscribe_weak_ref(self):
        """Test subscribing with weak reference."""
        mediator = EventMediator()
        callback = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback, use_weak_ref=True)

        assert mediator._subscribers[FittingEventType.FIT_REQUESTED][0] == (callback, True)

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        mediator = EventMediator()
        callback1 = Mock()
        callback2 = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback1)
        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback2)

        # Unsubscribe one callback
        mediator.unsubscribe(FittingEventType.FIT_REQUESTED, callback1)

        assert len(mediator._subscribers[FittingEventType.FIT_REQUESTED]) == 1
        assert mediator._subscribers[FittingEventType.FIT_REQUESTED][0] == (callback2, False)

    def test_publish_no_subscribers(self):
        """Test publishing event with no subscribers."""
        mediator = EventMediator()

        # Should not raise any errors
        mediator.publish(FittingEventType.FIT_REQUESTED, "test data")

    def test_publish_with_subscribers(self):
        """Test publishing event to subscribers."""
        mediator = EventMediator()
        callback1 = Mock()
        callback2 = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback1)
        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback2)

        test_data = {"param": "value"}
        mediator.publish(FittingEventType.FIT_REQUESTED, test_data)

        callback1.assert_called_once_with(test_data)
        callback2.assert_called_once_with(test_data)

    def test_publish_no_data(self):
        """Test publishing event without data."""
        mediator = EventMediator()
        callback = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback)
        mediator.publish(FittingEventType.FIT_REQUESTED)

        callback.assert_called_once_with(None)

    def test_publish_callback_error(self):
        """Test that callback errors don't stop other callbacks."""
        mediator = EventMediator()
        callback1 = Mock(side_effect=Exception("Test error"))
        callback2 = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback1)
        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback2)

        # Should not raise exception
        mediator.publish(FittingEventType.FIT_REQUESTED, "data")

        callback1.assert_called_once_with("data")
        callback2.assert_called_once_with("data")

    def test_clear_subscribers_specific_event(self):
        """Test clearing subscribers for specific event."""
        mediator = EventMediator()
        callback = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback)
        mediator.subscribe(FittingEventType.PLOT_REQUESTED, callback)

        mediator.clear_subscribers(FittingEventType.FIT_REQUESTED)

        assert len(mediator._subscribers[FittingEventType.FIT_REQUESTED]) == 0
        assert FittingEventType.PLOT_REQUESTED in mediator._subscribers

    def test_clear_subscribers_all(self):
        """Test clearing all subscribers."""
        mediator = EventMediator()
        callback = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback)
        mediator.subscribe(FittingEventType.PLOT_REQUESTED, callback)

        mediator.clear_subscribers()

        assert mediator._subscribers == {}

    def test_has_subscribers(self):
        """Test checking if event has subscribers."""
        mediator = EventMediator()

        assert not mediator.has_subscribers(FittingEventType.FIT_REQUESTED)

        mediator.subscribe(FittingEventType.FIT_REQUESTED, Mock())
        assert mediator.has_subscribers(FittingEventType.FIT_REQUESTED)

    def test_get_subscriber_count(self):
        """Test getting subscriber count."""
        mediator = EventMediator()

        assert mediator.get_subscriber_count(FittingEventType.FIT_REQUESTED) == 0

        mediator.subscribe(FittingEventType.FIT_REQUESTED, Mock())
        mediator.subscribe(FittingEventType.FIT_REQUESTED, Mock())

        assert mediator.get_subscriber_count(FittingEventType.FIT_REQUESTED) == 2

    def test_event_history(self):
        """Test event history recording."""
        mediator = EventMediator()

        mediator.publish(FittingEventType.FIT_REQUESTED, "data1")
        mediator.publish(FittingEventType.PLOT_REQUESTED, "data2")

        history = mediator.get_event_history()
        assert len(history) == 2
        assert history[0] == (FittingEventType.FIT_REQUESTED, "data1")
        assert history[1] == (FittingEventType.PLOT_REQUESTED, "data2")

    def test_event_history_size_limit(self):
        """Test event history size limit."""
        mediator = EventMediator()
        mediator._max_history_size = 3

        for i in range(5):
            mediator.publish(FittingEventType.FIT_REQUESTED, f"data{i}")

        history = mediator.get_event_history()
        assert len(history) == 3
        assert history[0] == (FittingEventType.FIT_REQUESTED, "data2")

    def test_clear_history(self):
        """Test clearing event history."""
        mediator = EventMediator()

        mediator.publish(FittingEventType.FIT_REQUESTED, "data")
        assert len(mediator.get_event_history()) == 1

        mediator.clear_history()
        assert len(mediator.get_event_history()) == 0

    def test_enable_logging(self):
        """Test enabling/disabling logging."""
        mediator = EventMediator()

        mediator.enable_logging(True)
        assert mediator._logging_enabled

        mediator.enable_logging(False)
        assert not mediator._logging_enabled


class TestEventBridge:
    """Test cases for EventBridge class."""

    def test_init(self):
        """Test EventBridge initialization."""
        mediator = EventMediator()
        bridge = EventBridge(mediator)
        assert bridge.mediator is mediator

    def test_connect_signal_single_arg(self):
        """Test connecting signal with single argument."""
        mediator = EventMediator()
        bridge = EventBridge(mediator)
        callback = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback)

        # Mock Qt signal
        signal = Mock()
        bridge.connect_signal(signal, FittingEventType.FIT_REQUESTED)

        # Emit signal
        signal.connect.assert_called_once()
        # Get the connected function
        connected_func = signal.connect.call_args[0][0]

        # Call the connected function
        connected_func("test_data")

        callback.assert_called_once_with("test_data")

    def test_connect_signal_multiple_args(self):
        """Test connecting signal with multiple arguments."""
        mediator = EventMediator()
        bridge = EventBridge(mediator)
        callback = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback)

        signal = Mock()
        bridge.connect_signal(signal, FittingEventType.FIT_REQUESTED)

        connected_func = signal.connect.call_args[0][0]
        connected_func("arg1", "arg2")

        callback.assert_called_once_with(("arg1", "arg2"))

    def test_connect_signal_no_args(self):
        """Test connecting signal with no arguments."""
        mediator = EventMediator()
        bridge = EventBridge(mediator)
        callback = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback)

        signal = Mock()
        bridge.connect_signal(signal, FittingEventType.FIT_REQUESTED)

        connected_func = signal.connect.call_args[0][0]
        connected_func()

        callback.assert_called_once_with(None)

    def test_connect_signal_with_transform(self):
        """Test connecting signal with data transformation."""
        mediator = EventMediator()
        bridge = EventBridge(mediator)
        callback = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback)

        signal = Mock()
        def transform(x):
            return f"transformed_{x}"
        bridge.connect_signal(signal, FittingEventType.FIT_REQUESTED, transform)

        connected_func = signal.connect.call_args[0][0]
        connected_func("input")

        callback.assert_called_once_with("transformed_input")

    def test_connect_action(self):
        """Test connecting action signal."""
        mediator = EventMediator()
        bridge = EventBridge(mediator)
        callback = Mock()

        mediator.subscribe(FittingEventType.FIT_REQUESTED, callback)

        signal = Mock()
        bridge.connect_action(signal, FittingEventType.FIT_REQUESTED)

        connected_func = signal.connect.call_args[0][0]
        connected_func()

        callback.assert_called_once_with(None)

    def test_publish_to_signal(self):
        """Test publishing event to Qt signal."""
        mediator = EventMediator()
        bridge = EventBridge(mediator)

        signal = Mock()
        bridge.publish_to_signal(FittingEventType.FIT_REQUESTED, signal)

        mediator.publish(FittingEventType.FIT_REQUESTED, "test_data")

        signal.emit.assert_called_once_with("test_data")
