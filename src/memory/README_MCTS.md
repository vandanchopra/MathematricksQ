# Monte Carlo Tree Search (MCTS) for Trading Strategy Optimization

This module implements Monte Carlo Tree Search (MCTS) to systematically explore and optimize trading strategies. It treats each idea as a node in a tree and uses Upper Confidence Bound (UCB) to balance exploration and exploitation.

## Overview

MCTS is a heuristic search algorithm that has been successfully applied to decision-making problems, most notably in games like Go and Chess. In this implementation, we adapt MCTS to the domain of trading strategy optimization.

The key components of MCTS are:
1. **Selection**: Using UCB to select the most promising node to explore
2. **Expansion**: Creating a new child node (a variation of the current strategy)
3. **Simulation**: Running a backtest for the new node and getting a reward
4. **Backpropagation**: Updating the statistics of all nodes in the path from the new node to the root

## Components

1. **mcts.py**: Main implementation of the MCTS algorithm
2. **run_mcts.py**: Command-line interface for running MCTS
3. **dashboard/enhanced_dashboard.py**: Dashboard with MCTS visualization

## Usage

### Running MCTS from the Command Line

```bash
python src/memory/run_mcts.py --idea-id <idea_id> --iterations 10 --exploration 1.0 --output best_idea.json
```

Parameters:
- `--idea-id`: ID of the root idea to start the search from
- `--iterations`: Number of iterations to run (default: 10)
- `--exploration`: Exploration constant for UCB (default: 1.0)
- `--output`: Output file for the best child (optional)

### Visualizing MCTS Trees in the Dashboard

1. Start the dashboard:
```bash
python src/memory/dashboard/enhanced_dashboard.py
```

2. Open the dashboard in your browser:
```
http://localhost:8054
```

3. Go to the "MCTS Visualization" tab
4. Select a root idea from the dropdown
5. Adjust the tree depth using the slider
6. Click "Refresh MCTS Tree" to visualize the tree

## How It Works

### 1. Selection

The selection phase uses the UCB1 formula to select the most promising node to explore:

```
UCB1 = Q + c * sqrt(ln(N_parent) / N_child)
```

Where:
- `Q` is the average reward of the node
- `c` is the exploration constant
- `N_parent` is the visit count of the parent node
- `N_child` is the visit count of the child node

### 2. Expansion

The expansion phase creates a new child node by varying either the context (market, timeframe) or the parameters of the current node.

### 3. Simulation

The simulation phase runs a backtest for the new node using your existing backtester agent and computes a score based on the backtest metrics:

```
score = 0.5 * Sharpe + 0.3 * CAGR - 0.2 * MaxDrawdown
```

### 4. Backpropagation

The backpropagation phase updates the statistics of all nodes in the path from the new node to the root:

```
node.N += 1
node.W += score
```

## Integration with Memory Graph

The MCTS implementation integrates with your existing memory graph:

- Each node in the MCTS tree corresponds to an Idea node in the memory graph
- Each simulation creates a Backtest node and connects it to the Idea node with a TESTED_IN relationship
- Each Backtest node is connected to a Context node with an EXECUTED_IN relationship
- The dashboard visualizes the MCTS tree using the memory graph data

## Customization

You can customize the MCTS implementation in several ways:

1. **Scoring Function**: Modify the `compute_score` function in `mcts.py` to use a different formula for computing the score
2. **Expansion Strategy**: Modify the `expand` function in `mcts.py` to use a different strategy for creating new child nodes
3. **Simulation Strategy**: Modify the `simulate` function in `mcts.py` to use a different strategy for running backtests
4. **UCB Formula**: Modify the `select` function in `mcts.py` to use a different formula for selecting nodes

## References

- [Monte Carlo Tree Search: A New Framework for Game AI](https://www.aaai.org/Papers/AIIDE/2008/AIIDE08-036.pdf)
- [A Survey of Monte Carlo Tree Search Methods](https://ieeexplore.ieee.org/document/6145622)
- [Bandit Algorithms for Website Optimization](https://www.oreilly.com/library/view/bandit-algorithms-for/9781449341565/)
