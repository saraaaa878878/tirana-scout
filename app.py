"""
Async Priority Task Scheduler with Retry, Backoff, and Metrics.

A small but "senior engineer"-flavored piece of code: type hints, dataclasses,
decorators, context managers, custom exceptions, generics, and asyncio —
all wired together into a working priority task scheduler.
"""

from __future__ import annotations

import asyncio
import heapq
import itertools
import logging
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
log = logging.getLogger("scheduler")

T = TypeVar("T")


class TaskFailedError(Exception):
    """Raised when a task exhausts all of its retry attempts."""

    def __init__(self, name: str, attempts: int, last_error: Exception):
        super().__init__(f"Task {name!r} failed after {attempts} attempts: {last_error!r}")
        self.name = name
        self.attempts = attempts
        self.last_error = last_error


def with_retry(max_attempts: int = 3, base_delay: float = 0.1) -> Callable:
    """Decorator that retries an async function with exponential backoff + jitter."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001 - intentional broad catch for retry logic
                    last_error = exc
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.05)
                    log.warning("attempt %d/%d failed for %s: %s (retrying in %.2fs)",
                                attempt, max_attempts, func.__name__, exc, delay)
                    await asyncio.sleep(delay)
            raise TaskFailedError(func.__name__, max_attempts, last_error)  # type: ignore[arg-type]

        return wrapper

    return decorator


@dataclass(order=True)
class Task(Generic[T]):
    priority: int
    name: str = field(compare=False)
    coro_factory: Callable[[], Awaitable[T]] = field(compare=False, repr=False)
    created_at: float = field(default_factory=time.monotonic, compare=False)


@dataclass
class SchedulerMetrics:
    completed: int = 0
    failed: int = 0
    total_latency: float = 0.0

    @property
    def avg_latency(self) -> float:
        return self.total_latency / self.completed if self.completed else 0.0


class PriorityScheduler:
    """Runs tasks with bounded concurrency, ordered by priority (lower = more urgent)."""

    def __init__(self, concurrency: int = 3):
        self._heap: list[tuple[int, int, Task]] = []
        self._counter = itertools.count()
        self._sem = asyncio.Semaphore(concurrency)
        self.metrics = SchedulerMetrics()

    def submit(self, task: Task) -> None:
        heapq.heappush(self._heap, (task.priority, next(self._counter), task))
        log.info("submitted %-12s priority=%d queue_size=%d", task.name, task.priority, len(self._heap))

    @asynccontextmanager
    async def _slot(self, name: str):
        async with self._sem:
            start = time.monotonic()
            try:
                yield
            finally:
                elapsed = time.monotonic() - start
                log.info("released slot for %-12s (%.3fs)", name, elapsed)

    async def _run_one(self, task: Task) -> None:
        start = time.monotonic()
        async with self._slot(task.name):
            try:
                await task.coro_factory()
                self.metrics.completed += 1
                self.metrics.total_latency += time.monotonic() - start
            except TaskFailedError as exc:
                self.metrics.failed += 1
                log.error("giving up on %s: %s", task.name, exc)

    async def run_all(self) -> None:
        pending = []
        while self._heap:
            _, _, task = heapq.heappop(self._heap)
            pending.append(asyncio.create_task(self._run_one(task)))
        await asyncio.gather(*pending)


@with_retry(max_attempts=4, base_delay=0.05)
async def flaky_job(name: str, fail_chance: float = 0.5) -> str:
    await asyncio.sleep(random.uniform(0.02, 0.08))
    if random.random() < fail_chance:
        raise RuntimeError(f"transient error in {name}")
    return f"{name} done"


async def main() -> None:
    scheduler = PriorityScheduler(concurrency=3)
    jobs = [("ingest-data", 1), ("send-email", 3), ("build-report", 2),
            ("cleanup-tmp", 5), ("sync-cache", 2)]

    for name, priority in jobs:
        scheduler.submit(Task(priority=priority, name=name,
                               coro_factory=lambda n=name: flaky_job(n)))

    await scheduler.run_all()
    m = scheduler.metrics
    log.info("done: completed=%d failed=%d avg_latency=%.3fs", m.completed, m.failed, m.avg_latency)


if __name__ == "__main__":
    asyncio.run(main())