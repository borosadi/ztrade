# ADR-004: Continuous Autonomous Trading Loops

**Date**: 2025-11-08
**Status**: Implemented

## Decision

Build continuous trading loop infrastructure with background thread support, market hours detection, and graceful control mechanisms.

## Rationale

- Manual trading cycles require constant user intervention
- Autonomous trading should run continuously during market hours
- Need proper lifecycle management (start/stop/pause/resume)
- State persistence for recovery after interruptions
- Market hours enforcement to prevent trading when markets are closed

## Components Created

### 1. `cli/utils/loop_manager.py` (390 lines)
- `LoopManager` class for orchestrating continuous loops
- `LoopSchedule` class for market hours detection
- `LoopStatus` enum for loop states (STOPPED, RUNNING, PAUSED, ERROR)
- Background daemon thread support per agent
- State persistence to JSON files
- Graceful shutdown with interruptible sleep

### 2. `cli/commands/loop.py` (95 lines)
- `loop start <agent_id>` - Start continuous loop with configurable parameters
- `loop stop <agent_id>` - Stop running loop gracefully
- `loop pause <agent_id>` - Pause temporarily
- `loop resume <agent_id>` - Resume from pause
- `loop status [agent_id]` - Show status of all or specific loop
- `loop market-hours` - Display current market hours status

## Key Features

### 1. Market Hours Detection
- Regular hours: 9:30 AM - 4:00 PM EST, Monday-Friday
- Pre-market: 4:00 AM - 9:30 AM EST (optional, not enabled by default)
- After-hours: 4:00 PM - 8:00 PM EST (optional, not enabled by default)
- Weekend detection (no trading Saturday/Sunday)
- TODO: Holiday calendar integration

### 2. Background Thread Management
- Each agent gets a daemon thread
- Thread runs cycle function at configurable intervals (default 300s = 5 min)
- Sleeps in 1-second increments to allow quick stop response
- Main process stays alive with monitoring loop
- Ctrl+C support for graceful shutdown

### 3. State Persistence
- Loop state saved to `oversight/loop_state/<agent_id>.json`
- Tracks: status, cycles_completed, started_at, last_cycle_at, last_error
- State reloaded on status checks (not auto-restart, must explicitly start)
- Enables recovery after system restart

### 4. Configurable Parameters
- `--interval`: Seconds between cycles (default 300 = 5 minutes)
- `--max-cycles`: Maximum cycles before automatic stop (optional)
- `--dry-run`: Simulate without executing trades
- `--manual/--subagent`: Execution mode
- `--market-hours/--no-market-hours`: Enforce trading hours (default: on)

## Usage Examples

```bash
# Start continuous loop with default 5-minute interval
uv run ztrade loop start agent_spy

# Start with custom interval and max cycles
uv run ztrade loop start agent_spy --interval 60 --max-cycles 100

# Trade 24/7 (ignore market hours)
uv run ztrade loop start agent_spy --no-market-hours

# Check status
uv run ztrade loop status agent_spy
uv run ztrade loop status  # All loops

# Control loop
uv run ztrade loop pause agent_spy
uv run ztrade loop resume agent_spy
uv run ztrade loop stop agent_spy

# Check market hours
uv run ztrade loop market-hours
```

## Testing Results

```
Test 1: 2 cycles with 2-second interval
- Started: 23:56:26
- Cycle 1: 23:56:26 (executed)
- Cycle 2: 23:56:28 (executed, 2s later)
- Completed: 23:56:28
- Status: STOPPED (max_cycles reached)
- ✅ SUCCESS

Test 2: Market hours detection
- After hours (11:45 PM): Loop waits for market open
- Market open (9:30 AM): Loop executes cycles
- ✅ SUCCESS

Test 3: Graceful shutdown
- Started loop with 10 max cycles
- Pressed Ctrl+C after 3 cycles
- Loop stopped gracefully
- State saved correctly
- ✅ SUCCESS
```

## Architecture Decision: Daemon Threads + Monitoring Loop

Initial implementation had daemon threads exiting when main CLI process ended. Solution:
- Main `loop start` command stays alive with monitoring loop
- Checks loop status every 0.5 seconds
- Exits when loop status becomes 'stopped' or 'error'
- Supports Ctrl+C for manual interruption
- This keeps daemon thread alive for full execution

## Critical Bug Fix

The initial implementation had daemon threads being killed when the CLI command returned. The background thread would start but only execute 1 cycle before the main process exited. Fixed by adding a monitoring loop in the `start` command that keeps the main process alive until:
1. Loop completes (max_cycles reached)
2. Loop status becomes 'stopped' or 'error'
3. User presses Ctrl+C

## Integration Points

- `cli/main.py`: Registered loop command group
- `cli/commands/loop.py`: Simplified cycle function (TODO: integrate full trading logic)
- `cli/utils/loop_manager.py`: Core loop orchestration

## Future Enhancements

- Background daemon process (detached from CLI, survives terminal close)
- Holiday calendar integration for market hours
- Adaptive interval based on volatility
- Multi-agent coordination (prevent overconcentration)
- Loop health monitoring and alerting
- Auto-restart on errors (with exponential backoff)
- Performance metrics per loop (avg cycle time, success rate)
