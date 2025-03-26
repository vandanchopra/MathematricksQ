# AgenticDeveloper Project Tasks

## HUMAN NOTES
I want to make an agentic system that does the following: It is a algorithmic trading agent system with the following parts (agents) using an AI agent framework.
0) [COMPLETED] use Langchain for the agent network. use quantconnect for backtesting and running queues.
1) [COMPLETED] The LLM brain of the system should work with a local deployed LLM using ollama or using API. The details will be in the agentsystem config file.
2) Tools: Lets have a tools folder, which all the agents can use. The tools we'll need will be : PDF reader, internet browser, internet search
3) The system is run from the CLI, and takes a flag --new or --{strategy_path} -- if it's new we are working on a new strategy. if it's a {strategy_path}, then the system is improving existing strategy.
4) Idea Researcher Agent: There is a research agent that comes up with ideas for strategies. It browses the internet and downloads whitepapers in html or pdf form. It reads whitepapers and summarizes the ideas in the whitepapers and creates a .md file with the ideas in a folder called 'research ideas'. the agent also updates a master .md file which has the paths to all the research paper md files, which are an ordered list.
5) [COMPLETED] Backtest Data Analyser Agent: There is a second agent which looks at all the backtests in the strategy folder (eg. /Users/vandanchopra/Vandan_Personal_Folder/CODE_STUFF/Projects/MathematricksQ/Strategies/SMAStrategy/backtests/2025-03-20_11-26-53) -- and based on all the backtests data, it creates a summary and then based on the summary it generates ideas to improve the strategy.
6) There is a third agent, which takes the inputs from the Idea Researcher Agent and Backtest Data Analyser Agent, and either writes a strategy from scratch, or improves the strategy that we are currently working on.
7) [COMPLETED] Backtester Agent: This agent runs the command, and runs the backtest. "lean backtest "Strategies/SMAStrategy"" -- This agent will pick one year data and only use that, so that we are not 'curve fitting'. Before backtesting is started, it decides the 'test data' and 'train data' logic.
8) Reporting Agent: There needs to be an agent whose only job is to update the human on 'what is currently going on, what is the current performance we have achieved' -- it will all go to the logger.
7) /Users/vandanchopra/Vandan_Personal_Folder/CODE_STUFF/Projects/MathematricksQ/AgenticDeveloper/research_ideas/master.md : This needs to be a numbered list. Also, the list should be ideas, not a list of papers. Also, lets remove dummy whitepapers, and actually find real whitepapers from the internet.
9) When the system runs, the system stops for 15 seconds before the new strategy is written, and waits for human to give guidance, if any. if not, the system continues to do its thing.

## Completed Tasks
1. [✓] Project Structure Setup
   - Created base directories (agents/, tools/, config/)
   - Setup requirements.txt with AI and essential dependencies
   - Created system_config.yaml for LLM settings

2. [✓] Core LLM Integration
   - Implemented flexible LLM client (supports both Ollama and API)
   - Added response parsing and validation
   - Setup basic logging system
   - Updated to use langchain-ollama package (fixing deprecation)

3. [✓] Backtester Agent Implementation
   - Created BacktesterAgent class with comprehensive test coverage
   - Implemented train/test data selection logic
   - Added Lean CLI integration
   - Implemented backtest results storage system
   - Successfully tested with SMAStrategy

4. [✓] Backtest Analyzer Agent Implementation
   - Created BacktestAnalyzerAgent class with JSON output
   - Implemented metrics analysis system
   - Added strategy code review functionality
   - Added trade pattern analysis
   - Successfully tested with SMAStrategy backtests
   - Created detailed improvement suggestion generator

## Next Tasks
1. [ ] Research Agent Implementation
   - Implement IdeaResearcherAgent
   - Add internet search capability
   - Implement PDF reading and analysis
   - Setup research database structure
   - Create and maintain research ideas list

2. [ ] Strategy Development Agent
   - Create StrategyDeveloperAgent
   - Implement strategy code generation
   - Add strategy modification capabilities
   - Setup version control integration

3. [ ] CLI Interface Development
   - Add --new flag for new strategy creation
   - Add --strategy_path flag for existing strategy
   - Implement configuration validation
   - Create workflow orchestrator

4. [ ] Reporting System
   - Create ReportingAgent
   - Implement progress tracking
   - Add human interaction pause points
   - Develop logging enhancements

## Technical Improvements
1. [ ] Testing
   - Add more unit tests for base agent
   - Create integration tests
   - Add performance benchmarking

2. [ ] Documentation
   - Add API documentation
   - Create user guide
   - Add example workflows

3. [ ] System Enhancements
   - Improve error handling
   - Add retry mechanisms
   - Enhance logging system
   - Add performance monitoring

## Known Issues
- None currently

## Notes
- Successfully migrated to langchain-ollama package
- Backtester now correctly stores all metrics and results
- BacktestAnalyzer successfully processes and analyzes backtests
