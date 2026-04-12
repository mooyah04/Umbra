"""Simple rate limiter for WCL API calls."""

import time
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Enforces a maximum call rate by sleeping between calls.

    Usage:
        limiter = RateLimiter(calls_per_second=2.0)
        limiter.wait()  # blocks until it's safe to make the next call
    """

    def __init__(self, calls_per_second: float = 2.0):
        self.min_interval = 1.0 / calls_per_second
        self._last_call: float = 0

    def wait(self):
        """Block until enough time has passed since the last call."""
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        self._last_call = time.time()
