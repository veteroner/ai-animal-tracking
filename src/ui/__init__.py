# src/ui/__init__.py
"""Web UI module for AI Animal Tracking System."""

__all__ = ['run_dashboard']


def run_dashboard():
    """Run the Streamlit dashboard."""
    import subprocess
    import sys
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "src/ui/dashboard.py",
        "--server.port", "8501",
        "--server.address", "localhost"
    ])
