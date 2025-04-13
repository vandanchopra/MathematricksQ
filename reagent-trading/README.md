# ReAgent Trading System

## Overview

ReAgent is an AI-powered trading strategy development system that uses genetic algorithms to evolve trading strategies that meet specific performance targets. The system now includes web browsing capabilities for market research and strategy discovery.

The system:

1. Generates a population of trading strategies
2. Backtests each strategy with real market data using QuantConnect's Lean engine in Docker
3. Evaluates performance against target metrics
4. Evolves the best strategies through genetic algorithms
5. Repeats until finding strategies that meet or exceed target performance
6. Provides web search capabilities for market research

## Performance Targets

The system is configured to find strategies that meet or exceed the following performance criteria:

- **CAGR (Compound Annual Growth Rate)**: Above 25%
- **Sharpe Ratio**: More than 1.0 (with a risk-free return of 5%)
- **Maximum Drawdown**: 20% or less
- **Average Profit per Trade**: At least 0.75%

## Implementation Status

The system has been configured with the target performance metrics and can generate valid trading strategies. It now includes:

1. Docker integration for running QuantConnect's Lean engine
2. Web browsing capabilities for market research and strategy discovery
3. Command-line interface for searching and researching trading strategies

## Usage

### Run the full ReAgent system

```bash
npm start
```

### Search for market information

```bash
npm start -- search "moving average crossover strategy performance"
```

### Research a specific strategy type

```bash
npm start -- research "mean reversion"
```

## Docker Setup

The system uses Docker containers for:

1. Running QuantConnect's Lean engine for backtesting
2. Running a headless Chrome browser for web search and research

To set up the Docker containers:

```bash
cd docker
docker-compose build
```

### Running Lean CLI in Docker

The system includes a script to run Lean CLI in Docker. This script allows you to create and backtest strategies without installing Lean CLI locally.

```bash
# Create a new strategy
./run_lean_cli.sh create-strategy my_strategy

# Run a backtest on a strategy
./run_lean_cli.sh backtest my_strategy

# List all available strategies
./run_lean_cli.sh list

# Start the web browser for market research
./run_lean_cli.sh browse
```

### Viewing Backtest Results

To view the backtest results, you can start a web server:

```bash
./start_web_server.sh
```

Then open your browser and navigate to http://localhost:8080/

## Testing

The system includes comprehensive integration tests to verify that all components work together correctly.

```bash
# Run all integration tests
./run_integration_tests.sh

# Run specific tests
python3 tests/test_lean_cli.py -v
python3 tests/test_web_browsing.py -v
python3 tests/test_reagent_system.py -v
```

See the [tests README](tests/README.md) for more information.

## Next Steps

To fully implement the system, the following steps are needed:

1. Run the full system with real data across 15 years
2. Allow the system to continue generating and evolving strategies until it finds ones that meet all target criteria
3. Implement a monitoring system to track the progress of the genetic algorithm

## Generated Strategies

The system generates Python strategies that can be run with QuantConnect's Lean engine. Each strategy includes:

- Technical indicators (SMA, EMA, MACD, RSI, etc.)
- Entry and exit rules based on indicator signals
- Risk management with stop-loss and take-profit levels

## Example Strategy

```python
# AI-Generated Trading Strategy

from AlgorithmImports import *
import numpy as np

class Strategy_Example(QCAlgorithm):
    def Initialize(self):
        # Set start date, end date, and initial cash
        self.SetStartDate(2010, 4, 17)
        self.SetEndDate(2025, 4, 13)
        self.SetCash(100000)

        # Add equity
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol

        # Initialize indicators
        self.ema = self.EMA("SPY", 46)
        self.macd = self.MACD("SPY", 22, 22, 13)
        self.atr = self.ATR("SPY", 7)

        # Set warm-up period
        self.SetWarmUp(TimeSpan.FromDays(100))

    def OnData(self, data):
        # Skip if we're still in warm-up or don't have data
        if self.IsWarmingUp or not data.ContainsKey(self.spy):
            return

        try:
            # Entry logic
            if not self.Portfolio.Invested:
                if self.ema.Current.Value > data[self.spy].Close and self.macd.Current.Value > 0:
                    self.SetHoldings(self.spy, 1.0)
                    self.Log(f"Buy signal: Close price {data[self.spy].Close}")
            # Exit logic
            else:
                if self.ema.Current.Value < data[self.spy].Close or self.macd.Current.Value < 0:
                    self.Liquidate(self.spy)
                    self.Log(f"Sell signal: Close price {data[self.spy].Close}")

            # Risk management
            self.ManageRisk()

        except Exception as e:
            self.Log(f"Error in OnData: {str(e)}")

    def ManageRisk(self):
        if self.Portfolio.Invested:
            holding = self.Portfolio[self.spy]

            # Implement stop loss
            if holding.Price < holding.AveragePrice * (1 - 0.03):
                self.Liquidate(self.spy)
                self.Log("Stop loss triggered")
                return

            # Implement take profit
            if holding.Price > holding.AveragePrice * (1 + 0.09):
                self.Liquidate(self.spy)
                self.Log("Take profit triggered")
                return
```
