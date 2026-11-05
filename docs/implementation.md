# jam.py Implementation Documentation

**Date**: November 5, 2026  
**Task**: Build the jam.py orchestrator experiment from scratch

## Overview

Built a complete Python-based multi-agent orchestrator system that coordinates multiple AI coding agents working on a shared project.

## What Was Built

### Core Components

#### 1. jam.py (Main Orchestrator)
- **Purpose**: Orchestrates multiple AI coding harnesses as subprocesses
- **Key Features**:
  - YAML configuration loading
  - Multi-process subprocess management
  - Real-time output capture and multiplexing
  - Timestamped, agent-prefixed logging
  - JSONL-based inter-agent communication
  - Clean shutdown with signal handling (SIGINT/SIGTERM)
  - Thread-safe logging with locks
  
- **Architecture**:
  - `AgentProcess` class: Manages individual agent subprocess
  - `Orchestrator` class: Coordinates all agents
  - Output capture threads for stdout/stderr
  - Signal handlers for graceful shutdown

- **Inter-Agent Communication**:
  - Each agent gets `messages/<agent-name>.jsonl` file
  - Agents log: timestamp, agent name, summary, files touched
  - Before starting, agents can read other agents' messages
  - Future: ACP (Agent Communication Protocol) integration point marked in code

#### 2. jam.yaml (Sample Configuration)
- Defines 4 agents:
  1. **codex**: OpenAI's code generation tool
  2. **claude**: Anthropic's Claude Code
  3. **opencode**: Alternative AI coding tool
  4. **python-agent**: Plain Python stub (works without external CLIs)

- Configuration schema:
  - `name`: Agent identifier
  - `command`: Launch command
  - `working_dir`: Working directory
  - `initial_prompt`: Task description

#### 3. Demo Project (demo/)
- **demo/index.html**: Simple HTML counter application
  - Button that increments a counter
  - Basic CSS styling
  - JavaScript interactivity
  - Small enough to observe multi-agent changes in real-time

#### 4. Plain Python Agent (agents/plain_python_agent.py)
- Functional stub agent that runs without external dependencies
- **Capabilities**:
  - Reads other agents' JSONL message files
  - Analyzes the demo project
  - Reports what it would do
  - Makes no actual changes (to avoid conflicts during testing)
- Allows smoke testing of jam.py without installing AI CLIs

#### 5. Supporting Files

##### README.md
- Comprehensive documentation including:
  - Quick start guide
  - Installation instructions
  - Configuration format
  - Architecture explanation
  - Inter-agent communication protocol
  - ACP integration notes
  - Project structure
  - Troubleshooting guide
  - Examples

##### requirements.txt
- Python dependencies: `PyYAML>=6.0`

##### .gitignore
- Excludes runtime files: `jam.log`, `messages/*.jsonl`
- Excludes Python artifacts: `__pycache__`, `*.pyc`, etc.
- Preserves directory structure with `messages/.gitkeep`

## Key Design Decisions

### V1 Philosophy: Deliberately Simple
- **No retries**: Agents run once, exit codes are logged
- **No crash recovery**: No checkpointing or resume
- **No sophisticated scheduling**: All agents start simultaneously
- **No conflict resolution**: Agents must coordinate via messages
- **Observable**: Everything logged with timestamps for easy debugging

### Future Extensibility
- **ACP Integration Point**: Code comment marks where Agent Communication Protocol would replace JSONL bus
- ACP would provide:
  - Agent discovery and capability declaration
  - Structured message exchange
  - Coordination primitives (locks, conflict resolution)
  - Event subscriptions

### Process Management
- Subprocess spawning with separate stdout/stderr pipes
- Thread-based output capture (non-blocking)
- Graceful shutdown: SIGTERM → 5s wait → SIGKILL
- Signal handlers for clean Ctrl+C behavior

### Logging Strategy
- **Dual output**: Terminal + `jam.log` file
- **Format**: `[timestamp] [agent-name] message`
- **Thread-safe**: Uses locks for concurrent writes
- **Real-time**: Line-buffered, immediate visibility

## Testing

### Smoke Test Performed
```bash
python3 jam.py jam-test.yaml
```

- Verified orchestrator starts correctly
- Confirmed agent subprocess spawning
- Validated output multiplexing and timestamps
- Checked JSONL message file creation
- Tested clean shutdown (timeout after 5s)

### Test Results
✅ Configuration loading  
✅ Agent subprocess spawning  
✅ Output capture and timestamping  
✅ Combined log file writing  
✅ JSONL message file creation  
✅ Agent name prefixing  
✅ Clean shutdown  
✅ No syntax errors  

## Project Structure
```
jam.py/
├── jam.py                    # Main orchestrator (executable)
├── jam.yaml                  # Sample 4-agent configuration
├── requirements.txt          # PyYAML dependency
├── README.md                 # Comprehensive documentation
├── .gitignore               # Git ignore patterns
├── demo/                    # Demo HTML project
│   └── index.html          # Simple counter app
├── agents/                  # Agent implementations
│   └── plain_python_agent.py  # Stub agent (executable)
├── messages/                # Inter-agent communication
│   └── .gitkeep            # Keep directory in git
├── jam.log                  # Combined output log (runtime, ignored)
└── docs/                    # Documentation
    └── implementation.md    # This file
```

## Usage Examples

### Basic Usage
```bash
# Install dependencies
pip install -r requirements.txt

# Run with default config
python jam.py

# Run with custom config
python jam.py myconfig.yaml

# Stop: Press Ctrl+C
```

### Watching Output
```bash
# In separate terminal
tail -f jam.log
```

### Checking Messages
```bash
cat messages/python-agent.jsonl
```

## What Was NOT Implemented (By Design)

Per V1 requirements, these were intentionally omitted:
- ❌ Retry logic
- ❌ Crash recovery / checkpointing
- ❌ Advanced scheduling
- ❌ Resource limits
- ❌ Agent pause/resume
- ❌ Conflict detection/resolution
- ❌ Web UI
- ❌ ACP protocol implementation (only integration point marked)

## Success Criteria Met

✅ `python jam.py` starts, loads config, spawns agents  
✅ Multiplexes tagged/timestamped output to terminal + log  
✅ Stop/clean kill works (Ctrl+C)  
✅ Sample jam.yaml with 4 agents provided  
✅ Demo HTML project included  
✅ Plain Python agent stub works without external CLIs  
✅ ACP noted as future-slot comment, not implemented  
✅ Clear README with usage, architecture, troubleshooting  
✅ Everything committed with clear message  
✅ Pushed to main branch  

## Technical Notes

### Python Version
- Requires Python 3.6+ (uses f-strings, type hints)
- Tested with Python 3.12.3

### Thread Safety
- Log writes use `threading.Lock()`
- File handles are not shared between threads
- Each agent has dedicated output capture threads

### Signal Handling
- `SIGINT` (Ctrl+C) and `SIGTERM` handled
- Propagates termination to all child processes
- 5-second grace period before force-kill

### File Formats
- **jam.yaml**: YAML configuration
- **messages/*.jsonl**: JSON Lines (one JSON object per line)
- **jam.log**: Plain text with structured prefixes

## Changes Made to Repository

### New Files (8)
1. `jam.py` - Main orchestrator script
2. `jam.yaml` - Sample configuration
3. `demo/index.html` - Demo project
4. `agents/plain_python_agent.py` - Stub agent
5. `messages/.gitkeep` - Directory placeholder
6. `requirements.txt` - Dependencies
7. `.gitignore` - Ignore patterns
8. `README.md` - Updated with full documentation

### Modified Files (1)
- `README.md` - Replaced placeholder with comprehensive docs

### Git Commit
```
commit 7ba74d0
Initial implementation of jam.py multi-agent orchestrator
```

## Future Enhancement Ideas

Documented in README for potential future work:
- ACP (Agent Communication Protocol) integration
- Better conflict detection and resolution
- Checkpoint/resume functionality
- Resource limiting and scheduling
- Metrics and observability
- Web dashboard
- Agent discovery service
- Capability-based routing
- Distributed agent pools

## Conclusion

Successfully delivered a working V1 multi-agent orchestrator that demonstrates:
- Process-based agent coordination
- Real-time output multiplexing
- Inter-agent communication primitives
- Clean lifecycle management

The system is intentionally simple, observable, and extensible. All code is working, tested, documented, and committed to the main branch.
