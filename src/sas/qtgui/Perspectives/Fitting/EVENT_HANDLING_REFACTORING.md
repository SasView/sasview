# Event Handling Refactoring - EventMediator Pattern

## Overview

This document describes the EventMediator pattern implementation for decoupling signal/slot connections in the FittingWidget and reducing tight coupling between components.

## Problem Statement

**Before refactoring:**
- FittingWidget acted as a central hub with 20+ direct signal/slot connections
- Tight coupling between widget and child components (OptionsWidget, SmearingWidget, PolydispersityWidget, MagnetismWidget)
- Hard to test individual components in isolation
- Difficult to trace event flow through the application
- Lambda functions scattered throughout `initializeSignals()` making code harder to read
- Direct `self` passing creates circular dependencies

**Example of problematic code:**
```python
self.polydispersity_widget.cmdFitSignal.connect(lambda: self.cmdFit.setEnabled(self.haveParamsToFit()))
self.polydispersity_widget.updateDataSignal.connect(lambda: self.updateData())
self.magnetism_widget.cmdFitSignal.connect(lambda: self.cmdFit.setEnabled(self.haveParamsToFit()))
```

## Solution: EventMediator Pattern

### Architecture

The EventMediator pattern provides:

1. **Centralized Event Routing** - All events flow through a single mediator
2. **Type-Safe Events** - Using `FittingEventType` enum prevents typos
3. **Decoupled Components** - Widgets don't need to know about each other
4. **Easier Testing** - Mock the mediator to test components in isolation
5. **Event History** - Built-in debugging support
6. **Weak References** - Optional to prevent memory leaks

### Components

#### 1. FittingEventType Enum

Defines all event types in the system:

```python
class FittingEventType(Enum):
    MODEL_SELECTED = auto()
    STRUCTURE_FACTOR_SELECTED = auto()
    FIT_REQUESTED = auto()
    DATA_UPDATED = auto()
    # ... etc
```

#### 2. EventMediator Class

Central event bus for publishing and subscribing:

```python
class EventMediator(QtCore.QObject):
    def subscribe(self, event_type: FittingEventType, callback: Callable):
        """Subscribe to an event"""
        
    def publish(self, event_type: FittingEventType, event_data: Any):
        """Publish an event to all subscribers"""
```

#### 3. EventBridge Class

Helper for bridging Qt signals to the mediator:

```python
class EventBridge:
    def connect_signal(self, signal: QtCore.Signal, event_type: FittingEventType):
        """Connect a Qt signal to publish an event"""
        
    def connect_action(self, signal: QtCore.Signal, event_type: FittingEventType):
        """Connect a parameterless signal (like button clicks)"""
```

## Migration Guide

### Before (Direct Connections)

```python
def initializeSignals(self):
    # Direct coupling
    self.cbModel.currentIndexChanged.connect(self.onSelectModel)
    self.cmdFit.clicked.connect(self.onFit)
    self.polydispersity_widget.updateDataSignal.connect(lambda: self.updateData())
```

### After (EventMediator Pattern)

```python
def initializeSignals(self):
    # Step 1: Bridge Qt signals to events
    self.event_bridge.connect_signal(
        self.cbModel.currentIndexChanged,
        FittingEventType.MODEL_SELECTED
    )
    self.event_bridge.connect_action(
        self.cmdFit.clicked,
        FittingEventType.FIT_REQUESTED
    )
    
    # Step 2: Subscribe to events
    self.event_mediator.subscribe(
        FittingEventType.MODEL_SELECTED,
        lambda _: self.onSelectModel()
    )
    self.event_mediator.subscribe(
        FittingEventType.FIT_REQUESTED,
        lambda _: self.onFit()
    )
    
    # Step 3: Aggregate duplicate subscriptions
    self.event_bridge.connect_action(
        self.polydispersity_widget.updateDataSignal,
        FittingEventType.DATA_UPDATED
    )
    self.event_bridge.connect_action(
        self.magnetism_widget.updateDataSignal,
        FittingEventType.DATA_UPDATED
    )
    # Single handler for both
    self.event_mediator.subscribe(
        FittingEventType.DATA_UPDATED,
        lambda _: self.updateData()
    )
```

## Benefits

### 1. Reduced Coupling

**Before:**
```python
# PolydispersityWidget knows about FittingWidget
self.polydispersity_widget.cmdFitSignal.connect(
    lambda: self.cmdFit.setEnabled(self.haveParamsToFit())
)
```

**After:**
```python
# PolydispersityWidget just publishes events
self.event_bridge.connect_action(
    self.polydispersity_widget.cmdFitSignal,
    FittingEventType.FIT_ENABLEMENT_CHANGED
)
# FittingWidget subscribes independently
self.event_mediator.subscribe(
    FittingEventType.FIT_ENABLEMENT_CHANGED,
    lambda _: self.cmdFit.setEnabled(self.haveParamsToFit())
)
```

### 2. Event Aggregation

Multiple widgets can publish the same event type:

```python
# Both widgets request data update
self.polydispersity_widget.updateDataSignal -> FIT_ENABLEMENT_CHANGED
self.magnetism_widget.updateDataSignal -> FIT_ENABLEMENT_CHANGED

# Single handler
self.event_mediator.subscribe(FIT_ENABLEMENT_CHANGED, handler)
```

### 3. Easier Testing

```python
# Mock the mediator
mock_mediator = Mock(spec=EventMediator)

# Test event publishing
widget.on_something_changed()
mock_mediator.publish.assert_called_with(
    FittingEventType.DATA_UPDATED,
    expected_data
)
```

### 4. Debugging Support

```python
# Enable logging
self.event_mediator.enable_logging(True)

# Check event history
history = self.event_mediator.get_event_history()
print(f"Last 10 events: {history[-10:]}")
```

## Migration Status

### ✅ Migrated to EventMediator (100% Complete!)

**UI Controls:**
- Model selection (cbModel, cbCategory, cbStructureFactor, cbFileNames)
- View toggles (chk2DView, chkPolydispersity, chkMagnetism, chkChainFit)
- Action buttons (cmdFit, cmdPlot, cmdHelp)

**Widget Signals:**
- Child widget events (smearing, polydispersity, magnetism)
- Options widget (plot_signal)
- System events (custom models, masked data, model categories)
- Keyboard events

**Data & Parameters:**
- Parameter model changes (_model_model.dataChanged) → `PARAMS_CHANGED`
- Parameter selection (lstParams.selectionModel) → `SELECTION_CHANGED`

**Calculations & Fitting:**
- Calculation 1D (Calc1DFinishedSignal) → `CALCULATION_1D_FINISHED`
- Calculation 2D (Calc2DFinishedSignal) → `CALCULATION_2D_FINISHED`
- Fitting finished (fittingFinishedSignal) → `FITTING_FINISHED`
- Batch fitting (batchFittingFinishedSignal) → `BATCH_FITTING_FINISHED`

### ⚠️ Kept Direct (Qt Requirements)

These connections **must** stay direct due to Qt framework requirements:
- `lstParams.installEventFilter(self)` - Qt event filter system
- `options_widget.txtMinRange.editingFinished` - Internal widget state (direct parent-child)
- `options_widget.txtMaxRange.editingFinished` - Internal widget state (direct parent-child)

### 🚫 Not Migrated (By Design)

`constraintAddedSignal` - This signal is used for **external** communication with the constraint tab in the perspective. It's part of the public API and should remain as a Qt signal for compatibility with other components.

## Future Enhancements

### 1. Weak References

Prevent memory leaks by using weak references for callbacks:

```python
self.event_mediator.subscribe(
    FittingEventType.DATA_UPDATED,
    self.onDataUpdated,
    use_weak_ref=True  # Automatically cleanup when widget is destroyed
)
```

### 2. Event Filtering

Add filtering capabilities:

```python
# Only handle events matching a condition
self.event_mediator.subscribe(
    FittingEventType.DATA_UPDATED,
    self.onDataUpdated,
    filter_fn=lambda data: data['source'] == 'user'
)
```

### 3. Event Priority

Handle critical events first:

```python
self.event_mediator.subscribe(
    FittingEventType.FIT_REQUESTED,
    self.validateParams,
    priority=EventPriority.HIGH
)
```

### 4. Async Event Handling

Support asynchronous event handlers:

```python
async def on_data_loaded(data):
    await process_large_dataset(data)

self.event_mediator.subscribe_async(
    FittingEventType.DATA_LOADED,
    on_data_loaded
)
```

## Best Practices

### 1. Event Naming

Use descriptive, action-oriented names:
- ✅ `FIT_REQUESTED` (action happened)
- ✅ `DATA_UPDATED` (state changed)
- ❌ `FIT` (ambiguous)
- ❌ `UPDATE` (too generic)

### 2. Event Data

Keep event data simple and immutable:

```python
# Good - simple dictionary
self.event_mediator.publish(
    FittingEventType.MODEL_SELECTED,
    {'model_name': 'sphere', 'index': 0}
)

# Avoid - complex mutable objects
self.event_mediator.publish(
    FittingEventType.MODEL_SELECTED,
    self.entire_widget_state  # Too much coupling
)
```

### 3. Subscription Lifecycle

Subscribe in `__init__` or `initializeSignals()`, unsubscribe in cleanup:

```python
def __init__(self):
    self.event_mediator.subscribe(
        FittingEventType.DATA_UPDATED,
        self.on_data_updated
    )
    
def cleanup(self):
    self.event_mediator.unsubscribe(
        FittingEventType.DATA_UPDATED,
        self.on_data_updated
    )
```

### 4. Error Handling

The mediator catches exceptions in callbacks:

```python
def risky_handler(data):
    raise Exception("Something went wrong")

# Other subscribers still get called
self.event_mediator.subscribe(FittingEventType.DATA_UPDATED, risky_handler)
self.event_mediator.subscribe(FittingEventType.DATA_UPDATED, safe_handler)
```

## Performance Considerations

- **Event History**: Limited to 100 events by default to prevent memory growth
- **Subscriber Lookup**: O(1) for event type lookup, O(n) for iterating subscribers
- **Overhead**: Minimal - one additional function call per event
- **Threading**: EventMediator is thread-safe if used with Qt's signal/slot mechanism

## Examples

### Example 1: Replace Direct Lambda Connections

**Before:**
```python
self.polydispersity_widget.cmdFitSignal.connect(
    lambda: self.cmdFit.setEnabled(self.haveParamsToFit())
)
self.magnetism_widget.cmdFitSignal.connect(
    lambda: self.cmdFit.setEnabled(self.haveParamsToFit())
)
```

**After:**
```python
# Both widgets publish the same event
self.event_bridge.connect_action(
    self.polydispersity_widget.cmdFitSignal,
    FittingEventType.FIT_ENABLEMENT_CHANGED
)
self.event_bridge.connect_action(
    self.magnetism_widget.cmdFitSignal,
    FittingEventType.FIT_ENABLEMENT_CHANGED
)

# Single handler
self.event_mediator.subscribe(
    FittingEventType.FIT_ENABLEMENT_CHANGED,
    lambda _: self.cmdFit.setEnabled(self.haveParamsToFit())
)
```

### Example 2: Testing with EventMediator

```python
def test_fit_button_enables_when_params_available(self):
    # Setup
    widget = FittingWidget()
    mock_mediator = Mock(spec=EventMediator)
    widget.event_mediator = mock_mediator
    
    # Action
    widget.polydispersity_widget.cmdFitSignal.emit()
    
    # Assert
    mock_mediator.publish.assert_called_with(
        FittingEventType.FIT_ENABLEMENT_CHANGED,
        None
    )
```

## References

- **Design Pattern**: Mediator Pattern (Gang of Four)
- **Qt Documentation**: [Signals and Slots](https://doc.qt.io/qt-6/signalsandslots.html)
- **Related Patterns**: Observer, Event Bus, Publish-Subscribe

## Questions?

For questions or suggestions about this refactoring, please contact the SasView development team or open an issue on GitHub.
