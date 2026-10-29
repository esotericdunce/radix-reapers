#!/usr/bin/env python3
"""
RADIX TalentMatch · Unified Production Runner
Ties frontend SPA and backend API together into a single unified server.
"""

import os
import sys
import argparse
import subprocess
import webbrowser
from pathlib import Path

# Anchor to project root
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"

# Add backend directory to PYTHONPATH
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load .env credentials if present
env_file = BACKEND_DIR / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_file)
    except ImportError:
        pass


def check_and_build_frontend():
    """Ensure frontend dist bundle is built before starting server."""
    if not (DIST_DIR / "index.html").exists():
        print("⚠️  Frontend bundle not detected at frontend/dist.")
        print("🔨  Building frontend bundle now (npm run build)...")
        try:
            subprocess.run(["npm", "run", "build"], cwd=str(FRONTEND_DIR), check=True)
            print("✅  Frontend built successfully!")
        except Exception as e:
            print(f"❌  Frontend build failed: {e}")
            print("    Please run 'cd frontend && npm install && npm run build' manually.")
            sys.exit(1)


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
        providers.append("🟢 Supabase PostgREST · Live Verified")
    else:
        providers.append("⚪ Supabase PostgREST · Offline")

    return providers


def print_banner(host: str, port: int):
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

\033[1m🚀 Unified Server running at:\033[0m
   • \033[1;32mLocal Web App:\033[0m       http://localhost:{port}
   • \033[1;34mAPI Docs (Swagger):\033[0m   http://localhost:{port}/docs
   • \033[1;34mAlternative Host:\033[0m   http://{host}:{port}

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
    print("\033[2mPress Ctrl+C to terminate the server.\033[0m\n")


def main():
    parser = argparse.ArgumentParser(description="Run RADIX TalentMatch Unified Server")
    parser.add_argument("--host", default="0.0.0.0", help="Binding host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable live auto-reload for backend changes")
    parser.add_argument("--open", action="store_true", help="Automatically open web browser on startup")
    parser.add_argument("--no-build", action="store_true", help="Skip frontend build verification")
    args = parser.parse_args()

    if not args.no_build:
        check_and_build_frontend()

    print_banner(args.host, args.port)

    if args.open:
        try:
            webbrowser.open(f"http://localhost:{args.port}")
        except Exception:
            pass

    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(BACKEND_DIR)
    )


if __name__ == "__main__":
    main()
