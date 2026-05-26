from agent.ranking.planner.templates import PlanStep


class PlanExecutor:
    async def execute_step(self, step: PlanStep, react_loop) -> str | None:
        try:
            result = await react_loop.run(start_state=step.id)
            return result
        except Exception as e:
            if step.allow_failure:
                return None
            raise
