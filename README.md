# jam.py - AI Agent Orchestrator

An experimental Python orchestrator that coordinates multiple AI coding agents working on a shared project.

## Overview

`jam.py` spawns multiple AI coding harnesses (like Codex, Claude Code, OpenCode, or custom Python agents) as subprocesses, captures their output in real-time, and facilitates inter-agent communication through a simple JSONL message bus.

### Key Features

- **Multi-agent orchestration**: Run multiple AI agents simultaneously on the same codebase
- **Unified logging**: All agent output is multiplexed into a single stream with timestamps and agent name prefixes
- **Inter-agent communication**: Agents share progress through JSONL message files (future: ACP protocol)
- **Live monitoring**: See all agent activity in real-time in your terminal
- **Clean shutdown**: Graceful termination of all child processes

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Make jam.py executable (optional)
chmod +x jam.py
```

### Running the Demo

```bash
# Start the orchestrator with the sample configuration
python jam.py

# Or specify a custom config
python jam.py myconfig.yaml
```

### Stopping

Press `Ctrl+C` in the terminal where `jam.py` is running. This will:
1. Send SIGTERM to all agent subprocesses
2. Wait up to 5 seconds for each to terminate gracefully
3. Force-kill any remaining processes
4. Close log files and exit

## Configuration

`jam.yaml` defines the agents and their settings:

```yaml
agents:
  - name: codex
    command: codex --prompt "Your task here"
    working_dir: ./demo
    initial_prompt: "Description of the agent's task"
  
  - name: claude
    command: claude-code --prompt "Your task here"
    working_dir: ./demo
    initial_prompt: "Another task description"
```

### Configuration Fields

- **name**: Unique identifier for the agent (used in logs and message files)
- **command**: Shell command to launch the agent (can be a string or list)
- **working_dir**: Directory where the agent runs (relative to jam.yaml location)
- **initial_prompt**: Description of the agent's initial task

## How It Works

### 1. Agent Spawning

`jam.py` reads the configuration and spawns each agent as a subprocess with:
- Separate stdout/stderr pipes
- The configured working directory
- Environment inherited from the parent process

### 2. Output Multiplexing

Every line of stdout/stderr from each agent is:
- Prefixed with `[timestamp] [agent-name]`
- Written to `jam.log` file
- Printed live to the terminal

Example output:
```
[2026-11-05 17:30:15.123] [codex] Starting analysis...
[2026-11-05 17:30:15.234] [claude] Reading project files...
[2026-11-05 17:30:16.456] [python-agent] Found 3 messages from other agents
```

### 3. Inter-Agent Communication

Each agent gets a JSONL file at `messages/<agent-name>.jsonl`. When an agent completes work, it logs:

```json
{
  "timestamp": "2026-11-05T17:30:15.123456",
  "agent": "codex",
  "summary": "Added dark mode toggle",
  "files_touched": ["index.html", "styles.css"]
}
```

Before starting work, agents should read other agents' message files to:
- Avoid duplicate effort
- Build on others' changes
- Coordinate complementary improvements

**Note**: V1 is deliberately simple. Agents must explicitly read message files. Future versions may inject system notes automatically.

### 4. Future: ACP (Agent Communication Protocol)

The current JSONL message bus is a placeholder. Future versions will integrate ACP to provide:
- **Agent discovery**: Automatic detection of available agents and their capabilities
- **Capability declaration**: Agents advertise what they can do
- **Structured messages**: Rich, typed messages beyond simple JSONL logs
- **Coordination primitives**: Locks, conflict resolution, task claiming
- **Event subscriptions**: Agents can subscribe to relevant changes

The integration point is marked in the code with a comment block.

## Project Structure

```
jam.py/
├── jam.py                    # Main orchestrator script
├── jam.yaml                  # Sample configuration
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── demo/                     # Demo HTML project
│   └── index.html           # Simple counter app
├── agents/                   # Agent implementations
│   └── plain_python_agent.py # Stub agent for testing
├── messages/                 # Inter-agent communication
│   ├── .gitkeep
│   └── *.jsonl              # One file per agent (runtime)
└── jam.log                   # Combined output log (runtime)
```

## Demo Project

The `demo/` directory contains a minimal HTML counter app with:
- A button that increments a counter
- Basic styling
- JavaScript for interactivity

This serves as a small, observable target for multiple agents to work on simultaneously. You can watch them add features like:
- Reset buttons
- Dark mode
- Animations
- Improved styling

## Agent Implementations

### Included: Plain Python Agent

`agents/plain_python_agent.py` is a fully functional stub that:
- Reads other agents' JSONL messages
- Analyzes the demo project
- Reports what it would do
- Makes no actual changes (to avoid conflicts in testing)

This allows you to run `jam.py` immediately without installing external AI CLI tools.

### External AI Agents (Require Installation)

The sample `jam.yaml` references:
- **Codex**: OpenAI's code generation tool
- **Claude Code**: Anthropic's coding assistant
- **OpenCode**: Alternative coding AI

To use these, install their respective CLI tools first. The plain Python agent works out-of-the-box for testing.

## V1 Design Philosophy

This is **V1**: intentionally simple and observable. It does NOT include:

- ❌ Automatic retry on agent failure
- ❌ Crash recovery or checkpoint/resume
- ❌ Sophisticated scheduling or resource limits
- ❌ Conflict detection or merge resolution
- ❌ Agent pause/resume controls
- ❌ Web UI or API

These features may come in future versions. The goal is to ship a working foundation that demonstrates multi-agent orchestration and provides a substrate for experimentation.

## Troubleshooting

### "PyYAML is required"

```bash
pip install PyYAML
```

### "Configuration file not found"

Make sure `jam.yaml` exists in the current directory, or specify the path:

```bash
python jam.py path/to/config.yaml
```

### Agents not starting

Check that:
1. The command in `jam.yaml` is correct
2. Required CLI tools are installed
3. Working directory paths exist
4. You have permission to execute the agent commands

### Output not appearing

- All output goes to both terminal and `jam.log`
- If terminal is quiet, check `jam.log` for errors
- Agents may take time to produce output

### Stopping doesn't work

If `Ctrl+C` doesn't cleanly stop all agents:

```bash
# Find jam.py process
ps aux | grep jam.py

# Force kill if needed
kill -9 <PID>

# Clean up any orphaned agent processes
pkill -f "codex|claude-code|opencode"
```

## Examples

### Custom Configuration

Create a new YAML file:

```yaml
agents:
  - name: frontend
    command: codex --prompt "Improve UI/UX"
    working_dir: ./src
    initial_prompt: "Focus on user interface improvements"
  
  - name: backend
    command: codex --prompt "Optimize API endpoints"
    working_dir: ./src
    initial_prompt: "Focus on backend performance"
  
  - name: tests
    command: python agents/test_writer.py
    working_dir: ./src
    initial_prompt: "Write tests for new code"
```

Then run:

```bash
python jam.py myproject.yaml
```

### Watching the Log

In a separate terminal:

```bash
tail -f jam.log
```

Or use a log viewer:

```bash
less +F jam.log  # Press Ctrl+C to stop following, 'q' to quit
```

## Contributing

This is an experimental project. Ideas for improvement:

- Better agent communication protocols (ACP integration)
- Conflict detection and resolution
- Checkpoint/resume functionality
- Resource limiting and scheduling
- Metrics and observability
- Web dashboard

## License

Experimental software. Use at your own risk.

## Version

**V1** - Initial implementation (2026-11-05)
- Basic multi-agent orchestration
- JSONL message bus
- Combined logging
- Clean shutdown
