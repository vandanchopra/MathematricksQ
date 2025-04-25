"""
Simple dashboard for the memory module.
This dashboard provides a simple interface to visualize the memory graph.
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_cytoscape as cyto
import pandas as pd
import plotly.graph_objects as go
import os
import math
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Neo4j connection parameters
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7688")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "trading123")

# Create a driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# Load extra layouts
cyto.load_extra_layouts()

# Create the app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Define node and edge styles
node_styles = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'text-wrap': 'wrap',
            'text-max-width': 100,
            'font-size': 12,
            'text-valign': 'center',
            'text-halign': 'center',
            'background-color': '#BFD7B5',
            'width': 50,
            'height': 50,
            'text-opacity': 0,  # Hide labels by default
        }
    },
    {
        'selector': 'node:hover',
        'style': {
            'text-opacity': 1,  # Show labels on hover
            'z-index': 9999,
            'text-background-color': 'white',
            'text-background-opacity': 0.8,
            'text-background-shape': 'roundrectangle',
            'text-background-padding': '3px',
            'font-weight': 'bold'
        }
    },
    # Idea nodes: size by score
    {
        'selector': '.idea',
        'style': {
            'background-color': '#3498db',  # Blue
            'shape': 'ellipse',
            'width': 'mapData(score, 0, 2, 20, 80)',
            'height': 'mapData(score, 0, 2, 20, 80)'
        }
    },
    # Backtest nodes: green squares
    {
        'selector': '.backtest',
        'style': {
            'background-color': '#2ecc71',  # Green
            'shape': 'rectangle'
        }
    },
    # Context nodes
    {
        'selector': '.context',
        'style': {
            'background-color': '#e74c3c',  # Red
            'shape': 'diamond'
        }
    },
    # Scenario nodes
    {
        'selector': '.scenario',
        'style': {
            'background-color': '#9b59b6',  # Purple
            'shape': 'hexagon'
        }
    },
    # Edge styles
    {
        'selector': 'edge',
        'style': {
            'label': 'data(label)',
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'line-color': '#ccc',
            'target-arrow-color': '#ccc',
            'width': 2,
            'text-opacity': 0  # Hide edge labels by default
        }
    },
    {
        'selector': 'edge:hover',
        'style': {
            'text-opacity': 1,  # Show edge labels on hover
            'z-index': 9999,
            'width': 4,
            'line-color': '#333',
            'target-arrow-color': '#333',
            'text-background-color': 'white',
            'text-background-opacity': 0.8,
            'text-background-shape': 'roundrectangle',
            'text-background-padding': '3px'
        }
    },
    {
        'selector': '.edge-tested',
        'style': {
            'line-color': '#3498db',
            'target-arrow-color': '#3498db',
        }
    },
    {
        'selector': '.edge-executed',
        'style': {
            'line-color': '#2ecc71',
            'target-arrow-color': '#2ecc71',
        }
    },
    {
        'selector': '.edge-applies',
        'style': {
            'line-color': '#e74c3c',
            'target-arrow-color': '#e74c3c',
        }
    },
    {
        'selector': '.edge-subidea',
        'style': {
            'line-color': '#9b59b6',
            'target-arrow-color': '#9b59b6',
        }
    },
    {
        'selector': '.highest-ucb',
        'style': {
            'border-color': '#FF0000',
            'border-width': 3,
            'border-style': 'dashed'
        }
    }
]

# Helper functions
def fetch_ideas():
    """Returns a list of available ideas from the database."""
    q = """
    MATCH (i:Idea)
    OPTIONAL MATCH (i)-[:TESTED_IN]->(b:Backtest)
    WITH i, count(b) as testCount
    RETURN i.id AS id, i.description AS description, testCount
    ORDER BY testCount DESC, i.id
    LIMIT 100
    """
    with driver.session() as session:
        result = session.run(q)
        ideas = [{"label": f"{record['description'][:50]}... ({record['testCount']} tests) ({record['id']})",
                 "value": record["id"]} for record in result]
        return [{"label": "All Ideas", "value": ""}] + ideas

def fetch_contexts():
    """Returns a list of available contexts from the database."""
    q = """
    MATCH (c:Context)
    OPTIONAL MATCH (b:Backtest)-[:EXECUTED_IN]->(c)
    WITH c, count(b) as backtestCount
    RETURN c.id as id, c.market as market, c.timeframe as timeframe, backtestCount
    ORDER BY backtestCount DESC, c.market, c.timeframe
    """
    with driver.session() as session:
        result = session.run(q)
        contexts = [{"label": f"{record['market']} {record['timeframe']} ({record['backtestCount']} backtests)",
                    "value": record["id"]} for record in result]
        return [{"label": "All Contexts", "value": ""}] + contexts

def fetch_graph_data(idea_id=None, context_id=None):
    """Fetch graph data from Neo4j."""
    elements = []

    with driver.session() as session:
        # Build the query based on filters
        where_clauses = []
        params = {}

        if idea_id:
            where_clauses.append("i.id = $idea_id")
            params["idea_id"] = idea_id

        if context_id:
            where_clauses.append("c.id = $context_id")
            params["context_id"] = context_id

        where = ""
        if where_clauses:
            where = "WHERE " + " AND ".join(where_clauses)

        # Query for Idea -> Backtest -> Context pattern
        q = f"""
        MATCH (i:Idea)-[r1:TESTED_IN]->(b:Backtest)-[r2:EXECUTED_IN]->(c:Context)
        {where}
        RETURN i, r1, b, r2, c
        LIMIT 100
        """

        result = session.run(q, params)

        # Process the results
        nodes = {}

        for record in result:
            i, b, c = record["i"], record["b"], record["c"]

            # Add Idea node
            if i.id not in nodes:
                nodes[i.id] = True
                elements.append({
                    "data": {
                        "id": i.id,
                        "label": i.get("description", "")[:50] + "...",
                        "type": "Idea"
                    },
                    "classes": "idea"
                })

            # Add Backtest node
            if b.id not in nodes:
                nodes[b.id] = True
                elements.append({
                    "data": {
                        "id": b.id,
                        "label": f"BT:{b.get('id', '')}",
                        "type": "Backtest"
                    },
                    "classes": "backtest"
                })

            # Add Context node
            if c.id not in nodes:
                nodes[c.id] = True
                elements.append({
                    "data": {
                        "id": c.id,
                        "label": f"{c.get('market', '')} {c.get('timeframe', '')}",
                        "type": "Context"
                    },
                    "classes": "context"
                })

            # Add TESTED_IN relationship
            elements.append({
                "data": {
                    "source": i.id,
                    "target": b.id,
                    "label": "TESTED_IN"
                },
                "classes": "edge-tested"
            })

            # Add EXECUTED_IN relationship
            elements.append({
                "data": {
                    "source": b.id,
                    "target": c.id,
                    "label": "EXECUTED_IN"
                },
                "classes": "edge-executed"
            })

        # Also get Scenario relationships
        scenario_q = """
        MATCH (i:Idea)-[r:SUBIDEA_OF]->(s:Scenario)
        RETURN i, r, s
        LIMIT 20
        """

        scenario_result = session.run(scenario_q)
        for record in scenario_result:
            i, s = record["i"], record["s"]

            # Add Idea node if not already added
            if i.id not in nodes:
                nodes[i.id] = True
                elements.append({
                    "data": {
                        "id": i.id,
                        "label": i.get("description", "")[:50] + "...",
                        "type": "Idea"
                    },
                    "classes": "idea"
                })

            # Add Scenario node
            if s.id not in nodes:
                nodes[s.id] = True
                elements.append({
                    "data": {
                        "id": s.id,
                        "label": s.get("description", "")[:50] + "...",
                        "type": "Scenario"
                    },
                    "classes": "scenario"
                })

            # Add SUBIDEA_OF relationship
            elements.append({
                "data": {
                    "source": i.id,
                    "target": s.id,
                    "label": "SUBIDEA_OF"
                },
                "classes": "edge-subidea"
            })

    return elements

def fetch_ideas_with_ucb(exploration_constant=1.0):
    """Fetch ideas with their UCB scores."""
    with driver.session() as session:
        # Get all ideas with their test counts and average scores
        result = session.run("""
        MATCH (i:Idea)
        OPTIONAL MATCH (i)-[:TESTED_IN]->(b:Backtest)
        WITH i, count(b) as testCount,
             CASE WHEN count(b) > 0 THEN i.totalScore / count(b) ELSE 0 END as avgScore
        RETURN i.id as id,
               i.description as description,
               testCount,
               avgScore
        ORDER BY avgScore DESC
        """)

        # Get total test count
        total_result = session.run("""
        MATCH (i:Idea)
        RETURN sum(i.testCount) as totalTests
        """)
        total_tests = total_result.single()["totalTests"]
        if total_tests is None or total_tests == 0:
            total_tests = 1

        # Convert to DataFrame
        data = []
        for record in result:
            idea_id = record["id"]
            description = record["description"]
            test_count = record["testCount"]
            avg_score = record["avgScore"]

            # Calculate UCB score
            if test_count > 0:
                ucb = avg_score + exploration_constant * math.sqrt(math.log(total_tests) / test_count)
            else:
                ucb = 999999  # High value for untested ideas

            data.append({
                "id": idea_id,
                "description": description,
                "testCount": test_count,
                "avgScore": avg_score,
                "ucb": ucb
            })

        df = pd.DataFrame(data)

        # Sort by UCB score
        if not df.empty:
            df = df.sort_values(by="ucb", ascending=False)

        return df

# App layout
app.layout = html.Div([
    html.H1("Memory Graph Explorer", className="text-center my-4"),

    html.Div([
        html.Div([
            html.Label("Filter by Idea:"),
            dcc.Dropdown(
                id="filter-idea",
                options=fetch_ideas(),
                value="",
                placeholder="All Ideas"
            ),
        ], className="col-md-6 mb-3"),

        html.Div([
            html.Label("Filter by Context:"),
            dcc.Dropdown(
                id="filter-context",
                options=fetch_contexts(),
                value="",
                placeholder="All Contexts"
            ),
        ], className="col-md-6 mb-3"),
    ], className="row mb-3"),

    html.Button("Refresh Graph", id="refresh-button", className="btn btn-primary mb-3"),

    html.Div([
        cyto.Cytoscape(
            id="cytoscape-graph",
            layout={"name": "cose", "animate": True, "fit": True},
            style={"width": "100%", "height": "600px", "border": "1px solid #ddd", "borderRadius": "5px"},
            elements=[],
            stylesheet=node_styles
        )
    ], className="mb-4"),

    html.Div([
        html.Div(id="node-info", className="card p-3 mt-3")
    ])
], className="container-fluid")

# Callbacks
@app.callback(
    Output("cytoscape-graph", "elements"),
    [Input("refresh-button", "n_clicks")],
    [State("filter-idea", "value"),
     State("filter-context", "value")]
)
def update_graph(n_clicks, idea_id, context_id):
    """Update the graph based on filters."""
    print(f"Refresh button clicked, n_clicks: {n_clicks}")
    print(f"Refreshing graph with idea: {idea_id}, context: {context_id}")

    # Fetch graph data
    elements = fetch_graph_data(idea_id, context_id)

    # Get the idea with the highest UCB score
    df = fetch_ideas_with_ucb(1.0)  # Use default exploration constant
    if not df.empty:
        highest_ucb_id = df.iloc[0]['id']

        # Add the highest-ucb class to the node with the highest UCB score
        for element in elements:
            if element.get('data', {}).get('id') == highest_ucb_id and element.get('data', {}).get('type') == 'Idea':
                if 'classes' in element:
                    element['classes'] += ' highest-ucb'
                else:
                    element['classes'] = 'idea highest-ucb'

    print(f"Returned {len(elements)} elements")
    return elements

@app.callback(
    Output("node-info", "children"),
    Input("cytoscape-graph", "tapNodeData")
)
def display_node_info(node_data):
    """Display information about the selected node."""
    if not node_data:
        return html.Div("Click on a node to see details")

    # Extract data from the node
    node_type = node_data.get("type")
    node_label = node_data.get("label")

    # Get more information from the database
    with driver.session() as session:
        if node_type == "Idea":
            result = session.run("""
            MATCH (i:Idea {id: $id})
            RETURN i.description as description, i.testCount as testCount, i.totalScore as totalScore
            """, id=node_data.get("id"))
            record = result.single()
            if record:
                return html.Div([
                    html.H4(f"Idea: {node_label}", className="mt-3"),
                    html.Hr(),
                    html.P(f"Description: {record['description']}"),
                    html.P(f"Test Count: {record['testCount']}"),
                    html.P(f"Total Score: {record['totalScore']}")
                ], className="card p-3")

        elif node_type == "Backtest":
            result = session.run("""
            MATCH (b:Backtest {id: $id})
            RETURN b.metric_Sharpe as Sharpe, b.metric_CAGR as CAGR, b.metric_MaxDrawdown as MaxDD,
                   b.metric_WinRate as WinRate, b.metric_TotalTrades as TotalTrades, b.date as date
            """, id=node_data.get("id"))
            record = result.single()
            if record:
                return html.Div([
                    html.H4(f"Backtest: {node_label}", className="mt-3"),
                    html.Hr(),
                    html.P(f"Sharpe: {record['Sharpe']}"),
                    html.P(f"CAGR: {record['CAGR']}"),
                    html.P(f"Max Drawdown: {record['MaxDD']}"),
                    html.P(f"Win Rate: {record['WinRate']}"),
                    html.P(f"Total Trades: {record['TotalTrades']}"),
                    html.P(f"Date: {record['date']}")
                ], className="card p-3")

        elif node_type == "Context":
            result = session.run("""
            MATCH (c:Context {id: $id})
            RETURN c.market as market, c.timeframe as timeframe
            """, id=node_data.get("id"))
            record = result.single()
            if record:
                return html.Div([
                    html.H4(f"Context: {node_label}", className="mt-3"),
                    html.Hr(),
                    html.P(f"Market: {record['market']}"),
                    html.P(f"Timeframe: {record['timeframe']}")
                ], className="card p-3")

        elif node_type == "Scenario":
            result = session.run("""
            MATCH (s:Scenario {id: $id})
            RETURN s.description as description
            """, id=node_data.get("id"))
            record = result.single()
            if record:
                return html.Div([
                    html.H4(f"Scenario: {node_label}", className="mt-3"),
                    html.Hr(),
                    html.P(f"Description: {record['description']}")
                ], className="card p-3")

    return html.Div("No additional information available")

if __name__ == "__main__":
    app.run(debug=True, port=8055)
