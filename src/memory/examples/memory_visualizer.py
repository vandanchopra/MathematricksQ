#!/usr/bin/env python3
"""
Memory Graph Visualizer - Specifically for visualizing the original memory knowledge graph
with Idea-Strategy-Context relationships
"""

import os
import sys
import logging
import plotly.graph_objects as go
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple, Set

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MemoryVisualizer")

class MemoryVisualizer:
    """Visualizer for the memory knowledge graph."""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """Initialize the memory visualizer.

        Args:
            uri: Neo4j URI
            user: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.node_labels = {}  # Store node labels for visualization
        logger.info("MemoryVisualizer initialized")

    def fetch_idea_strategy_context_paths(self, limit: int = 200) -> List[Tuple[str, str]]:
        """Fetch paths from Idea to Strategy to Context.

        Args:
            limit: Maximum number of paths to fetch

        Returns:
            List of edges (node1, node2)
        """
        edges = []
        with self.driver.session() as session:
            # Query for complete Idea-Backtest-Context paths
            result = session.run(
                """
                MATCH p=(i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
                RETURN i.id AS idea, i.description AS idea_desc,
                       b.id AS backtest,
                       c.id AS context, c.market AS market, c.timeframe AS timeframe
                LIMIT $limit
                """,
                limit=limit
            )

            for record in result:
                # Store node labels for visualization
                self.node_labels[record["idea"]] = record["idea_desc"]
                self.node_labels[record["backtest"]] = f"Backtest: {record['backtest']}"
                self.node_labels[record["context"]] = f"{record['market']} {record['timeframe']}"

                # Add edges for the path
                edges.append((record["idea"], record["backtest"]))
                edges.append((record["backtest"], record["context"]))

            # Also fetch Idea-Context direct relationships
            result = session.run(
                """
                MATCH (i:Idea)-[:APPLIES_IN]->(c:Context)
                RETURN i.id AS idea, i.description AS idea_desc,
                       c.id AS context, c.market AS market, c.timeframe AS timeframe
                LIMIT $limit
                """,
                limit=limit
            )

            for record in result:
                # Store node labels for visualization
                self.node_labels[record["idea"]] = record["idea_desc"]
                self.node_labels[record["context"]] = f"{record['market']} {record['timeframe']}"

                # Add edges for the direct relationship
                edges.append((record["idea"], record["context"]))

            # Fetch Scenario-Idea relationships
            result = session.run(
                """
                MATCH (s:Scenario)-[:SUBIDEA_OF]->(i:Idea)
                RETURN s.id AS scenario, s.description AS scenario_desc,
                       i.id AS idea, i.description AS idea_desc
                LIMIT $limit
                """,
                limit=limit
            )

            for record in result:
                # Store node labels for visualization
                self.node_labels[record["scenario"]] = record["scenario_desc"]
                self.node_labels[record["idea"]] = record["idea_desc"]

                # Add edges for the relationship
                edges.append((record["scenario"], record["idea"]))

            # Fetch Scenario-Context relationships
            result = session.run(
                """
                MATCH (s:Scenario)-[:APPLIES_IN]->(c:Context)
                RETURN s.id AS scenario, s.description AS scenario_desc,
                       c.id AS context, c.market AS market, c.timeframe AS timeframe
                LIMIT $limit
                """,
                limit=limit
            )

            for record in result:
                # Store node labels for visualization
                self.node_labels[record["scenario"]] = record["scenario_desc"]
                self.node_labels[record["context"]] = f"{record['market']} {record['timeframe']}"

                # Add edges for the relationship
                edges.append((record["scenario"], record["context"]))

        return edges

    def get_node_types(self) -> Dict[str, str]:
        """Determine node types based on node labels.

        Returns:
            Dictionary mapping node IDs to node types
        """
        node_types = {}
        for node_id, label in self.node_labels.items():
            if "Backtest:" in label:
                node_types[node_id] = "backtest"
            elif "/" in label and any(tf in label for tf in ["1d", "1h", "4h", "15m"]):
                node_types[node_id] = "context"
            elif node_id.startswith("scenario"):
                node_types[node_id] = "scenario"
            else:
                node_types[node_id] = "idea"

        return node_types

    def visualize(self, limit: int = 200, output_file: Optional[str] = None) -> go.Figure:
        """Visualize the memory knowledge graph.

        Args:
            limit: Maximum number of paths to fetch
            output_file: Path to save the visualization HTML file

        Returns:
            Plotly figure object
        """
        # Fetch edges
        edges = self.fetch_idea_strategy_context_paths(limit)

        # Create a directed graph
        G = nx.DiGraph()

        # Add edges to the graph
        for source, target in edges:
            G.add_edge(source, target)

        # Also add all nodes from the database, even if they don't have connections
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
                   END AS description
            """)

            for record in result:
                node_id = record["id"]
                node_label = record["label"]
                node_desc = record["description"]

                # Add node to graph if it doesn't exist
                if node_id not in G.nodes():
                    G.add_node(node_id)

                # Store node label for visualization
                self.node_labels[node_id] = node_desc

        # Get node types
        node_types = {}
        for node in G.nodes():
            # Determine node type based on node ID and label
            if node.startswith("bt") or "Backtest:" in self.node_labels.get(node, ""):
                node_types[node] = "backtest"
            elif node.startswith("scenario"):
                node_types[node] = "scenario"
            elif any(tf in self.node_labels.get(node, "") for tf in ["1d", "1h", "4h", "15m"]) and "/" in self.node_labels.get(node, ""):
                node_types[node] = "context"
            else:
                node_types[node] = "idea"

        # Create node positions using spring layout
        pos = nx.spring_layout(G, seed=42)

        # Create node traces for each node type
        node_traces = {}
        for node_type in ["idea", "backtest", "context", "scenario"]:
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
                name=node_type.capitalize()
            )

        # Set colors for each node type
        node_traces["idea"].marker.color = 'blue'
        node_traces["backtest"].marker.color = 'green'
        node_traces["context"].marker.color = 'red'
        node_traces["scenario"].marker.color = 'purple'

        # Add nodes to traces
        for node in G.nodes():
            x, y = pos[node]
            node_type = node_types.get(node, "idea")  # Default to idea if type not found
            node_traces[node_type].x = node_traces[node_type].x + (x,)
            node_traces[node_type].y = node_traces[node_type].y + (y,)
            node_traces[node_type].text = node_traces[node_type].text + (self.node_labels.get(node, node),)

        # Create edge trace
        edge_trace = go.Scatter(
            x=[],
            y=[],
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        # Add edges to trace
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace.x += (x0, x1, None)
            edge_trace.y += (y0, y1, None)

        # Create figure
        fig = go.Figure(
            data=[edge_trace] + list(node_traces.values()),
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

        # Save to file if specified
        if output_file:
            fig.write_html(output_file)
            logger.info(f"Visualization saved to {output_file}")

        return fig

    def visualize_metrics(self, metric: str = "Sharpe", limit: int = 10, output_file: Optional[str] = None) -> go.Figure:
        """Visualize idea performance metrics.

        Args:
            metric: Metric to visualize (e.g., "Sharpe", "CAGR")
            limit: Maximum number of ideas to show
            output_file: Path to save the visualization HTML file

        Returns:
            Plotly figure object
        """
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)
                RETURN i.id AS idea, i.description AS idea_desc, b.metric_{metric} AS metric_value
                ORDER BY b.metric_{metric} DESC
                LIMIT $limit
                """,
                limit=limit
            )

            ideas = []
            metrics = []

            for record in result:
                ideas.append(record["idea_desc"])
                metrics.append(record["metric_value"])

            if not ideas:
                logger.warning(f"No ideas found with metric: {metric}")
                # Create an empty figure
                fig = go.Figure()
                fig.update_layout(
                    title=f"No ideas found with metric: {metric}",
                    xaxis=dict(title="Ideas"),
                    yaxis=dict(title=f"{metric} Value")
                )

                if output_file:
                    fig.write_html(output_file)
                    logger.info(f"Visualization saved to {output_file}")

                return fig

            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=ideas,
                    y=metrics,
                    marker=dict(color='blue')
                )
            ])

            fig.update_layout(
                title=f"Idea Performance by {metric}",
                xaxis=dict(title="Ideas"),
                yaxis=dict(title=f"{metric} Value")
            )

            if output_file:
                fig.write_html(output_file)
                logger.info(f"Visualization saved to {output_file}")

            return fig

    def visualize_context_performance(self, context_id: str, metric: str = "Sharpe", limit: int = 10, output_file: Optional[str] = None) -> go.Figure:
        """Visualize idea performance in a specific context.

        Args:
            context_id: Context ID to visualize
            metric: Metric to visualize (e.g., "Sharpe", "CAGR")
            limit: Maximum number of ideas to show
            output_file: Path to save the visualization HTML file

        Returns:
            Plotly figure object
        """
        with self.driver.session() as session:
            # Get ideas for the context with their metrics
            result = session.run(
                f"""
                MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context {{id: $context_id}})
                RETURN i.id AS idea, i.description AS idea_desc, b.metric_{metric} AS metric_value
                ORDER BY b.metric_{metric} DESC
                LIMIT $limit
                """,
                context_id=context_id, limit=limit
            )

            ideas = []
            metrics = []

            for record in result:
                ideas.append(record["idea_desc"])
                metrics.append(record["metric_value"])

            # Get context details
            context_result = session.run(
                """
                MATCH (c:Context {id: $context_id})
                RETURN c.market AS market, c.timeframe AS timeframe
                """,
                context_id=context_id
            ).single()

            if not ideas:
                logger.warning(f"No ideas found for context: {context_id} with metric: {metric}")
                # Create an empty figure
                fig = go.Figure()
                fig.update_layout(
                    title=f"No ideas found for context: {context_id}",
                    xaxis=dict(title="Ideas"),
                    yaxis=dict(title=f"{metric} Value")
                )

                if output_file:
                    fig.write_html(output_file)
                    logger.info(f"Visualization saved to {output_file}")

                return fig

            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=ideas,
                    y=metrics,
                    marker=dict(color='red')
                )
            ])

            context_title = f"{context_result['market']} {context_result['timeframe']}"

            fig.update_layout(
                title=f"Idea Performance in {context_title} by {metric}",
                xaxis=dict(title="Ideas"),
                yaxis=dict(title=f"{metric} Value")
            )

            if output_file:
                fig.write_html(output_file)
                logger.info(f"Visualization saved to {output_file}")

            return fig

    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()

def main():
    """Run the memory visualizer."""
    logger.info("Starting memory visualizer...")

    # Initialize the visualizer
    visualizer = MemoryVisualizer(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )

    # Create visualizations
    logger.info("Creating knowledge graph visualization...")
    visualizer.visualize(limit=200, output_file="memory_knowledge_graph.html")

    logger.info("Creating metrics visualization...")
    visualizer.visualize_metrics(metric="Sharpe", limit=10, output_file="memory_metrics.html")

    logger.info("Creating context performance visualization...")
    visualizer.visualize_context_performance(
        context_id="us_equity_daily",
        metric="Sharpe",
        limit=10,
        output_file="memory_context_performance.html"
    )

    # Close the visualizer
    visualizer.close()

    logger.info("Memory visualizer completed successfully!")
    logger.info("Check the following files:")
    logger.info("- memory_knowledge_graph.html")
    logger.info("- memory_metrics.html")
    logger.info("- memory_context_performance.html")

if __name__ == "__main__":
    main()
