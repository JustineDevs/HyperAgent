#!/usr/bin/env python3
"""Quick script to check workflow status with progress bar"""
import httpx
import json
import sys
import time

def print_progress_bar(progress: int, stage: str = "", width: int = 40):
    """Print Unicode progress bar"""
    filled = int((progress / 100) * width)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    percent = int(progress)
    print(f"\r[...] [{stage:12}] |{bar}| {percent:3}%", end="", flush=True)

workflow_id = sys.argv[1] if len(sys.argv) > 1 else "aef382b1-f36a-40b5-a629-6769541c8543"

try:
    response = httpx.get(f"http://localhost:8000/api/v1/workflows/{workflow_id}", timeout=10.0)
    response.raise_for_status()
    data = response.json()
    
    # Show progress bar if workflow is in progress
    status = data.get("status", "unknown")
    progress = data.get("progress_percentage", 0)
    
    stage_map = {
        "created": "Initializing",
        "generating": "Generating",
        "compiling": "Compiling",
        "auditing": "Auditing",
        "testing": "Testing",
        "deploying": "Deploying",
        "completed": "Completed",
        "failed": "Failed"
    }
    stage = stage_map.get(status, status.title() if status else "Unknown")
    
    if status not in ["completed", "failed"]:
        print_progress_bar(progress, stage)
        print()  # New line
    
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")

