#!/usr/bin/env python3
"""
Enhanced Memory Visualizer with filtering and search capabilities
"""

import os
import sys
import logging
import plotly.graph_objects as go
import networkx as nx
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Set
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EnhancedVisualizer")

class EnhancedVisualizer:
    """Enhanced visualizer for the memory knowledge graph with filtering and search."""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """Initialize the enhanced visualizer.

        Args:
            uri: Neo4j URI
            user: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.node_labels = {}  # Store node labels for visualization
        logger.info("EnhancedVisualizer initialized")

    def fetch_all_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all nodes from the database.

        Returns:
            Dictionary mapping node IDs to node properties
        """
        nodes = {}
        with self.driver.session() as session:
            # Get all nodes
            result = session.run("""
            MATCH (n)
            WHERE labels(n)[0] IN ['Idea', 'Backtest', 'Context', 'Scenario']
            RETURN n.id AS id, labels(n)[0] AS label,
                   CASE
                     WHEN labels(n)[0] = 'Idea' THEN n.description
                     WHEN labels(n)[0] = 'Backtest' THEN 'Backtest: ' + n.id
                     WHEN labels(n)[0] = 'Context' THEN n.market + ' ' + n.timeframe
                     WHEN labels(n)[0] = 'Scenario' THEN n.description
                     ELSE n.id
                   END AS description,
                   CASE
                     WHEN labels(n)[0] = 'Backtest' THEN n.metrics
                     ELSE {}
                   END AS metrics
            """)

            for record in result:
                node_id = record["id"]
                node_label = record["label"]
                node_desc = record["description"]
                node_metrics = record["metrics"]

                nodes[node_id] = {
                    "id": node_id,
                    "label": node_label,
                    "description": node_desc,
                    "metrics": node_metrics
                }

                # Store node label for visualization
                self.node_labels[node_id] = node_desc

        return nodes

    def fetch_all_relationships(self) -> List[Dict[str, Any]]:
        """Fetch all relationships from the database.

        Returns:
            List of relationships
        """
        relationships = []
        with self.driver.session() as session:
            # Get all relationships
            result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN a.id AS source, b.id AS target, type(r) AS type
            """)

            for record in result:
                relationships.append({
                    "source": record["source"],
                    "target": record["target"],
                    "type": record["type"]
                })

        return relationships

    def build_graph(self, nodes: Dict[str, Dict[str, Any]], relationships: List[Dict[str, Any]],
                   node_types: Optional[List[str]] = None,
                   relationship_types: Optional[List[str]] = None,
                   search_query: Optional[str] = None) -> nx.DiGraph:
        """Build a NetworkX graph from nodes and relationships with filtering.

        Args:
            nodes: Dictionary mapping node IDs to node properties
            relationships: List of relationships
            node_types: List of node types to include (e.g., ["Idea", "Backtest"])
            relationship_types: List of relationship types to include (e.g., ["TESTED_IN", "EXECUTED_IN"])
            search_query: Search query to filter nodes by description

        Returns:
            NetworkX DiGraph
        """
        G = nx.DiGraph()

        # Filter nodes by type and search query
        filtered_nodes = {}
        for node_id, node in nodes.items():
            # Filter by node type
            if node_types and node["label"] not in node_types:
                continue

            # Filter by search query
            if search_query and search_query.lower() not in node["description"].lower():
                continue

            filtered_nodes[node_id] = node
            G.add_node(node_id, **node)

        # Filter relationships by type and ensure nodes exist
        for rel in relationships:
            source = rel["source"]
            target = rel["target"]
            rel_type = rel["type"]

            # Filter by relationship type
            if relationship_types and rel_type not in relationship_types:
                continue

            # Ensure both nodes exist in the filtered set
            if source in filtered_nodes and target in filtered_nodes:
                G.add_edge(source, target, type=rel_type)

        return G

    def create_visualization(self, G: nx.DiGraph) -> go.Figure:
        """Create a Plotly visualization of the graph.

        Args:
            G: NetworkX DiGraph

        Returns:
            Plotly figure
        """
        # Create node positions using spring layout
        pos = nx.spring_layout(G, seed=42)

        # Create node traces for each node type
        node_traces = {}
        for node_type in ["Idea", "Backtest", "Context", "Scenario"]:
            node_traces[node_type] = go.Scatter(
                x=[],
                y=[],
                text=[],
                mode='markers',
                hoverinfo='text',
                marker=dict(
                    size=15,
                    line=dict(width=2)
                ),
                name=node_type
            )

        # Set colors for each node type
        node_traces["Idea"].marker.color = 'blue'
        node_traces["Backtest"].marker.color = 'green'
        node_traces["Context"].marker.color = 'red'
        node_traces["Scenario"].marker.color = 'purple'

        # Add nodes to traces
        for node_id, node_data in G.nodes(data=True):
            x, y = pos[node_id]
            node_type = node_data["label"]
            node_traces[node_type].x = node_traces[node_type].x + (x,)
            node_traces[node_type].y = node_traces[node_type].y + (y,)

            # Create hover text with metrics if available
            hover_text = node_data["description"]
            if "metrics" in node_data and node_data["metrics"]:
                hover_text += "<br>Metrics:<br>"
                for metric, value in node_data["metrics"].items():
                    hover_text += f"{metric}: {value}<br>"

            node_traces[node_type].text = node_traces[node_type].text + (hover_text,)

        # Create edge traces for each relationship type
        edge_traces = {}
        rel_types = set()
        for source, target, data in G.edges(data=True):
            rel_type = data.get("type", "unknown")
            rel_types.add(rel_type)

            if rel_type not in edge_traces:
                edge_traces[rel_type] = go.Scatter(
                    x=[],
                    y=[],
                    line=dict(width=1),
                    hoverinfo='text',
                    mode='lines',
                    name=rel_type
                )

            x0, y0 = pos[source]
            x1, y1 = pos[target]
            edge_traces[rel_type].x += (x0, x1, None)
            edge_traces[rel_type].y += (y0, y1, None)

        # Set colors for each relationship type
        colors = ['#888', '#f00', '#0f0', '#00f', '#ff0', '#0ff', '#f0f']
        for i, rel_type in enumerate(rel_types):
            edge_traces[rel_type].line.color = colors[i % len(colors)]

        # Create figure
        fig = go.Figure(
            data=list(edge_traces.values()) + list(node_traces.values()),
            layout=go.Layout(
                title='Memory Knowledge Graph',
                titlefont=dict(size=16),
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )

        return fig

    def get_metrics_dataframe(self) -> pd.DataFrame:
        """Get a DataFrame of all metrics for analysis.

        Returns:
            Pandas DataFrame with metrics
        """
        with self.driver.session() as session:
            # Get all backtests with their metrics and related ideas and contexts
            result = session.run("""
            MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
            RETURN i.id AS idea_id, i.description AS idea_description,
                   b.id AS backtest_id, b.metrics AS metrics,
                   c.id AS context_id, c.market AS market, c.timeframe AS timeframe
            """)

            rows = []
            for record in result:
                metrics = record["metrics"]
                if not metrics:
                    continue

                row = {
                    "idea_id": record["idea_id"],
                    "idea_description": record["idea_description"],
                    "backtest_id": record["backtest_id"],
                    "context_id": record["context_id"],
                    "market": record["market"],
                    "timeframe": record["timeframe"]
                }

                # Add metrics to the row
                for metric, value in metrics.items():
                    row[metric] = value

                rows.append(row)

            return pd.DataFrame(rows)

    def create_metrics_visualization(self, df: pd.DataFrame, metric: str = "Sharpe") -> go.Figure:
        """Create a visualization of metrics.

        Args:
            df: DataFrame with metrics
            metric: Metric to visualize

        Returns:
            Plotly figure
        """
        if metric not in df.columns:
            return go.Figure()

        # Group by idea and context, and calculate mean of the metric
        grouped = df.groupby(["idea_id", "idea_description", "context_id"])[metric].mean().reset_index()

        # Sort by metric value
        grouped = grouped.sort_values(by=metric, ascending=False)

        # Create figure
        fig = go.Figure(data=[
            go.Bar(
                x=grouped["idea_id"],
                y=grouped[metric],
                text=grouped["idea_description"],
                hoverinfo="text",
                marker_color="blue"
            )
        ])

        fig.update_layout(
            title=f"{metric} by Strategy",
            xaxis_title="Strategy",
            yaxis_title=metric,
            xaxis_tickangle=-45
        )

        return fig

    def create_context_comparison(self, df: pd.DataFrame, contexts: List[str], metric: str = "Sharpe") -> go.Figure:
        """Create a comparison of strategies across contexts.

        Args:
            df: DataFrame with metrics
            contexts: List of context IDs to compare
            metric: Metric to compare

        Returns:
            Plotly figure
        """
        if metric not in df.columns:
            return go.Figure()

        # Filter to only include the specified contexts
        filtered_df = df[df["context_id"].isin(contexts)]

        # Group by idea and context, and calculate mean of the metric
        grouped = filtered_df.groupby(["idea_id", "idea_description", "context_id"])[metric].mean().reset_index()

        # Pivot to get contexts as columns
        pivot_df = grouped.pivot(index="idea_id", columns="context_id", values=metric)

        # Create figure with one trace per context
        fig = go.Figure()

        for context in contexts:
            if context in pivot_df.columns:
                # Sort by this context's values
                sorted_df = pivot_df.sort_values(by=context, ascending=False)

                fig.add_trace(go.Bar(
                    x=sorted_df.index,
                    y=sorted_df[context],
                    name=context
                ))

        fig.update_layout(
            title=f"{metric} Comparison Across Contexts",
            xaxis_title="Strategy",
            yaxis_title=metric,
            xaxis_tickangle=-45,
            barmode="group"
        )

        return fig

    def create_strategy_evolution(self, df: pd.DataFrame, strategy_prefix: str, metric: str = "Sharpe") -> go.Figure:
        """Create a visualization of strategy evolution over versions.

        Args:
            df: DataFrame with metrics
            strategy_prefix: Prefix of strategy IDs to track evolution
            metric: Metric to visualize

        Returns:
            Plotly figure
        """
        if metric not in df.columns:
            return go.Figure()

        # Filter to only include strategies with the given prefix
        filtered_df = df[df["idea_id"].str.startswith(strategy_prefix)]

        # Extract version numbers from strategy IDs
        import re
        filtered_df["version"] = filtered_df["idea_id"].apply(
            lambda x: re.search(r'v(\d+(?:\.\d+)*)', x).group(1) if re.search(r'v(\d+(?:\.\d+)*)', x) else "1.0"
        )

        # Convert version strings to tuples of integers for proper sorting
        filtered_df["version_tuple"] = filtered_df["version"].apply(
            lambda x: tuple(int(part) for part in x.split("."))
        )

        # Sort by version
        filtered_df = filtered_df.sort_values(by="version_tuple")

        # Group by version and calculate mean of the metric
        grouped = filtered_df.groupby(["version"])[metric].mean().reset_index()

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

    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()

def create_dash_app():
    """Create a Dash app for interactive visualization."""
    # Initialize the visualizer
    visualizer = EnhancedVisualizer(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )

    # Fetch all nodes and relationships
    nodes = visualizer.fetch_all_nodes()
    relationships = visualizer.fetch_all_relationships()

    # Get metrics DataFrame
    metrics_df = visualizer.get_metrics_dataframe()

    # Handle empty DataFrame
    if metrics_df.empty:
        available_metrics = ["Sharpe", "CAGR", "MaxDrawdown", "WinRate"]
        available_contexts = []
    else:
        # Get available metrics
        available_metrics = [col for col in metrics_df.columns if col not in
                            ["idea_id", "idea_description", "backtest_id", "context_id", "market", "timeframe"]]

        # Get available contexts
        if "context_id" in metrics_df.columns:
            available_contexts = metrics_df["context_id"].unique().tolist()
        else:
            available_contexts = []

    # Get available strategy prefixes
    import re
    strategy_prefixes = []
    if not metrics_df.empty and "idea_id" in metrics_df.columns:
        for idea_id in metrics_df["idea_id"].unique():
            match = re.match(r'(idea_[^_v]+)', idea_id)
            if match:
                prefix = match.group(1)
                if prefix not in strategy_prefixes:
                    strategy_prefixes.append(prefix)

    # If no strategy prefixes found, add a default one
    if not strategy_prefixes:
        strategy_prefixes = ["idea_strategy"]

    # Create Dash app
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Memory Knowledge Graph Explorer", className="text-center my-4")
            ])
        ]),

        dbc.Tabs([
            # Tab 1: Graph Visualization
            dbc.Tab(label="Graph Visualization", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Filters", className="mt-3"),
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Node Types"),
                                dbc.Checklist(
                                    id="node-type-filter",
                                    options=[
                                        {"label": "Ideas", "value": "Idea"},
                                        {"label": "Backtests", "value": "Backtest"},
                                        {"label": "Contexts", "value": "Context"},
                                        {"label": "Scenarios", "value": "Scenario"}
                                    ],
                                    value=["Idea", "Backtest", "Context", "Scenario"],
                                    inline=True
                                ),

                                html.H5("Relationship Types", className="mt-3"),
                                dbc.Checklist(
                                    id="relationship-type-filter",
                                    options=[
                                        {"label": "TESTED_IN", "value": "TESTED_IN"},
                                        {"label": "EXECUTED_IN", "value": "EXECUTED_IN"},
                                        {"label": "APPLIES_IN", "value": "APPLIES_IN"},
                                        {"label": "SUBIDEA_OF", "value": "SUBIDEA_OF"}
                                    ],
                                    value=["TESTED_IN", "EXECUTED_IN", "APPLIES_IN", "SUBIDEA_OF"],
                                    inline=True
                                ),

                                html.H5("Search", className="mt-3"),
                                dbc.Input(
                                    id="search-input",
                                    type="text",
                                    placeholder="Search nodes by description..."
                                ),

                                dbc.Button(
                                    "Apply Filters",
                                    id="apply-filters-button",
                                    color="primary",
                                    className="mt-3"
                                )
                            ])
                        ])
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id="graph-visualization", style={"height": "800px"})
                    ])
                ])
            ]),

            # Tab 2: Metrics Analysis
            dbc.Tab(label="Metrics Analysis", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Metrics Visualization", className="mt-3"),
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Select Metric"),
                                dcc.Dropdown(
                                    id="metric-selector",
                                    options=[{"label": metric, "value": metric} for metric in available_metrics],
                                    value=available_metrics[0] if available_metrics else None
                                ),

                                dbc.Button(
                                    "Update Visualization",
                                    id="update-metrics-button",
                                    color="primary",
                                    className="mt-3"
                                )
                            ])
                        ])
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id="metrics-visualization", style={"height": "600px"})
                    ])
                ])
            ]),

            # Tab 3: Context Comparison
            dbc.Tab(label="Context Comparison", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Compare Strategies Across Contexts", className="mt-3"),
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Select Contexts"),
                                dcc.Dropdown(
                                    id="context-selector",
                                    options=[{"label": context, "value": context} for context in available_contexts],
                                    value=available_contexts[:2] if len(available_contexts) >= 2 else available_contexts,
                                    multi=True
                                ),

                                html.H5("Select Metric", className="mt-3"),
                                dcc.Dropdown(
                                    id="context-metric-selector",
                                    options=[{"label": metric, "value": metric} for metric in available_metrics],
                                    value=available_metrics[0] if available_metrics else None
                                ),

                                dbc.Button(
                                    "Update Comparison",
                                    id="update-context-button",
                                    color="primary",
                                    className="mt-3"
                                )
                            ])
                        ])
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id="context-comparison", style={"height": "600px"})
                    ])
                ])
            ]),

            # Tab 4: Strategy Evolution
            dbc.Tab(label="Strategy Evolution", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Track Strategy Evolution", className="mt-3"),
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Select Strategy"),
                                dcc.Dropdown(
                                    id="strategy-selector",
                                    options=[{"label": prefix, "value": prefix} for prefix in strategy_prefixes],
                                    value=strategy_prefixes[0] if strategy_prefixes else None
                                ),

                                html.H5("Select Metric", className="mt-3"),
                                dcc.Dropdown(
                                    id="evolution-metric-selector",
                                    options=[{"label": metric, "value": metric} for metric in available_metrics],
                                    value=available_metrics[0] if available_metrics else None
                                ),

                                dbc.Button(
                                    "Update Evolution",
                                    id="update-evolution-button",
                                    color="primary",
                                    className="mt-3"
                                )
                            ])
                        ])
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id="strategy-evolution", style={"height": "600px"})
                    ])
                ])
            ])
        ])
    ], fluid=True)

    # Callback for graph visualization
    @app.callback(
        Output("graph-visualization", "figure"),
        [Input("apply-filters-button", "n_clicks")],
        [State("node-type-filter", "value"),
         State("relationship-type-filter", "value"),
         State("search-input", "value")]
    )
    def update_graph(n_clicks, node_types, relationship_types, search_query):
        # Build graph with filters
        G = visualizer.build_graph(nodes, relationships, node_types, relationship_types, search_query)

        # Create visualization
        fig = visualizer.create_visualization(G)

        return fig

    # Callback for metrics visualization
    @app.callback(
        Output("metrics-visualization", "figure"),
        [Input("update-metrics-button", "n_clicks")],
        [State("metric-selector", "value")]
    )
    def update_metrics(n_clicks, metric):
        if not metric:
            return go.Figure()

        # Create metrics visualization
        fig = visualizer.create_metrics_visualization(metrics_df, metric)

        return fig

    # Callback for context comparison
    @app.callback(
        Output("context-comparison", "figure"),
        [Input("update-context-button", "n_clicks")],
        [State("context-selector", "value"),
         State("context-metric-selector", "value")]
    )
    def update_context_comparison(n_clicks, contexts, metric):
        if not contexts or not metric:
            return go.Figure()

        # Create context comparison
        fig = visualizer.create_context_comparison(metrics_df, contexts, metric)

        return fig

    # Callback for strategy evolution
    @app.callback(
        Output("strategy-evolution", "figure"),
        [Input("update-evolution-button", "n_clicks")],
        [State("strategy-selector", "value"),
         State("evolution-metric-selector", "value")]
    )
    def update_strategy_evolution(n_clicks, strategy_prefix, metric):
        if not strategy_prefix or not metric:
            return go.Figure()

        # Create strategy evolution visualization
        fig = visualizer.create_strategy_evolution(metrics_df, strategy_prefix, metric)

        return fig

    return app

def main():
    """Run the enhanced visualizer."""
    logger.info("Starting enhanced visualizer...")

    # Create Dash app
    app = create_dash_app()

    # Run the app
    app.run(debug=True, port=8050)

    logger.info("Enhanced visualizer completed successfully!")

if __name__ == "__main__":
    main()
