# MathematricksQ Examples

This directory contains example scripts demonstrating how to use the MathematricksQ system.

## Memory System Examples

### memory_example.py

This example demonstrates how to use the hybrid memory system with the agents:

1. Sets up memory contexts for different markets and timeframes
2. Researches trading ideas using the IdeaResearcherAgent
3. Queries similar ideas from memory
4. Gets recommendations for a strategy in a specific context

To run the example:

```bash
python examples/memory_example.py
```

### test_memory.py

This example tests the core functionality of the hybrid memory system without using agents:

1. Stores contexts, ideas, and backtests directly in the memory system
2. Queries similar ideas based on a text description
3. Gets recommendations based on a text description
4. Queries top ideas by metrics

To run the example:

```bash
python examples/test_memory.py
```

### backtester_memory_example.py

This example demonstrates how to use the backtester agent with memory integration:

1. Sets up memory contexts for different markets and timeframes
2. Runs a backtest for a strategy and stores the results in memory
3. Analyzes the backtest and stores the analysis in memory
4. Queries similar strategies from memory

To run the example:

```bash
python examples/backtester_memory_example.py
```

## Prerequisites

Before running the examples, make sure you have:

1. Installed all required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Started the PatANN server:
   ```bash
   docker run -d --name patann-dev -p 9200:9200 patann/patann-dev
   ```

3. Started the Neo4j server:
   ```bash
   docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.15
   ```

## Environment Variables

The examples use the following environment variables:

- `NEO4J_URI`: URI for the Neo4j server (default: `bolt://localhost:7687`)
- `NEO4J_USER`: Username for the Neo4j server (default: `neo4j`)
- `NEO4J_PASSWORD`: Password for the Neo4j server (default: `password`)
- `PATANN_URL`: URL for the PatANN server (default: `http://localhost:9200`)
- `OPENROUTER_API_KEY`: API key for OpenRouter (required for LLM access)

You can set these variables in a `.env` file in the project root directory.
