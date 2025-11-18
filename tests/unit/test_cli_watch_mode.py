#!/usr/bin/env python3
"""Test script to verify watch mode Unicode encoding fix on Windows"""
import sys
import platform
from hyperagent.cli.formatters import format_unicode_progress_bar, format_progress_bar_windows_safe

def test_progress_bar_encoding():
    """Test that progress bars work on Windows"""
    print(f"[*] Testing progress bar encoding on {platform.system()}")
    print(f"[*] Default encoding: {sys.stdout.encoding}")
    print()
    
    # Test Unicode progress bar
    print("[*] Test 1: Unicode progress bar")
    try:
        progress_bar = format_unicode_progress_bar(50, stage="Testing", label="Workflow")
        print(f"    Success: {progress_bar}")
    except UnicodeEncodeError as e:
        print(f"    [-] Unicode encoding error: {e}")
        print(f"    [*] Falling back to Windows-safe version...")
        progress_bar = format_progress_bar_windows_safe(50, stage="Testing", label="Workflow")
        print(f"    [+] Windows-safe: {progress_bar}")
    
    print()
    
    # Test Windows-safe progress bar
    print("[*] Test 2: Windows-safe progress bar")
    try:
        progress_bar = format_progress_bar_windows_safe(75, stage="Deploying", label="Workflow")
        print(f"    Success: {progress_bar}")
    except Exception as e:
        print(f"    [-] Error: {e}")
    
    print()
    
    # Test writing to stdout
    print("[*] Test 3: Writing progress bar to stdout")
    try:
        progress_bar = format_unicode_progress_bar(30, stage="Generating", label="Workflow")
        sys.stdout.write(f"\r[...] {progress_bar}")
        sys.stdout.flush()
        print()  # New line
        print("    [+] Successfully written to stdout")
    except UnicodeEncodeError as e:
        print(f"    [-] Unicode encoding error: {e}")
        print(f"    [*] Using Windows-safe version...")
        progress_bar = format_progress_bar_windows_safe(30, stage="Generating", label="Workflow")
        sys.stdout.write(f"\r[...] {progress_bar}")
        sys.stdout.flush()
        print()  # New line
        print("    [+] Successfully written with ASCII fallback")
    
    print()
    print("[+] All progress bar encoding tests completed")

if __name__ == "__main__":
    test_progress_bar_encoding()

