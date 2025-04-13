# MathematricksQ: AI-Powered Algorithmic Trading System

MathematricksQ is an advanced algorithmic trading system that leverages AI agents to research, develop, test, and improve trading strategies. The system uses the QuantConnect Lean engine for backtesting and supports both local and cloud-based LLM integration.

## ReAgent Trading System

The `reagent-trading` directory contains the ReAgent trading system, which is an AI-powered trading strategy development and optimization system with web browsing capabilities. It uses the Agent2Agent (A2A) protocol for enhanced communication and interoperability between different agent components.

### ReAgent Features

- AI-powered strategy generation
- Backtesting with real market data using QuantConnect's Lean engine in Docker
- Strategy evaluation and scoring
- Strategy optimization using genetic algorithms
- Performance metrics tracking
- Web browsing capabilities for market research
- Search functionality for trading strategies and market information
- Agent2Agent (A2A) protocol integration for enhanced decision making

### Getting Started with ReAgent

To get started with the ReAgent trading system, navigate to the `reagent-trading` directory and follow the instructions in the README.md file.

```bash
cd reagent-trading
npm install
npm run build
npm start
```

## System Architecture

The system is composed of multiple specialized agents working together:

### 1. Idea Researcher Agent
- Searches arXiv for new trading strategy research papers (fetches 5-6 per run)
- Downloads original PDFs and saves them in `AgenticDeveloper/research_papers/`
- Extracts and analyzes PDF/HTML content using LLMs
- Extracts **multiple distinct trading ideas** per paper with detailed descriptions and pseudocode
- Saves ideas in `research_ideas.json` with metadata:
  - Description, pseudocode, source title, authors, URL, local PDF path
- Skips already-processed papers to avoid duplicates
- Uses chunk-based targeted prompts and retries to improve extraction quality
- Maintains a master list of all extracted ideas

### 2. Backtest Analyzer Agent
- Analyzes backtest results and performance metrics
- Generates detailed performance assessments
- Provides specific improvement suggestions
- Analyzes trade patterns and risk metrics

### 3. Strategy Developer Agent
- Creates new trading strategies from research
- Improves existing strategies based on analysis
- Integrates with version control
- Implements risk management rules

### 4. Backtester Agent
- Manages strategy backtesting through Lean CLI
- Implements train/test data splitting
- Prevents overfitting through period selection
- Stores comprehensive backtest results

### 5. Reporting Agent
- Provides real-time progress updates
- Maintains system logs
- Facilitates human interaction points
- Tracks performance metrics

## Project Structure

```
MathematricksQ/
├── AgenticDeveloper/               # Main agent system
│   ├── agents/                     # Agent implementations
│   ├── tools/                      # Shared tools
│   │   ├── web_tools.py            # arXiv search, PDF, and HTML tools
│   ├── config/                     # System configuration
│   ├── research_ideas/             # Research summaries and ideas JSON
│   ├── research_papers/            # Downloaded original research PDFs
│   └── tests/                      # Test suite
├── Strategies/                     # Trading strategies
│   └── SMAStrategy/               # Example strategy
│       ├── main.py                # Strategy implementation
│       ├── config.json            # Strategy config
│       └── backtests/             # Backtest results
├── reagent-trading/                # ReAgent trading system
│   ├── src/                        # Source code
│   │   ├── trading/                # Trading logic
│   │   │   ├── agents/             # Agent implementations
│   │   │   ├── config.ts           # Configuration
│   │   │   ├── types.ts            # Type definitions
│   │   │   └── reagent.ts          # Main ReAgent class
│   ├── docker/                     # Docker configuration
│   ├── strategies/                 # Trading strategies
│   ├── results/                    # Backtest results
│   └── tests/                      # Test suite
└── data/                          # Trading data
```

## Features

### AgenticDeveloper Features

- **Flexible LLM Integration**: Supports both local (Ollama) and cloud (OpenAI) LLM providers
- **Systematic Research**: AI-driven research and idea generation
- **Multi-idea Extraction**: Extracts multiple detailed trading ideas per paper with pseudocode
- **PDF and HTML Parsing**: Downloads, saves, and extracts content from research papers
- **Robust Backtesting**: Prevents overfitting through smart data splitting
- **Automated Analysis**: Comprehensive performance analysis and improvement suggestions
- **Version Control**: Tracks strategy evolution and changes
- **Human Oversight**: Includes pause points for human guidance

### ReAgent Features

- **Agent2Agent Protocol**: Enhanced communication and interoperability between agents
- **Autopilot Strategy Development**: Autonomous generation and backtesting of strategies
- **Docker Integration**: Runs QuantConnect's Lean engine in Docker containers
- **Web Browsing Capabilities**: Searches for market information and trading strategies
- **Push Notifications**: Real-time updates on trading activities
- **Recursive Questioning**: Improved decision making through clarifying questions
- **Backtracking**: Automatic recovery from low-confidence or contradictory states
- **Genetic Optimization**: Evolves strategies to meet performance targets

## Usage

### AgenticDeveloper Usage

The AgenticDeveloper system can be run in two modes:

1. New Strategy Development:
```bash
python run.py --new
```

2. Existing Strategy Improvement:
```bash
python run.py --strategy_path "Strategies/StrategyName"
```

### ReAgent Usage

The ReAgent trading system can be run in several modes:

1. Run the full ReAgent system:
```bash
cd reagent-trading
npm start
```

2. Search for market information:
```bash
cd reagent-trading
npm start -- search "moving average crossover strategy performance"
```

3. Research a specific strategy type:
```bash
cd reagent-trading
npm start -- research "mean reversion"
```

4. Run a backtest on a specific strategy:
```bash
cd reagent-trading
./run_lean_cli.sh backtest sma_crossover
```

## Configuration

### AgenticDeveloper Configuration

The AgenticDeveloper system is configured through YAML files:

- `system_config.yaml`: Main configuration file
  - LLM provider settings
  - Agent-specific configurations
  - Tool settings
  - System parameters

### ReAgent Configuration

The ReAgent trading system is configured through several files:

- `src/trading/config.ts`: Main configuration file
  - Trading targets (CAGR, Sharpe ratio, etc.)
  - Backtest parameters
  - System settings

- `docker/docker-compose.yml`: Docker configuration
  - Lean engine configuration
  - Browser service configuration
  - Web server configuration

- `config/a2a_enhanced_config.json`: A2A protocol configuration
  - A2A endpoints
  - Authentication settings
  - Push notification settings

## Example Strategies

### AgenticDeveloper Example Strategy

The repository includes an example SMA (Simple Moving Average) strategy in the `Strategies/SMAStrategy` directory that demonstrates:
- Strategy initialization and setup
- Data handling and indicator usage
- Trading logic implementation
- Position management

### ReAgent Example Strategy

The ReAgent trading system includes an example SMA crossover strategy in the `reagent-trading/strategies/sma_crossover` directory that demonstrates:
- Strategy initialization with fast and slow moving averages
- Buy and sell signal generation
- Risk management with stop loss and take profit
- Backtesting with QuantConnect's Lean engine in Docker

## Development Status

### AgenticDeveloper Status

#### In Progress
- [ ] Strategy developer agent
- [ ] CLI interface
- [ ] Reporting system

#### Completed
- [x] Core LLM integration
- [x] Backtester agent implementation
- [x] Backtest analyzer agent
- [x] Base agent framework
- [x] Research agent implementation (multi-paper, multi-idea extraction, PDF saving)

### ReAgent Status

#### In Progress
- [ ] Full integration with AgenticDeveloper
- [ ] Enhanced A2A protocol features
- [ ] Advanced strategy optimization

#### Completed
- [x] Docker integration for Lean CLI
- [x] Web browsing capabilities
- [x] A2A protocol integration
- [x] Autopilot strategy development
- [x] Backtesting with QuantConnect's Lean engine
- [x] Strategy evaluation and scoring
- [x] Push notification system

## Requirements

### AgenticDeveloper Requirements

- Python 3.8+
- QuantConnect Lean CLI
- Required Python packages in requirements.txt
- Local or cloud LLM access

### ReAgent Requirements

- Node.js 14+
- npm
- Docker and Docker Compose
- QuantConnect Lean CLI
- Python 3.8+ (for running tests)

## Testing

### AgenticDeveloper Testing

The AgenticDeveloper system includes comprehensive tests:
- Unit tests for individual agents
- Integration tests for agent interactions
- Performance benchmarks

#### Research Agent Testing
- Run `python AgenticDeveloper/tests/test_research_agent.py`
- Downloads and analyzes multiple new papers
- Extracts multiple trading ideas per paper with detailed descriptions and pseudocode
- Saves ideas with metadata and local PDF paths
- Prints saved ideas to console for verification

### ReAgent Testing

The ReAgent trading system includes comprehensive integration tests:

```bash
cd reagent-trading
./run_integration_tests.sh
```

The tests include:
- Lean CLI integration tests
- Web browsing capability tests
- Full ReAgent system tests
- Docker integration tests

You can also run individual tests:

```bash
python3 reagent-trading/tests/test_lean_cli.py -v
python3 reagent-trading/tests/test_web_browsing.py -v
python3 reagent-trading/tests/test_reagent_system.py -v
```