from __future__ import annotations

import sched
from datetime import datetime, timedelta
from threading import Lock
from typing import Callable, Any

_scheduler = sched.scheduler()


class RepeatingScheduler:
    def __init__(self, start_time: datetime, interval: timedelta):
        """
        Create a scheduler that repeatedly runs actions with a set interval and start time.

        :param start_time: When to start the scheduler.
        :param interval: The interval between runs.
        """
        self._start_time = start_time + interval
        self._interval = interval
        self._actions = []
        self._next_event = _scheduler.enter(
            (start_time - datetime.now(start_time.tzinfo)).total_seconds(),
            1,
            self._periodic
        )
        self._running_lock = Lock()
        self._stopped = False

    def _periodic(self):
        with self._running_lock:
            if self._stopped:
                return
            self._next_event = _scheduler.enter(
                (self._start_time - datetime.now(self._start_time.tzinfo)).total_seconds(),
                1,
                self._periodic
            )
            self._start_time = self._start_time + self._interval

            for action, actionargs in self._actions:
                action(*actionargs)

    def register_action(self, action: Callable[..., Any], actionargs=()) -> RepeatingScheduler:
        self._actions.append((action, actionargs))
        return self

    def stop(self):
        with self._running_lock:
            self._stopped = True
            _scheduler.cancel(self._next_event)
