"""Continuous trading loop management for autonomous agents."""

from typing import Dict, Any, Optional, Callable
from datetime import datetime, time
from pathlib import Path
import json
import time as time_module
import threading
from enum import Enum

from cli.utils.logger import get_logger

logger = get_logger(__name__)


class LoopStatus(Enum):
    """Status of a trading loop."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class LoopSchedule:
    """Market hours and trading schedule."""

    # US Market hours: 9:30 AM - 4:00 PM EST
    MARKET_OPEN = time(9, 30)
    MARKET_CLOSE = time(16, 0)

    # Pre-market: 4:00 AM - 9:30 AM EST (optional)
    PREMARKET_OPEN = time(4, 0)

    # After-hours: 4:00 PM - 8:00 PM EST (optional)
    AFTERHOURS_CLOSE = time(20, 0)

    @staticmethod
    def is_market_hours(include_premarket: bool = False, include_afterhours: bool = False) -> bool:
        """
        Check if current time is within market hours.

        Args:
            include_premarket: Include pre-market hours (4 AM - 9:30 AM)
            include_afterhours: Include after-hours (4 PM - 8 PM)

        Returns:
            True if current time is within market hours, False otherwise
        """
        now = datetime.now().time()

        # Regular market hours
        if LoopSchedule.MARKET_OPEN <= now < LoopSchedule.MARKET_CLOSE:
            return True

        # Pre-market
        if include_premarket and LoopSchedule.PREMARKET_OPEN <= now < LoopSchedule.MARKET_OPEN:
            return True

        # After-hours
        if include_afterhours and LoopSchedule.MARKET_CLOSE <= now < LoopSchedule.AFTERHOURS_CLOSE:
            return True

        return False

    @staticmethod
    def is_market_day() -> bool:
        """Check if today is a market day (Monday-Friday, excluding holidays)."""
        now = datetime.now()
        # 0 = Monday, 6 = Sunday
        if now.weekday() >= 5:  # Saturday or Sunday
            return False

        # TODO: Add holiday check
        return True

    @staticmethod
    def time_to_market_open() -> int:
        """Minutes until market opens."""
        if not LoopSchedule.is_market_day():
            # If it's weekend, count until Monday 9:30 AM
            days_until_monday = (7 - datetime.now().weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            return days_until_monday * 24 * 60 + (LoopSchedule.MARKET_OPEN.hour * 60)

        now = datetime.now().time()
        if now < LoopSchedule.MARKET_OPEN:
            diff = datetime.combine(datetime.today(), LoopSchedule.MARKET_OPEN) - \
                   datetime.combine(datetime.today(), now)
            return int(diff.total_seconds() / 60)

        # Market is open or closed for the day
        return 0


class LoopManager:
    """Manages continuous trading loops for agents."""

    def __init__(self, state_dir: str = "oversight/loop_state"):
        """
        Initialize loop manager.

        Args:
            state_dir: Directory for storing loop state
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.loops: Dict[str, Dict[str, Any]] = {}
        self._load_loop_states()

    def start_loop(
        self,
        agent_id: str,
        interval_seconds: int = 300,  # 5 minutes default
        max_cycles: Optional[int] = None,
        dry_run: bool = False,
        manual: bool = False,
        subagent: bool = False,
        automated: bool = False,
        market_hours_only: bool = True,
        detached: bool = False,
        cycle_func: Optional[Callable] = None
    ) -> bool:
        """
        Start a continuous trading loop for an agent.

        Args:
            agent_id: Agent ID to run
            interval_seconds: Seconds between cycles (default 5 min)
            max_cycles: Maximum cycles before stopping (None = unlimited)
            dry_run: Run without executing trades
            manual: Use manual mode
            subagent: Use subagent mode
            automated: Use automated mode (Anthropic API)
            market_hours_only: Only trade during market hours
            detached: Run in detached mode (non-daemon thread)
            cycle_func: Function to call for each cycle

        Returns:
            True if loop started successfully
        """
        if agent_id in self.loops and self.loops[agent_id]["status"] == LoopStatus.RUNNING:
            logger.warning(f"Loop already running for {agent_id}")
            return False

        try:
            loop_config = {
                "agent_id": agent_id,
                "status": LoopStatus.RUNNING,
                "interval_seconds": interval_seconds,
                "max_cycles": max_cycles,
                "dry_run": dry_run,
                "manual": manual,
                "subagent": subagent,
                "market_hours_only": market_hours_only,
                "started_at": datetime.utcnow().isoformat(),
                "cycles_completed": 0,
                "last_cycle_at": None,
                "last_error": None,
                "cycle_func": cycle_func,
                "thread": None
            }

            # Start loop in background thread
            # Use non-daemon thread for detached mode so it survives process exit
            thread = threading.Thread(
                target=self._run_loop,
                args=(loop_config,),
                daemon=not detached
            )
            loop_config["thread"] = thread
            thread.start()

            self.loops[agent_id] = loop_config
            self._save_loop_state(agent_id)

            logger.info(
                f"Started loop for {agent_id}: interval={interval_seconds}s, "
                f"market_hours_only={market_hours_only}, dry_run={dry_run}"
            )

            return True

        except Exception as e:
            logger.error(f"Error starting loop for {agent_id}: {e}")
            return False

    def stop_loop(self, agent_id: str) -> bool:
        """
        Stop a running loop.

        Args:
            agent_id: Agent ID to stop

        Returns:
            True if loop stopped successfully
        """
        if agent_id not in self.loops:
            logger.warning(f"No loop found for {agent_id}")
            return False

        try:
            loop = self.loops[agent_id]
            loop["status"] = LoopStatus.STOPPED
            self._save_loop_state(agent_id)

            logger.info(
                f"Stopped loop for {agent_id}: "
                f"completed {loop['cycles_completed']} cycles"
            )

            return True

        except Exception as e:
            logger.error(f"Error stopping loop for {agent_id}: {e}")
            return False

    def pause_loop(self, agent_id: str) -> bool:
        """Pause a running loop."""
        if agent_id not in self.loops:
            return False

        self.loops[agent_id]["status"] = LoopStatus.PAUSED
        self._save_loop_state(agent_id)
        logger.info(f"Paused loop for {agent_id}")
        return True

    def resume_loop(self, agent_id: str) -> bool:
        """Resume a paused loop."""
        if agent_id not in self.loops:
            return False

        self.loops[agent_id]["status"] = LoopStatus.RUNNING
        self._save_loop_state(agent_id)
        logger.info(f"Resumed loop for {agent_id}")
        return True

    def get_loop_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a loop."""
        if agent_id not in self.loops:
            return None

        loop = self.loops[agent_id]
        return {
            "agent_id": agent_id,
            "status": loop["status"].value,
            "cycles_completed": loop["cycles_completed"],
            "started_at": loop["started_at"],
            "last_cycle_at": loop["last_cycle_at"],
            "last_error": loop["last_error"],
            "interval_seconds": loop["interval_seconds"],
        }

    def list_loops(self) -> Dict[str, Dict[str, Any]]:
        """List all active loops."""
        return {
            agent_id: self.get_loop_status(agent_id)
            for agent_id in self.loops
            if self.loops[agent_id]["status"] != LoopStatus.STOPPED
        }

    # ==================== Private Methods ====================

    def _run_loop(self, loop_config: Dict[str, Any]) -> None:
        """
        Run the main loop in background thread.

        Args:
            loop_config: Loop configuration dict
        """
        agent_id = loop_config["agent_id"]
        cycles_completed = 0
        logger.info(f"Loop thread started for {agent_id}")

        try:
            while loop_config["status"] == LoopStatus.RUNNING:
                # Check market hours if required
                if loop_config["market_hours_only"]:
                    if not LoopSchedule.is_market_hours():
                        logger.debug(f"Market closed, waiting for {agent_id}")
                        time_to_open = LoopSchedule.time_to_market_open()
                        # Sleep in 60-second chunks to allow for quick stop
                        # If time_to_open is 0 (market closed for the day), sleep for 60 seconds before rechecking
                        sleep_iterations = max(1, min(time_to_open * 60, 3600))
                        for _ in range(sleep_iterations):
                            if loop_config["status"] != LoopStatus.RUNNING:
                                break
                            time_module.sleep(1)
                        continue

                # Execute cycle
                try:
                    logger.info(f"Executing cycle {cycles_completed + 1} for {agent_id}")

                    # Call the cycle function if provided
                    if loop_config["cycle_func"]:
                        loop_config["cycle_func"](agent_id, loop_config)
                    else:
                        logger.warning(f"No cycle function for {agent_id}")

                    cycles_completed += 1
                    loop_config["cycles_completed"] = cycles_completed
                    loop_config["last_cycle_at"] = datetime.utcnow().isoformat()
                    loop_config["last_error"] = None

                    # Check max cycles
                    if loop_config["max_cycles"] and cycles_completed >= loop_config["max_cycles"]:
                        logger.info(f"Reached max cycles ({loop_config['max_cycles']}) for {agent_id}")
                        loop_config["status"] = LoopStatus.STOPPED
                        break

                except Exception as e:
                    logger.error(f"Error in cycle for {agent_id}: {e}")
                    loop_config["last_error"] = str(e)
                    loop_config["status"] = LoopStatus.ERROR

                # Save state
                self._save_loop_state(agent_id)

                # Wait for next cycle
                if loop_config["status"] == LoopStatus.RUNNING:
                    for _ in range(loop_config["interval_seconds"]):
                        if loop_config["status"] != LoopStatus.RUNNING:
                            break
                        time_module.sleep(1)

        except Exception as e:
            logger.error(f"Fatal error in loop for {agent_id}: {e}")
            loop_config["status"] = LoopStatus.ERROR
            loop_config["last_error"] = str(e)
            self._save_loop_state(agent_id)
        finally:
            logger.info(f"Loop thread exited for {agent_id}, status={loop_config['status']}, cycles_completed={cycles_completed}")

    def _save_loop_state(self, agent_id: str) -> None:
        """Save loop state to file."""
        try:
            if agent_id not in self.loops:
                return

            loop = self.loops[agent_id]
            state = {
                "agent_id": agent_id,
                "status": loop["status"].value,
                "cycles_completed": loop["cycles_completed"],
                "started_at": loop["started_at"],
                "last_cycle_at": loop["last_cycle_at"],
                "last_error": loop["last_error"],
                "interval_seconds": loop["interval_seconds"],
            }

            state_file = self.state_dir / f"{agent_id}.json"
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.warning(f"Could not save loop state for {agent_id}: {e}")

    def _load_loop_states(self) -> None:
        """Load loop states from files."""
        try:
            for state_file in self.state_dir.glob("*.json"):
                with open(state_file, "r") as f:
                    state = json.load(f)

                agent_id = state['agent_id']

                # Restore loop state to memory (don't restart threads)
                # Convert status string back to enum
                status = LoopStatus(state.get('status', 'stopped'))

                self.loops[agent_id] = {
                    "agent_id": agent_id,
                    "status": status,
                    "cycles_completed": state.get('cycles_completed', 0),
                    "started_at": state.get('started_at'),
                    "last_cycle_at": state.get('last_cycle_at'),
                    "last_error": state.get('last_error'),
                    "interval_seconds": state.get('interval_seconds', 300),
                    "max_cycles": None,  # Not persisted, will use current request value
                    "dry_run": False,
                    "manual": False,
                    "subagent": False,
                    "market_hours_only": True,
                    "cycle_func": None,
                    "thread": None  # Thread is gone, don't try to restart
                }

                logger.info(f"Loaded loop state for {agent_id}: status={status.value}")

        except Exception as e:
            logger.warning(f"Could not load loop states: {e}")


def get_loop_manager(state_dir: str = "oversight/loop_state") -> LoopManager:
    """Factory function to get loop manager instance."""
    return LoopManager(state_dir)
