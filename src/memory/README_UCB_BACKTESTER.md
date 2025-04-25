# UCB-Based Backtester

This module implements a UCB (Upper Confidence Bound) based backtester that learns over time by balancing exploration and exploitation. It uses real backtests to evaluate trading ideas and stores the results in a Neo4j graph database.

## Overview

The UCB algorithm is a popular approach in reinforcement learning for balancing exploration (trying new ideas) and exploitation (focusing on ideas that have performed well). It's particularly useful in scenarios where you want to maximize the cumulative reward over time.

The UCB score for an idea is calculated as:

```
UCB = avgScore + c * sqrt(ln(totalTests) / testCount)
```

Where:
- `avgScore` = totalScore / testCount (average score of the idea)
- `totalTests` = sum of testCount over all ideas (total number of backtests run)
- `testCount` = number of times this idea has been tested
- `c` = exploration constant (controls the balance between exploration and exploitation)

The score for each backtest is calculated as:

```
score = 0.5 * Sharpe + 0.3 * CAGR - 0.2 * MaxDrawdown
```

## Components

1. **ucb_backtester.py**: Main script that implements the UCB algorithm and runs backtests.
2. **backtester_agent.py**: Mock implementation of a backtester agent (replace with your actual backtester).
3. **initialize_ucb.py**: Script to initialize UCB properties in Neo4j.
4. **dashboard/enhanced_dashboard.py**: Dashboard with UCB visualization.

## Setup

1. Initialize the UCB properties in Neo4j:

```bash
python src/memory/initialize_ucb.py
```

2. Run the UCB backtester:

```bash
python src/memory/ucb_backtester.py
```

3. Start the dashboard:

```bash
python src/memory/dashboard/enhanced_dashboard.py
```

## Neo4j Schema

The UCB backtester uses the following Neo4j schema:

- **Idea**: Trading idea node
  - `id`: Unique identifier
  - `description`: Description of the idea
  - `testCount`: Number of times this idea has been tested
  - `totalScore`: Sum of scores from all backtests

- **Backtest**: Backtest node
  - `id`: Unique identifier
  - `metric_Sharpe`: Sharpe ratio
  - `metric_CAGR`: Compound Annual Growth Rate
  - `metric_MaxDrawdown`: Maximum drawdown
  - `metric_WinRate`: Win rate
  - `metric_TotalTrades`: Total number of trades
  - `metric_ProfitFactor`: Profit factor
  - `date`: Date of the backtest

- **Context**: Market context node
  - `id`: Unique identifier
  - `market`: Market (e.g., BTC, ETH)
  - `timeframe`: Timeframe (e.g., DAILY, HOURLY)

- **Scenario**: Scenario node
  - `id`: Unique identifier
  - `description`: Description of the scenario

- **Relationships**:
  - `(Idea)-[:TESTED_IN]->(Backtest)`: Idea was tested in a backtest
  - `(Backtest)-[:EXECUTED_IN]->(Context)`: Backtest was executed in a context
  - `(Backtest)-[:APPLIES_TO]->(Scenario)`: Backtest applies to a scenario
  - `(Idea)-[:SUBIDEA_OF]->(Scenario)`: Idea is a sub-idea of a scenario

## Dashboard

The dashboard provides visualizations of the UCB scores and backtest history:

1. **Graph Explorer Tab**: Visualize the memory graph with ideas, backtests, contexts, and scenarios.
2. **UCB Visualization Tab**: View UCB scores for each idea and backtest history.

## Customization

To customize the UCB backtester for your needs:

1. Replace the mock backtester in `backtester_agent.py` with your actual backtester.
2. Adjust the score formula in `ucb_backtester.py` to match your trading strategy evaluation criteria.
3. Modify the exploration constant in the UCB formula to control the balance between exploration and exploitation.

## References

- [Upper Confidence Bound Algorithm](https://en.wikipedia.org/wiki/Multi-armed_bandit#Upper_confidence_bound_algorithm)
- [Multi-Armed Bandit Problem](https://en.wikipedia.org/wiki/Multi-armed_bandit)
- [Reinforcement Learning: An Introduction](http://incompleteideas.net/book/the-book-2nd.html) by Richard S. Sutton and Andrew G. Barto
