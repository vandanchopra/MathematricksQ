#!/usr/bin/env python3
"""
Script to generate and email weekly reports of top-performing strategies
"""

import os
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Connect to Neo4j
driver = GraphDatabase.driver(
    os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
    auth=(
        os.environ.get("NEO4J_USER", "neo4j"),
        os.environ.get("NEO4J_PASSWORD", "password")
    )
)

def generate_top_strategies_report():
    """Generate a report of top-performing strategies."""
    with driver.session() as session:
        # Query for top strategies by Sharpe ratio
        result = session.run("""
        MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
        RETURN i.id AS strategy, i.description AS description,
               b.metric_Sharpe AS Sharpe, b.metric_CAGR AS CAGR,
               b.metric_MaxDrawdown AS MaxDrawdown, b.metric_WinRate AS WinRate,
               c.market + ' ' + c.timeframe AS Context
        ORDER BY b.metric_Sharpe DESC
        LIMIT 10
        """)
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(record) for record in result])
        
        if df.empty:
            print("No data found for report")
            return None
        
        # Create figure
        fig = go.Figure(data=[
            go.Bar(
                x=df["strategy"],
                y=df["Sharpe"],
                text=df["Sharpe"].round(2),
                textposition="auto"
            )
        ])
        
        fig.update_layout(
            title="Top 10 Strategies by Sharpe Ratio",
            xaxis_title="Strategy",
            yaxis_title="Sharpe Ratio",
            xaxis_tickangle=-45
        )
        
        # Save figure
        report_dir = os.path.join(os.path.dirname(__file__), "../../reports")
        os.makedirs(report_dir, exist_ok=True)
        
        fig_path = os.path.join(report_dir, "top_strategies.png")
        fig.write_image(fig_path)
        
        # Create HTML table
        html_table = df.to_html(index=False)
        
        return {
            "figure_path": fig_path,
            "html_table": html_table,
            "data": df
        }

def send_email_report(report_data, recipients):
    """Send the report via email."""
    if not report_data:
        print("No report data to send")
        return
    
    # Email configuration
    sender = os.environ.get("EMAIL_SENDER", "reports@example.com")
    password = os.environ.get("EMAIL_PASSWORD", "")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    
    # Create message
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"Weekly Trading Strategy Report - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Email body
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h1 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Weekly Trading Strategy Report</h1>
        <p>Here are the top-performing strategies for this week:</p>
        
        {report_data["html_table"]}
        
        <p>Please see the attached chart for a visual representation.</p>
        
        <p>This report was automatically generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, "html"))
    
    # Attach figure
    with open(report_data["figure_path"], "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="png")
        attachment.add_header("Content-Disposition", "attachment", filename="top_strategies.png")
        msg.attach(attachment)
    
    # Send email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        if password:  # Only login if password is provided
            server.login(sender, password)
        
        server.sendmail(sender, recipients, msg.as_string())
        server.close()
        print(f"Email sent successfully to {', '.join(recipients)}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def main():
    """Generate and send the weekly report."""
    # Generate report
    report_data = generate_top_strategies_report()
    
    if report_data:
        # Get recipients from environment variable
        recipients_str = os.environ.get("REPORT_RECIPIENTS", "")
        if recipients_str:
            recipients = [email.strip() for email in recipients_str.split(",")]
            send_email_report(report_data, recipients)
        else:
            print("No recipients specified. Set REPORT_RECIPIENTS environment variable.")
    
    # Close the Neo4j driver
    driver.close()

if __name__ == "__main__":
    main()
