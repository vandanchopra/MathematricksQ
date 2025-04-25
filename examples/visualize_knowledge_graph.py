#!/usr/bin/env python3
"""Script to visualize the knowledge graph with directed relationships."""

from neo4j import GraphDatabase
import networkx as nx
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Any

class KnowledgeGraphVisualizer:
    def __init__(self, uri="bolt://localhost:7688", user="neo4j", password="trading123"):
        """Initialize the visualizer."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()

    def fetch_core_relationships(self):
        """Fetch core strategy-idea relationships."""
        with self.driver.session() as session:
            # Fetch nodes
            result = session.run("""
                MATCH (s:Strategy)-[:IMPLEMENTS]->(i:Idea)
                WITH DISTINCT s, i
                RETURN DISTINCT
                    ID(s) as id, 'Strategy' as type, s.name as name,
                    s.description as description, s.score as score,
                    s.sharpe as sharpe, s.cagr as cagr,
                    s.max_drawdown as max_drawdown, s.win_rate as win_rate
                UNION ALL
                MATCH (s:Strategy)-[:IMPLEMENTS]->(i:Idea)
                WITH DISTINCT i
                RETURN DISTINCT
                    ID(i) as id, 'Idea' as type, i.name as name,
                    i.description as description, 
                    0.0 as score, null as sharpe, null as cagr,
                    null as max_drawdown, null as win_rate
            """)
            
            nodes = [{
                'id': record['id'],
                'type': record['type'],
                'name': record['name'],
                'description': record['description'],
                'score': record['score'],
                'metrics': {
                    'sharpe': record['sharpe'],
                    'cagr': record['cagr'],
                    'max_drawdown': record['max_drawdown'],
                    'win_rate': record['win_rate']
                } if record['type'] == 'Strategy' else {}
            } for record in result]
            
            # Fetch relationships
            result = session.run("""
                MATCH (s:Strategy)-[r:IMPLEMENTS]->(i:Idea)
                RETURN ID(s) as source, ID(i) as target, type(r) as type
            """)
            
            edges = [{
                'source': record['source'],
                'target': record['target'],
                'type': record['type']
            } for record in result]
            
        return nodes, edges

    def create_graph(self, nodes, edges):
        """Create NetworkX graph from nodes and edges."""
        G = nx.DiGraph()
        
        # Add nodes
        for node in nodes:
            # Create hover text
            hover_text = f"{node['name']}<br>"
            hover_text += f"Type: {node['type']}<br>"
            
            if node['metrics']:
                hover_text += "<br>Metrics:<br>"
                hover_text += f"Sharpe: {node['metrics'].get('sharpe', 0):.2f}<br>"
                hover_text += f"CAGR: {node['metrics'].get('cagr', 0):.2%}<br>"
                hover_text += f"Max DD: {node['metrics'].get('max_drawdown', 0):.2%}<br>"
                hover_text += f"Win Rate: {node['metrics'].get('win_rate', 0):.2%}<br>"
                hover_text += f"Score: {node['score']:.2f}"
            
            if node['description']:
                hover_text += f"<br><br>Description: {node['description'][:200]}..."
            
            G.add_node(node['id'],
                      type=node['type'],
                      name=node['name'],
                      hover_text=hover_text,
                      score=node['score'])
        
        # Add edges
        for edge in edges:
            G.add_edge(edge['source'], edge['target'], type=edge['type'])
        
        # Use spring layout
        pos = nx.spring_layout(G, k=2, iterations=50)
            
        return G, pos

    def create_figure(self, G, pos):
        """Create Plotly figure from NetworkX graph."""
        # Node styling
        node_colors = {
            "Idea": "#2ca02c",    # green
            "Strategy": "#ff7f0e"  # orange
        }
        node_symbols = {
            "Idea": "diamond",
            "Strategy": "square"
        }
        
        # Create node traces by type
        node_traces = {
            node_type: go.Scatter(
                x=[],
                y=[],
                mode='markers+text',
                name=node_type,
                text=[],
                hovertext=[],
                hoverinfo='text',
                textposition='bottom center',
                marker=dict(
                    symbol=node_symbols[node_type],
                    color=node_colors[node_type],
                    size=[],
                    line=dict(width=1, color='#000')
                )
            ) for node_type in ["Idea", "Strategy"]
        }
        
        # Add nodes to traces
        for node_id in G.nodes():
            node = G.nodes[node_id]
            x, y = pos[node_id]
            node_type = node['type']
            
            # Calculate node size based on score
            base_size = 20
            score_multiplier = 30
            node_size = base_size + score_multiplier * node.get('score', 0)
            
            node_traces[node_type].x = list(node_traces[node_type].x) + [x]
            node_traces[node_type].y = list(node_traces[node_type].y) + [y]
            node_traces[node_type].text = list(node_traces[node_type].text) + [node['name']]
            node_traces[node_type].hovertext = list(node_traces[node_type].hovertext) + [node['hover_text']]
            node_traces[node_type].marker.size = list(node_traces[node_type].marker.size) + [node_size]
        
        # Create edge trace
        edge_x = []
        edge_y = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=1, color='#e377c2'),  # pink
            hoverinfo='none',
            mode='lines',
            name='IMPLEMENTS'
        )
        
        # Combine all traces
        data = [edge_trace] + list(node_traces.values())
        
        # Create figure
        fig = go.Figure(
            data=data,
            layout=go.Layout(
                title=dict(
                    text='Strategy Implementation Graph<br>Strategy nodes sized by score = 0.5·Sharpe + 0.3·CAGR - 0.2·|DrawDown|',
                    x=0.5,
                    y=0.95
                ),
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=80),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    title=dict(text="Node Types"),
                    bgcolor="rgba(255, 255, 255, 0.8)",
                    bordercolor="rgba(0, 0, 0, 0.2)",
                    borderwidth=1
                )
            )
        )
        
        return fig

    def create_visualization(self):
        """Create the core strategy-idea visualization."""
        nodes, edges = self.fetch_core_relationships()
        G, pos = self.create_graph(nodes, edges)
        fig = self.create_figure(G, pos)
        
        # Save the visualization
        fig.write_html("knowledge_graph_visualization.html")
        print("Created knowledge_graph_visualization.html")

def main():
    """Main function to create visualization."""
    visualizer = KnowledgeGraphVisualizer()
    try:
        visualizer.create_visualization()
    finally:
        visualizer.close()

if __name__ == "__main__":
    main()