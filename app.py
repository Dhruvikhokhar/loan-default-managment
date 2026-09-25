"""
LoanIQ - AI Powered Loan Default Risk Prediction & Management
Entry point for Streamlit Cloud and local deployment.
"""
import runpy
from pathlib import Path

# Run frontend.py in the current namespace
frontend_script = Path(__file__).parent / "frontend.py"
runpy.run_path(str(frontend_script), run_name="__main__")
