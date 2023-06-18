from api.rateLimit import RateLimit


class ReservableRateLimit(RateLimit):
    def __init__(self, max_amount: int, time_min: int):
        """
        A ratelimit where tasks can reserve/free usages.

        :param max_amount: The amount of requests allowed
        :param time_min: The time in minutes for the allowed amount
        """
        super().__init__(max_amount, time_min)
        self._reservations: dict[int, RateLimit] = {}
        self._next_reserver_id = 0

    def reserve(self, amount: int) -> int:
        """
        Reserve a portion of the ratelimit and recieve an ID to identify usages of the reserved ratelimit amount.
        """
        curr_id = self._next_reserver_id
        self._next_reserver_id += 1

        self._reservations[curr_id] = RateLimit(amount, self.time_min)
        self.max_amount -= amount
        return curr_id

    def free(self, reserver_id: int):
        if reserver_id not in self._reservations:
            raise TypeError(f"There is no reservation with ID {reserver_id}.")

        reservation = self._reservations[reserver_id]
        self.curr_req_amount -= reservation.max_amount - reservation.curr_usage()
        self._reservations[reserver_id].set_full()

    def get_reservation(self, reserver_id: int) -> RateLimit:
        if reserver_id not in self._reservations:
            raise TypeError(f"There is no reservation with ID {reserver_id}.")
        return self._reservations[reserver_id]

    def set_full(self):
        for reservation in self._reservations.values():
            reservation.set_full()
        super().set_full()

    def _minute_passed(self):
        for reservation in self._reservations.values():
            reservation._minute_passed()
        super()._minute_passed()

    def curr_usage(self):
        return sum(r.curr_usage() for r in self._reservations.values()) + super().curr_usage()
