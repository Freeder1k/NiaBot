from http import HTTPStatus
from queue import Queue
from threading import Lock

from aiohttp import ClientResponseError
from discord.ext import tasks


class RateLimitException(Exception):
    pass


class RateLimit:
    def __init__(self, max_amount: int, time_min: int):
        """
        A ratelimit checker. Use with 'with RateLimit:'. If amount requests in the specified time were exceeded throws
        RateLimitException.

        :param max_amount: The amount of requests allowed
        :param time_min: The time in minutes for the allowed amount
        """
        self.max_amount = max_amount
        self.time_min = time_min
        self.request_amounts = Queue(maxsize=time_min)
        self.curr_req_amount = 0
        self._enter_lock = Lock()

    def __enter__(self):
        """
        :raises RateLimitException: If the rate limit was exceeded.
         Also catches NonSuccessExceptions and checks for TOO_MANY_REQUESTS code and sets the rate limit to full if so.
        """
        with self._enter_lock:
            if self.curr_usage() >= self.max_amount:
                raise RateLimitException(f"Rate limit of {self.max_amount} requests per {self.time_min}min reached!")

            self.curr_req_amount += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._enter_lock:
            if exc_type is ClientResponseError and exc_val.status == HTTPStatus.TOO_MANY_REQUESTS:
                req_amount = self.curr_req_amount
                self.set_full()
                raise RateLimitException(
                    f"Rate limit of {self.max_amount} requests per {self.time_min}min reached! (Request amount: {req_amount})")

    def set_full(self):
        self.curr_req_amount += self.max_amount - sum(self.request_amounts.queue)

    def _minute_passed(self):
        with self._enter_lock:
            while not self.request_amounts.empty() and self.request_amounts.qsize() >= self.time_min:
                self.request_amounts.get()

            if self.time_min >= 1:
                self.request_amounts.put(self.curr_req_amount)
            self.curr_req_amount = 0

    def curr_usage(self):
        return sum(self.request_amounts.queue) + self.curr_req_amount

    def get_remaining(self):
        return self.max_amount - self.curr_usage()


_rate_limits = []


def register_new_ratelimit(max_amount: int, time_min: int) -> RateLimit:
    r = RateLimit(max_amount, time_min)
    register_ratelimit(r)
    return r


def register_ratelimit(rate_limit: RateLimit):
    _rate_limits.append(rate_limit)


@tasks.loop(minutes=1)
async def ratelimit_updater():
    for rate_limit in _rate_limits:
        rate_limit._minute_passed()
