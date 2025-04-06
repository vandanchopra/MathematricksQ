# MathematricksQ: AI-Powered Algorithmic Trading System

MathematricksQ is an advanced algorithmic trading system that leverages AI agents to research, develop, test, and improve trading strategies. The system uses the QuantConnect Lean engine for backtesting and supports both local and cloud-based LLM integration.

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
└── data/                          # Trading data
```

## Features

- **Flexible LLM Integration**: Supports both local (Ollama) and cloud (OpenAI) LLM providers
- **Systematic Research**: AI-driven research and idea generation
- **Multi-idea Extraction**: Extracts multiple detailed trading ideas per paper with pseudocode
- **PDF and HTML Parsing**: Downloads, saves, and extracts content from research papers
- **Robust Backtesting**: Prevents overfitting through smart data splitting
- **Automated Analysis**: Comprehensive performance analysis and improvement suggestions
- **Version Control**: Tracks strategy evolution and changes
- **Human Oversight**: Includes pause points for human guidance

## Usage

The system can be run in two modes:

1. New Strategy Development:
```bash
python run.py --new
```

2. Existing Strategy Improvement:
```bash
python run.py --strategy_path "Strategies/StrategyName"
```

## Configuration

The system is configured through YAML files:

- `system_config.yaml`: Main configuration file
  - LLM provider settings
  - Agent-specific configurations
  - Tool settings
  - System parameters

## Example Strategy

The repository includes an example SMA (Simple Moving Average) strategy that demonstrates:
- Strategy initialization and setup
- Data handling and indicator usage
- Trading logic implementation
- Position management

## Development Status

### In Progress
- [ ] Strategy developer agent
- [ ] CLI interface
- [ ] Reporting system

### Completed
- [x] Core LLM integration
- [x] Backtester agent implementation
- [x] Backtest analyzer agent
- [x] Base agent framework
- [x] Research agent implementation (multi-paper, multi-idea extraction, PDF saving)

## Requirements

- Python 3.8+
- QuantConnect Lean CLI
- Required Python packages in requirements.txt
- Local or cloud LLM access

## Testing

The system includes comprehensive tests:
- Unit tests for individual agents
- Integration tests for agent interactions
- Performance benchmarks

### Research Agent Testing
- Run `python AgenticDeveloper/tests/test_research_agent.py`
- Downloads and analyzes multiple new papers
- Extracts multiple trading ideas per paper with detailed descriptions and pseudocode
- Saves ideas with metadata and local PDF paths
- Prints saved ideas to console for verification