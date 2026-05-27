import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.task import Task
from app.schemas.task import TaskCreateRequest, TaskResponse
from app.config import SCREENSHOTS_DIR
from app.services.task_service import execute_task
from app.api.ws import manager

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(req: TaskCreateRequest, db: AsyncSession = Depends(get_db)):
    task = Task(query=req.query, status="creating", progress=0, brand_keyword=req.brand_keyword)
    db.add(task)
    await db.commit()
    await db.refresh(task)

    await manager.broadcast({
        "type": "task_created",
        "data": {
            "task_id": task.id,
            "query": task.query,
            "brand_keyword": task.brand_keyword,
            "status": task.status,
            "created_at": task.created_at,
        }
    })

    asyncio.create_task(execute_task(task.id, req.query, brand_keyword=req.brand_keyword))

    return TaskResponse.model_validate(task)


@router.get("", response_model=list[TaskResponse])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).order_by(desc(Task.created_at)))
    tasks = result.scalars().all()
    return [TaskResponse.model_validate(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.get("/{task_id}/screenshot")
async def get_screenshot(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task or not task.screenshot_path:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    file_path = SCREENSHOTS_DIR / task.screenshot_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Screenshot file not found")

    return FileResponse(str(file_path), media_type="image/png")


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.screenshot_path:
        file_path = SCREENSHOTS_DIR / task.screenshot_path
        if file_path.exists():
            file_path.unlink()

    await db.delete(task)
    await db.commit()
