from handlers.rateLimit import RateLimit


class ReservableRateLimit(RateLimit):
    def __init__(self, max_calls: int, period: int):
        """
        Subclass of RateLimit which can be (partially) reserved.

        :param max_calls: The amount of requests allowed
        :param period: The time in minutes for the allowed amount
        """
        super().__init__(max_calls, period)
        self._reservations: list[RateLimit] = []

    def _set_full(self):
        for reservation in self._reservations:
            reservation._set_full()
        super()._set_full()

    def reserve(self, amount: int) -> RateLimit:
        """
        Reserve a portion of the ratelimit and recieve an ID to identify usages of the reserved ratelimit amount.
        """
        if self._max_calls - amount < 0:
            raise ValueError("Total amount of reservations exceeds ratelimit maximum.")

        self._max_calls -= amount

        r = RateLimit(amount, self._period)
        self._reservations.append(r)
        return r
