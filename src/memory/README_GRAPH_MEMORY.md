# Graph Memory System

A hybrid memory system that combines Neo4j for graph relationships and PatANN for vector embeddings.

## Overview

The Graph Memory System is designed to store and retrieve trading ideas, scenarios, contexts, and backtests. It uses Neo4j for storing the graph structure and relationships, and PatANN for vector embeddings and similarity search.

## Components

### 1. Knowledge Graph Builder (`kg_builder.py`)

The Knowledge Graph Builder provides functions for building and maintaining the Neo4j knowledge graph:

- `setup_schema()`: Set up the Neo4j schema with constraints and indexes
- `store_idea()`: Store an Idea node in the knowledge graph
- `store_scenario()`: Store a Scenario node in the knowledge graph
- `store_context()`: Store a Context node in the knowledge graph
- `store_backtest()`: Store a Backtest node in the knowledge graph
- `get_description()`: Get the description of a node by its ID
- `clear_database()`: Clear all data from the database

### 2. PatANN Indexer (`patann_indexer.py`)

The PatANN Indexer provides functions for indexing and searching vectors in PatANN:

- `PatANNClient`: Client for interacting with the PatANN vector database
- `index_idea()`: Index an idea in PatANN
- `index_scenario()`: Index a scenario in PatANN
- `search_similar()`: Search for similar nodes in PatANN
- `rank_next_ideas()`: Rank the next ideas to explore based on the current strategy

### 3. Graph Memory (`graph_memory.py`)

The Graph Memory provides a hybrid memory system that combines Neo4j and PatANN:

- `GraphMemory`: Hybrid memory system that combines Neo4j for graph relationships and PatANN for vector embeddings
- `add_idea()`: Add an idea to the memory system
- `add_scenario()`: Add a scenario to the memory system
- `add_context()`: Add a context to the memory system
- `add_backtest()`: Add a backtest to the memory system
- `find_similar_ideas()`: Find ideas similar to the given text
- `find_similar_scenarios()`: Find scenarios similar to the given text
- `get_idea_backtests()`: Get all backtests for a given idea
- `get_context_backtests()`: Get all backtests for a given context
- `get_best_ideas()`: Get the best ideas based on a specific metric
- `recommend_next_ideas()`: Recommend the next ideas to explore based on the current ideas
- `get_idea_scenarios()`: Get all scenarios for a given idea
- `get_scenario_backtests()`: Get all backtests for a given scenario
- `get_full_subgraph()`: Get the full subgraph for visualization
- `clear()`: Clear all data from the memory system

### 4. Graph Memory Agent (`graph_memory_agent.py`)

The Graph Memory Agent provides a simplified interface for working with the memory system:

- `GraphMemoryAgent`: Agent for interacting with the graph memory system
- `remember_idea()`: Remember an idea
- `remember_scenario()`: Remember a scenario
- `remember_context()`: Remember a context
- `remember_backtest()`: Remember a backtest
- `recall_similar_ideas()`: Recall ideas similar to the given description
- `recall_best_ideas()`: Recall the best ideas based on a specific metric
- `recommend_ideas()`: Recommend ideas to explore next based on the current ideas
- `get_idea_performance()`: Get the performance of an idea across all backtests
- `compare_ideas()`: Compare multiple ideas based on a specific metric
- `get_context_performance()`: Get the performance of all ideas in a specific context
- `compare_contexts()`: Compare multiple contexts based on a specific metric
- `get_visualization_data()`: Get data for visualizing the memory graph
- `export_to_json()`: Export the memory graph to a JSON file
- `import_from_json()`: Import the memory graph from a JSON file

## Schema

The memory system uses the following schema:

### Nodes

1. **Idea**: A trading idea
   - `id`: Unique identifier
   - `description`: Description of the idea
   - `created_at`: Timestamp when the idea was created
   - `tags`: List of tags for the idea

2. **Scenario**: A specific scenario for an idea
   - `id`: Unique identifier
   - `description`: Description of the scenario
   - `created_at`: Timestamp when the scenario was created
   - `tags`: List of tags for the scenario

3. **Context**: A market context
   - `id`: Unique identifier
   - `market`: Market identifier (e.g., "BTC/USD")
   - `timeframe`: Timeframe (e.g., "1d", "4h")
   - `description`: Description of the context

4. **Backtest**: A backtest of an idea in a specific context
   - `id`: Unique identifier
   - `date`: Timestamp when the backtest was created
   - `metric_*`: Metrics for the backtest (e.g., `metric_Sharpe`, `metric_CAGR`)
   - `notes`: Additional notes about the backtest

### Relationships

1. **TESTED_IN**: An idea is tested in a backtest
   - From: Idea
   - To: Backtest

2. **EXECUTED_IN**: A backtest is executed in a context
   - From: Backtest
   - To: Context

3. **APPLIES_TO**: A backtest applies to a scenario
   - From: Backtest
   - To: Scenario

4. **SUBIDEA_OF**: A scenario is a sub-idea of an idea
   - From: Scenario
   - To: Idea

## Usage

### Basic Usage

```python
from src.memory.graph_memory_agent import GraphMemoryAgent

# Create a memory agent
agent = GraphMemoryAgent()

# Remember an idea
idea_id = agent.remember_idea(
    description="Using Internal Bar Strength (IBS) for mean reversion trading",
    tags=["mean-reversion", "technical-indicator", "IBS"]
)

# Remember a scenario
scenario_id = agent.remember_scenario(
    description="IBS applied to country ETFs",
    parent_idea_id=idea_id,
    tags=["ETF", "country", "global"]
)

# Remember a context
context_id = agent.remember_context(
    market="ETF-Basket",
    timeframe="1d",
    description="Daily timeframe for a basket of country ETFs"
)

# Remember a backtest
backtest_id = agent.remember_backtest(
    idea_id=idea_id,
    context_id=context_id,
    scenario_id=scenario_id,
    metrics={
        "Sharpe": 1.85,
        "CAGR": 0.12,
        "MaxDrawdown": 0.15,
        "WinRate": 0.58,
        "ProfitFactor": 1.65,
        "TotalTrades": 250
    },
    notes="Initial test of IBS strategy on country ETFs"
)

# Recall similar ideas
similar_ideas = agent.recall_similar_ideas(
    description="mean reversion trading strategies",
    k=5
)

# Get best ideas by metric
best_ideas = agent.recall_best_ideas(metric="Sharpe", k=5)

# Get idea performance
performance = agent.get_idea_performance(idea_id)

# Compare ideas
comparison = agent.compare_ideas([idea1_id, idea2_id, idea3_id], metric="Sharpe")

# Get context performance
context_performance = agent.get_context_performance(context_id)

# Compare contexts
context_comparison = agent.compare_contexts([context1_id, context2_id, context3_id], metric="Sharpe")

# Get visualization data
graph = agent.get_visualization_data()

# Export to JSON
agent.export_to_json("memory_graph.json")

# Import from JSON
agent.import_from_json("memory_graph.json")
```

### Advanced Usage

For more advanced usage, see the example script in `examples/memory_example.py`.

## Requirements

- Neo4j (4.4+)
- PatANN (from https://github.com/mesibo/patann)
- Python 3.8+
- sentence-transformers
- neo4j-python-driver
- requests
- numpy
- python-dotenv

## Configuration

The memory system can be configured using environment variables:

- `NEO4J_URI`: URI for the Neo4j server (default: "bolt://localhost:7687")
- `NEO4J_USER`: Username for the Neo4j server (default: "neo4j")
- `NEO4J_PASSWORD`: Password for the Neo4j server (default: "password")
- `PATANN_URL`: URL for the PatANN server (default: "http://localhost:9200")

These can be set in a `.env` file in the project root directory.

## Examples

See the `examples` directory for example scripts demonstrating how to use the memory system.

## Visualization

The memory system provides data for visualizing the knowledge graph. This data can be used with visualization libraries like Plotly, NetworkX, or Dash Cytoscape.

See the `examples/enhanced_visualizer.py` script for an example of how to visualize the memory graph using Dash Cytoscape.
