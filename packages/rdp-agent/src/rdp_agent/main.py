"""Entry point for the Windows agent."""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
from pathlib import Path

from .actions import Action, ActionExecutor
from .config import AgentConfig
from .pipeline import ProcessingPipeline

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-time RDP screen analysis agent")
    parser.add_argument("--config", type=Path, help="Path to configuration JSON", default=None)
    parser.add_argument("--state", type=Path, help="Path to persist agent state", default=Path("state.json"))
    parser.add_argument("--loop", action="store_true", help="Run continuously with configured FPS")
    return parser.parse_args()


async def handle_actions(pipeline: ProcessingPipeline, executor: ActionExecutor) -> None:
    async for payload in pipeline.transport.iter_actions():
        LOGGER.debug("Received action payload: %s", payload)
        pipeline.state.update(payload.frame_id, payload.state_delta)
        await executor.execute(Action(**payload.action))


async def main_async() -> None:
    args = parse_args()
    config = AgentConfig.load(args.config)

    pipeline = ProcessingPipeline(config=config, state_path=args.state)
    executor = ActionExecutor()

    await pipeline.start()

    action_task = asyncio.create_task(handle_actions(pipeline, executor))

    try:
        if not args.loop:
            await pipeline.run_once()
            return

        interval = 1.0 / max(config.capture_fps, 0.1)
        while True:
            await pipeline.run_once()
            await asyncio.sleep(interval)
    finally:
        action_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await action_task
        await pipeline.stop()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

