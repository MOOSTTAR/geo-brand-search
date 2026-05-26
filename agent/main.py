"""Agent CLI entry point.

Usage:
    python -m agent.main --task-id <uuid> --query "what is AI" [--headed]

Communicates with the backend via stdout JSON Lines protocol:
    {"type": "progress", "step": "...", "message": "...", "progress": N}
    {"type": "result", "status": "completed", "screenshot": "task_xxx.png"}
    {"type": "error", "status": "failed", "error": "..."}
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import asyncio

from agent.harness.runner import Runner


async def main():
    parser = argparse.ArgumentParser(description="GEO品牌查询 Agent")
    parser.add_argument("--task-id", required=True, help="Task UUID")
    parser.add_argument("--query", required=True, help="Search query for DeepSeek")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()

    runner = Runner(task_id=args.task_id, query=args.query, headless=args.headless)
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
