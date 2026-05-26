import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from agent.harness.errors import TimeoutExceededError


class TimeoutManager:
    def __init__(self, default_timeout: float = 120.0):
        self.default_timeout = default_timeout

    @asynccontextmanager
    async def with_timeout(self, timeout: float | None = None) -> AsyncGenerator[None, None]:
        """Run a block with a timeout. Raises TimeoutExceededError on expiry."""
        t = timeout if timeout is not None else self.default_timeout
        try:
            async with asyncio.timeout(t):
                yield
        except TimeoutError:
            raise TimeoutExceededError(f"Operation timed out after {t}s")
