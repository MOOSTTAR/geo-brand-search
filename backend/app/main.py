from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models.task import Base
from app.api.tasks import router as tasks_router
from app.api.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add new columns that may be missing in existing databases
        try:
            await conn.run_sync(
                lambda sync_conn: sync_conn.exec_driver_sql(
                    "ALTER TABLE tasks ADD COLUMN platform_results TEXT"
                )
            )
        except Exception:
            pass  # Column already exists
    yield
    await engine.dispose()


app = FastAPI(title="GEO品牌查询 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
