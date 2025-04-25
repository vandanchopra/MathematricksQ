#!/usr/bin/env python3
"""
PlotlyVisualizer - A visualization agent for the hybrid memory system.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from datetime import datetime

from neo4j import GraphDatabase
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio

class PlotlyVisualizer:
    """
    Visualization agent for the hybrid memory system using Plotly and NetworkX.
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password"
    ):
        """
        Initialize the PlotlyVisualizer.
        
        Args:
            uri: URI for the Neo4j database
            user: Username for Neo4j
            password: Password for Neo4j
        """
        self.logger = logging.getLogger("PlotlyVisualizer")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.logger.info("PlotlyVisualizer initialized")
    
    def fetch_edges(self, limit: int = 100) -> List[Tuple[str, str]]:
        """
        Pull up to `limit` Idea→Backtest→Context paths.
        
        Args:
            limit: Maximum number of paths to fetch
            
        Returns:
            List of (source, target) edge tuples
        """
        query = """
        MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
        RETURN i.id AS idea, i.description AS idea_desc, 
               b.id AS backtest, 
               c.id AS context, c.market AS market, c.timeframe AS timeframe
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            edges = []
            node_labels = {}
            
            for record in result:
                # Add edges
                edges.append((record["idea"], record["backtest"]))
                edges.append((record["backtest"], record["context"]))
                
                # Store node labels for later use
                node_labels[record["idea"]] = record["idea_desc"]
                node_labels[record["backtest"]] = f"Backtest: {record['backtest']}"
                node_labels[record["context"]] = f"{record['market']} {record['timeframe']}"
            
            self.node_labels = node_labels
            return edges
    
    def fetch_scenario_edges(self, limit: int = 100) -> List[Tuple[str, str]]:
        """
        Pull up to `limit` Scenario→Idea and Scenario→Context paths.
        
        Args:
            limit: Maximum number of paths to fetch
            
        Returns:
            List of (source, target) edge tuples
        """
        query = """
        MATCH (s:Scenario)-[:SUBIDEA_OF]->(i:Idea)
        OPTIONAL MATCH (s)-[:APPLIES_IN]->(c:Context)
        RETURN s.id AS scenario, s.description AS scenario_desc, 
               i.id AS idea, i.description AS idea_desc,
               c.id AS context, c.market AS market, c.timeframe AS timeframe
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            edges = []
            
            for record in result:
                # Add Scenario→Idea edge
                edges.append((record["scenario"], record["idea"]))
                
                # Add Scenario→Context edge if context exists
                if record["context"]:
                    edges.append((record["scenario"], record["context"]))
                
                # Store node labels
                self.node_labels[record["scenario"]] = record["scenario_desc"]
                self.node_labels[record["idea"]] = record["idea_desc"]
                if record["context"]:
                    self.node_labels[record["context"]] = f"{record['market']} {record['timeframe']}"
            
            return edges
    
    def fetch_all_edges(self, limit: int = 100) -> List[Tuple[str, str]]:
        """
        Fetch all edges in the knowledge graph.
        
        Args:
            limit: Maximum number of paths to fetch
            
        Returns:
            List of (source, target) edge tuples
        """
        self.node_labels = {}
        edges = self.fetch_edges(limit)
        scenario_edges = self.fetch_scenario_edges(limit)
        return edges + scenario_edges
    
    def get_node_types(self) -> Dict[str, str]:
        """
        Determine the type of each node based on its ID or label.
        
        Returns:
            Dictionary mapping node IDs to their types
        """
        node_types = {}
        
        for node_id, label in self.node_labels.items():
            if label.startswith("Backtest:"):
                node_types[node_id] = "backtest"
            elif ":" in label and any(tf in label for tf in ["1d", "1h", "4h", "1m", "5m", "15m", "1D", "1H"]):
                node_types[node_id] = "context"
            elif node_id.startswith("scenario"):
                node_types[node_id] = "scenario"
            else:
                node_types[node_id] = "idea"
        
        return node_types
    
    def visualize(self, limit: int = 100, output_file: Optional[str] = None) -> go.Figure:
        """
        Visualize the knowledge graph.
        
        Args:
            limit: Maximum number of paths to fetch
            output_file: Optional file path to save the visualization
            
        Returns:
            Plotly figure object
        """
        # 1) Build NetworkX graph
        G = nx.DiGraph()
        for src, dst in self.fetch_all_edges(limit):
            G.add_edge(src, dst)
        
        if not G.nodes():
            self.logger.warning("No nodes found in the graph")
            return None
        
        # 2) Compute layout (2D positions)
        pos = nx.spring_layout(G, seed=42)
        
        # 3) Determine node types and colors
        node_types = self.get_node_types()
        
        # Define color map for node types
        color_map = {
            "idea": "rgba(31, 119, 180, 0.8)",      # Blue
            "backtest": "rgba(255, 127, 14, 0.8)",  # Orange
            "context": "rgba(44, 160, 44, 0.8)",    # Green
            "scenario": "rgba(214, 39, 40, 0.8)"    # Red
        }
        
        # 4) Create edge traces
        edge_traces = []
        for src, dst in G.edges():
            x0, y0 = pos[src]
            x1, y1 = pos[dst]
            
            # Determine edge color based on source node type
            src_type = node_types.get(src, "idea")
            edge_color = color_map.get(src_type, "rgba(128, 128, 128, 0.5)")
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=1, color=edge_color),
                hoverinfo='none',
                mode='lines',
                showlegend=False
            )
            edge_traces.append(edge_trace)
        
        # 5) Create node traces by type
        node_traces = {}
        for node_type in set(node_types.values()):
            node_traces[node_type] = go.Scatter(
                x=[],
                y=[],
                text=[],
                mode='markers+text',
                textposition="top center",
                hoverinfo='text',
                marker=dict(
                    size=15,
                    color=color_map.get(node_type, "rgba(128, 128, 128, 0.8)"),
                    line=dict(width=1, color='rgba(0, 0, 0, 0.5)')
                ),
                name=node_type.capitalize()
            )
        
        # 6) Add nodes to their respective traces
        for node in G.nodes():
            x, y = pos[node]
            node_type = node_types.get(node, "idea")
            node_label = self.node_labels.get(node, node)
            
            node_traces[node_type].x = list(node_traces[node_type].x) + [x]
            node_traces[node_type].y = list(node_traces[node_type].y) + [y]
            node_traces[node_type].text = list(node_traces[node_type].text) + [node_label]
        
        # 7) Create figure
        fig = go.Figure(
            data=edge_traces + list(node_traces.values()),
            layout=go.Layout(
                title='Knowledge Graph (Idea→Backtest→Context)',
                showlegend=True,
                legend=dict(
                    x=1.05,
                    y=0.5
                ),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                margin=dict(t=50, l=25, r=25, b=25),
                hovermode='closest',
                plot_bgcolor='rgba(255, 255, 255, 1)',
                paper_bgcolor='rgba(255, 255, 255, 1)',
            )
        )
        
        # 8) Save to file if specified
        if output_file:
            pio.write_html(fig, file=output_file, auto_open=False)
            self.logger.info(f"Visualization saved to {output_file}")
        
        return fig
    
    def visualize_metrics(self, metric: str = "Sharpe", limit: int = 100, output_file: Optional[str] = None) -> go.Figure:
        """
        Visualize the knowledge graph with node sizes based on metrics.
        
        Args:
            metric: Metric to use for node sizing (e.g., "Sharpe", "CAGR")
            limit: Maximum number of paths to fetch
            output_file: Optional file path to save the visualization
            
        Returns:
            Plotly figure object
        """
        # 1) Fetch ideas with metrics
        query = f"""
        MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)
        WHERE b.metric_{metric} IS NOT NULL
        RETURN i.id AS idea, i.description AS idea_desc, b.metric_{metric} AS metric_value
        ORDER BY b.metric_{metric} DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            ideas = []
            metric_values = []
            hover_texts = []
            
            for record in result:
                ideas.append(record["idea"])
                metric_values.append(record["metric_value"])
                hover_texts.append(f"{record['idea_desc']}<br>{metric}: {record['metric_value']:.2f}")
        
        if not ideas:
            self.logger.warning(f"No ideas found with metric: {metric}")
            return None
        
        # 2) Create scatter plot
        fig = go.Figure(
            data=[go.Bar(
                x=ideas,
                y=metric_values,
                text=hover_texts,
                hoverinfo='text',
                marker=dict(
                    color='rgba(31, 119, 180, 0.8)',
                    line=dict(width=1, color='rgba(0, 0, 0, 0.5)')
                )
            )],
            layout=go.Layout(
                title=f'Top Ideas by {metric}',
                xaxis=dict(title='Ideas'),
                yaxis=dict(title=metric),
                margin=dict(t=50, l=50, r=25, b=100),
                hovermode='closest',
                plot_bgcolor='rgba(255, 255, 255, 1)',
                paper_bgcolor='rgba(255, 255, 255, 1)',
            )
        )
        
        # 3) Save to file if specified
        if output_file:
            pio.write_html(fig, file=output_file, auto_open=False)
            self.logger.info(f"Visualization saved to {output_file}")
        
        return fig
    
    def visualize_context_performance(self, context_id: str, metric: str = "Sharpe", limit: int = 10, output_file: Optional[str] = None) -> go.Figure:
        """
        Visualize the performance of ideas in a specific context.
        
        Args:
            context_id: ID of the context to visualize
            metric: Metric to use for comparison (e.g., "Sharpe", "CAGR")
            limit: Maximum number of ideas to include
            output_file: Optional file path to save the visualization
            
        Returns:
            Plotly figure object
        """
        # 1) Fetch ideas with metrics for the specified context
        query = f"""
        MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context {{id: $context_id}})
        WHERE b.metric_{metric} IS NOT NULL
        RETURN i.id AS idea, i.description AS idea_desc, b.metric_{metric} AS metric_value
        ORDER BY b.metric_{metric} DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, context_id=context_id, limit=limit)
            ideas = []
            metric_values = []
            hover_texts = []
            
            for record in result:
                ideas.append(record["idea"])
                metric_values.append(record["metric_value"])
                hover_texts.append(f"{record['idea_desc']}<br>{metric}: {record['metric_value']:.2f}")
        
        if not ideas:
            self.logger.warning(f"No ideas found for context: {context_id} with metric: {metric}")
            return None
        
        # 2) Get context details
        context_query = """
        MATCH (c:Context {id: $context_id})
        RETURN c.market AS market, c.timeframe AS timeframe
        """
        
        with self.driver.session() as session:
            context_result = session.run(context_query, context_id=context_id).single()
            if context_result:
                market = context_result["market"]
                timeframe = context_result["timeframe"]
                context_label = f"{market} {timeframe}"
            else:
                context_label = context_id
        
        # 3) Create bar chart
        fig = go.Figure(
            data=[go.Bar(
                x=ideas,
                y=metric_values,
                text=hover_texts,
                hoverinfo='text',
                marker=dict(
                    color='rgba(44, 160, 44, 0.8)',
                    line=dict(width=1, color='rgba(0, 0, 0, 0.5)')
                )
            )],
            layout=go.Layout(
                title=f'Top Ideas by {metric} in {context_label}',
                xaxis=dict(title='Ideas'),
                yaxis=dict(title=metric),
                margin=dict(t=50, l=50, r=25, b=100),
                hovermode='closest',
                plot_bgcolor='rgba(255, 255, 255, 1)',
                paper_bgcolor='rgba(255, 255, 255, 1)',
            )
        )
        
        # 4) Save to file if specified
        if output_file:
            pio.write_html(fig, file=output_file, auto_open=False)
            self.logger.info(f"Visualization saved to {output_file}")
        
        return fig
    
    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()
