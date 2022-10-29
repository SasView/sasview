from typing import TypeVar, Generic, Callable, Any, List, Optional

import time
import threading

T = TypeVar('T')

class FloodBarrier(Generic[T], threading.Event):
    """ A single entry LIFO queue holds up a function call for a period
    of time, waiting to see if another value comes along. If another value
    does come along, then it relplaces it and waits.

    This should prevent a flood of messages being sent to a calculation."""
    def __init__(self, done_call: Callable[[T], Any], initial_value: T, wait_time_s: float = 0.05):
        super().__init__()

        self.done_call = done_call
        self.wait_time_s = wait_time_s
        self.value = initial_value

        self.current_timer: Optional[threading.Timer] = None

    def on_timout(self):
        self.done_call(self.value)

    def __call__(self, value: T):

        if self.current_timer is not None:
            self.current_timer.cancel()

        self.value = value

        self.current_timer = threading.Timer(self.wait_time_s, self.on_timout)
        self.current_timer.start()
