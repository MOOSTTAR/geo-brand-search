class AgentError(Exception):
    """Base exception for all agent errors."""


class BrowserError(AgentError):
    """Browser-related errors (launch, crash, etc.)."""


class ElementNotFoundError(AgentError):
    """Target element not found on page."""


class TimeoutExceededError(AgentError):
    """Operation timed out."""


class MaxRetriesExceeded(AgentError):
    """Retry attempts exhausted."""


class MaxIterationsExceeded(AgentError):
    """ReAct loop exceeded max iterations."""


class NavigationError(AgentError):
    """Page navigation failed."""
