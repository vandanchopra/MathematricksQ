# src/memory/dashboard/enhanced_dashboard.py

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_cytoscape as cyto
import pandas as pd
import plotly.graph_objects as go
# import plotly.express as px  # Not used
import os
import math
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load extra layouts like dagre
cyto.load_extra_layouts()

# Load environment variables
load_dotenv()

# Initialize Dash app
app = dash.Dash(__name__,
                suppress_callback_exceptions=True,
                external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'])

# Neo4j driver (point at your memory KG)
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7688")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "trading123")
patann_url = os.getenv("PATANN_URL", "http://localhost:9200")

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# --- Helper: fetch available contexts ---
def fetch_contexts():
    """Returns a list of available contexts from the database."""
    q = """
    MATCH (c:Context)
    OPTIONAL MATCH (b:Backtest)-[:EXECUTED_IN]->(c)
    WITH c, count(b) as backtestCount
    RETURN c.market + ' ' + c.timeframe AS context, backtestCount
    ORDER BY backtestCount DESC, context
    """
    with driver.session() as session:
        result = session.run(q)
        contexts = [{"label": f"{record['context']} ({record['backtestCount']} backtests)", "value": record["context"]} for record in result]
        return [{"label": "All Contexts", "value": ""}] + contexts

# --- Helper: fetch available ideas ---
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

# --- Fetch function for idea subgraph ---
def fetch_subgraph_for_idea(idea_id, context_id=None):
    """
    Fetch a simple Idea -> Backtest -> Context/Scenario subgraph for the given idea and context.
    """
    if not idea_id and not context_id:
        return [], None

    # Build the query with proper filtering
    where_clauses = []
    params = {}

    if idea_id:
        where_clauses.append("i.id = $idea_id")
        params["idea_id"] = idea_id

    if context_id:
        where_clauses.append("(c.id = $context_id OR s.id = $context_id)")
        params["context_id"] = context_id

    where = ""
    if where_clauses:
        where = "WHERE " + " AND ".join(where_clauses)

    # Single comprehensive query that brings back the entire chain
    q = f"""
    MATCH (i:Idea)
    OPTIONAL MATCH (i)-[r1:TESTED_IN]->(b:Backtest)
    OPTIONAL MATCH (b)-[r2:EXECUTED_IN]->(c:Context)
    OPTIONAL MATCH (b)-[r3:APPLIES_TO]->(s:Scenario)
    OPTIONAL MATCH (i)-[r4:SUBIDEA_OF]->(parent:Idea)
    {where}
    RETURN i, r1, b, r2, c, r3, s, r4, parent
    LIMIT 50
    """

    print(f"Running query for idea: {idea_id}, context: {context_id}")
    records = driver.session().run(q, params).data()
    print(f"Found {len(records)} records")

    # If no records found and we have an idea_id, try to at least get the idea node
    if not records and idea_id:
        idea_q = """
        MATCH (i:Idea {id: $idea_id})
        RETURN i
        """
        idea_records = driver.session().run(idea_q, idea_id=idea_id).data()
        if idea_records:
            print(f"Found idea node without connections")
            return idea_records, None

    # If still no records, return empty results
    if not records:
        return [], None

    # Use the idea ID from the records if available, otherwise use the input ID
    query_id = records[0]['i']['id'] if records and 'i' in records[0] else idea_id

    if not query_id:
        return records, None

    # Fetch the best metrics for this idea
    agg_q = """
    MATCH (i:Idea {id: $idea_id})-[r:TESTED_IN]->(b:Backtest)
    RETURN
      max(b.metric_Sharpe)       AS Sharpe_max,
      max(b.metric_CAGR)         AS CAGR_max,
      min(b.metric_MaxDrawdown)  AS DD_min
    """

    try:
        agg = driver.session().run(agg_q, idea_id=query_id).single()
        print(f"Aggregated metrics: {agg}")
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        agg = {"Sharpe_max": 0, "CAGR_max": 0, "DD_min": 0}

    return records, agg

# --- Fetch graph data with proper filtering ---
def fetch_graph_data(context_id=None, idea_id=None, node_types=None, rel_types=None):
    """
    Fetch graph data from Neo4j with proper filtering.
    Returns elements in Cytoscape format.
    """
    elements = []
    nodes_added = set()  # Track nodes we've already added

    # Print query info for debugging
    print(f"Filtering with: context={context_id}, idea={idea_id}")

    try:
        with driver.session() as session:
            # Build the query based on filters
            params = {}

            # If we have an idea_id, use a focused query for that idea
            if idea_id and idea_id.strip():
                params["idea_id"] = idea_id

                # First, get the idea node itself
                idea_q = """
                MATCH (i:Idea {id: $idea_id})
                RETURN i
                """

                print(f"Getting idea node: {idea_id}")
                idea_result = session.run(idea_q, params)
                idea_record = idea_result.single()

                if idea_record:
                    i = idea_record["i"]
                    # Add the idea node
                    if i.id not in nodes_added and (not node_types or "Idea" in node_types):
                        nodes_added.add(i.id)
                        elements.append({
                            "data": {
                                "id": i.id,
                                "label": i.get("description", "")[:50] + "...",
                                "type": "Idea",
                                "properties": {k: v for k, v in i.items()}
                            }
                        })

                # Add context filter if provided
                context_filter = ""
                if context_id and context_id.strip():
                    context_filter = "AND (c.market + ' ' + c.timeframe) = $context_id"
                    params["context_id"] = context_id

                # Query for Idea -> Backtest -> Context pattern
                q = f"""
                MATCH (i:Idea {{id: $idea_id}})-[r1:TESTED_IN]->(b:Backtest)-[r2:EXECUTED_IN]->(c:Context)
                {context_filter}
                RETURN i, r1, b, r2, c
                """

                print(f"Running focused query for idea: {idea_id}")
                result = session.run(q, params)

                # Process the results
                for record in result:
                    i, b, c = record["i"], record["b"], record["c"]

                    # Add Idea node if not already added and if node type is included
                    if i.id not in nodes_added and (not node_types or "Idea" in node_types):
                        nodes_added.add(i.id)
                        elements.append({
                            "data": {
                                "id": i.id,
                                "label": i.get("description", "")[:50] + "...",
                                "type": "Idea",
                                "properties": {k: v for k, v in i.items()}
                            }
                        })

                    # Add Backtest node if not already added and if node type is included
                    if b.id not in nodes_added and (not node_types or "Backtest" in node_types):
                        nodes_added.add(b.id)
                        elements.append({
                            "data": {
                                "id": b.id,
                                "label": f"BT:{b.get('id', '')}",
                                "type": "Backtest",
                                "properties": {k: v for k, v in b.items()}
                            }
                        })

                    # Add Context node if not already added and if node type is included
                    if c.id not in nodes_added and (not node_types or "Context" in node_types):
                        nodes_added.add(c.id)
                        elements.append({
                            "data": {
                                "id": c.id,
                                "label": f"{c.get('market', '')} {c.get('timeframe', '')}",
                                "type": "Context",
                                "properties": {k: v for k, v in c.items()}
                            }
                        })

                    # Add TESTED_IN relationship if both node types are included
                    if (not rel_types or "TESTED_IN" in rel_types) and \
                       (not node_types or ("Idea" in node_types and "Backtest" in node_types)):
                        elements.append({
                            "data": {
                                "source": i.id,
                                "target": b.id,
                                "label": "TESTED_IN",
                                "rel": "TESTED_IN"
                            }
                        })

                    # Add EXECUTED_IN relationship if both node types are included
                    if (not rel_types or "EXECUTED_IN" in rel_types) and \
                       (not node_types or ("Backtest" in node_types and "Context" in node_types)):
                        elements.append({
                            "data": {
                                "source": b.id,
                                "target": c.id,
                                "label": "EXECUTED_IN",
                                "rel": "EXECUTED_IN"
                            }
                        })

                # Also look for Scenario relationships if we have an idea
                scenario_q = """
                MATCH (i:Idea {id: $idea_id})-[r:SUBIDEA_OF]->(s:Scenario)
                RETURN i, r, s
                """

                scenario_result = session.run(scenario_q, params)
                for record in scenario_result:
                    i, s = record["i"], record["s"]

                    # Add Scenario node if not already added and if node type is included
                    if s.id not in nodes_added and (not node_types or "Scenario" in node_types):
                        nodes_added.add(s.id)
                        elements.append({
                            "data": {
                                "id": s.id,
                                "label": s.get("description", "")[:50] + "...",
                                "type": "Scenario",
                                "properties": {k: v for k, v in s.items()}
                            }
                        })

                    # Add SUBIDEA_OF relationship if both node types are included
                    if (not rel_types or "SUBIDEA_OF" in rel_types) and \
                       (not node_types or ("Idea" in node_types and "Scenario" in node_types)):
                        elements.append({
                            "data": {
                                "source": i.id,
                                "target": s.id,
                                "label": "SUBIDEA_OF",
                                "rel": "SUBIDEA_OF"
                            }
                        })

            # If we only have a context filter, query for that context
            elif context_id and context_id.strip():
                params["context_id"] = context_id

                q = """
                MATCH (i:Idea)-[r1:TESTED_IN]->(b:Backtest)-[r2:EXECUTED_IN]->(c:Context)
                WHERE (c.market + ' ' + c.timeframe) = $context_id
                RETURN i, r1, b, r2, c
                """

                print(f"Running focused query for context: {context_id}")
                result = session.run(q, params)

                # Process the results (same as above)
                for record in result:
                    i, b, c = record["i"], record["b"], record["c"]

                    # Add Idea node
                    if i.id not in nodes_added and (not node_types or "Idea" in node_types):
                        nodes_added.add(i.id)
                        elements.append({
                            "data": {
                                "id": i.id,
                                "label": i.get("description", "")[:50] + "...",
                                "type": "Idea",
                                "properties": {k: v for k, v in i.items()}
                            }
                        })

                    # Add Backtest node
                    if b.id not in nodes_added and (not node_types or "Backtest" in node_types):
                        nodes_added.add(b.id)
                        elements.append({
                            "data": {
                                "id": b.id,
                                "label": f"BT:{b.get('id', '')}",
                                "type": "Backtest",
                                "properties": {k: v for k, v in b.items()}
                            }
                        })

                    # Add Context node
                    if c.id not in nodes_added and (not node_types or "Context" in node_types):
                        nodes_added.add(c.id)
                        elements.append({
                            "data": {
                                "id": c.id,
                                "label": f"{c.get('market', '')} {c.get('timeframe', '')}",
                                "type": "Context",
                                "properties": {k: v for k, v in c.items()}
                            }
                        })

                    # Add TESTED_IN relationship
                    if (not rel_types or "TESTED_IN" in rel_types) and \
                       (not node_types or ("Idea" in node_types and "Backtest" in node_types)):
                        elements.append({
                            "data": {
                                "source": i.id,
                                "target": b.id,
                                "label": "TESTED_IN",
                                "rel": "TESTED_IN"
                            }
                        })

                    # Add EXECUTED_IN relationship
                    if (not rel_types or "EXECUTED_IN" in rel_types) and \
                       (not node_types or ("Backtest" in node_types and "Context" in node_types)):
                        elements.append({
                            "data": {
                                "source": b.id,
                                "target": c.id,
                                "label": "EXECUTED_IN",
                                "rel": "EXECUTED_IN"
                            }
                        })

            # If no specific filters, get a sample of the graph
            else:
                # Get a limited sample of the graph
                q = """
                MATCH (i:Idea)-[r1:TESTED_IN]->(b:Backtest)-[r2:EXECUTED_IN]->(c:Context)
                RETURN i, r1, b, r2, c
                LIMIT 20
                """

                print("Running sample query for the graph")
                result = session.run(q)

                # Process the results (same as above)
                for record in result:
                    i, b, c = record["i"], record["b"], record["c"]

                    # Add Idea node
                    if i.id not in nodes_added and (not node_types or "Idea" in node_types):
                        nodes_added.add(i.id)
                        elements.append({
                            "data": {
                                "id": i.id,
                                "label": i.get("description", "")[:50] + "...",
                                "type": "Idea",
                                "properties": {k: v for k, v in i.items()}
                            }
                        })

                    # Add Backtest node
                    if b.id not in nodes_added and (not node_types or "Backtest" in node_types):
                        nodes_added.add(b.id)
                        elements.append({
                            "data": {
                                "id": b.id,
                                "label": f"BT:{b.get('id', '')}",
                                "type": "Backtest",
                                "properties": {k: v for k, v in b.items()}
                            }
                        })

                    # Add Context node
                    if c.id not in nodes_added and (not node_types or "Context" in node_types):
                        nodes_added.add(c.id)
                        elements.append({
                            "data": {
                                "id": c.id,
                                "label": f"{c.get('market', '')} {c.get('timeframe', '')}",
                                "type": "Context",
                                "properties": {k: v for k, v in c.items()}
                            }
                        })

                    # Add TESTED_IN relationship
                    if (not rel_types or "TESTED_IN" in rel_types) and \
                       (not node_types or ("Idea" in node_types and "Backtest" in node_types)):
                        elements.append({
                            "data": {
                                "source": i.id,
                                "target": b.id,
                                "label": "TESTED_IN",
                                "rel": "TESTED_IN"
                            }
                        })

                    # Add EXECUTED_IN relationship
                    if (not rel_types or "EXECUTED_IN" in rel_types) and \
                       (not node_types or ("Backtest" in node_types and "Context" in node_types)):
                        elements.append({
                            "data": {
                                "source": b.id,
                                "target": c.id,
                                "label": "EXECUTED_IN",
                                "rel": "EXECUTED_IN"
                            }
                        })

                # Also get some Scenario nodes
                scenario_q = """
                MATCH (i:Idea)-[r:SUBIDEA_OF]->(s:Scenario)
                RETURN i, r, s
                LIMIT 10
                """

                scenario_result = session.run(scenario_q)
                for record in scenario_result:
                    i, s = record["i"], record["s"]

                    # Add Idea node if not already added
                    if i.id not in nodes_added and (not node_types or "Idea" in node_types):
                        nodes_added.add(i.id)
                        elements.append({
                            "data": {
                                "id": i.id,
                                "label": i.get("description", "")[:50] + "...",
                                "type": "Idea",
                                "properties": {k: v for k, v in i.items()}
                            }
                        })

                    # Add Scenario node
                    if s.id not in nodes_added and (not node_types or "Scenario" in node_types):
                        nodes_added.add(s.id)
                        elements.append({
                            "data": {
                                "id": s.id,
                                "label": s.get("description", "")[:50] + "...",
                                "type": "Scenario",
                                "properties": {k: v for k, v in s.items()}
                            }
                        })

                    # Add SUBIDEA_OF relationship
                    if (not rel_types or "SUBIDEA_OF" in rel_types) and \
                       (not node_types or ("Idea" in node_types and "Scenario" in node_types)):
                        elements.append({
                            "data": {
                                "source": i.id,
                                "target": s.id,
                                "label": "SUBIDEA_OF",
                                "rel": "SUBIDEA_OF"
                            }
                        })

            # If we still don't have any elements, try a more general query
            if not elements:
                print("No elements found with the specified filters. Trying a more general query...")

                # If we have an idea ID but no relationships, try to find related nodes
                if idea_id and idea_id.strip():
                    # Try to find any relationships for this idea
                    general_q = """
                    MATCH (i:Idea {id: $idea_id})
                    OPTIONAL MATCH (i)-[r]-(n)
                    WHERE n:Backtest OR n:Context OR n:Scenario
                    RETURN i, r, n
                    LIMIT 20
                    """

                    general_result = session.run(general_q, params)
                    for record in general_result:
                        if "i" in record and record["i"] is not None:
                            i = record["i"]
                            if i.id not in nodes_added and (not node_types or "Idea" in node_types):
                                nodes_added.add(i.id)
                                elements.append({
                                    "data": {
                                        "id": i.id,
                                        "label": i.get("description", "")[:50] + "...",
                                        "type": "Idea",
                                        "properties": {k: v for k, v in i.items()}
                                    }
                                })

                        if "n" in record and record["n"] is not None:
                            n = record["n"]
                            if n.id not in nodes_added:
                                nodes_added.add(n.id)

                                # Determine node type and label
                                labels = list(n.labels)
                                node_type = labels[0] if labels else "Unknown"

                                if node_type == "Backtest":
                                    label = f"BT:{n.get('id', '')}"
                                elif node_type == "Context":
                                    label = f"{n.get('market', '')} {n.get('timeframe', '')}"
                                elif node_type == "Scenario":
                                    label = n.get("description", "")[:50] + "..."
                                else:
                                    label = n.get("description", "") or n.get("id", "")

                                if not node_types or node_type in node_types:
                                    elements.append({
                                        "data": {
                                            "id": n.id,
                                            "label": label,
                                            "type": node_type,
                                            "properties": {k: v for k, v in n.items()}
                                        }
                                    })

                            # Add relationship if it exists
                            if "r" in record and record["r"] is not None and "i" in record and record["i"] is not None:
                                r = record["r"]
                                rel_type = type(r).__name__

                                if not rel_types or rel_type in rel_types:
                                    elements.append({
                                        "data": {
                                            "source": record["i"].id,
                                            "target": n.id,
                                            "label": rel_type,
                                            "rel": rel_type
                                        }
                                    })
                else:
                    # If no specific idea, get a sample of nodes
                    general_q = """
                    MATCH (n)
                    WHERE n:Idea OR n:Backtest OR n:Context OR n:Scenario
                    RETURN n, labels(n) as labels
                    LIMIT 20
                    """

                    general_result = session.run(general_q)
                    for record in general_result:
                        node = record["n"]
                        labels = record["labels"]

                        if node.id not in nodes_added and (not node_types or any(label in node_types for label in labels)):
                            nodes_added.add(node.id)

                            # Determine label and type
                            node_type = labels[0] if labels else "Unknown"
                            if node_type == "Idea":
                                label = node.get("description", "")[:50] + "..."
                            elif node_type == "Backtest":
                                label = f"BT:{node.get('id', '')}"
                            elif node_type == "Context":
                                label = f"{node.get('market', '')} {node.get('timeframe', '')}"
                            elif node_type == "Scenario":
                                label = node.get("description", "")[:50] + "..."
                            else:
                                label = node.get("description", "") or node.get("id", "")

                            elements.append({
                                "data": {
                                    "id": node.id,
                                    "label": label,
                                    "type": node_type,
                                    "properties": {k: v for k, v in node.items()}
                                }
                            })

    except Exception as e:
        print(f"Error fetching graph: {e}")

    # Filter elements based on node_types and rel_types
    if node_types or rel_types:
        filtered_elements = []
        for elem in elements:
            # For nodes, check if the type is in node_types
            if 'source' not in elem['data'] and (not node_types or elem['data']['type'] in node_types):
                filtered_elements.append(elem)
            # For edges, check if the rel is in rel_types
            elif 'source' in elem['data'] and (not rel_types or elem['data']['rel'] in rel_types):
                filtered_elements.append(elem)
        elements = filtered_elements

    print(f"Returning {len(elements)} elements")
    return elements

# --- Helper: fetch metrics table for bar charts ---
def fetch_metrics(context=None, metric_name="Sharpe"):
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

    # Sort by the specified metric if it exists in the dataframe
    if metric_name in df.columns:
        df = df.sort_values(by=metric_name, ascending=False)

    return df

# --- Graph Controls ---
graph_controls = html.Div([
    html.Div([
        html.Div([
            html.Label("Show node types:"),
            dcc.Checklist(
                id="filter-node-types",
                options=[{"label": lbl, "value": lbl} for lbl in ["Idea", "Backtest", "Context", "Scenario"]],
                value=["Idea", "Backtest", "Context", "Scenario"],
                inline=True
            ),
        ], className="col-md-6"),

        html.Div([
            html.Label("Show relationship types:"),
            dcc.Checklist(
                id="filter-rel-types",
                options=[{"label": r, "value": r} for r in ["TESTED_IN", "EXECUTED_IN", "APPLIES_IN", "SUBIDEA_OF"]],
                value=["TESTED_IN", "EXECUTED_IN", "APPLIES_IN", "SUBIDEA_OF"],
                inline=True
            ),
        ], className="col-md-6"),
    ], className="row mb-3"),

    html.Div([
        html.Div([
            html.Label("Filter by Context:"),
            dcc.Dropdown(
                id="filter-context",
                options=[],  # Will be populated by callback
                value="",
                placeholder="All Contexts"
            ),
        ], className="col-md-4"),

        html.Div([
            html.Label("Filter by Idea:"),
            dcc.Dropdown(
                id="filter-idea",
                options=[],  # Will be populated by callback
                value="",
                placeholder="All Ideas"
            ),
        ], className="col-md-4"),

        html.Div([
            html.Label("Layout:"),
            dcc.Dropdown(
                id="layout-selector",
                options=[
                    {"label": "Force-directed (cose)", "value": "cose"},
                    {"label": "Breadth-first", "value": "breadthfirst"},
                    {"label": "Circle", "value": "circle"},
                    {"label": "Concentric", "value": "concentric"},
                    {"label": "Grid", "value": "grid"},
                    {"label": "Random", "value": "random"}
                ],
                value="cose",
                placeholder="Select Layout"
            ),
        ], className="col-md-4"),
    ], className="row mb-3"),

    html.Button("Refresh Graph", id="refresh-graph", className="btn btn-primary mb-3")
])

# Define node and edge styles with hover effects
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
    {
        'selector': '.idea:hover',
        'style': {
            'label': 'data(label)',
            'text-opacity': 1
        }
    },
    # Backtest nodes: green squares, show metrics on hover
    {
        'selector': '.backtest',
        'style': {
            'background-color': '#2ecc71',  # Green
            'shape': 'rectangle'
        }
    },
    {
        'selector': '.backtest:hover',
        'style': {
            'label': 'data(label)',
            'text-opacity': 1
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

graph_area = html.Div([
    cyto.Cytoscape(
        id="cytoscape-graph",
        layout={"name": "cose", "animate": True, "fit": True},
        style={"width": "100%", "height": "600px", "border": "1px solid #ddd", "borderRadius": "5px"},
        elements=[],
        stylesheet=node_styles
    ),
    html.Div([
        html.Div(id="node-info", className="card p-3 mt-3")
    ])
])

# --- UCB Visualization Tab ---
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

        # If DataFrame is empty, return empty DataFrame with columns
        if df.empty:
            return pd.DataFrame(columns=["id", "description", "testCount", "avgScore", "ucb"])

        return df

def fetch_backtest_history():
    """Fetch backtest history for all ideas."""
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

# --- App Layout ---
# --- MCTS Visualization Tab ---
mcts_tab = html.Div([
    html.H3("MCTS Tree Visualization", className="mt-4"),
    html.P("Visualize Monte Carlo Tree Search trees for strategy optimization."),

    html.Div([
        html.Div([
            html.Label("Root Idea:"),
            dcc.Dropdown(
                id="mcts-root-idea",
                options=[],
                placeholder="Select Root Idea"
            ),
        ], className="col-md-6 mb-3"),

        html.Div([
            html.Label("Tree Depth:"),
            dcc.Slider(
                id="mcts-depth-slider",
                min=1,
                max=5,
                step=1,
                value=2,
                marks={i: str(i) for i in range(1, 6)},
                className="mb-4"
            ),
        ], className="col-md-6 mb-3"),
    ], className="row mb-3"),

    html.Button("Refresh MCTS Tree", id="refresh-mcts-button", className="btn btn-primary mb-3"),

    html.Div([
        cyto.Cytoscape(
            id="mcts-cytoscape-graph",
            layout={'name': 'breadthfirst', 'directed': True},
            style={'width': '100%', 'height': '600px'},
            elements=[],
            stylesheet=node_styles
        )
    ], className="mb-4"),

    html.Div([
        html.H4("Best Path", className="mt-4"),
        html.Div(id="mcts-best-path")
    ])
])

app.layout = html.Div([
    html.H1("Memory Knowledge Graph Explorer", className="text-center my-4"),

    dcc.Tabs([
        dcc.Tab(label="Graph Explorer", children=[
            html.Div([graph_controls, graph_area], className="container-fluid mt-3")
        ]),
        dcc.Tab(label="UCB Visualization", children=[
            html.Div([ucb_tab], className="container-fluid mt-3")
        ]),
        dcc.Tab(label="MCTS Visualization", children=[
            html.Div([mcts_tab], className="container-fluid mt-3")
        ])
    ]),

    # Interval for auto-refresh
    dcc.Interval(
        id="auto-refresh",
        interval=30 * 1000,  # 30 seconds
        n_intervals=0
    )
], className="container-fluid")

# --- Update Graph Layout ---
@app.callback(
    Output("cytoscape-graph", "layout"),
    Input("layout-selector", "value")
)
def update_layout(layout_name):
    if not layout_name:
        layout_name = "cose"

    layout_options = {
        "name": layout_name,
        "animate": True,
        "fit": True
    }

    # Add specific options for different layouts
    if layout_name == "breadthfirst":
        layout_options["directed"] = True
        layout_options["spacingFactor"] = 1.5
    elif layout_name == "circle":
        layout_options["radius"] = 500
    elif layout_name == "concentric":
        layout_options["minNodeSpacing"] = 100
    elif layout_name == "grid":
        layout_options["rows"] = 3
        layout_options["cols"] = 3

    return layout_options

# --- Build elements function ---
def build_elements(records, agg, node_types=None, rel_types=None):
    """
    Build Cytoscape elements from Neo4j records with metrics and scores.
    """
    elements = []
    seen = set()  # Track nodes we've already added

    # Compute the idea score
    Sharpe_max = agg['Sharpe_max'] if agg and agg['Sharpe_max'] is not None else 0
    CAGR_max = agg['CAGR_max'] if agg and agg['CAGR_max'] is not None else 0
    DD_min = agg['DD_min'] if agg and agg['DD_min'] is not None else 0

    idea_score = 0.5 * Sharpe_max + 0.3 * CAGR_max - 0.2 * DD_min
    print(f"Idea score: {idea_score}")

    for rec in records:
        # Extract nodes and relationships from the record
        i = rec.get('i')  # Idea
        b = rec.get('b')  # Backtest
        c = rec.get('c')  # Context
        s = rec.get('s')  # Scenario
        parent = rec.get('parent')  # Parent idea

        # Skip if no idea
        if not i or not i.get('id'):
            continue

        # 1) Idea node with score
        if i['id'] not in seen and (not node_types or "Idea" in node_types):
            seen.add(i['id'])
            idea_desc = i.get('name', '') or i.get('description', '')[:50] + "..."
            idea_label = f"{idea_desc}\nScore: {idea_score:.2f}"
            elements.append({
                'data': {
                    'id': i['id'],
                    'label': idea_label,
                    'type': 'Idea',
                    'score': idea_score,
                    'description': i.get('description', ''),
                    'testCount': i.get('testCount', 0),
                    'totalScore': i.get('totalScore', 0)
                },
                'classes': 'idea'
            })

        # 2) Backtest node with metrics
        if b and b.get('id') and b['id'] not in seen and (not node_types or "Backtest" in node_types):
            seen.add(b['id'])
            # Format metrics for display
            sharpe = b.get('metric_Sharpe', 0)
            cagr = b.get('metric_CAGR', 0)
            maxdd = b.get('metric_MaxDrawdown', 0)
            bt_score = 0.5 * sharpe + 0.3 * cagr - 0.2 * maxdd

            # Create a label with key metrics
            bt_label = f"S:{sharpe:.2f} C:{cagr:.2f}\nD:{maxdd:.2f}\nScore:{bt_score:.2f}"

            elements.append({
                'data': {
                    'id': b['id'],
                    'label': bt_label,
                    'type': 'Backtest',
                    'Sharpe': sharpe,
                    'CAGR': cagr,
                    'MaxDD': maxdd,
                    'WinRate': b.get('metric_WinRate', 0),
                    'TotalTrades': b.get('metric_TotalTrades', 0),
                    'ProfitFactor': b.get('metric_ProfitFactor', 0),
                    'score': bt_score,
                    'date': str(b.get('date', '')) if b.get('date') else ''
                },
                'classes': 'backtest'
            })

        # 3) Context node (if present)
        if c and c.get('id') and c['id'] not in seen and (not node_types or "Context" in node_types):
            seen.add(c['id'])
            context_label = f"{c.get('market', '')} {c.get('timeframe', '')}"
            elements.append({
                'data': {
                    'id': c['id'],
                    'label': context_label,
                    'type': 'Context',
                    'market': c.get('market', ''),
                    'timeframe': c.get('timeframe', '')
                },
                'classes': 'context'
            })

        # 4) Scenario node (if present)
        if s and s.get('id') and s['id'] not in seen and (not node_types or "Scenario" in node_types):
            seen.add(s['id'])
            scenario_desc = s.get('description', '')[:50] + "..."
            elements.append({
                'data': {
                    'id': s['id'],
                    'label': scenario_desc,
                    'type': 'Scenario',
                    'description': s.get('description', '')
                },
                'classes': 'scenario'
            })

        # 5) Parent Idea node (if present)
        if parent and parent.get('id') and parent['id'] not in seen and (not node_types or "Idea" in node_types):
            seen.add(parent['id'])
            parent_desc = parent.get('name', '') or parent.get('description', '')[:50] + "..."
            parent_score = parent.get('totalScore', 0) / max(parent.get('testCount', 1), 1)
            parent_label = f"{parent_desc}\nScore: {parent_score:.2f}"
            elements.append({
                'data': {
                    'id': parent['id'],
                    'label': parent_label,
                    'type': 'Idea',
                    'score': parent_score,
                    'description': parent.get('description', ''),
                    'testCount': parent.get('testCount', 0),
                    'totalScore': parent.get('totalScore', 0)
                },
                'classes': 'idea parent'
            })

        # 6) Edges
        # TESTED_IN relationship between Idea and Backtest
        if b and b.get('id') and (not rel_types or "TESTED_IN" in rel_types) and \
           (not node_types or ("Idea" in node_types and "Backtest" in node_types)):
            edge_id = f"e1_{i['id']}_{b['id']}"
            if edge_id not in seen:
                seen.add(edge_id)
                elements.append({
                    'data': {
                        'id': edge_id,
                        'source': i['id'],
                        'target': b['id'],
                        'label': 'TESTED_IN',
                        'rel': 'TESTED_IN'
                    },
                    'classes': 'edge-tested'
                })

        # EXECUTED_IN relationship between Backtest and Context (if Context exists)
        if b and b.get('id') and c and c.get('id') and (not rel_types or "EXECUTED_IN" in rel_types) and \
           (not node_types or ("Backtest" in node_types and "Context" in node_types)):
            edge_id = f"e2_{b['id']}_{c['id']}"
            if edge_id not in seen:
                seen.add(edge_id)
                elements.append({
                    'data': {
                        'id': edge_id,
                        'source': b['id'],
                        'target': c['id'],
                        'label': 'EXECUTED_IN',
                        'rel': 'EXECUTED_IN'
                    },
                    'classes': 'edge-executed'
                })

        # APPLIES_TO relationship between Backtest and Scenario (if Scenario exists)
        if b and b.get('id') and s and s.get('id') and (not rel_types or "APPLIES_TO" in rel_types) and \
           (not node_types or ("Backtest" in node_types and "Scenario" in node_types)):
            edge_id = f"e3_{b['id']}_{s['id']}"
            if edge_id not in seen:
                seen.add(edge_id)
                elements.append({
                    'data': {
                        'id': edge_id,
                        'source': b['id'],
                        'target': s['id'],
                        'label': 'APPLIES_TO',
                        'rel': 'APPLIES_TO'
                    },
                    'classes': 'edge-applies'
                })

        # SUBIDEA_OF relationship between Idea and Parent Idea (if Parent exists)
        if parent and parent.get('id') and (not rel_types or "SUBIDEA_OF" in rel_types) and \
           (not node_types or "Idea" in node_types):
            edge_id = f"e4_{i['id']}_{parent['id']}"
            if edge_id not in seen:
                seen.add(edge_id)
                elements.append({
                    'data': {
                        'id': edge_id,
                        'source': i['id'],
                        'target': parent['id'],
                        'label': 'SUBIDEA_OF',
                        'rel': 'SUBIDEA_OF'
                    },
                    'classes': 'edge-subidea'
                })

    return elements

# --- Refresh Graph ---
@app.callback(
    Output("cytoscape-graph", "elements"),
    [Input("refresh-graph", "n_clicks")],
    [State("filter-idea", "value"),
     State("filter-context", "value"),
     State("filter-node-types", "value"),
     State("filter-rel-types", "value"),
     State("layout-selector", "value")]
)
def update_graph(n_clicks, idea_id, context_id, node_types, rel_types, layout):
    # Print the filter values for debugging
    print(f"Refresh button clicked, n_clicks: {n_clicks}")
    print(f"Refreshing graph with idea: {idea_id}, context: {context_id}")
    print(f"Node types: {node_types}")
    print(f"Relationship types: {rel_types}")
    print(f"Layout: {layout}")

    if not idea_id and not context_id:
        return []

    # Fetch the subgraph for the idea and context
    result = fetch_subgraph_for_idea(idea_id, context_id)
    if not result or len(result) != 2:
        return []

    records, agg = result
    print(f"Records: {records}")

    # Build elements from the records
    elements = build_elements(records, agg, node_types, rel_types)

    # If no records found, at least show the idea node
    if not elements and idea_id:
        # Get the idea node
        idea_q = """
        MATCH (i:Idea {id: $idea_id})
        RETURN i
        """
        idea_record = driver.session().run(idea_q, idea_id=idea_id).single()
        if idea_record:
            i = idea_record["i"]
            elements.append({
                'data': {
                    'id': i['id'],
                    'label': i.get('name', '') or i.get('description', '')[:50] + "...",
                    'type': 'Idea',
                    'score': 0  # Default score for ideas with no backtests
                }
            })

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

    # Print the number of elements returned
    print(f"Returned {len(elements)} elements")

    return elements

# --- Display Node Info on Click ---
@app.callback(
    Output("node-info", "children"),
    Input("cytoscape-graph", "tapNodeData")
)
def display_node_info(node_data):
    if not node_data:
        return html.Div("Click on a node to see details")

    # Extract data directly from the node_data
    node_type = node_data.get("type")
    node_label = node_data.get("label")
    properties = node_data.get("properties", {})

    # Create property table
    property_rows = []
    for key, value in properties.items():
        if key not in ["id", "description"]:
            property_rows.append(html.Tr([
                html.Td(key),
                html.Td(str(value))
            ]))

    # Create node info display
    return html.Div([
        html.H4(f"{node_type}: {node_label}", className="mt-3"),
        html.Hr(),
        html.Table([
            html.Thead(html.Tr([html.Th("Property"), html.Th("Value")])),
            html.Tbody(property_rows)
        ], className="table table-striped") if property_rows else html.Div("No additional properties")
    ], className="card p-3")

# --- UCB Visualization Callbacks ---
@app.callback(
    Output("ucb-bar-chart", "figure"),
    [Input("exploration-slider", "value"),
     Input("auto-refresh", "n_intervals")]
)
def update_ucb_chart(exploration_constant, _):
    """Update the UCB bar chart."""
    # Fetch ideas with UCB scores
    df = fetch_ideas_with_ucb(exploration_constant)

    if df.empty:
        return go.Figure()

    # Sort by UCB score
    df = df.sort_values(by="ucb", ascending=False).head(10)

    # Create the bar chart
    fig = go.Figure()

    # Add UCB score bars
    fig.add_trace(go.Bar(
        x=df["ucb"],
        y=df["description"].apply(lambda x: x[:50] + "..." if len(x) > 50 else x),
        orientation="h",
        name="UCB Score",
        marker_color="#3498db"
    ))

    # Add average score bars
    fig.add_trace(go.Bar(
        x=df["avgScore"],
        y=df["description"].apply(lambda x: x[:50] + "..." if len(x) > 50 else x),
        orientation="h",
        name="Average Score",
        marker_color="#2ecc71"
    ))

    # Update layout
    fig.update_layout(
        title="Top 10 Ideas by UCB Score",
        xaxis_title="Score",
        yaxis_title="Idea",
        barmode="group",
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

@app.callback(
    Output("backtest-history-table", "children"),
    [Input("auto-refresh", "n_intervals")]
)
def update_backtest_history(_):
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
                html.Th("Date"),
                html.Th("Sharpe"),
                html.Th("CAGR"),
                html.Th("MaxDD"),
                html.Th("Win Rate"),
                html.Th("Total Trades"),
                html.Th("Score")
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(row["idea_description"][:50] + "..." if len(row["idea_description"]) > 50 else row["idea_description"]),
                html.Td(str(row["date"])),
                html.Td(f"{row['Sharpe']:.2f}"),
                html.Td(f"{row['CAGR']:.2f}"),
                html.Td(f"{row['MaxDrawdown']:.2f}"),
                html.Td(f"{row['WinRate']:.2f}"),
                html.Td(str(row["TotalTrades"])),
                html.Td(f"{row['score']:.2f}")
            ]) for _, row in df.iterrows()
        ])
    ], className="table table-striped table-hover")

    return table

@app.callback(
    Output("backtest-history-table", "children", allow_duplicate=True),
    [Input("auto-refresh", "n_intervals")],
    prevent_initial_call=True
)
def update_backtest_history(_):
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

# --- Auto-Refresh Graph ---
@app.callback(
    Output("cytoscape-graph", "elements", allow_duplicate=True),
    [Input("auto-refresh", "n_intervals")],
    [State("filter-idea", "value"),
     State("filter-context", "value"),
     State("filter-node-types", "value"),
     State("filter-rel-types", "value"),
     State("layout-selector", "value")],
    prevent_initial_call=True
)
def auto_refresh_graph(n_intervals, idea_id, context_id, node_types, rel_types, _):
    """Auto-refresh the graph."""
    print(f"Auto-refresh triggered, n_intervals: {n_intervals}")
    print(f"Refreshing graph with idea: {idea_id}, context: {context_id}")

    if not idea_id and not context_id:
        return []

    # Fetch the subgraph for the idea and context
    result = fetch_subgraph_for_idea(idea_id, context_id)
    if not result or len(result) != 2:
        return []

    records, agg = result

    # Build elements from the records
    elements = build_elements(records, agg, node_types, rel_types)

    # If no records found, at least show the idea node
    if not elements and idea_id:
        # Get the idea node
        idea_q = """
        MATCH (i:Idea {id: $idea_id})
        RETURN i
        """
        idea_record = driver.session().run(idea_q, idea_id=idea_id).single()
        if idea_record:
            i = idea_record["i"]
            elements.append({
                'data': {
                    'id': i['id'],
                    'label': i.get('name', '') or i.get('description', '')[:50] + "...",
                    'type': 'Idea',
                    'score': 0  # Default score for ideas with no backtests
                }
            })

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

    print(f"Auto-refresh returned {len(elements)} elements")
    return elements

# --- Update Dropdowns ---
@app.callback(
    [Output("filter-idea", "options"),
     Output("filter-context", "options")],
    [Input("auto-refresh", "n_intervals")]
)
def update_filter_dropdowns(_):
    """Update the filter dropdowns."""
    return fetch_ideas(), fetch_contexts()

# --- MCTS Visualization Callbacks ---

# Callback to populate the root idea dropdown
@app.callback(
    Output("mcts-root-idea", "options"),
    [Input("auto-refresh", "n_intervals")]
)
def update_mcts_root_ideas(_):
    """Update the root idea dropdown for MCTS visualization."""
    with driver.session() as session:
        # Get ideas with at least one backtest
        result = session.run("""
        MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)
        WITH i, count(b) as testCount
        WHERE testCount > 0
        RETURN i.id as id, i.description as description, testCount
        ORDER BY testCount DESC
        LIMIT 20
        """)

        # Convert to options
        options = []
        for record in result:
            idea_id = record["id"]
            description = record["description"]
            test_count = record["testCount"]

            if description and len(description) > 50:
                description = description[:50] + "..."

            options.append({"label": f"{description} ({test_count} tests)", "value": idea_id})

        return options

# Callback to update the MCTS tree visualization is defined below

def fetch_mcts_tree(root_idea_id, depth=2):
    """Fetch the MCTS tree for a root idea."""
    elements = []
    seen = set()

    with driver.session() as session:
        # Get the root idea
        root_q = """
        MATCH (i:Idea {id: $root_id})
        RETURN i
        """
        root_result = session.run(root_q, root_id=root_idea_id)
        root_record = root_result.single()

        if not root_record:
            return []

        root = root_record["i"]

        # Add the root idea node
        elements.append({
            "data": {
                "id": root["id"],
                "label": root.get("description", "")[:50] + "...",
                "type": "Idea",
                "level": 0,
                "testCount": root.get("testCount", 0),
                "totalScore": root.get("totalScore", 0),
                "avgScore": root.get("totalScore", 0) / max(root.get("testCount", 1), 1)
            },
            "classes": "idea root"
        })
        seen.add(root["id"])

        # Get child ideas (SUBIDEA_OF relationships)
        for level in range(1, depth + 1):
            # Get all ideas at the current level
            if level == 1:
                # Direct children of the root
                q = """
                MATCH (child:Idea)-[:SUBIDEA_OF]->(parent:Idea {id: $parent_id})
                RETURN child, parent
                """
                result = session.run(q, parent_id=root_idea_id)
            else:
                # Children of the previous level
                q = """
                MATCH (child:Idea)-[:SUBIDEA_OF]->(parent:Idea)
                WHERE parent.id IN $parent_ids
                RETURN child, parent
                """
                parent_ids = [elem["data"]["id"] for elem in elements if elem["data"]["level"] == level - 1]
                result = session.run(q, parent_ids=parent_ids)

            # Process the results
            for record in result:
                child = record["child"]
                parent = record["parent"]

                # Skip if already seen
                if child["id"] in seen:
                    continue

                # Add the child node
                avg_score = child.get("totalScore", 0) / max(child.get("testCount", 1), 1)
                elements.append({
                    "data": {
                        "id": child["id"],
                        "label": child.get("description", "")[:50] + "...",
                        "type": "Idea",
                        "level": level,
                        "testCount": child.get("testCount", 0),
                        "totalScore": child.get("totalScore", 0),
                        "avgScore": avg_score
                    },
                    "classes": "idea"
                })
                seen.add(child["id"])

                # Add the edge
                edge_id = f"e_{child['id']}_{parent['id']}"
                elements.append({
                    "data": {
                        "id": edge_id,
                        "source": child["id"],
                        "target": parent["id"],
                        "label": "SUBIDEA_OF"
                    },
                    "classes": "edge-subidea"
                })

        # Get the UCB scores for all ideas in the tree
        df = fetch_ideas_with_ucb(1.0)  # Use default exploration constant
        if not df.empty:
            # Get the idea with the highest UCB score
            highest_ucb_id = df.iloc[0]["id"]

            # Add UCB scores to the nodes and highlight the highest UCB node
            for element in elements:
                if element.get("data", {}).get("type") == "Idea":
                    idea_id = element["data"]["id"]
                    idea_row = df[df["id"] == idea_id]

                    if not idea_row.empty:
                        element["data"]["ucb"] = float(idea_row["ucb"].iloc[0])

                        # Highlight the highest UCB node
                        if idea_id == highest_ucb_id:
                            if "classes" in element:
                                element["classes"] += " highest-ucb"
                            else:
                                element["classes"] = "idea highest-ucb"

    return elements

# Callback to update the best path display is defined below

# Callback to update the MCTS tree visualization
@app.callback(
    Output("mcts-cytoscape-graph", "elements", allow_duplicate=True),
    [Input("refresh-mcts-button", "n_clicks")],
    [State("mcts-root-idea", "value"),
     State("mcts-depth-slider", "value")],
    prevent_initial_call=True
)
def update_mcts_tree(n_clicks, root_idea_id, depth):
    """Update the MCTS tree visualization."""
    if not n_clicks or not root_idea_id:
        return []

    print(f"Refreshing MCTS tree for root idea: {root_idea_id}, depth: {depth}")

    # Fetch the MCTS tree
    elements = fetch_mcts_tree(root_idea_id, depth)

    print(f"Returned {len(elements)} elements for MCTS tree")
    return elements

# Callback to update the best path
@app.callback(
    Output("mcts-best-path", "children", allow_duplicate=True),
    [Input("mcts-cytoscape-graph", "elements")],
    prevent_initial_call=True
)
def update_best_path(elements):
    """Update the best path display."""
    if not elements:
        return html.Div("No MCTS tree available.")

    # Find the node with the highest UCB score
    highest_ucb_node = None
    highest_ucb = -1

    for element in elements:
        if element.get("data", {}).get("type") == "Idea" and "ucb" in element.get("data", {}):
            ucb = element["data"]["ucb"]
            if ucb > highest_ucb:
                highest_ucb = ucb
                highest_ucb_node = element

    if not highest_ucb_node:
        return html.Div("No node with UCB score found.")

    # Build the path from the highest UCB node to the root
    path = []
    current_node = highest_ucb_node

    while current_node:
        path.append(current_node)

        # Find the parent node
        parent_id = None
        for element in elements:
            if element.get("data", {}).get("source") == current_node["data"]["id"]:
                parent_id = element["data"]["target"]
                break

        if not parent_id:
            break

        # Find the parent node
        current_node = None
        for element in elements:
            if element.get("data", {}).get("id") == parent_id and element.get("data", {}).get("type") == "Idea":
                current_node = element
                break

    # Reverse the path to go from root to leaf
    path.reverse()

    # Create the path display
    path_items = []
    for i, node in enumerate(path):
        node_data = node["data"]

        # Add an arrow between nodes
        if i > 0:
            path_items.append(html.Span(" → ", className="mx-2"))

        # Add the node
        node_text = f"{node_data['label']} (UCB: {node_data.get('ucb', 'N/A'):.4f})"
        path_items.append(html.Span(node_text, className="badge badge-primary p-2"))

    return html.Div(path_items, className="d-flex flex-wrap align-items-center")

if __name__ == "__main__":
    app.run(debug=True, port=8054)
