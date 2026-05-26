import asyncio
from dataclasses import dataclass
from typing import Callable, Any

from agent.harness.errors import MaxRetriesExceeded
from agent.harness.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)


class RetryExecutor:
    def __init__(self, policy: RetryPolicy | None = None):
        self.policy = policy or RetryPolicy()

    async def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        last_error: Exception | None = None
        for attempt in range(self.policy.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except self.policy.retryable_exceptions as e:
                last_error = e
                if attempt < self.policy.max_retries:
                    delay = self.policy.base_delay * (self.policy.backoff_factor ** attempt)
                    logger.warning(f"Retry attempt {attempt + 1}/{self.policy.max_retries} "
                                   f"after error: {e}. Waiting {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    raise MaxRetriesExceeded(f"Max retries ({self.policy.max_retries}) exceeded: {last_error}")
        raise MaxRetriesExceeded(f"Unexpected: {last_error}")
