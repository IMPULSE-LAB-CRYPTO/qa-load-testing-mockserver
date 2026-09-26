"""
Locust load test for MockServer with exact RPS profile and token correlation.

Target profile (per endpoint):
- /api/v1/init   -> 30 RPS (producer of tokens)
- /api/v1/second -> 20 RPS (consumer of tokens)
- /api/v1/third  -> 10 RPS (consumer of tokens)

Design:
- InitUser (weight 30) calls /init once per second and pushes each token
  into a shared in-process queue.
- SecondUser (weight 20) and ThirdUser (weight 10) pull tokens from the
  same queue and call the corresponding endpoint.
- constant_pacing(1) makes each user run exactly 1 iteration per second.

Run with: -u 60 -r 6
    (30 + 20 + 10 users, spawned at 6/s -> reaches 60 users in 10 s)

Usage (headless):
    locust -f locustfile.py --host http://mockserver:1080 \
        --headless -u 60 -r 6 --run-time 1h \
        --csv /mnt/locust/reports/full-test
"""

import gevent.queue

from locust import HttpUser, task, constant_pacing


# ---------------------------------------------------------------------------
# Shared token pool between producer and consumers
# ---------------------------------------------------------------------------
# Producer rate:  30 tokens/s (InitUser).
# Consumer rate:  20 + 10 = 30 tokens/s (SecondUser + ThirdUser).
# Balanced after warm-up, so the queue size stays stable.
TOKEN_QUEUE = gevent.queue.Queue(maxsize=10_000)

# Max seconds a consumer waits for a token before skipping the iteration.
TOKEN_GET_TIMEOUT = 5


# ---------------------------------------------------------------------------
# Producer
# ---------------------------------------------------------------------------
class InitUser(HttpUser):
    """30 RPS on /api/v1/init. Produces tokens for the consumers."""

    weight = 30
    wait_time = constant_pacing(1)

    @task
    def flow(self):
        with self.client.get("/api/v1/init", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"init failed: HTTP {response.status_code}")
                return
            try:
                token = response.json().get("token")
            except Exception as exc:  # noqa: BLE001
                response.failure(f"init: invalid JSON ({exc})")
                return
            if not token:
                response.failure("init: empty token")
                return

            try:
                TOKEN_QUEUE.put_nowait(token)
            except gevent.queue.Full:
                # Consumers are slower than producers — drop oldest token.
                try:
                    TOKEN_QUEUE.get_nowait()
                    TOKEN_QUEUE.put_nowait(token)
                except gevent.queue.Empty:
                    pass


# ---------------------------------------------------------------------------
# Consumers
# ---------------------------------------------------------------------------
class SecondUser(HttpUser):
    """20 RPS on /api/v1/second. Consumes tokens from the shared queue."""

    weight = 20
    wait_time = constant_pacing(1)

    @task
    def flow(self):
        try:
            token = TOKEN_QUEUE.get(timeout=TOKEN_GET_TIMEOUT)
        except gevent.queue.Empty:
            # Normally never happens in steady state.
            return
        self.client.get(
            f"/api/v1/second?token={token}",
            name="/api/v1/second",
        )


class ThirdUser(HttpUser):
    """10 RPS on /api/v1/third. Consumes tokens from the shared queue."""

    weight = 10
    wait_time = constant_pacing(1)

    @task
    def flow(self):
        try:
            token = TOKEN_QUEUE.get(timeout=TOKEN_GET_TIMEOUT)
        except gevent.queue.Empty:
            return
        self.client.get(
            f"/api/v1/third?token={token}",
            name="/api/v1/third",
        )