import math
import time
from http import HTTPStatus

from aiohttp import ClientResponseError

from common.api.rateLimit import RateLimit, RateLimitException


class WynnRateLimit(RateLimit):
    def __init__(self):
        """
        Rate limit checker for the Wynncraft API.
        """
        super().__init__(120, 1)
        self._remaining_calls = self._max_calls
        # the second of the minute at which the rate limit resets
        self._reset_time = 0
        self._next_reset = math.ceil(time.time()) + 60

    def __enter__(self):
        """
        :raises RateLimitException: If the rate limit was exceeded.
         Also catches ClientResponseError and checks for TOO_MANY_REQUESTS code and sets the rate limit to full if so.
        """
        with self._lock:
            if self.calculate_remaining_calls() <= 0:
                raise RateLimitException(f"Rate limit of {self._max_calls} requests per {self._period}min reached!")

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            if exc_type is ClientResponseError and exc_val.status == HTTPStatus.TOO_MANY_REQUESTS:
                self._set_full()
                raise RateLimitException(
                    f"Rate limited by server! (Request amount:"
                    f" {self._max_calls - self._remaining_calls}/{self._max_calls} per min)")
        return False  # re-raise any exceptions

    def _check_if_reset(self):
        if time.time() > self._next_reset:
            self._next_reset = int(time.time()) + self.get_time_until_reset()
            self._remaining_calls = self._max_calls

    def _clear_expired_calls(self):
        raise NotImplementedError("This method is not implemented for the Wynncraft API.")

    def _set_full(self):
        self._remaining_calls = 0

    def set_remaining(self, amount):
        """
        Updates the remaining calls to the specified amount.
        """
        with self._lock:
            if amount < self.calculate_remaining_calls():
                self._remaining_calls = amount

    def get_time_until_reset(self) -> int:
        """
        :return: The time in seconds until the rate limit resets (in seconds).
        """
        return math.ceil((self._reset_time - time.time()) % 60)

    def set_time_until_reset(self, t: int):
        """
        Sets the time until the rate limit resets (in seconds).
        """
        with self._lock:
            self._reset_time = math.ceil((time.time() + t) % 60)

    def get_time_until_next_free(self) -> int:
        """
        :return: The time in seconds until the next free request.
        """
        if self.calculate_remaining_calls() > 0:
            return 0
        return self.get_time_until_reset()

    def calculate_usage(self) -> int:
        """
        Calculates the amount of requests made in the current period.
        """
        return self.get_max_calls() - self.calculate_remaining_calls()

    def calculate_remaining_calls(self) -> int:
        """
        Calculates the amount of requests left in the current period.
        """
        self._check_if_reset()
        return self._remaining_calls
