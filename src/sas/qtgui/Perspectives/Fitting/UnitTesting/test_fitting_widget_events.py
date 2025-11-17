"""
Unit tests for FittingWidget event mediator and bridge functionality.
"""
from unittest.mock import Mock

import pytest

from sas.qtgui.Perspectives.Fitting.EventMediator import FittingEventType


@pytest.fixture
def mock_parent():
    """Mock parent widget."""
    return Mock()


"""
Unit tests for FittingWidget event mediator and bridge functionality.
"""
@pytest.fixture
def mock_parent_widget():
    """Mock parent widget."""
    return Mock()


def test_event_mediator_creation():
    """Test that EventMediator can be created and used."""
    from sas.qtgui.Perspectives.Fitting.EventMediator import EventMediator

    # Create mediator
    mediator = EventMediator()

    # Test basic functionality
    assert mediator is not None
    assert hasattr(mediator, 'publish')
    assert hasattr(mediator, 'subscribe')
    assert hasattr(mediator, 'has_subscribers')


def test_event_bridge_creation():
    """Test that EventBridge can be created."""
    from sas.qtgui.Perspectives.Fitting.EventMediator import EventBridge, EventMediator

    # Create mediator and bridge
    mediator = EventMediator()
    bridge = EventBridge(mediator)

    # Test basic functionality
    assert bridge is not None
    assert bridge.mediator is mediator
    assert hasattr(bridge, 'connect_signal')
    assert hasattr(bridge, 'connect_action')


def test_event_mediator_publish_subscribe():
    """Test that EventMediator can publish and subscribe to events."""
    from sas.qtgui.Perspectives.Fitting.EventMediator import EventMediator

    mediator = EventMediator()
    callback_called = []

    def test_callback(data=None):
        callback_called.append(data)

    # Subscribe to an event
    mediator.subscribe(FittingEventType.FIT_REQUESTED, test_callback)

    # Check that we have subscribers
    assert mediator.has_subscribers(FittingEventType.FIT_REQUESTED)

    # Publish the event
    mediator.publish(FittingEventType.FIT_REQUESTED, "test_data")

    # Check that callback was called
    assert len(callback_called) == 1
    assert callback_called[0] == "test_data"


def test_event_bridge_connect_signal():
    """Test that EventBridge can connect signals."""
    from sas.qtgui.Perspectives.Fitting.EventMediator import EventBridge, EventMediator

    mediator = EventMediator()
    bridge = EventBridge(mediator)

    # Mock signal
    mock_signal = Mock()

    # Connect signal
    bridge.connect_signal(mock_signal, FittingEventType.FIT_REQUESTED)

    # Check that signal.connect was called
    mock_signal.connect.assert_called_once()


def test_event_bridge_connect_action():
    """Test that EventBridge can connect actions."""
    from sas.qtgui.Perspectives.Fitting.EventMediator import EventBridge, EventMediator

    mediator = EventMediator()
    bridge = EventBridge(mediator)

    # Mock action (like a button click)
    mock_action = Mock()

    # Connect action
    bridge.connect_action(mock_action, FittingEventType.PLOT_REQUESTED)

    # Check that action.connect was called
    mock_action.connect.assert_called_once()


def test_multiple_subscribers():
    """Test that multiple subscribers can be registered for the same event."""
    from sas.qtgui.Perspectives.Fitting.EventMediator import EventMediator

    mediator = EventMediator()
    callback1_called = []
    callback2_called = []

    def callback1(data=None):
        callback1_called.append(data)

    def callback2(data=None):
        callback2_called.append(data)

    # Subscribe both callbacks
    mediator.subscribe(FittingEventType.MODEL_SELECTED, callback1)
    mediator.subscribe(FittingEventType.MODEL_SELECTED, callback2)

    # Publish event
    mediator.publish(FittingEventType.MODEL_SELECTED, "model_data")

    # Check both callbacks were called
    assert len(callback1_called) == 1
    assert len(callback2_called) == 1
    assert callback1_called[0] == "model_data"
    assert callback2_called[0] == "model_data"


def test_event_types_defined():
    """Test that all expected event types are defined."""
    # Check that key event types exist
    assert hasattr(FittingEventType, 'FIT_REQUESTED')
    assert hasattr(FittingEventType, 'PLOT_REQUESTED')
    assert hasattr(FittingEventType, 'HELP_REQUESTED')
    assert hasattr(FittingEventType, 'MODEL_SELECTED')
    assert hasattr(FittingEventType, 'CATEGORY_SELECTED')
    assert hasattr(FittingEventType, 'STRUCTURE_FACTOR_SELECTED')
    assert hasattr(FittingEventType, 'BATCH_FILE_SELECTED')
    assert hasattr(FittingEventType, 'VIEW_2D_TOGGLED')
    assert hasattr(FittingEventType, 'POLYDISPERSITY_TOGGLED')
    assert hasattr(FittingEventType, 'MAGNETISM_TOGGLED')
    assert hasattr(FittingEventType, 'CHAIN_FIT_TOGGLED')
    assert hasattr(FittingEventType, 'PARAMS_CHANGED')
    assert hasattr(FittingEventType, 'SELECTION_CHANGED')
    assert hasattr(FittingEventType, 'FIT_ENABLEMENT_CHANGED')
    assert hasattr(FittingEventType, 'DATA_UPDATED')
    assert hasattr(FittingEventType, 'MODEL_ITERATION_REQUESTED')
    assert hasattr(FittingEventType, 'OPTIONS_UPDATE_REQUESTED')
    assert hasattr(FittingEventType, 'CUSTOM_MODEL_CHANGED')
    assert hasattr(FittingEventType, 'SMEARING_OPTIONS_UPDATED')
    assert hasattr(FittingEventType, 'MODEL_CATEGORIES_UPDATED')
    assert hasattr(FittingEventType, 'MASKED_DATA_UPDATED')
    assert hasattr(FittingEventType, 'KEY_PRESSED')
