# Memory Knowledge Graph Reports

This module provides tools for generating and scheduling reports based on the memory knowledge graph.

## Features

- **Weekly Strategy Reports**: Generate reports of top-performing trading strategies
- **Email Delivery**: Send reports via email to specified recipients
- **Scheduled Execution**: Run reports on a schedule using cron jobs

## Usage

### Running Reports Manually

```bash
cd src/memory/reports
python weekly_report.py
```

### Scheduling Reports

Add a cron job to run the reports automatically:

```bash
# Run weekly report every Monday at 8:00 AM
0 8 * * 1 /path/to/MathematricksQ/src/memory/reports/schedule_reports.sh
```

## Configuration

Configure the reports by editing the `.env` file:

```
# Neo4j connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Email configuration
EMAIL_SENDER=reports@example.com
EMAIL_PASSWORD=your-email-password
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
REPORT_RECIPIENTS=recipient1@example.com,recipient2@example.com
```

## Customization

### Adding New Reports

To create a new report:

1. Create a new Python file in the `reports` directory
2. Implement the report generation logic
3. Add the report to the scheduling script if needed

### Modifying Existing Reports

To modify the weekly strategy report:

1. Edit the `weekly_report.py` file
2. Modify the `generate_top_strategies_report` function to change the report content
3. Modify the `send_email_report` function to change the email format
