"""Agent CLI entry point.

Usage:
    python -m agent.main --task-id <uuid> --query "what is AI" [--headless] [--platforms deepseek,doubao]

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
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--brand-keyword", default=None, help="Optional brand keyword for rank lookup")
    parser.add_argument("--platforms", default=None, help="Comma-separated platform keys (e.g. deepseek,doubao)")
    args = parser.parse_args()

    platform_list = None
    if args.platforms:
        platform_list = [p.strip() for p in args.platforms.split(",") if p.strip()]

    runner = Runner(
        task_id=args.task_id, query=args.query, headless=args.headless,
        brand_keyword=args.brand_keyword, platforms=platform_list,
    )
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
