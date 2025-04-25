# Enhanced Memory Knowledge Graph Dashboard

This is an enhanced version of the Memory Knowledge Graph Dashboard with improved graph visualization features.

## New Features

### 1. Dynamic Filtering

- **Context Filtering**: Filter the graph to show only nodes related to a specific context (e.g., "BTC/USD 1d")
- **Idea Filtering**: Filter the graph to show only nodes related to a specific idea
- **Node Type Filtering**: Show/hide specific node types (Idea, Backtest, Context, Scenario)
- **Relationship Type Filtering**: Show/hide specific relationship types (TESTED_IN, EXECUTED_IN, etc.)

### 2. Multiple Layout Options

Choose from various layout algorithms to better visualize your graph:

- **Force-directed (cose)**: Good for general-purpose visualization
- **Hierarchical (dagre)**: Shows hierarchical relationships clearly
- **Breadth-first**: Organizes nodes in a tree-like structure
- **Circle**: Arranges nodes in a circle
- **Concentric**: Arranges nodes in concentric circles
- **Grid**: Arranges nodes in a grid pattern

### 3. Improved Node and Edge Styling

- **Hide Labels by Default**: Labels are hidden by default to reduce clutter
- **Show Labels on Hover**: Labels appear when you hover over nodes or edges
- **Highlight on Hover**: Nodes and edges are highlighted when hovered
- **Node Coloring**: Different node types have different colors
- **Edge Coloring**: Different relationship types have different colors

### 4. Node Details on Click

Click on any node to see detailed information about it in the panel below the graph.

## Usage

1. Run the dashboard:

```bash
cd src/memory/dashboard
python enhanced_dashboard.py
```

2. Open your browser at http://localhost:8052

3. Use the controls to filter and explore the graph:
   - Select node types and relationship types to show
   - Filter by context or idea
   - Choose a layout algorithm
   - Click "Refresh Graph" to update the visualization
   - Hover over nodes and edges to see labels
   - Click on nodes to see detailed information

## Customization

You can customize the dashboard by modifying the following:

- **Node Styles**: Edit the `node_styles` list to change node appearance
- **Layout Options**: Add or modify layout options in the `update_layout` function
- **Filtering Options**: Add additional filters in the `graph_controls` section
- **Query Logic**: Modify the `fetch_graph` function to change how data is retrieved from Neo4j
