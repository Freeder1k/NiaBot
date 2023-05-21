from queue import Queue
from threading import Lock

import util


class RateLimitException(Exception):
    pass


class RateLimit:
    def __init__(self, amount: int, time: int):
        """
        A ratelimit checker. Use with 'with RateLimit:'. If amount requests in the specified time were exceeded throws
        RateLimitException.

        :param amount: The amount of requests allowed
        :param time: The time in minutes for the allowed amount
        """
        self.amount = amount
        self.time = time
        self.request_amounts = Queue(maxsize=time)
        self.curr_req_amount = 0
        self._enter_lock = Lock()

    def __enter__(self):
        """
        :raises RateLimitException: If the rate limit was exceeded.
        """
        with self._enter_lock:
            if sum(list(self.request_amounts.queue)) + self.curr_req_amount > self.amount:
                raise RateLimitException(f"Rate limit of {self.amount} requests per {self.time}min reached!")

            self.curr_req_amount += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def time_passed(self):
        with self._enter_lock:
            while self.request_amounts.qsize() >= self.time:
                self.request_amounts.get()

            self.request_amounts.put(self.curr_req_amount)
            self.curr_req_amount = 0


_rate_limits = []


def add_ratelimit(rate_limit: RateLimit):
    _rate_limits.append(rate_limit)


def update_ratelimits():
    for rate_limit in _rate_limits:
        rate_limit.time_passed()
    util.dlog(f"Updated {len(_rate_limits)} ratelimits.")
