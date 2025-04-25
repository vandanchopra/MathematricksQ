#!/usr/bin/env python3
"""
Complete Mesh Visualizer - Shows the complete quad-partite mesh of Idea-Backtest-Context-Scenario
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
logger = logging.getLogger("CompleteMeshVisualizer")

class CompleteMeshVisualizer:
    """Visualizer for the complete memory knowledge graph mesh."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """Initialize the complete mesh visualizer.
        
        Args:
            uri: Neo4j URI
            user: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.node_labels = {}  # Store node labels for visualization
        logger.info("CompleteMeshVisualizer initialized")
    
    def fetch_complete_mesh(self, limit: int = 200) -> List[Tuple[str, str]]:
        """Fetch the complete mesh of Idea-Backtest-Context-Scenario.
        
        Args:
            limit: Maximum number of paths to fetch
            
        Returns:
            List of edges (node1, node2)
        """
        edges = []
        with self.driver.session() as session:
            # Query for Idea-Backtest-Context paths
            logger.info("Fetching Idea-Backtest-Context paths...")
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
            
            # Fetch Scenario-Idea relationships
            logger.info("Fetching Scenario-Idea relationships...")
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
            logger.info("Fetching Scenario-Context relationships...")
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
            
            # Fetch Idea-Context direct relationships
            logger.info("Fetching Idea-Context direct relationships...")
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
        
        return edges
    
    def fetch_all_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all nodes from the database, including orphans.
        
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
                   END AS description
            """)
            
            for record in result:
                node_id = record["id"]
                node_label = record["label"]
                node_desc = record["description"]
                
                nodes[node_id] = {
                    "label": node_label,
                    "description": node_desc
                }
                
                # Store node label for visualization
                self.node_labels[node_id] = node_desc
        
        return nodes
    
    def get_node_types(self) -> Dict[str, str]:
        """Determine node types based on node labels.
        
        Returns:
            Dictionary mapping node IDs to node types
        """
        node_types = {}
        for node_id, label in self.node_labels.items():
            if "Backtest:" in label:
                node_types[node_id] = "backtest"
            elif "/" in label and any(tf in label for tf in ["1d", "1h", "4h", "1m", "15m"]):
                node_types[node_id] = "context"
            elif node_id.startswith("scenario"):
                node_types[node_id] = "scenario"
            else:
                node_types[node_id] = "idea"
        
        return node_types
    
    def visualize_complete_mesh(self, limit: int = 200, include_orphans: bool = True, output_file: Optional[str] = None) -> go.Figure:
        """Visualize the complete mesh of Idea-Backtest-Context-Scenario.
        
        Args:
            limit: Maximum number of paths to fetch
            include_orphans: Whether to include orphaned nodes (nodes without connections)
            output_file: Path to save the visualization HTML file
            
        Returns:
            Plotly figure object
        """
        # Fetch edges
        logger.info("Fetching edges for the complete mesh...")
        edges = self.fetch_complete_mesh(limit)
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add edges to the graph
        for source, target in edges:
            G.add_edge(source, target)
        
        # Add orphaned nodes if requested
        if include_orphans:
            logger.info("Including orphaned nodes...")
            nodes = self.fetch_all_nodes()
            for node_id, node_props in nodes.items():
                if node_id not in G.nodes():
                    G.add_node(node_id)
        
        # Get node types
        node_types = {}
        for node in G.nodes():
            # Determine node type based on node ID and label
            if node.startswith("bt") or "Backtest:" in self.node_labels.get(node, ""):
                node_types[node] = "backtest"
            elif node.startswith("scenario"):
                node_types[node] = "scenario"
            elif any(tf in self.node_labels.get(node, "") for tf in ["1d", "1h", "4h", "1m", "15m"]) and "/" in self.node_labels.get(node, ""):
                node_types[node] = "context"
            else:
                node_types[node] = "idea"
        
        # Create node positions using spring layout
        logger.info("Creating layout...")
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
        logger.info("Creating figure...")
        fig = go.Figure(
            data=[edge_trace] + list(node_traces.values()),
            layout=go.Layout(
                title='Complete Memory Knowledge Graph Mesh',
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
    
    def visualize_without_orphans(self, limit: int = 200, output_file: Optional[str] = None) -> go.Figure:
        """Visualize the complete mesh without orphaned nodes.
        
        Args:
            limit: Maximum number of paths to fetch
            output_file: Path to save the visualization HTML file
            
        Returns:
            Plotly figure object
        """
        # Fetch edges
        logger.info("Fetching edges for the complete mesh...")
        edges = self.fetch_complete_mesh(limit)
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add edges to the graph
        for source, target in edges:
            G.add_edge(source, target)
        
        # Remove orphaned nodes (nodes with degree 0)
        logger.info("Removing orphaned nodes...")
        orphans = [n for n, d in G.degree() if d == 0]
        G.remove_nodes_from(orphans)
        logger.info(f"Removed {len(orphans)} orphaned nodes")
        
        # Get node types
        node_types = {}
        for node in G.nodes():
            # Determine node type based on node ID and label
            if node.startswith("bt") or "Backtest:" in self.node_labels.get(node, ""):
                node_types[node] = "backtest"
            elif node.startswith("scenario"):
                node_types[node] = "scenario"
            elif any(tf in self.node_labels.get(node, "") for tf in ["1d", "1h", "4h", "1m", "15m"]) and "/" in self.node_labels.get(node, ""):
                node_types[node] = "context"
            else:
                node_types[node] = "idea"
        
        # Create node positions using spring layout
        logger.info("Creating layout...")
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
        logger.info("Creating figure...")
        fig = go.Figure(
            data=[edge_trace] + list(node_traces.values()),
            layout=go.Layout(
                title='Complete Memory Knowledge Graph Mesh (No Orphans)',
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
    
    def find_orphaned_nodes(self) -> Dict[str, List[str]]:
        """Find orphaned nodes in the database.
        
        Returns:
            Dictionary mapping node types to lists of orphaned node IDs
        """
        orphans = {
            "idea": [],
            "backtest": [],
            "context": [],
            "scenario": []
        }
        
        with self.driver.session() as session:
            # Find Ideas without TESTED_IN or SUBIDEA_OF
            result = session.run("""
            MATCH (i:Idea)
            WHERE NOT ((i)-[:TESTED_IN]->()) OR NOT (()-[:SUBIDEA_OF]->(i))
            RETURN i.id AS id, i.description AS description
            """)
            
            for record in result:
                orphans["idea"].append(f"{record['id']} ({record['description']})")
            
            # Find Backtests without TESTED_IN or EXECUTED_IN
            result = session.run("""
            MATCH (b:Backtest)
            WHERE NOT ((b)<-[:TESTED_IN]-()) OR NOT ((b)-[:EXECUTED_IN]->())
            RETURN b.id AS id
            """)
            
            for record in result:
                orphans["backtest"].append(record["id"])
            
            # Find Contexts without EXECUTED_IN or APPLIES_IN
            result = session.run("""
            MATCH (c:Context)
            WHERE NOT ((c)<-[:EXECUTED_IN]-()) AND NOT ((c)<-[:APPLIES_IN]-())
            RETURN c.id AS id, c.market AS market, c.timeframe AS timeframe
            """)
            
            for record in result:
                orphans["context"].append(f"{record['id']} ({record['market']} {record['timeframe']})")
            
            # Find Scenarios without SUBIDEA_OF or APPLIES_IN
            result = session.run("""
            MATCH (s:Scenario)
            WHERE NOT ((s)-[:SUBIDEA_OF]->()) OR NOT ((s)-[:APPLIES_IN]->())
            RETURN s.id AS id, s.description AS description
            """)
            
            for record in result:
                orphans["scenario"].append(f"{record['id']} ({record['description']})")
        
        return orphans
    
    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()

def main():
    """Run the complete mesh visualizer."""
    logger.info("Starting complete mesh visualizer...")
    
    # Initialize the visualizer
    visualizer = CompleteMeshVisualizer(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    # Find orphaned nodes
    logger.info("Finding orphaned nodes...")
    orphans = visualizer.find_orphaned_nodes()
    
    for node_type, nodes in orphans.items():
        if nodes:
            logger.info(f"Orphaned {node_type} nodes ({len(nodes)}):")
            for node in nodes[:5]:  # Show only the first 5 to avoid cluttering the log
                logger.info(f"  {node}")
            if len(nodes) > 5:
                logger.info(f"  ... and {len(nodes) - 5} more")
    
    # Create visualizations
    logger.info("Creating complete mesh visualization with orphans...")
    visualizer.visualize_complete_mesh(
        limit=200, 
        include_orphans=True, 
        output_file="complete_mesh_with_orphans.html"
    )
    
    logger.info("Creating complete mesh visualization without orphans...")
    visualizer.visualize_without_orphans(
        limit=200, 
        output_file="complete_mesh_without_orphans.html"
    )
    
    # Close the visualizer
    visualizer.close()
    
    logger.info("Complete mesh visualizer completed successfully!")
    logger.info("Check the following files:")
    logger.info("- complete_mesh_with_orphans.html")
    logger.info("- complete_mesh_without_orphans.html")

if __name__ == "__main__":
    main()
