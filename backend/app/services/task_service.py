import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.task import Task
from app.api.ws import manager
from app.services.agent_bridge import run_agent


async def execute_task(task_id: str, query: str):
    """Execute a task by running the agent and updating state."""
    async with async_session() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return

        task.status = "executing"
        task.progress = 0
        await db.commit()

        await manager.broadcast({
            "type": "task_progress",
            "data": {
                "task_id": task_id,
                "status": "executing",
                "step": "start",
                "message": "Agent 启动中...",
                "progress": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        })

    try:
        async for msg in run_agent(task_id, query):
            msg_type = msg["type"]
            data = msg["data"]

            async with async_session() as db:
                result = await db.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one_or_none()
                if not task:
                    return

                if msg_type == "progress":
                    progress = data.get("progress", task.progress)
                    step = data.get("step", "")
                    message = data.get("message", "")

                    task.progress = progress
                    task.current_step = step
                    task.status = "executing"
                    task.updated_at = datetime.now(timezone.utc).isoformat()
                    await db.commit()

                    await manager.broadcast({
                        "type": "task_progress",
                        "data": {
                            "task_id": task_id,
                            "status": "executing",
                            "step": step,
                            "message": message,
                            "progress": progress,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    })

                elif msg_type == "result":
                    task.status = "completed"
                    task.progress = 100
                    task.screenshot_path = data.get("screenshot", "")
                    task.response_text = data.get("response_text", "")
                    task.thinking_text = data.get("thinking_text", "")
                    task.answer_text = data.get("answer_text", "")
                    task.answer_html = data.get("answer_html", "")
                    task.ranking_table = data.get("ranking_table", "")
                    task.current_step = "done"
                    task.completed_at = datetime.now(timezone.utc).isoformat()
                    task.updated_at = datetime.now(timezone.utc).isoformat()
                    await db.commit()

                    await manager.broadcast({
                        "type": "task_completed",
                        "data": {
                            "task_id": task_id,
                            "status": "completed",
                            "screenshot_path": task.screenshot_path,
                            "response_text": task.response_text,
                            "thinking_text": task.thinking_text,
                            "answer_text": task.answer_text,
                            "answer_html": task.answer_html,
                            "ranking_table": task.ranking_table,
                            "completed_at": task.completed_at,
                        }
                    })

                elif msg_type == "ranking":
                    task.ranking_table = data.get("ranking_table", "")
                    task.updated_at = datetime.now(timezone.utc).isoformat()
                    await db.commit()

                    await manager.broadcast({
                        "type": "task_ranking",
                        "data": {
                            "task_id": task_id,
                            "ranking_table": task.ranking_table,
                        }
                    })

                elif msg_type == "error":
                    task.status = "failed"
                    task.error_message = data.get("error", "Unknown error")
                    task.updated_at = datetime.now(timezone.utc).isoformat()
                    await db.commit()

                    await manager.broadcast({
                        "type": "task_failed",
                        "data": {
                            "task_id": task_id,
                            "status": "failed",
                            "error": task.error_message,
                            "failed_at": task.updated_at,
                        }
                    })

    except Exception as e:
        import traceback
        print(f"[ERROR] execute_task failed: {e!r}", flush=True)
        traceback.print_exc()
        async with async_session() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task:
                task.status = "failed"
                task.error_message = repr(e) if not str(e) else str(e)
                task.updated_at = datetime.now(timezone.utc).isoformat()
                await db.commit()

                await manager.broadcast({
                    "type": "task_failed",
                    "data": {
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e),
                        "failed_at": task.updated_at,
                    }
                })
