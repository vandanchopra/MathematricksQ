"""
Run the memory dashboard.
This script runs the memory dashboard, which visualizes the memory graph.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Dashboard")

# Load environment variables
load_dotenv()

def run_dashboard():
    """
    Run the memory dashboard.
    """
    logger.info("Starting memory dashboard")
    
    # Import the dashboard
    from dashboard.enhanced_dashboard import app
    
    # Run the dashboard
    app.run_server(debug=True, host='0.0.0.0', port=8054)

if __name__ == "__main__":
    run_dashboard()
