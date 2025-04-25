# Hybrid Memory System

This module implements a hybrid memory system for trading strategies, combining Neo4j for graph relationships and PatANN for vector embeddings.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Components

The memory system consists of the following components:

1. **Interface**: Defines the protocol for memory backends
2. **PatANN Backend**: Vector database for similarity search
3. **Neo4j Backend**: Graph database for relationships and metrics
4. **Hybrid Backend**: Combines both backends for optimal performance
5. **Memory Agent**: Provides a simplified interface for working with the memory system
6. **Dashboard**: Interactive visualization of the memory knowledge graph
7. **Reports**: Automated generation of strategy performance reports

## Setup

### PatANN Setup

You have two options for setting up PatANN:

#### Option 1: Using Docker Compose

The easiest way to get started is to use the Docker Compose file provided in this repository:

```bash
docker-compose up -d
```

This will start both Neo4j and PatANN servers.

#### Option 2: Local Installation

Alternatively, you can set up PatANN locally:

1. Clone the PatANN repository:

```bash
git clone https://github.com/mesibo/patann.git
```

2. Copy the `patann_server.py` file from this repository to your project directory.

3. Install the required packages:

```bash
pip install fastapi uvicorn
```

4. Run the server:

```bash
python patann_server.py
```

The PatANN server will be available at http://localhost:9200

### Neo4j Setup

1. Start the Neo4j server:

```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5.15
```

2. The Neo4j browser will be available at http://localhost:7474

## Usage

### Using the HybridMemory Class

```python
from src.memory import HybridMemory

# Initialize the memory system
memory = HybridMemory(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
    patann_url="http://localhost:9200",
    model_name="all-MiniLM-L6-v2"
)

# Store a context
memory.store_context("btc_daily", "BTC/USD", "1d")

# Store an idea
memory.store_idea("idea1", "Buy when RSI is below 30", ["btc_daily"])

# Store a backtest
memory.store_backtest("bt1", {"Sharpe": 1.5, "CAGR": 0.25}, "idea1", "btc_daily")

# Query similar ideas
embedding = memory.vector_backend._get_embedding("Buy when price is low")
similar_ideas = memory.query_similar_ideas(embedding, "btc_daily", 5)

# Get recommendations
recommendations = memory.recommend_ideas(embedding, "btc_daily", 3)
```

### Using the Memory Agent

The Memory Agent provides a simplified interface for working with the memory system:

```python
from src.memory.memory_agent import MemoryAgent

# Initialize the memory agent
memory_agent = MemoryAgent(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
    patann_url="http://localhost:9200",
    model_name="all-MiniLM-L6-v2"
)

# Store a context
result = memory_agent.run(
    "store_context",
    context_id="btc_daily",
    market="BTC/USD",
    timeframe="1d"
)

# Store an idea
result = memory_agent.run(
    "store_idea",
    idea_name="RSI Oversold",
    description="Buy when RSI is below 30",
    context_ids=["btc_daily"]
)

# Store a backtest
result = memory_agent.run(
    "store_backtest",
    backtest_id="bt1",
    metrics={"Sharpe": 1.5, "CAGR": 0.25},
    idea_id="idea1",
    context_id="btc_daily"
)

# Query similar ideas
result = memory_agent.run(
    "query_similar_ideas",
    query_text="Buy when price is low",
    context_id="btc_daily",
    top_k=5
)

# Get recommendations
result = memory_agent.run(
    "recommend_ideas",
    strategy_text="This strategy uses RSI to identify oversold conditions",
    context_id="btc_daily",
    top_k=3
)
```

## Schema

The memory system uses the following schema:

- **Idea**: A trading idea with a description
- **Scenario**: A specific implementation of an idea
- **Context**: A market and timeframe combination
- **Backtest**: Results of testing an idea in a context

### Relationships

- Idea -[APPLIES_IN]-> Context
- Scenario -[SUBIDEA_OF]-> Idea
- Scenario -[APPLIES_IN]-> Context
- Idea -[TESTED_IN]-> Backtest
- Backtest -[EXECUTED_IN]-> Context

## Advanced Features

The hybrid memory system provides several advanced features:

1. **Vector Similarity Search**: Find similar ideas based on semantic meaning
2. **Graph Relationship Queries**: Find related ideas, scenarios, and backtests
3. **Metric-Based Ranking**: Rank ideas based on backtest metrics
4. **Hybrid Recommendations**: Combine vector similarity with graph metrics
5. **Interactive Visualization**: Explore the knowledge graph with dynamic filtering and multiple layouts
6. **Automated Reporting**: Generate and schedule reports on strategy performance
7. **UCB-Based Backtesting**: Use Upper Confidence Bound algorithm to balance exploration and exploitation
8. **MCTS Visualization**: Visualize Monte Carlo Tree Search trees for strategy optimization
9. **Automated Idea Expansion**: Automatically create variations of the best ideas using PatANN similarity search

## Examples

The `examples` directory contains example scripts demonstrating how to use the hybrid memory system:

1. **test_memory.py**: Tests the core functionality of the hybrid memory system
2. **memory_agent_example.py**: Demonstrates how to use the memory agent
3. **enhanced_visualizer.py**: Shows how to visualize the memory knowledge graph

See the [Examples README](examples/README.md) for more information.

## Dashboard

The dashboard provides an interactive visualization of the memory knowledge graph, allowing you to explore relationships between ideas, backtests, contexts, and scenarios.

### Features

- **Dynamic Filtering**: Filter the graph by context, idea, node type, or relationship type
- **Multiple Layouts**: Choose from various layout algorithms to better visualize your graph
- **Interactive Exploration**: Hover over nodes to see details, click to view properties
- **Metrics Analysis**: Analyze strategy performance across different contexts
- **UCB Visualization**: Visualize the UCB scores of ideas with adjustable exploration constant
- **MCTS Visualization**: Visualize Monte Carlo Tree Search trees for strategy optimization

### Usage

```bash
python run_dashboard.py
```

See the [Dashboard README](dashboard/README.md) for more information.

## Automated Backtester

The automated backtester combines the UCB backtester, PatANN similarity search, and real backtester to automate the process of selecting ideas, running backtests, and creating variations of the best ideas.

### Features

- **UCB-Based Selection**: Use Upper Confidence Bound algorithm to balance exploration and exploitation
- **Real Backtesting**: Run backtests on different markets and timeframes using QuantConnect Lean
- **Automated Idea Expansion**: Automatically create variations of the best ideas using PatANN similarity search
- **Relationship Creation**: Automatically create SUBIDEA_OF relationships between similar ideas

### Usage

```bash
python automated_backtester.py --iterations 10 --exploration 1.0 --sleep 5
```

### Command Line Arguments

- `--iterations`: Number of iterations to run (default: 10)
- `--exploration`: Exploration constant for UCB (default: 1.0)
- `--sleep`: Time to sleep between iterations in seconds (default: 5)
- `--no-variations`: Do not create variations of the best ideas
- `--num-variations`: Number of variations to create (default: 3)
- `--no-relationships`: Do not create SUBIDEA_OF relationships

## Reports

The reports module provides tools for generating and scheduling reports based on the memory knowledge graph.

### Features

- **Weekly Strategy Reports**: Generate reports of top-performing trading strategies
- **Email Delivery**: Send reports via email to specified recipients
- **Scheduled Execution**: Run reports on a schedule using cron jobs

### Usage

```bash
python src/memory/reports/weekly_report.py
```

See the [Reports README](reports/README.md) for more information.
