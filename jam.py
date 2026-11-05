#!/usr/bin/env python3
"""
jam.py - AI Agent Orchestrator

Orchestrates multiple AI coding agents working on a shared project.
Multiplexes their output, manages inter-agent communication via JSONL message files,
and coordinates their work through a simple process supervision model.

Created: Initial implementation of multi-agent orchestration system
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML")
    sys.exit(1)


class AgentProcess:
    """Manages a single agent subprocess with output capture and message logging."""
    
    def __init__(self, name: str, command: List[str], working_dir: str, 
                 initial_prompt: str, messages_dir: Path, log_file):
        self.name = name
        self.command = command
        self.working_dir = working_dir
        self.initial_prompt = initial_prompt
        self.messages_dir = messages_dir
        self.log_file = log_file
        self.process: Optional[subprocess.Popen] = None
        self.message_file = messages_dir / f"{name}.jsonl"
        
        # Ensure message file exists
        self.message_file.parent.mkdir(parents=True, exist_ok=True)
        self.message_file.touch(exist_ok=True)
    
    def read_other_agents_messages(self, orchestrator) -> str:
        """Generate a system note about other agents' recent work."""
        other_messages = []
        
        for agent_name, agent in orchestrator.agents.items():
            if agent_name == self.name:
                continue
            
            if agent.message_file.exists():
                # Read last 5 messages from other agents
                try:
                    with open(agent.message_file, 'r') as f:
                        lines = f.readlines()
                        recent = lines[-5:] if len(lines) > 5 else lines
                        for line in recent:
                            try:
                                msg = json.loads(line)
                                other_messages.append(
                                    f"[{agent_name}] {msg.get('summary', 'working...')}"
                                )
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    orchestrator.log(self.name, f"Warning: Could not read {agent_name} messages: {e}")
        
        if other_messages:
            return (
                "\n=== SYSTEM NOTE: Other agents' recent activity ===\n"
                + "\n".join(other_messages[-10:])  # Last 10 messages across all agents
                + "\n=== End system note. Consider incorporating relevant changes. ===\n"
            )
        return ""
    
    def log_message(self, summary: str, files_touched: List[str] = None):
        """Append a message entry to this agent's JSONL file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "summary": summary,
            "files_touched": files_touched or []
        }
        
        try:
            with open(self.message_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[{self.name}] Error writing message: {e}", file=sys.stderr)
    
    def start(self, orchestrator):
        """Start the agent subprocess."""
        # Log agent starting
        system_note = self.read_other_agents_messages(orchestrator)
        
        if system_note:
            orchestrator.log(self.name, "Reading other agents' messages...")
            # Note: In a real implementation, we'd inject this into the agent's input
            # For V1, we just log it. Future versions could use stdin or temp files.
        
        orchestrator.log(self.name, f"Starting with command: {' '.join(self.command)}")
        orchestrator.log(self.name, f"Working directory: {self.working_dir}")
        orchestrator.log(self.name, f"Initial prompt: {self.initial_prompt}")
        
        try:
            self.process = subprocess.Popen(
                self.command,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.log_message(f"Agent started with PID {self.process.pid}")
            
            # Start output capture threads
            threading.Thread(
                target=self._capture_output,
                args=(self.process.stdout, orchestrator, "stdout"),
                daemon=True
            ).start()
            
            threading.Thread(
                target=self._capture_output,
                args=(self.process.stderr, orchestrator, "stderr"),
                daemon=True
            ).start()
            
        except Exception as e:
            orchestrator.log(self.name, f"ERROR: Failed to start: {e}")
            self.log_message(f"Failed to start: {e}")
    
    def _capture_output(self, pipe, orchestrator, stream_name):
        """Capture output from subprocess pipe and log it."""
        try:
            for line in pipe:
                line = line.rstrip()
                if line:
                    orchestrator.log(self.name, line, stream_name)
        except Exception as e:
            orchestrator.log(self.name, f"Error capturing {stream_name}: {e}")
    
    def stop(self):
        """Stop the agent subprocess gracefully."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print(f"[{self.name}] Error stopping: {e}", file=sys.stderr)


class Orchestrator:
    """Main orchestrator that manages all agent processes."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.agents: Dict[str, AgentProcess] = {}
        self.log_file_path = Path("jam.log")
        self.log_file = None
        self.messages_dir = Path("messages")
        self.running = False
        self.log_lock = threading.Lock()
        
        # Set up signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\n\nReceived shutdown signal, stopping all agents...")
        self.stop()
        sys.exit(0)
    
    def log(self, agent_name: str, message: str, stream: str = "stdout"):
        """Log a message with timestamp and agent name to both file and terminal."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] [{agent_name}] {message}"
        
        with self.log_lock:
            # Print to terminal
            print(log_line)
            
            # Write to log file
            if self.log_file:
                self.log_file.write(log_line + "\n")
                self.log_file.flush()
    
    def load_config(self):
        """Load and parse the jam.yaml configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            agents_config = config.get('agents', [])
            
            for agent_cfg in agents_config:
                name = agent_cfg['name']
                command = agent_cfg['command']
                working_dir = agent_cfg.get('working_dir', '.')
                initial_prompt = agent_cfg.get('initial_prompt', '')
                
                # Expand working_dir to absolute path
                working_dir = os.path.abspath(working_dir)
                
                # Parse command string into list
                if isinstance(command, str):
                    command = command.split()
                
                agent = AgentProcess(
                    name=name,
                    command=command,
                    working_dir=working_dir,
                    initial_prompt=initial_prompt,
                    messages_dir=self.messages_dir,
                    log_file=self.log_file
                )
                
                self.agents[name] = agent
            
            self.log("ORCHESTRATOR", f"Loaded {len(self.agents)} agents from config")
            
        except Exception as e:
            print(f"Error loading config: {e}", file=sys.stderr)
            sys.exit(1)
    
    def start(self):
        """Start the orchestrator and all configured agents."""
        self.running = True
        
        # Open log file
        self.log_file = open(self.log_file_path, 'a')
        
        self.log("ORCHESTRATOR", "=" * 60)
        self.log("ORCHESTRATOR", "jam.py starting")
        self.log("ORCHESTRATOR", f"Config: {self.config_path}")
        self.log("ORCHESTRATOR", f"Log file: {self.log_file_path}")
        self.log("ORCHESTRATOR", f"Messages dir: {self.messages_dir}")
        self.log("ORCHESTRATOR", "=" * 60)
        
        # NOTE: Future ACP (Agent Communication Protocol) integration point
        # ACP would replace the JSONL message bus with:
        # - Standardized agent discovery and capability declaration
        # - Structured message exchange protocol
        # - Richer coordination primitives (locks, conflict resolution, etc.)
        # For V1, we use simple JSONL files for inter-agent communication.
        
        self.load_config()
        
        # Start all agents
        for name, agent in self.agents.items():
            agent.start(self)
            time.sleep(0.5)  # Small delay between agent starts
        
        self.log("ORCHESTRATOR", f"All {len(self.agents)} agents started")
        self.log("ORCHESTRATOR", "Press Ctrl+C to stop all agents")
        
        # Monitor agents
        try:
            while self.running:
                time.sleep(1)
                
                # Check if any agents have exited
                for name, agent in self.agents.items():
                    if agent.process and agent.process.poll() is not None:
                        exit_code = agent.process.returncode
                        self.log(name, f"Process exited with code {exit_code}")
                        agent.log_message(f"Process exited with code {exit_code}")
                        agent.process = None
        
        except KeyboardInterrupt:
            self.log("ORCHESTRATOR", "Keyboard interrupt received")
            self.stop()
    
    def stop(self):
        """Stop all agents and clean up."""
        if not self.running:
            return
        
        self.running = False
        self.log("ORCHESTRATOR", "Stopping all agents...")
        
        for name, agent in self.agents.items():
            self.log(name, "Stopping...")
            agent.stop()
            agent.log_message("Agent stopped by orchestrator")
        
        self.log("ORCHESTRATOR", "All agents stopped")
        
        if self.log_file:
            self.log_file.close()


def main():
    parser = argparse.ArgumentParser(
        description="jam.py - AI Agent Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python jam.py                 # Use default jam.yaml
  python jam.py myconfig.yaml   # Use custom config
  python jam.py stop            # Stop running orchestrator (Ctrl+C)
        """
    )
    
    parser.add_argument(
        'config',
        nargs='?',
        default='jam.yaml',
        help='Configuration file (default: jam.yaml)'
    )
    
    args = parser.parse_args()
    
    if args.config == 'stop':
        print("To stop jam.py, press Ctrl+C in the terminal where it's running")
        sys.exit(0)
    
    if not os.path.exists(args.config):
        print(f"Error: Configuration file '{args.config}' not found", file=sys.stderr)
        sys.exit(1)
    
    orchestrator = Orchestrator(args.config)
    orchestrator.start()


if __name__ == "__main__":
    main()
