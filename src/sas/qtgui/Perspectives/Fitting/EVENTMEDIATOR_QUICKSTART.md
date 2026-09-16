# EventMediator Quick Start Guide

## Installation

The EventMediator is already integrated into FittingWidget. No additional setup required!

## Basic Usage

### 1. Publishing Events

When something happens in your code, publish an event:

```python
# Simple event with no data
self.event_mediator.publish(FittingEventType.FIT_REQUESTED)

# Event with data
self.event_mediator.publish(
    FittingEventType.DATA_UPDATED,
    {'source': 'user', 'timestamp': time.time()}
)
```

### 2. Subscribing to Events

Listen for events and handle them:

```python
def on_fit_requested(event_data):
    print(f"Fit requested: {event_data}")
    # Handle the event

# Subscribe
self.event_mediator.subscribe(
    FittingEventType.FIT_REQUESTED,
    on_fit_requested
)
```

### 3. Bridging Qt Signals

Connect existing Qt signals to the event system:

```python
# For signals with parameters
self.event_bridge.connect_signal(
    self.someComboBox.currentIndexChanged,
    FittingEventType.SELECTION_CHANGED
)

# For signals without parameters (buttons, actions)
self.event_bridge.connect_action(
    self.someButton.clicked,
    FittingEventType.BUTTON_CLICKED
)
```

## Common Patterns

### Pattern 1: Replace Direct Signal Connection

**Before:**
```python
self.myButton.clicked.connect(self.onButtonClicked)
```

**After:**
```python
# In initializeSignals():
self.event_bridge.connect_action(
    self.myButton.clicked,
    FittingEventType.BUTTON_CLICKED
)
self.event_mediator.subscribe(
    FittingEventType.BUTTON_CLICKED,
    lambda _: self.onButtonClicked()
)
```

### Pattern 2: Multiple Widgets → Same Event

```python
# Both widgets publish the same event type
self.event_bridge.connect_action(
    self.widget1.someSignal,
    FittingEventType.UPDATE_NEEDED
)
self.event_bridge.connect_action(
    self.widget2.anotherSignal,
    FittingEventType.UPDATE_NEEDED
)

# Single handler for both
self.event_mediator.subscribe(
    FittingEventType.UPDATE_NEEDED,
    lambda _: self.performUpdate()
)
```

### Pattern 3: Event Chain

```python
# Event A triggers Event B
def on_data_loaded(data):
    # Process data
    processed = process(data)
    # Trigger another event
    self.event_mediator.publish(
        FittingEventType.DATA_PROCESSED,
        processed
    )

self.event_mediator.subscribe(FittingEventType.DATA_LOADED, on_data_loaded)
self.event_mediator.subscribe(FittingEventType.DATA_PROCESSED, on_data_processed)
```

## Debugging

### Enable Logging

See all events as they occur:

```python
self.event_mediator.enable_logging(True)

# Now all events print to console:
# [EventMediator] FIT_REQUESTED: None
# [EventMediator] DATA_UPDATED: {'source': 'user'}
```

### Check Event History

```python
# Get last 10 events
history = self.event_mediator.get_event_history()
for event_type, event_data in history[-10:]:
    print(f"{event_type.name}: {event_data}")
```

### Check Subscribers

```python
# See how many handlers are subscribed
count = self.event_mediator.get_subscriber_count(FittingEventType.FIT_REQUESTED)
print(f"{count} subscribers for FIT_REQUESTED")

# Check if any subscribers exist
has_subs = self.event_mediator.has_subscribers(FittingEventType.FIT_REQUESTED)
```

## Available Event Types

See `EventMediator.py` for the complete list. Common ones:

**UI Events:**
- `MODEL_SELECTED`
- `FIT_REQUESTED`
- `PLOT_REQUESTED`
- `VIEW_2D_TOGGLED`

**Data Events:**
- `DATA_LOADED`
- `DATA_UPDATED`
- `Q_RANGE_UPDATED`

**Calculation Events:**
- `CALCULATION_STARTED`
- `CALCULATION_FINISHED`
- `CALCULATION_1D_FINISHED`
- `CALCULATION_2D_FINISHED`

**Fitting Events:**
- `FITTING_STARTED`
- `FITTING_FINISHED`
- `BATCH_FITTING_FINISHED`

## Tips & Tricks

### Tip 1: Unsubscribe When Done

```python
def cleanup(self):
    self.event_mediator.unsubscribe(
        FittingEventType.FIT_REQUESTED,
        self.on_fit_requested
    )
```

### Tip 2: Use Lambda for Simple Handlers

```python
# Instead of creating a method
self.event_mediator.subscribe(
    FittingEventType.FIT_REQUESTED,
    lambda _: self.cmdFit.setEnabled(False)
)
```

### Tip 3: Pass Context in Event Data

```python
# Include context to help handlers
self.event_mediator.publish(
    FittingEventType.ERROR_OCCURRED,
    {
        'error': str(e),
        'source': 'data_loader',
        'severity': 'critical'
    }
)
```

### Tip 4: Clear Event History Periodically

```python
# In a long-running operation
self.event_mediator.clear_history()
# ... do work ...
# Now history only contains recent events
```

## Testing Example

```python
from unittest.mock import Mock

def test_button_click_publishes_event():
    # Arrange
    widget = FittingWidget()
    mock_mediator = Mock(spec=EventMediator)
    widget.event_mediator = mock_mediator
    
    # Act
    widget.cmdFit.click()
    
    # Assert
    mock_mediator.publish.assert_called_with(
        FittingEventType.FIT_REQUESTED,
        None  # No data for button clicks
    )
```

## When NOT to Use EventMediator

**DON'T use for:**
- Internal widget communication (parent-child in same component)
- High-frequency events (>100/second) - use direct signals
- Qt model/view updates (use Qt's built-in signals)

**DO use for:**
- Cross-widget communication
- Business logic events
- Events that multiple components care about
- Events you want to test or debug

## Need Help?

1. Check `EVENT_HANDLING_REFACTORING.md` for detailed docs
2. Look at existing examples in `FittingWidget.initializeSignals()`
3. Enable logging to see event flow
4. Check event history for debugging

## Adding New Event Types

```python
# 1. Add to FittingEventType enum
class FittingEventType(Enum):
    MY_NEW_EVENT = auto()

# 2. Publish it
self.event_mediator.publish(
    FittingEventType.MY_NEW_EVENT,
    {'my_data': 'value'}
)

# 3. Subscribe to it
self.event_mediator.subscribe(
    FittingEventType.MY_NEW_EVENT,
    self.handle_my_event
)
```

That's it! You're now ready to use the EventMediator pattern in your code.
