"""
Dashboard for visualizing UCB scores and backtest results.
This extends the existing dashboard with UCB-specific visualizations.
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_cytoscape as cyto
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import math

# Load environment variables
load_dotenv()

# Neo4j connection parameters
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7688")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "trading123")

# Create a driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Load extra Cytoscape layouts
cyto.load_extra_layouts()

# --- Helper functions ---

def fetch_ideas_with_ucb(exploration_constant=1.0):
    """
    Fetch ideas with their UCB scores.
    
    Args:
        exploration_constant (float): Controls exploration vs. exploitation
        
    Returns:
        pd.DataFrame: DataFrame with idea IDs, descriptions, and UCB scores
    """
    with driver.session() as session:
        # Get all ideas with their UCB scores
        result = session.run(f"""
        MATCH (i:Idea)
        OPTIONAL MATCH (i)-[:TESTED_IN]->(b:Backtest)
        WITH i, count(b) as testCount, 
             CASE WHEN count(b) > 0 THEN i.totalScore / count(b) ELSE 0 END as avgScore
        WITH i, testCount, avgScore, sum(testCount) OVER () as N
        RETURN i.id as id, 
               i.description as description, 
               testCount,
               avgScore,
               CASE 
                 WHEN testCount > 0 
                 THEN avgScore + {exploration_constant} * sqrt(log(CASE WHEN N > 0 THEN N ELSE 1 END) / testCount) 
                 ELSE 999999 
               END as ucb
        ORDER BY ucb DESC
        """)
        
        # Convert to DataFrame
        data = [dict(record) for record in result]
        df = pd.DataFrame(data)
        
        # If DataFrame is empty, return empty DataFrame with columns
        if df.empty:
            return pd.DataFrame(columns=["id", "description", "testCount", "avgScore", "ucb"])
        
        return df

def fetch_backtest_history():
    """
    Fetch backtest history for all ideas.
    
    Returns:
        pd.DataFrame: DataFrame with backtest history
    """
    with driver.session() as session:
        # Get all backtests with their metrics and ideas
        result = session.run("""
        MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)
        RETURN i.id as idea_id, 
               i.description as idea_description,
               b.id as backtest_id,
               b.date as date,
               b.metric_Sharpe as Sharpe,
               b.metric_CAGR as CAGR,
               b.metric_MaxDrawdown as MaxDrawdown,
               b.metric_WinRate as WinRate,
               b.metric_TotalTrades as TotalTrades,
               b.metric_ProfitFactor as ProfitFactor
        ORDER BY b.date DESC
        """)
        
        # Convert to DataFrame
        data = [dict(record) for record in result]
        df = pd.DataFrame(data)
        
        # If DataFrame is empty, return empty DataFrame with columns
        if df.empty:
            return pd.DataFrame(columns=["idea_id", "idea_description", "backtest_id", "date", 
                                        "Sharpe", "CAGR", "MaxDrawdown", "WinRate", "TotalTrades", "ProfitFactor"])
        
        # Compute score
        df["score"] = 0.5 * df["Sharpe"] + 0.3 * df["CAGR"] - 0.2 * df["MaxDrawdown"]
        
        return df

# --- Dashboard layout ---

# UCB Visualization Tab
ucb_tab = html.Div([
    html.H3("UCB Scores", className="mt-4"),
    html.P("Upper Confidence Bound scores for each idea, balancing exploration and exploitation."),
    
    html.Div([
        html.Label("Exploration Constant (c):"),
        dcc.Slider(
            id="exploration-slider",
            min=0.1,
            max=2.0,
            step=0.1,
            value=1.0,
            marks={i/10: str(i/10) for i in range(1, 21)},
            className="mb-4"
        ),
    ], className="mb-4"),
    
    dcc.Graph(id="ucb-bar-chart"),
    
    html.H3("Backtest History", className="mt-4"),
    html.P("History of all backtests, ordered by date."),
    
    html.Div(id="backtest-history-table", className="mt-3")
])

# Main layout
app.layout = html.Div([
    html.H1("UCB Backtester Dashboard", className="text-center my-4"),
    
    dcc.Tabs([
        dcc.Tab(label="UCB Visualization", children=ucb_tab),
        # Add more tabs as needed
    ]),
    
    # Refresh button
    html.Button("Refresh Data", id="refresh-button", className="btn btn-primary mt-3"),
    
    # Interval for auto-refresh
    dcc.Interval(
        id="auto-refresh",
        interval=30 * 1000,  # 30 seconds
        n_intervals=0
    )
], className="container")

# --- Callbacks ---

@app.callback(
    Output("ucb-bar-chart", "figure"),
    [Input("refresh-button", "n_clicks"),
     Input("auto-refresh", "n_intervals"),
     Input("exploration-slider", "value")]
)
def update_ucb_chart(n_clicks, n_intervals, exploration_constant):
    """Update the UCB bar chart."""
    # Fetch ideas with UCB scores
    df = fetch_ideas_with_ucb(exploration_constant)
    
    if df.empty:
        # Return empty figure if no data
        return go.Figure()
    
    # Limit to top 20 ideas for readability
    df = df.head(20)
    
    # Create the figure
    fig = go.Figure()
    
    # Add UCB score bars
    fig.add_trace(go.Bar(
        x=df["id"],
        y=df["ucb"],
        name="UCB Score",
        marker_color="blue",
        hovertemplate="<b>%{x}</b><br>UCB: %{y:.4f}<extra></extra>"
    ))
    
    # Add average score bars
    fig.add_trace(go.Bar(
        x=df["id"],
        y=df["avgScore"],
        name="Average Score",
        marker_color="green",
        hovertemplate="<b>%{x}</b><br>Avg Score: %{y:.4f}<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title="UCB Scores by Idea",
        xaxis_title="Idea ID",
        yaxis_title="Score",
        barmode="group",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="closest"
    )
    
    return fig

@app.callback(
    Output("backtest-history-table", "children"),
    [Input("refresh-button", "n_clicks"),
     Input("auto-refresh", "n_intervals")]
)
def update_backtest_history(n_clicks, n_intervals):
    """Update the backtest history table."""
    # Fetch backtest history
    df = fetch_backtest_history()
    
    if df.empty:
        return html.Div("No backtest history available.")
    
    # Create the table
    table = html.Table([
        html.Thead(
            html.Tr([
                html.Th("Idea"),
                html.Th("Backtest ID"),
                html.Th("Date"),
                html.Th("Sharpe"),
                html.Th("CAGR"),
                html.Th("MaxDD"),
                html.Th("Score")
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(row["idea_description"][:30] + "..."),
                html.Td(row["backtest_id"]),
                html.Td(str(row["date"])),
                html.Td(f"{row['Sharpe']:.2f}"),
                html.Td(f"{row['CAGR']:.2f}"),
                html.Td(f"{row['MaxDrawdown']:.2f}"),
                html.Td(f"{row['score']:.2f}")
            ]) for _, row in df.iterrows()
        ])
    ], className="table table-striped")
    
    return table

if __name__ == "__main__":
    app.run_server(debug=True, port=8053)
