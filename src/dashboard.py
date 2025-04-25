# src/dashboard.py

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_cytoscape as cyto
import pandas as pd
import plotly.graph_objects as go
import requests
import json
import re
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'])

# Neo4j driver (point at your memory KG)
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
patann_url = os.getenv("PATANN_URL", "http://localhost:9200")

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# --- Helper: fetch nodes/edges from Neo4j ---
def fetch_graph(nodes=None, rels=None):
    """
    Returns cytoscape-style elements filtered by node label & rel type.
    nodes = ["Idea","Backtest","Context","Scenario"] or None for all
    rels  = ["TESTED_IN","EXECUTED_IN",…] or None for all
    """
    node_filter = ""
    if nodes:
        lbls = " or ".join(f"labels(n)[0] = '{lbl}'" for lbl in nodes)
        node_filter = f"WHERE {lbls}"
    q = f"""
    MATCH (n)-[r]->(m)
    {node_filter}
    RETURN n, type(r) AS rel, m
    LIMIT 500
    """
    elements = []
    with driver.session() as sess:
        for rec in sess.run(q):
            n, rel, m = rec["n"], rec["rel"], rec["m"]
            for node in (n, m):
                nid = node.id
                if not any(el.get("data",{}).get("id")==str(nid) for el in elements):
                    elements.append({
                        "data": {
                            "id": str(nid),
                            "label": node.get("description")
                                or node.get("market", "") + " " + node.get("timeframe",""),
                            "type": list(node.labels)[0]
                        }
                    })
            elements.append({
                "data": {
                    "source": str(n.id),
                    "target": str(m.id),
                    "label": rel
                }
            })
    return elements

# --- Helper: fetch metrics table for bar charts ---
def fetch_metrics(context=None, metric="Sharpe"):
    """
    Returns a DataFrame of Idea descriptions vs metric value,
    optionally filtered to a single Context node.
    """
    q = """
    MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
    RETURN i.description AS Idea,
           b.metric_Sharpe AS Sharpe,
           b.metric_CAGR AS CAGR,
           b.metric_MaxDrawdown AS MaxDrawdown,
           b.metric_WinRate AS WinRate,
           b.metric_TotalTrades AS TotalTrades,
           b.metric_ProfitFactor AS ProfitFactor,
           c.market + ' ' + c.timeframe AS Context
    """
    df = pd.DataFrame([dict(rec) for rec in driver.session().run(q)])
    if context:
        df = df[df["Context"] == context]
    return df

# --- PatANN Integration ---
def query_patann(query_text, limit=5):
    """Query the PatANN vector database for similar nodes."""
    # Use the PatANN URL from environment variables
    url = f"{patann_url}/search"

    payload = {
        "query": query_text,
        "limit": limit
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"PatANN query failed with status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# --- Search Tab Content ---
search_controls = html.Div([
    html.H4("Search Memory Graph", className="mt-3"),
    html.Div([
        dcc.Input(
            id="search-input",
            type="text",
            placeholder="Search by description...",
            style={"width": "70%"}
        ),
        html.Button("Search", id="search-button", className="ml-2 btn btn-primary")
    ], className="d-flex mb-3"),

    # Filters
    html.Div([
        html.Div([
            html.Label("Node Type:"),
            dcc.Dropdown(
                id="search-node-type",
                options=[
                    {"label": "Idea", "value": "Idea"},
                    {"label": "Backtest", "value": "Backtest"},
                    {"label": "Context", "value": "Context"},
                    {"label": "Scenario", "value": "Scenario"}
                ],
                value=None,
                placeholder="All Types"
            )
        ], className="col-md-4"),

        html.Div([
            html.Label("Metric:"),
            dcc.Dropdown(
                id="metric-type",
                options=[
                    {"label": "Sharpe", "value": "Sharpe"},
                    {"label": "CAGR", "value": "CAGR"},
                    {"label": "MaxDrawdown", "value": "MaxDrawdown"},
                    {"label": "WinRate", "value": "WinRate"},
                    {"label": "ProfitFactor", "value": "ProfitFactor"}
                ],
                value="Sharpe",
                placeholder="Select Metric"
            )
        ], className="col-md-4"),

        html.Div([
            html.Label("Metric Range:"),
            html.Div([
                dcc.Input(
                    id="metric-min",
                    type="number",
                    placeholder="Min",
                    className="form-control",
                    style={"width": "45%"}
                ),
                dcc.Input(
                    id="metric-max",
                    type="number",
                    placeholder="Max",
                    className="form-control",
                    style={"width": "45%", "marginLeft": "10%"}
                )
            ], className="d-flex")
        ], className="col-md-4")
    ], className="row mb-3")
])

search_results = html.Div([
    dash_table.DataTable(
        id="search-results-table",
        columns=[
            {"name": "ID", "id": "id"},
            {"name": "Type", "id": "type"},
            {"name": "Description", "id": "description"},
            {"name": "Metrics", "id": "metrics"}
        ],
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "10px"
        },
        style_header={
            "backgroundColor": "rgb(230, 230, 230)",
            "fontWeight": "bold"
        },
        page_size=10,
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "rgb(248, 248, 248)"
            }
        ]
    ),

    # Detail view for selected node
    html.Div(id="node-detail-view", className="mt-4")
])

# --- Similarity Search Tab Content ---
similarity_controls = html.Div([
    html.H4("Similarity Search", className="mt-3"),
    html.Div([
        dcc.Textarea(
            id="similarity-query",
            placeholder="Describe the trading strategy or idea you're looking for...",
            style={"width": "100%", "height": 100},
            className="form-control"
        ),
        html.Button("Find Similar", id="similarity-search-button", className="mt-2 btn btn-primary")
    ])
])

similarity_results = html.Div(id="similarity-results", className="mt-4")

# --- Layout with Tabs ---
app.layout = html.Div([
    html.H1("Memory Knowledge Graph Explorer", className="text-center my-4"),
    dcc.Tabs(id="tabs", value="tab-graph", children=[
        dcc.Tab(label="Graph Visualization", value="tab-graph"),
        dcc.Tab(label="Metrics Analysis", value="tab-metrics"),
        dcc.Tab(label="Context Comparison", value="tab-compare"),
        dcc.Tab(label="Strategy Evolution", value="tab-evolution"),
        dcc.Tab(label="Search", value="tab-search"),
        dcc.Tab(label="Similarity Search", value="tab-similarity"),
    ]),
    html.Div(id="tab-content", className="container-fluid mt-3")
], className="container-fluid")

# --- Graph Tab Content ---
graph_controls = html.Div([
    html.Label("Show node types:"),
    dcc.Checklist(
        id="filter-node-types",
        options=[{"label":lbl,"value":lbl} for lbl in ["Idea","Backtest","Context","Scenario"]],
        value=["Idea","Backtest","Context","Scenario"],
        inline=True
    ),
    html.Label("Show rel types:"),
    dcc.Checklist(
        id="filter-rel-types",
        options=[{"label":r,"value":r} for r in ["TESTED_IN","EXECUTED_IN","APPLIES_IN","SUBIDEA_OF"]],
        value=["TESTED_IN","EXECUTED_IN","APPLIES_IN","SUBIDEA_OF"],
        inline=True
    ),
    html.Button("Refresh Graph", id="refresh-graph")
])

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
        }
    },
    {
        'selector': 'node[type="Idea"]',
        'style': {
            'background-color': '#3498db',  # Blue
            'shape': 'ellipse'
        }
    },
    {
        'selector': 'node[type="Backtest"]',
        'style': {
            'background-color': '#2ecc71',  # Green
            'shape': 'rectangle'
        }
    },
    {
        'selector': 'node[type="Context"]',
        'style': {
            'background-color': '#e74c3c',  # Red
            'shape': 'diamond'
        }
    },
    {
        'selector': 'node[type="Scenario"]',
        'style': {
            'background-color': '#9b59b6',  # Purple
            'shape': 'hexagon'
        }
    },
    {
        'selector': 'edge',
        'style': {
            'label': 'data(label)',
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'line-color': '#ccc',
            'target-arrow-color': '#ccc',
            'width': 2
        }
    },
    {
        'selector': 'edge[label="TESTED_IN"]',
        'style': {
            'line-color': '#3498db',
            'target-arrow-color': '#3498db',
        }
    },
    {
        'selector': 'edge[label="EXECUTED_IN"]',
        'style': {
            'line-color': '#2ecc71',
            'target-arrow-color': '#2ecc71',
        }
    },
    {
        'selector': 'edge[label="APPLIES_IN"]',
        'style': {
            'line-color': '#e74c3c',
            'target-arrow-color': '#e74c3c',
        }
    },
    {
        'selector': 'edge[label="SUBIDEA_OF"]',
        'style': {
            'line-color': '#9b59b6',
            'target-arrow-color': '#9b59b6',
        }
    }
]

graph_area = cyto.Cytoscape(
    id="cytoscape-graph",
    layout={"name":"cose", "animate": True, "fit": True},
    style={"width":"100%","height":"600px"},
    elements=[],
    stylesheet=node_styles
)

# --- Metrics Tab Content ---
metrics_controls = html.Div([
    html.Label("Select Metric:"),
    dcc.Dropdown(
        id="select-metric",
        options=[
            {"label":"Sharpe Ratio","value":"Sharpe"},
            {"label":"CAGR","value":"CAGR"},
            {"label":"Max Drawdown","value":"MaxDrawdown"},
            {"label":"Win Rate","value":"WinRate"},
            {"label":"Total Trades","value":"TotalTrades"},
            {"label":"Profit Factor","value":"ProfitFactor"},
        ],
        value="Sharpe"
    ),
    html.Label("Filter Context (optional):"),
    dcc.Dropdown(
        id="select-context",
        options=[],  # we'll populate dynamically
        value=None,
        placeholder="All contexts"
    ),
    html.Button("Show Metrics", id="refresh-metrics")
])
metrics_area = dcc.Graph(id="metrics-bar")

# --- Context Comparison Tab Content ---
context_comparison_controls = html.Div([
    html.Label("Select Contexts to Compare:"),
    dcc.Dropdown(
        id="compare-contexts",
        options=[],  # we'll populate dynamically
        value=[],
        multi=True,
        placeholder="Select contexts to compare"
    ),
    html.Label("Select Metric:", className="mt-3"),
    dcc.Dropdown(
        id="compare-metric",
        options=[
            {"label":"Sharpe Ratio","value":"Sharpe"},
            {"label":"CAGR","value":"CAGR"},
            {"label":"Max Drawdown","value":"MaxDrawdown"},
            {"label":"Win Rate","value":"WinRate"},
            {"label":"Profit Factor","value":"ProfitFactor"},
        ],
        value="Sharpe"
    ),
    html.Button("Compare Contexts", id="refresh-comparison")
])
context_comparison_area = dcc.Graph(id="context-comparison-chart")

# --- Strategy Evolution Tab Content ---
evolution_controls = html.Div([
    html.Label("Select Strategy:"),
    dcc.Dropdown(
        id="select-strategy",
        options=[],  # we'll populate dynamically
        value=None,
        placeholder="Select a strategy"
    ),
    html.Label("Select Metric:", className="mt-3"),
    dcc.Dropdown(
        id="evolution-metric",
        options=[
            {"label":"Sharpe Ratio","value":"Sharpe"},
            {"label":"CAGR","value":"CAGR"},
            {"label":"Max Drawdown","value":"MaxDrawdown"},
            {"label":"Win Rate","value":"WinRate"},
            {"label":"Profit Factor","value":"ProfitFactor"},
        ],
        value="Sharpe"
    ),
    html.Button("Show Evolution", id="refresh-evolution")
])
evolution_area = dcc.Graph(id="evolution-chart")

# --- Search Tab Content ---
search_controls = html.Div([
    html.Label("Search for Nodes:"),
    dcc.Input(
        id="search-input",
        type="text",
        placeholder="Enter search term...",
        style={"width": "100%"}
    ),
    html.Button("Search", id="search-button", className="mt-2")
])
search_results = html.Div(id="search-results")

# --- Callbacks to swap tabs and populate content ---
@app.callback(Output("tab-content","children"),
              Input("tabs","value"))
def render_tab(tab):
    if tab == "tab-graph":
        return html.Div([graph_controls, graph_area])
    elif tab == "tab-metrics":
        return html.Div([metrics_controls, metrics_area])
    elif tab == "tab-compare":
        return html.Div([context_comparison_controls, context_comparison_area])
    elif tab == "tab-evolution":
        return html.Div([evolution_controls, evolution_area])
    elif tab == "tab-search":
        return html.Div([search_controls, search_results])
    elif tab == "tab-similarity":
        return html.Div([similarity_controls, similarity_results])
    # ... you can stub out other tabs similarly ...
    return html.Div(f"Coming soon: {tab}")

# --- Populate Context dropdown ---
@app.callback(
    [Output("select-context","options"),
     Output("compare-contexts","options")],
    Input("tabs","value")
)
def load_contexts(tab):
    if tab in ["tab-metrics", "tab-compare"]:
        df = fetch_metrics()
        context_options = [{"label":c,"value":c} for c in sorted(df["Context"].unique())]
        return context_options, context_options
    return [], []

# --- Refresh Graph ---
@app.callback(
    Output("cytoscape-graph","elements"),
    Input("refresh-graph","n_clicks"),
    State("filter-node-types","value"),
    State("filter-rel-types","value")
)
def update_graph(n, node_types, rel_types):
    return fetch_graph(nodes=node_types, rels=rel_types)

# --- Refresh Metrics Bar Chart ---
@app.callback(
    Output("metrics-bar","figure"),
    Input("refresh-metrics","n_clicks"),
    State("select-metric","value"),
    State("select-context","value")
)
def update_metrics(n, metric, context):
    df = fetch_metrics(context=context)
    if df.empty:
        return go.Figure().update_layout(title="No data available")

    df = df.sort_values(metric, ascending=False).head(10)
    fig = go.Figure(go.Bar(
        x=df["Idea"],
        y=df[metric]
    ))
    fig.update_layout(
        title=f"Idea Performance{' in '+context if context else ''} by {metric}",
        xaxis_tickangle=-45
    )
    return fig

# --- Context Comparison Chart ---
@app.callback(
    Output("context-comparison-chart","figure"),
    Input("refresh-comparison","n_clicks"),
    State("compare-contexts","value"),
    State("compare-metric","value")
)
def update_context_comparison(n, contexts, metric):
    if not contexts or len(contexts) == 0:
        return go.Figure().update_layout(title="Please select at least one context")

    # Create a figure
    fig = go.Figure()

    # For each context, add a trace
    for context in contexts:
        df = fetch_metrics(context=context)
        if not df.empty:
            # Sort by metric value
            df = df.sort_values(metric, ascending=False).head(5)

            # Add a bar trace for this context
            fig.add_trace(go.Bar(
                name=context,
                x=df["Idea"],
                y=df[metric]
            ))

    # Update layout
    fig.update_layout(
        title=f"Comparison of {metric} Across Contexts",
        xaxis_title="Idea",
        yaxis_title=metric,
        barmode='group',
        xaxis_tickangle=-45
    )

    return fig

# --- Helper: fetch strategy versions ---
def fetch_strategy_versions(strategy_prefix=None):
    """
    Returns a DataFrame of strategy versions and their metrics.
    """
    if strategy_prefix is None:
        # Get all strategies
        q = """
        MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)
        RETURN i.id AS strategy_id, i.description AS description
        """
        df = pd.DataFrame([dict(rec) for rec in driver.session().run(q)])
        return df
    else:
        # Get versions of a specific strategy
        q = """
        MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
        WHERE i.id STARTS WITH $prefix
        RETURN i.id AS strategy_id, i.description AS description,
               b.metric_Sharpe AS Sharpe, b.metric_CAGR AS CAGR,
               b.metric_MaxDrawdown AS MaxDrawdown, b.metric_WinRate AS WinRate,
               b.metric_ProfitFactor AS ProfitFactor,
               c.market + ' ' + c.timeframe AS Context
        """
        df = pd.DataFrame([dict(rec) for rec in driver.session().run(q, prefix=strategy_prefix)])
        return df

# --- Populate Strategy dropdown ---
@app.callback(
    Output("select-strategy","options"),
    Input("tabs","value")
)
def load_strategies(tab):
    if tab=="tab-evolution":
        df = fetch_strategy_versions()
        if df.empty:
            return []

        # Extract strategy prefixes (e.g., "idea_strategy1" from "idea_strategy1_v1")
        import re
        prefixes = set()
        for strategy_id in df["strategy_id"]:
            match = re.match(r'(idea_[^_v]+)', strategy_id)
            if match:
                prefixes.add(match.group(1))

        return [{"label":p,"value":p} for p in sorted(prefixes)]
    return []

# --- Strategy Evolution Chart ---
@app.callback(
    Output("evolution-chart","figure"),
    Input("refresh-evolution","n_clicks"),
    State("select-strategy","value"),
    State("evolution-metric","value")
)
def update_strategy_evolution(n, strategy_prefix, metric):
    if not strategy_prefix:
        return go.Figure().update_layout(title="Please select a strategy")

    # Get strategy versions
    df = fetch_strategy_versions(strategy_prefix)
    if df.empty:
        return go.Figure().update_layout(title=f"No data available for {strategy_prefix}")

    # Extract version numbers
    import re
    df["version"] = df["strategy_id"].apply(
        lambda x: re.search(r'v(\d+(?:\.\d+)*)', x).group(1) if re.search(r'v(\d+(?:\.\d+)*)', x) else "1.0"
    )

    # Convert version strings to tuples for proper sorting
    df["version_tuple"] = df["version"].apply(
        lambda x: tuple(int(part) for part in x.split("."))
    )

    # Sort by version
    df = df.sort_values(by="version_tuple")

    # Group by version and calculate mean of the metric
    grouped = df.groupby(["version"])[metric].mean().reset_index()

    # Create figure
    fig = go.Figure(data=[
        go.Scatter(
            x=grouped["version"],
            y=grouped[metric],
            mode="lines+markers",
            marker=dict(size=10),
            line=dict(width=2)
        )
    ])

    fig.update_layout(
        title=f"{metric} Evolution for {strategy_prefix}",
        xaxis_title="Version",
        yaxis_title=metric
    )

    return fig

# --- Search Callback ---
@app.callback(
    Output("search-results-table", "data"),
    [Input("search-button", "n_clicks")],
    [State("search-input", "value"),
     State("search-node-type", "value"),
     State("metric-type", "value"),
     State("metric-min", "value"),
     State("metric-max", "value")]
)
def search_nodes(n_clicks, search_text, node_type, metric_type, metric_min, metric_max):
    if not n_clicks:
        return []

    # Build query based on filters
    query = "MATCH (n)"
    where_clauses = []

    if node_type:
        where_clauses.append(f"labels(n)[0] = '{node_type}'")

    if search_text:
        where_clauses.append(f"n.description CONTAINS '{search_text}'")

    if metric_type and (metric_min is not None or metric_max is not None):
        if node_type == "Backtest" or not node_type:
            metric_path = f"n.metric_{metric_type}"
            if metric_min is not None:
                where_clauses.append(f"{metric_path} >= {metric_min}")
            if metric_max is not None:
                where_clauses.append(f"{metric_path} <= {metric_max}")

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " RETURN n LIMIT 100"

    # Execute query
    results = []
    with driver.session() as session:
        try:
            records = session.run(query)
            for record in records:
                node = record["n"]
                node_type = list(node.labels)[0]

                # Format metrics for display
                metrics_str = ""
                if node_type == "Backtest":
                    metrics = {k.replace("metric_", ""): v for k, v in node.items() if k.startswith("metric_")}
                    metrics_str = ", ".join([f"{k}: {v}" for k, v in metrics.items()])

                results.append({
                    "id": node.get("id", ""),
                    "type": node_type,
                    "description": node.get("description", ""),
                    "metrics": metrics_str
                })
        except Exception as e:
            print(f"Error executing query: {e}")

    return results

# --- Node Detail View Callback ---
@app.callback(
    Output("node-detail-view", "children"),
    [Input("search-results-table", "active_cell")],
    [State("search-results-table", "data")]
)
def show_node_details(active_cell, data):
    if not active_cell or not data:
        return html.Div()

    row = active_cell["row"]
    node_data = data[row]
    node_id = node_data["id"]
    node_type = node_data["type"]

    # Query for detailed node information
    query = f"""
    MATCH (n:{node_type} {{id: $node_id}})
    OPTIONAL MATCH (n)-[r]->(m)
    OPTIONAL MATCH (o)-[r2]->(n)
    RETURN n,
           collect(DISTINCT {{type: type(r), target: m.id, target_type: labels(m)[0]}}) as outgoing,
           collect(DISTINCT {{type: type(r2), source: o.id, source_type: labels(o)[0]}}) as incoming
    """

    with driver.session() as session:
        try:
            record = session.run(query, node_id=node_id).single()

            if not record:
                return html.Div("Node details not found")

            node = record["n"]
            outgoing = record["outgoing"]
            incoming = record["incoming"]

            # Create detail view
            details = []

            # Node properties
            details.append(html.H4(f"{node_type}: {node.get('id')}", className="mt-3"))
            details.append(html.P(node.get("description", "")))

            # Node properties table
            property_rows = []
            for key, value in node.items():
                if key not in ["id", "description"]:
                    property_rows.append(html.Tr([
                        html.Td(key),
                        html.Td(str(value))
                    ]))

            if property_rows:
                details.append(html.H5("Properties", className="mt-3"))
                details.append(html.Table([
                    html.Thead(html.Tr([html.Th("Property"), html.Th("Value")])),
                    html.Tbody(property_rows)
                ], className="table table-striped"))

            # Relationships
            if incoming:
                details.append(html.H5("Incoming Relationships", className="mt-3"))
                incoming_rows = []
                for rel in incoming:
                    if rel["source"]:
                        incoming_rows.append(html.Tr([
                            html.Td(rel["type"]),
                            html.Td(f"{rel['source_type']}: {rel['source']}")
                        ]))

                if incoming_rows:
                    details.append(html.Table([
                        html.Thead(html.Tr([html.Th("Relationship"), html.Th("From")])),
                        html.Tbody(incoming_rows)
                    ], className="table table-striped"))

            if outgoing:
                details.append(html.H5("Outgoing Relationships", className="mt-3"))
                outgoing_rows = []
                for rel in outgoing:
                    if rel["target"]:
                        outgoing_rows.append(html.Tr([
                            html.Td(rel["type"]),
                            html.Td(f"{rel['target_type']}: {rel['target']}")
                        ]))

                if outgoing_rows:
                    details.append(html.Table([
                        html.Thead(html.Tr([html.Th("Relationship"), html.Th("To")])),
                        html.Tbody(outgoing_rows)
                    ], className="table table-striped"))

            return html.Div(details, className="card p-3")
        except Exception as e:
            return html.Div(f"Error retrieving node details: {str(e)}")

# --- Similarity Search Callback ---
@app.callback(
    Output("similarity-results", "children"),
    [Input("similarity-search-button", "n_clicks")],
    [State("similarity-query", "value")]
)
def perform_similarity_search(n_clicks, query_text):
    if not n_clicks or not query_text:
        return html.Div()

    # Query PatANN
    try:
        results = query_patann(query_text)

        if "error" in results:
            return html.Div(f"Error: {results['error']}", className="alert alert-danger")

        # Format results
        result_cards = []
        for item in results.get("results", []):
            # Get node details from Neo4j
            node_id = item.get("id")
            similarity = item.get("similarity", 0)

            with driver.session() as session:
                node_record = session.run(
                    "MATCH (n {id: $id}) RETURN n, labels(n)[0] as type",
                    id=node_id
                ).single()

                if node_record:
                    node = node_record["n"]
                    node_type = node_record["type"]

                    # Create metrics section if it's a backtest
                    metrics_section = []
                    if node_type == "Backtest":
                        metrics = {k.replace("metric_", ""): v for k, v in node.items() if k.startswith("metric_")}
                        for k, v in metrics.items():
                            metrics_section.append(html.P(f"{k}: {v}", className="mb-1"))

                    # Create card for this result
                    card = html.Div([
                        html.H5(f"{node_type}: {node.get('id')}"),
                        html.P(f"Similarity: {similarity:.2f}", className="text-muted"),
                        html.P(node.get("description", "")),
                        html.Div(metrics_section) if metrics_section else html.Div()
                    ], className="card p-3 mb-3")

                    result_cards.append(card)

        if not result_cards:
            return html.Div("No similar items found", className="alert alert-info")

        return html.Div([
            html.H4("Similar Items", className="mt-3"),
            html.Div(result_cards)
        ])
    except Exception as e:
        return html.Div(f"Error performing similarity search: {str(e)}", className="alert alert-danger")

if __name__ == "__main__":
    app.run(debug=True, port=8051)
