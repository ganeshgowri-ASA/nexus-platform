#!/usr/bin/env python3
"""
Streamlit Application Launcher for NEXUS Document Management System

This script launches the Streamlit frontend application with proper configuration.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Launch Streamlit application."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Change to project root
    os.chdir(project_root)

    # Load environment variables
    env_file = project_root / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    # Configuration
    port = os.getenv("STREAMLIT_SERVER_PORT", "8501")
    backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")

    print("=" * 60)
    print("NEXUS Document Management System")
    print("=" * 60)
    print(f"Streamlit UI: http://localhost:{port}")
    print(f"Backend API: {backend_url}")
    print("=" * 60)
    print()

    # Streamlit command
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "frontend/app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--theme.primaryColor", "#667eea",
        "--theme.backgroundColor", "#ffffff",
        "--theme.secondaryBackgroundColor", "#f8f9fa",
        "--theme.textColor", "#212529",
        "--theme.font", "sans serif",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\nShutting down Streamlit application...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
