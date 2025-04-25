#!/bin/bash
# Script to run weekly reports

# Change to the project directory
cd "$(dirname "$0")/../../../"

# Activate virtual environment if needed
# source venv/bin/activate

# Run the weekly report script
python src/memory/reports/weekly_report.py

# Log the execution
echo "Weekly report executed at $(date)" >> reports/report_log.txt
