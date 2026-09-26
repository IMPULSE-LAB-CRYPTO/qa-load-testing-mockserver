"""
Locust load test for MockServer with token correlation.

Three user classes simulate three endpoints with a target profile:
- InitUser:   30 RPS on /api/v1/init
- SecondUser: 20 RPS on /api/v1/second (with token from init)
- ThirdUser:  10 RPS on /api/v1/third  (with token from init)

Each user extracts the token from the first response and passes it
to the subsequent requests, demonstrating request correlation.

Usage (headless):
    locust -f locustfile.py --host http://mockserver:1080 \
        --headless -u 200 -r 20 --run-time 1h \
        --csv /mnt/locust/reports/full-test
"""

import random
import time

from locust import HttpUser, task, constant_throughput


# Random delay
MIN_DELAY = 0.5
MAX_DELAY = 1.5


def _random_delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


class BaseUser(HttpUser):
    """Shared helpers for all user classes."""

    abstract = True

    def _fetch_token(self):
        """Call /init and return the token. Returns None on failure."""
        with self.client.get("/api/v1/init", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"init failed: HTTP {response.status_code}")
                return None
            try:
                token = response.json().get("token")
            except Exception as exc:  # noqa: BLE001
                response.failure(f"init: invalid JSON ({exc})")
                return None
            if not token:
                response.failure("init: empty token")
                return None
            return token

    def _call_second(self, token):
        """Call the second endpoint with the token."""
        self.client.get(
            f"/api/v1/second?token={token}",
            name="/api/v1/second?token=[token]",
        )

    def _call_third(self, token):
        """Call the third endpoint with the token."""
        self.client.get(
            f"/api/v1/third?token={token}",
            name="/api/v1/third?token=[token]",
        )


class InitUser(BaseUser):
    """30 RPS on /init, then chains into /second and /third."""

    wait_time = constant_throughput(30)

    @task
    def flow(self):
        token = self._fetch_token()
        if not token:
            return

        _random_delay()
        self._call_second(token)

        _random_delay()
        self._call_third(token)


class SecondUser(BaseUser):
    """20 RPS on /second (fetches token first)."""

    wait_time = constant_throughput(20)

    @task
    def flow(self):
        token = self._fetch_token()
        if not token:
            return

        _random_delay()
        self._call_second(token)


class ThirdUser(BaseUser):
    """10 RPS on /third (fetches token first)."""

    wait_time = constant_throughput(10)

    @task
    def flow(self):
        token = self._fetch_token()
        if not token:
            return

        _random_delay()
        self._call_second(token)

        _random_delay()
        self._call_third(token)