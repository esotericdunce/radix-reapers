#!/usr/bin/env python3
"""
Root entrypoint for Neural Reapers Placement Hub
Delegates to radix-talentmatch/main.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET_MAIN = ROOT / "radix-talentmatch" / "main.py"

if __name__ == "__main__":
    if not TARGET_MAIN.exists():
        print(f"Error: Could not find target main at {TARGET_MAIN}")
        sys.exit(1)
    
    # Prepend backend venv python if available and not already in virtualenv
    venv_py = ROOT / "radix-talentmatch" / "backend" / ".venv" / "bin" / "python3"
    if venv_py.exists() and sys.executable != str(venv_py):
        os.execv(str(venv_py), [str(venv_py), str(TARGET_MAIN)] + sys.argv[1:])
    else:
        # Run directly
        import runpy
        sys.argv[0] = str(TARGET_MAIN)
        runpy.run_path(str(TARGET_MAIN), run_name="__main__")
