#!/usr/bin/env python3
"""
plain_python_agent.py - Simple Python agent stub

A minimal agent that demonstrates the orchestrator's functionality without
requiring external AI CLI tools. This agent:
1. Reads other agents' JSONL message files
2. Makes a trivial change or reports what it would do
3. Exits cleanly

This is a stub for testing jam.py orchestration. Real agents would be
sophisticated AI coding tools like Codex, Claude Code, or OpenCode.

Created: Agent stub for jam.py orchestration testing
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


def read_agent_messages():
    """Read messages from other agents in the messages/ directory."""
    messages_dir = Path("../messages")
    
    if not messages_dir.exists():
        print("No messages directory found yet.", flush=True)
        return []
    
    all_messages = []
    
    for message_file in messages_dir.glob("*.jsonl"):
        # Skip our own messages
        if message_file.stem == "python-agent":
            continue
        
        try:
            with open(message_file, 'r') as f:
                for line in f:
                    try:
                        msg = json.loads(line)
                        all_messages.append(msg)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Warning: Could not read {message_file}: {e}", flush=True)
    
    return all_messages


def analyze_project():
    """Analyze the demo project files."""
    print("=== Python Agent Starting ===", flush=True)
    print(f"Current directory: {os.getcwd()}", flush=True)
    print(f"Timestamp: {datetime.now().isoformat()}", flush=True)
    print("", flush=True)
    
    # Read other agents' messages
    print("Reading other agents' messages...", flush=True)
    messages = read_agent_messages()
    
    if messages:
        print(f"Found {len(messages)} messages from other agents:", flush=True)
        for msg in messages[-5:]:  # Show last 5
            print(f"  [{msg['agent']}] {msg['summary']}", flush=True)
    else:
        print("No messages from other agents yet.", flush=True)
    
    print("", flush=True)
    
    # Check what files exist
    print("Analyzing project files...", flush=True)
    files = list(Path(".").glob("*.*"))
    print(f"Found {len(files)} files: {', '.join(f.name for f in files)}", flush=True)
    print("", flush=True)
    
    # Simulate some work
    print("Analyzing code structure...", flush=True)
    time.sleep(2)
    
    if Path("index.html").exists():
        with open("index.html", 'r') as f:
            content = f.read()
            print(f"index.html is {len(content)} characters long", flush=True)
            
            # Check for various features
            has_counter = "counter" in content.lower()
            has_button = "button" in content.lower()
            has_styles = "<style>" in content
            
            print(f"  - Has counter: {has_counter}", flush=True)
            print(f"  - Has button: {has_button}", flush=True)
            print(f"  - Has styles: {has_styles}", flush=True)
    
    print("", flush=True)
    print("Analysis complete. In a real scenario, I would:", flush=True)
    print("  1. Read the current code", flush=True)
    print("  2. Review what other agents have done", flush=True)
    print("  3. Make complementary improvements", flush=True)
    print("  4. Avoid conflicting changes", flush=True)
    print("", flush=True)
    print("For this demo, I'm making no changes to avoid conflicts.", flush=True)
    print("This allows you to see the orchestrator working without side effects.", flush=True)
    print("", flush=True)
    print("=== Python Agent Complete ===", flush=True)


def main():
    """Main entry point for the plain Python agent."""
    try:
        analyze_project()
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
