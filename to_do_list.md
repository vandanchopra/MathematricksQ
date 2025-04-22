# AgenticDeveloper Project Tasks

to do: 
1) [DONE] check if burke ratio is the one we want to follow.
2) find out if we can download the backtest details using the backtest id (You'l have to recreate this from --verbose logs)
3) write the code to find the delta and save the same.


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

5. [✓] Research Agent Implementation: In @AgenticDeveloper/agents/research_agent.py
   - Implement IdeaResearcherAgent
   - Add arxiv search capability (put this in the 'tools' folder)
   - Implement PDF reading and analysis
   - Implement HTML reading and analysis
   - Create and maintain research ideas_dump - ideas should be in a json, which is in this format {'idea_name':{'description': , 'pseudo_code': , 'learnings_from_testing': ['learnings1', 'learnings2']}}
   - Create a unit test in @test_research_agent.py, which will get variable inputs from the user and various parts of the Research Agent Implementation

6. [✓] Improve Backtester Agent: Write tests and make it work @test_backtester.py
   - Make the local backtest work
   - Make the random data backtest work
   - Make the cloud backtest work

7. [✓] Strategy Writer Agent
   - Create StrategyDeveloperAgent: 
   - Implement strategy code generation
      1) Strategy development agent will start with getting 'instructions': These instructions will be in 'str' format. Sometimes it'll be psuedo code, sometimes it'll be ideas, sometimes it'll be errors in the current code, sometimes it could be something else. 
      2) We need to use an LLM to decipher what needs to be done and write the strategy in Quantconnect Lean format. The strategy should have a 'development_test_period' and 'development_list_of_assets' in it, which are only used for checking if the code is working (which are outside of the actual strategy requirements)
      3) Once the strategy is written, we will use the 'Backtester Agent' to run the code on a small test of maybe 3 months with a limited number of 'assets'. Once the code test passes, then the strategy is 'ready for testing'.
      4) Every time a strategy is created, it's created with a 'version'....eg. v1.23.23 (major.minor.bug_fixes format)
   - Add strategy modification capabilities
   - Setup version control integration
   - Create a unit test in @test_strategy_writer_agent.py, which will take the first idea from @/Users/vandanchopra/Vandan_Personal_Folder/CODE_STUFF/Projects/MathematricksQ/AgenticDeveloper/research_ideas/research_ideas.json and give that as 'instructions' to 'strategy development agent'


## Next Tasks
2. [ ] Alpha Seeker Agent:
   - Detailed implementation @/Users/vandanchopra/Vandan_Personal_Folder/CODE_STUFF/Projects/MathematricksQ/AlphaSeeker_Workflow.md
   - The job of the Alpha Seeker is the use the StrategyWriter Agent, the reasearch agent, the Backtester Agent Implementation, and the strategy analyser agent and the strategy writer agent to continuously improve the strategy.
   - I want this agent to be like the CEO Agent, which uses all the agents that we have developed and find the most efficient way to improve performance:
      - Coordinator agent — manages and synchronizes other agents
      - Centralized controller — a single agent making decisions for all agents (contrasts with decentralized approaches)
      - Meta-agent — an agent that reasons about or controls the behavior of lower-level agents
      - Orchestrator — organizes, sequences, and manages multiple agents’ activities (common in AI system orchestration)
   - Also, i want this agent to improve strategies, one small idea at a time, each idea will be treated as a new indicator, and then backtested to see if adding it helped improve performance in any way, and if not, then we move to try out a new indicator. The idea is to find small incremental 'edges' / 'alphas', so that we can put them together to create a better strategy.
      i) The start point of this agent could be a) None - in which case it starts with running the 'research agent' for new ideas, b) STR: in which case it starts with running the 'research agent' for new ideas, but this time with the string input as a start point c) an existing strategy: in which case, it looks for the latest test results, uses the latest test results as benchmark and gives the latest test results to the strategy analyser agent to come up with 'feedback' which is then sent to the research agent.
      ii) Then the inputs from the research agent are sent to the strategy writer to come up with an improved strategy.
      iii) Then the improved strategy is backtested and it's results are sent to strategy analyser agent.
      iv) the output of the strategy analyser agent are sent to step (i) where the researcher can do more research and come up with new ideas.
   - The Alpha Seeker agent should also find out what data is available, and break it up into train-test, so that we're not curve fitting.
   - Overall the Alpha Seekers job is to think about how to develop strategies in a way that we're not 'curve-fitting' or over-training on our train-data set.

{
'''
        if new_strategy:
            generate a new strategy name and initialize the directory
            (next_idea = xxxx) now go to research analyst and fetch next idea: (the logic here should be to fetch an idea that has not yet been tested on this strategy)
            create the state object.
            now, go to strategy writer and generate the strategy code for this idea
            now go to backtester and run the backtest
            now go to backtest analyzer and analyze the results
            now create the state
        
        2. (delta = xxx ) now calculate the delta in performance (if new, delta will be full, even if it's -ve) - (the metric we will use for delta calcuation is (CAGR * Sharpe ratio))
        Check if number of orders is greater than 100, if not, go one of the following to increase the number of orders:
            - Increase the time period
            - add more assets
            - reduce the timeframe / resolution being traded
            - Alter the strategy parameters (if rebalancing, increase the rebalancing frequency)
        3. (parent = xxx ) Now, based on the delta in performance, decide whether to keep the version, or discard it. if the version is kept, it is called the 'parent', else, we go back to the original parent.
        ---- now you want to decide what direction to give to the strategy writer tool.
        4. (next_idea = xxx) - find out the version of the upcoming strategy, 
            - if it's odd, then 'alpha seeker decides what to do next', 
            - if it's even, then alpha seeker goes to researcher with a 'prompt' and gets ideas. Now, with that idea, thinking LLM decides what to do next and creates a 'direction' for strategy writer.
        5. Now strategy writer writes a new strategy.
        6. Now, backtester runs the strategy.
        7. Now, backtest analyzer analyzes the results.
        8. Update Google Sheet with key Metrics (CAGR, Sharpe, Burke, Max DD, Sortino, Win %, Avg Win, Avg Loss, Total Orders)
        8. Now, we go back to step 2.
        
        '''


Development Plan for AlphaSeekerMetaAgent Refactoring:

Helper Methods to Add:
def _get_latest_version_number(self, strategy_path: str) -> int:
    # Extract last number from strategy filename
    # Returns int for odd/even decision making
def _calculate_performance_delta(self, current_results, parent_results) -> float:
    # Calculate CAGR * Sharpe ratio delta between versions
    # Returns float representing improvement
def _update_google_sheets(self, metrics: dict):
    # Update performance metrics to Google Sheets
    # Uses environment variables for authentication
Core Process Methods:
async def _initialize_new_strategy(self) -> dict:
    # Generate strategy name
    # Set up directory structure
    # Return initial state
async def _get_next_research_idea(self, state: dict) -> dict:
    # Use research agent to fetch untested idea
    # Update state with current idea
async def _generate_strategy_direction(self, state: dict) -> str:
    # Based on version number (odd/even):
    # - Even: Get research ideas and create direction
    # - Odd: Let alpha seeker decide direction
Main Run Function Flow:
async def run(self, new_strategy: bool, human_input: str = "", start_point_filepath: str = None):
    # 1. Initialize/Load Strategy
    if new_strategy:
        state = await self._initialize_new_strategy()
        idea = await self._get_next_research_idea(state)
    else:
        state = self._load_existing_strategy(start_point_filepath)
    
    while True:
        # 2. Generate Strategy
        direction = await self._generate_strategy_direction(state)
        new_strategy = await self._write_strategy(direction)
        
        # 3. Test & Analyze
        results = await self._run_backtest(new_strategy)
        analysis = await self._analyze_results(results)
        
        # 4. Calculate Delta & Update State
        delta = self._calculate_performance_delta(results, state['parent_results'])
        state = self._update_state(state, results, delta)
        
        # 5. Record Performance
        await self._update_google_sheets(results)
        
        # 6. Get Next Direction
        next_version = self._get_latest_version_number(state['current_strategy'])
        if next_version % 2 == 0:
            # Even: Get new research ideas
            idea = await self._get_next_research_idea(state)
Dependencies to Add:
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import Dict, Optional
import os
import json
import re
from datetime import datetime
Required Environment Variables:
GOOGLE_SHEETS_CREDENTIALS={"type": "service_account", ...}
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SHEETS_WORKSHEET_NAME=StrategyPerformance
Implementation Strategy:

First implement helper methods and test each individually
Then implement core process methods with proper error handling
Finally tie everything together in main run function
Add comprehensive logging throughout
Add type hints and docstrings for better maintainability
This structure keeps AlphaSeeker as the "brain" while delegating specific tasks to other agents. Each method has a single responsibility, making the code easier to maintain and test.

}


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
   - [COMPLETED] Add example workflows {Created comprehensive README.md with system architecture, usage examples, and workflows}

3. [ ] System Enhancements
   - Improve error handling
   - Add retry mechanisms
   - Enhance logging system
   - Add performance monitoring

## Known Issues
- None currently

{Debugging OpenRouter API calls on 2025-04-09:\n- Initial approach used LangChain's deprecated OpenAI wrapper, which caused 400 errors ('Input required: specify "prompt"').\n- Updated to langchain-openai package, but still received 400 errors.\n- Root cause: LangChain wrappers incompatible with OpenRouter's API payload expectations.\n- Created a direct test script using the official OpenAI SDK with base_url set to OpenRouter.\n- This direct approach worked perfectly, returning valid completions.\n- **Conclusion:** Use the official OpenAI SDK directly for OpenRouter API calls.\n- **Next:** Refactor BaseAgent to replace LangChain LLM calls with OpenAI SDK client calls.\n- This will ensure compatibility and fix the prompt errors.\n}\n
## Notes
- Successfully migrated to langchain-ollama package
- Backtester now correctly stores all metrics and results
- BacktestAnalyzer successfully processes and analyzes backtests


## PHASE 2: 

I want to make changes to @/AgenticDeveloper/agents/research_agent.py : 1) I want to see a tqdm loader when the various chunks are being run in _analyze_resource function, and the tqdm should print the a random part of the LLM response (about 30 characters only, so that we can see the LLM progress happening) 2) when the pdf is loaded, lets also save it to the disk somewhere, and put the name of the 'study' and it's 'authors' in the final findings' 3) Lets save the final findings in the folder /Users/vandanchopra/Vandan_Personal_Folder/CODE_STUFF/Projects/MathematricksQ/AgenticDeveloper/research_ideas -- in a file called 'research_ideas.json'. with name of the 'study' and it's 'authors' and the path to the saved pdf.

- Download data from IBKR so that you can run backtests locally, and therefore faster (When using alternative data, run backtests in cloud, so that you can use their free data).
- learn to save strategies from "lean cloud pull" to 'Strategies' folder.



- [ ] Improve Backtester Agent: Make IBKR data download work on a mac.