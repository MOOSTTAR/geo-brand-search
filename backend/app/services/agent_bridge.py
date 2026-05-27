import json
import asyncio
import sys
import subprocess
from pathlib import Path
from typing import Any, AsyncGenerator

AGENT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "agent"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _read_stream(stream):
    """Read all lines from a stream (called in thread)."""
    for line in iter(stream.readline, ""):
        yield line
    stream.close()


async def _run_subprocess(cmd: list[str], cwd: str, env: dict) -> tuple[list[str], str, int]:
    """Run a subprocess in a thread, yield stdout lines, return (stdout_lines, stderr, rc)."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=cwd,
        bufsize=1,
    )

    stdout_lines: list[str] = []
    stderr_text = ""

    def _read_stdout():
        nonlocal stdout_lines
        for line in iter(proc.stdout.readline, ""):
            stdout_lines.append(line.rstrip("\n\r"))
        proc.stdout.close()

    def _read_stderr():
        nonlocal stderr_text
        stderr_text = proc.stderr.read()
        proc.stderr.close()

    loop = asyncio.get_event_loop()
    stdout_task = loop.run_in_executor(None, _read_stdout)
    stderr_task = loop.run_in_executor(None, _read_stderr)

    # Yield lines as they come in by polling
    last_idx = 0
    while not stdout_task.done():
        while last_idx < len(stdout_lines):
            yield stdout_lines[last_idx], None, None
            last_idx += 1
        await asyncio.sleep(0.1)

    # Drain remaining lines
    while last_idx < len(stdout_lines):
        yield stdout_lines[last_idx], None, None
        last_idx += 1

    await stderr_task
    proc.wait()

    yield None, stderr_text, proc.returncode


async def run_agent(task_id: str, query: str, brand_keyword: str | None = None) -> AsyncGenerator[dict[str, Any], None]:
    """Run the agent as a subprocess and parse stdout JSON Lines."""
    import os
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    cmd = [
        sys.executable, "-m", "agent.main",
        "--task-id", task_id,
        "--query", query,
    ]
    if brand_keyword:
        cmd.extend(["--brand-keyword", brand_keyword])

    final_error: str | None = None
    stderr_text = ""
    returncode = 0

    async for line, err, rc in _run_subprocess(cmd, str(PROJECT_ROOT), env):
        if err is not None:
            stderr_text = err
            returncode = rc or 0
            break
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = msg.get("type")
        if msg_type in ("progress", "result", "ranking"):
            yield {"type": msg_type, "data": msg}
        elif msg_type == "error":
            final_error = msg.get("error", "Agent failed")
            yield {"type": "error", "data": msg}

    if returncode != 0:
        err = stderr_text.strip() or f"Agent exited with code {returncode}"
        if not final_error:
            yield {
                "type": "error",
                "data": {"status": "failed", "error": err},
            }
