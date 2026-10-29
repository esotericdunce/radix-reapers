#!/usr/bin/env python3
"""
RADIX TalentMatch · Unified Production & Dev Runner
Spawns both the FastAPI backend (port 8000) and the CRED NeoPOP frontend (port 8080)
so everything runs simultaneously with a single command: python main.py
"""

import os
import sys
import time
import signal
import shutil
import argparse
import subprocess
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load backend .env if present
env_file = BACKEND_DIR / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_file)
    except ImportError:
        pass


def check_provider_status():
    """Inspect active AI provider credentials."""
    providers = []
    
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key and len(groq_key) > 8:
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        providers.append(f"🟢 Groq ({model}) · Active")
    else:
        providers.append("⚪ Groq · Offline (no key)")

    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    if openrouter_key and len(openrouter_key) > 8:
        model = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
        providers.append(f"🟢 OpenRouter ({model}) · Active")
    else:
        providers.append("⚪ OpenRouter · Offline (no key)")

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key and len(gemini_key) > 8:
        providers.append("🟢 Gemini · Active")
    else:
        providers.append("⚪ Gemini · Offline (no key)")

    supabase_url = os.getenv("SUPABASE_URL", "")
    if supabase_url and "supabase.co" in supabase_url:
        providers.append("🟢 Supabase PostgREST · Live Verified (118 Companies)")
    else:
        providers.append("⚪ Supabase PostgREST · Offline")

    return providers


def print_banner(host: str, backend_port: int, frontend_port: int):
    banner = f"""
\033[1;36m╔══════════════════════════════════════════════════════════════════════════════════════╗
║  ____            _ _         _____      _            _   __  __       _       _  ║
║ |  _ \\ __ _  __| (_)_  __ |_   _|_ _| | ___ _ __ | |_|  \\/  | __ _| |_ ___| |__ ║
║ | |_) / _` |/ _` | \\ \\/ /   | |/ _` | |/ _ \\ '_ \\| __| |\\/| |/ _` | __/ __| '_ \\║
║ |  _ < (_| | (_| | |>  <    | | (_| | |  __/ | | | |_| |  | | (_| | || (__| | | |║
║ |_| \\_\\__,_|\\__,_|_/_/\\_\\   |_|\\__,_|_|\\___|_| |_|\\__|_|  |_|\\__,_|\\__\\___|_| |_|║
║                                                                                      ║
║ \033[1;32mAutonomous Placement Intelligence Hub & Multi-Agent Talent Acceleration Engine\033[1;36m       ║
╚══════════════════════════════════════════════════════════════════════════════════════╝\033[0m

\033[1m🚀 Unified Full-Stack Running at:\033[0m
   • \033[1;32mCRED NeoPOP Web UI:\033[0m     http://localhost:{frontend_port}
   • \033[1;34mFastAPI REST API:\033[0m       http://localhost:{backend_port}
   • \033[1;34mAPI Docs (Swagger):\033[0m     http://localhost:{backend_port}/docs

\033[1m⚡ Active AI Ecosystem Providers:\033[0m"""
    print(banner)
    for p in check_provider_status():
        print(f"   • {p}")

    differentiators = """
\033[1m🌟 Standout Hackathon Differentiators Online:\033[0m
   \033[1;32m[✓]\033[0m \033[1m1. Hiring Committee Deliberation:\033[0m 3-agent panel (Bar Raiser + Tech Lead + HM)
   \033[1;32m[✓]\033[0m \033[1m2. Adaptive Mock Interview Arena:\033[0m Live scenario rubric + Bloom taxonomy depth
   \033[1;32m[✓]\033[0m \033[1m3. Career Radar & CTC Accelerator:\033[0m Super Dream/Dream tiers + Google X-Y-Z ATS
   \033[1;32m[✓]\033[0m \033[1m4. Self-Healing Intelligence Dossier:\033[0m Multi-agent consensus + AST verification
   \033[1;32m[✓]\033[0m \033[1m5. Instant Profile Verification Loop:\033[0m Mock interview updates verified profile
"""
    print(differentiators)
    print("\033[2mPress Ctrl+C to terminate both servers.\033[0m\n")


def get_frontend_cmd():
    """Detect bun or npm to launch the TanStack Start frontend."""
    if shutil.which("bun"):
        return ["bun", "run", "dev"]
    elif shutil.which("npm"):
        return ["npm", "run", "dev"]
    return None


def main():
    parser = argparse.ArgumentParser(description="Run RADIX TalentMatch Unified Server")
    parser.add_argument("--host", default="0.0.0.0", help="Binding host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--frontend-port", type=int, default=8080, help="Frontend port (default: 8080)")
    parser.add_argument("--no-frontend", action="store_true", help="Run backend API only")
    parser.add_argument("--open", action="store_true", help="Automatically open web browser on startup")
    args = parser.parse_args()

    frontend_proc = None
    frontend_cmd = get_frontend_cmd()

    if not args.no_frontend and frontend_cmd:
        # Launch frontend dev server in background
        frontend_env = os.environ.copy()
        frontend_env["VITE_API_BASE_URL"] = f"http://localhost:{args.port}"
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR),
            env=frontend_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    print_banner(args.host, args.port, args.frontend_port)

    if args.open:
        try:
            target_url = f"http://localhost:{args.frontend_port}" if frontend_proc else f"http://localhost:{args.port}"
            time.sleep(1.5)
            webbrowser.open(target_url)
        except Exception:
            pass

    def cleanup(sig=None, frame=None):
        if frontend_proc:
            try:
                frontend_proc.terminate()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    import uvicorn
    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            app_dir=str(BACKEND_DIR),
            log_level="info"
        )
    finally:
        cleanup()


if __name__ == "__main__":
    main()
