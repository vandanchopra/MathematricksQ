# ReAgent Trading System

## Overview

ReAgent is an AI-powered trading strategy development system that uses genetic algorithms to evolve trading strategies that meet specific performance targets. The system includes comprehensive market data access, web browsing capabilities for market research, and an Agent-to-Agent (A2A) communication protocol for interoperability between different AI agents.

The system:

1. Generates a population of trading strategies
2. Backtests each strategy with real market data using QuantConnect's Lean engine in Docker
3. Evaluates performance against target metrics
4. Evolves the best strategies through genetic algorithms
5. Repeats until finding strategies that meet or exceed target performance
6. Provides web search capabilities for market research
7. Accesses multiple financial data sources including Yahoo Finance, Alpha Vantage, and Polygon.io
8. Enables Agent-to-Agent (A2A) communication for enhanced AI collaboration
9. Integrates with academic research through arXiv MCP servers
10. Supports automated strategy development and backtesting on autopilot

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
4. Multiple financial data sources integration (Yahoo Finance, Alpha Vantage, Polygon.io)
5. Agent-to-Agent (A2A) communication protocol for AI interoperability
6. Academic research integration through arXiv MCP servers
7. Machine learning capabilities for strategy optimization
8. Database integration for storing and analyzing historical data and strategy results
9. Visualization tools for performance analysis

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

### Get financial data from Yahoo Finance

```bash
npm start -- get-historical-data AAPL 1y 1d
```

### Get financial data from Alpha Vantage

```bash
npm start -- alpha-vantage-daily MSFT
```

### Get financial data from Polygon.io

```bash
npm start -- ticker-details TSLA
npm start -- daily-open-close TSLA 2023-01-03
npm start -- previous-close TSLA
npm start -- aggregates TSLA 1 day 2023-01-01 2023-12-31
npm start -- ticker-news TSLA --limit=5
```

### Run academic research integration

```bash
npm start -- arxiv-search "machine learning trading"
```

### Use database functions

```bash
npm start -- store-historical-data AAPL 1y 1d
npm start -- get-historical-data-db AAPL --start=2022-01-01 --end=2022-12-31
npm start -- execute-query "SELECT * FROM historical_data LIMIT 10"
```

### Generate and backtest strategies

```bash
npm start -- generate-strategy "mean reversion SPY"
npm start -- backtest-strategy "strategy_001"
npm start -- optimize-strategy "strategy_001"
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

## System Architecture

The ReAgent Trading System is built with a modular, agent-based architecture that enables extensibility and interoperability. The system consists of the following components:

### Core Components

1. **ReAgent Core**: The central orchestrator that manages the workflow and communication between agents.

2. **Agent System**: A collection of specialized agents that perform specific tasks:
   - **BacktestAgent**: Interfaces with QuantConnect's Lean engine for strategy backtesting
   - **WebSearchAgent**: Performs web searches for market research
   - **StrategyGeneratorAgent**: Creates trading strategies based on research and parameters
   - **StrategyEvaluatorAgent**: Evaluates strategy performance against targets
   - **StrategyOptimizerAgent**: Optimizes strategies using genetic algorithms
   - **ResearchAgent**: Conducts deep research on specific topics
   - **YahooFinanceAgent**: Retrieves data from Yahoo Finance
   - **AlphaVantageAgent**: Retrieves data from Alpha Vantage API
   - **PolygonAgent**: Retrieves data from Polygon.io API
   - **AcademicSearchAgent**: Searches academic papers for trading strategies
   - **DataAnalysisAgent**: Analyzes financial data for patterns and insights
   - **VisualizationAgent**: Creates visualizations of strategy performance
   - **MLAgent**: Applies machine learning techniques to strategy optimization
   - **DatabaseAgent**: Manages database operations for storing and retrieving data

3. **Agent-to-Agent (A2A) Protocol**: A communication protocol that enables agents to exchange information and collaborate on tasks.

4. **Data Sources**:
   - Yahoo Finance for historical price data
   - Alpha Vantage for real-time and historical financial data
   - Polygon.io for comprehensive market data
   - arXiv for academic research papers
   - Web search results for market research

5. **Storage**:
   - SQLite database for storing historical data and strategy results
   - File system for storing generated strategies and backtest results

6. **Docker Environment**:
   - QuantConnect Lean engine for backtesting
   - Headless Chrome for web browsing
   - MCP servers for academic research integration

### Data Flow

1. The ReAgent Core receives a command from the user
2. The appropriate agent(s) are activated to handle the command
3. Agents communicate with each other using the A2A protocol to complete the task
4. Results are returned to the ReAgent Core and presented to the user

### Agent-to-Agent (A2A) Protocol

The A2A protocol enables agents to communicate with each other using a standardized message format. Each message includes:

- **Sender**: The agent sending the message
- **Recipient**: The agent receiving the message
- **Intent**: The purpose of the message (request, response, notification)
- **Content**: The actual data being transmitted
- **Metadata**: Additional information about the message

This protocol enables complex workflows where multiple agents collaborate to complete a task.

## Next Steps

To fully implement the system, the following steps are needed:

1. Run the full system with real data across 15 years
2. Allow the system to continue generating and evolving strategies until it finds ones that meet all target criteria
3. Implement a monitoring system to track the progress of the genetic algorithm
4. Enhance the A2A protocol to support more complex agent interactions
5. Integrate additional MCP servers for expanded research capabilities
6. Implement real-time trading capabilities through broker APIs

## Generated Strategies

The system generates Python strategies that can be run with QuantConnect's Lean engine. Each strategy includes:

- Technical indicators (SMA, EMA, MACD, RSI, etc.)
- Entry and exit rules based on indicator signals
- Risk management with stop-loss and take-profit levels

## For AI Coding Agents

This section provides important information for AI coding agents working with the ReAgent Trading System.

### Project Structure

- **src/trading/reagent.ts**: The main ReAgent class that orchestrates the system
- **src/trading/agents/**: Directory containing all agent implementations
  - **index.ts**: Exports all agents
  - **agent.ts**: Base Agent class
  - **backtest-agent.ts**: BacktestAgent implementation
  - **web-search-agent.ts**: WebSearchAgent implementation
  - **strategy-generator-agent.ts**: StrategyGeneratorAgent implementation
  - **yahoo-finance-agent.ts**: YahooFinanceAgent implementation
  - **alpha-vantage-agent.ts**: AlphaVantageAgent implementation
  - **polygon-agent.ts**: PolygonAgent implementation
  - ... (other agent implementations)
- **src/trading/models/**: Data models and interfaces
- **src/trading/utils/**: Utility functions
- **src/cli.ts**: Command-line interface implementation
- **docker/**: Docker configuration files

### Key Interfaces and Classes

```typescript
// Base Agent interface
interface Agent {
  name: string;
  execute(params: any): Promise<any>;
  communicate(message: A2AMessage): Promise<A2AMessage>;
}

// Agent-to-Agent Message format
interface A2AMessage {
  sender: string;
  recipient: string;
  intent: 'request' | 'response' | 'notification';
  content: any;
  metadata: {
    timestamp: number;
    id: string;
    [key: string]: any;
  };
}

// ReAgent main class
class ReAgent {
  // Agents
  private backtestAgent: BacktestAgent;
  private webSearchAgent: WebSearchAgent;
  private strategyGeneratorAgent: StrategyGeneratorAgent;
  private yahooFinanceAgent: YahooFinanceAgent;
  private alphaVantageAgent: AlphaVantageAgent;
  private polygonAgent: PolygonAgent;
  // ... other agents

  // Methods for interacting with agents
  public async generateStrategy(prompt: string): Promise<any>;
  public async backtestStrategy(strategyName: string): Promise<any>;
  public async optimizeStrategy(strategyName: string): Promise<any>;
  public async searchWeb(query: string): Promise<any>;
  // ... other methods
}
```

### Working with the System

1. **Adding a New Agent**:
   - Create a new file in `src/trading/agents/`
   - Implement the Agent interface
   - Add the agent to the exports in `src/trading/agents/index.ts`
   - Initialize the agent in the ReAgent constructor
   - Add methods to the ReAgent class to interact with the agent

2. **Adding a New Data Source**:
   - Create a new agent for the data source
   - Implement the necessary API calls
   - Add methods to the ReAgent class to access the data
   - Update the CLI to support commands for the new data source

3. **Extending the A2A Protocol**:
   - The A2A protocol is implemented in the base Agent class
   - Messages are sent and received through the `communicate` method
   - The protocol can be extended to support new message types and workflows

4. **Environment Variables**:
   - API keys and configuration settings are stored in environment variables
   - The system uses dotenv to load environment variables from a .env file
   - Required environment variables include:
     - `OPENAI_API_KEY`: OpenAI API key for AI capabilities
     - `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key
     - `POLYGON_API_KEY`: Polygon.io API key
     - `OPENROUTER_API_KEY`: OpenRouter API key for fallback LLM access

5. **Error Handling**:
   - All agent methods should handle errors gracefully
   - Use try/catch blocks to catch and log errors
   - Return meaningful error messages to the user

### Common Patterns

1. **Agent Communication**:
```typescript
// Example of agent communication
const message: A2AMessage = {
  sender: 'StrategyGeneratorAgent',
  recipient: 'BacktestAgent',
  intent: 'request',
  content: { strategyName: 'strategy_001' },
  metadata: { timestamp: Date.now(), id: uuidv4() }
};

const response = await this.backtestAgent.communicate(message);
```

2. **API Calls**:
```typescript
// Example of API call pattern
async function getTickerDetails(ticker: string): Promise<any> {
  try {
    const url = `${this.baseUrl}/v3/reference/tickers/${ticker}?apiKey=${this.apiKey}`;
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    console.error(`Error getting ticker details for ${ticker}:`, error);
    return { error: error.message };
  }
}
```

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
