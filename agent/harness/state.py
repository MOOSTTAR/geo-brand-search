from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


@dataclass
class StepResult:
    step_id: str
    success: bool
    description: str = ""
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentStatus:
    state: AgentState = AgentState.IDLE
    current_step_index: int = 0
    total_steps: int = 0
    progress: int = 0
    step_history: list[StepResult] = field(default_factory=list)

    def transition(self, new_state: AgentState):
        self.state = new_state

    def record_step(self, result: StepResult):
        self.step_history.append(result)
        self.current_step_index = len(self.step_history)
        if self.total_steps > 0:
            self.progress = int((self.current_step_index / self.total_steps) * 100)

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "current_step_index": self.current_step_index,
            "total_steps": self.total_steps,
            "progress": self.progress,
            "step_history": [
                {"step_id": s.step_id, "success": s.success, "error": s.error}
                for s in self.step_history
            ],
        }
