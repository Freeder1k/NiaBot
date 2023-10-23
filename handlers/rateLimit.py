import collections
import time
from http import HTTPStatus
from threading import Lock

from aiohttp import ClientResponseError


class RateLimitException(Exception):
    pass


class RateLimit:
    def __init__(self, max_calls: int, period: int):
        """
        A ratelimit checker. Use with 'with RateLimit:'. If amount requests in the specified time were exceeded throws
        RateLimitException.

        :param max_calls: The amount of requests allowed
        :param period: The time period in minutes of the ratelimit
        """
        self._max_calls = max_calls
        self._period = period
        self._calls = collections.deque(maxlen=max_calls)
        self._curr_call_amount = 0
        self._lock = Lock()

    def __enter__(self):
        """
        :raises RateLimitException: If the rate limit was exceeded.
         Also catches NonSuccessExceptions and checks for TOO_MANY_REQUESTS code and sets the rate limit to full if so.
        """
        with self._lock:
            if self.calculate_usage() >= self._max_calls:
                raise RateLimitException(f"Rate limit of {self._max_calls} requests per {self._period}min reached!")

            self._curr_call_amount += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            self._curr_call_amount -= 1
            curr_time = time.time()

            while len(self._calls) > 0 and self._calls[0] - curr_time >= self._period * 60:
                self._calls.popleft()

            self._calls.append(curr_time)

            if exc_type is ClientResponseError and exc_val.status == HTTPStatus.TOO_MANY_REQUESTS:
                usage = self.calculate_usage()
                self._set_full()
                raise RateLimitException(
                    f"Rate limited by server! (Request amount: {usage}/{self._max_calls} per {self._period}min)")

    def _set_full(self):
        amount_not_used = self._max_calls - self.calculate_usage()
        curr_time = time.time()
        self._calls.extend([curr_time] * amount_not_used)

    def calculate_usage(self) -> int:
        curr_time = time.time()
        while len(self._calls) > 0 and self._calls[0] - curr_time >= self._period * 60:
            self._calls.popleft()
        return len(self._calls) + self._curr_call_amount

    def calculate_remaining_calls(self) -> int:
        return self.get_max_calls() - self.calculate_usage()

    def get_max_calls(self) -> int:
        return self._max_calls

    def get_period(self) -> int:
        return self._period
