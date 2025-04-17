# AgenticDeveloper Project Tasks

i want @/AgenticDeveloper/agents/backtester.py to also now run in mode == 'cloud': 
   1) First we rename the strategy version we want to run to main.py in that strategy folder.
   2) We cloud push so that the strategy is now in the cloud.
   3) then we run lean cloud backtest {strategy_folder_path}
   4) now we wait for the test to run.
   5) Once the test is complete and successful (We get the performance table in the console), we take the performance and put it in a file called 'summary.json'. If it didn't work right, we put the 'console errors' into a file called 'errors.json'


read @terminal for how backtests are run in the cloud, we run :lean cloud backtest "Hyper-Active Apricot Alligator": -- which automatically runs the main.py. but before we run the backtest, we need to push the project to cloud using 'lean cloud push'.



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
Alpha Seeker Agent Implementation Plan by Roo (2025-09-04):

1. Carefully review existing agent implementations:
   - research_agent.py
   - backtest_analyzer.py
   - strategy_developer.py
   - backtester.py
   - Understand their APIs, inputs, outputs, and integration points.

2. Design AlphaSeekerAgent class:
   - Define core methods: __init__, run, coordinate_agents, evaluate_results
   - Plan for start modes: no input, string input, existing strategy
   - Plan incremental improvement loop and orchestration logic

3. Create AlphaSeekerAgent skeleton in AgenticDeveloper/agents/alpha_seeker.py:
   - Add class definition and init method
   - Add placeholders for core methods

4. Integrate existing agents step-by-step:
   - Start with Research Agent integration
   - Then Strategy Developer
   - Then Backtester
   - Then Backtest Analyzer

5. Implement incremental improvement loop:
   - Run research, develop strategy, backtest, analyze
   - Loop with stopping criteria and human pause points

6. Add logging, progress updates, and error handling

7. Develop unit tests for AlphaSeekerAgent logic

8. Create integration tests with mock agents

9. Document AlphaSeekerAgent usage and update README.md

10. Mark this task as complete in to_do_list.md when done
}
{
Created AlphaSeekerAgent skeleton in AgenticDeveloper/agents/alpha_seeker.py
- Inherits from BaseAgent
- Initializes Research, Strategy Developer, Backtester, Backtest Analyzer agents
- Added async run(), coordinate_agents(), evaluate_results() placeholders
- Ready for incremental integration of agent workflows

Refactored AlphaSeekerAgent methods to use explicit parameters
- run() and coordinate_agents() now accept: new_strategy (bool), existing_strategy_path (Optional[str]), initial_prompt (Optional[str])
- Improved docstrings for clarity
- Renamed start_mode param to new_strategy (bool)

Implemented core orchestration logic:
- NewStrategy mode: runs research and strategy generation
- ExistingStrategy mode: runs backtest analysis
- Added error handling and progress logging

Added iterative workflow loop with decision points:
- Loop calls research, strategy writing, backtesting, analysis
- Stubbed decide_next_step() method controls loop flow
- Placeholders for minor fix and new research branches
- Aligns with AlphaSeeker meta-agent architecture
- Next: Implement decision logic and dynamic tool invocation
}

{AlphaSeeker Orchestration Refactor Plan (2025-04-10):

1. Remove reliance on LangChain OpenAI Functions agent for orchestration.
2. Implement a **custom async loop** inside AlphaSeekerMetaAgent.run():
   - If NewStrategy:
     - Call ResearchTool with initial prompt
     - Pass research output to StrategyWriterTool
   - Else (ExistingStrategy):
     - Analyze existing strategy and backtest results
     - Decide to fix or research
3. After strategy generation:
   - Call BacktesterTool
   - Call BacktestAnalyzerTool
4. Use analysis to decide:
   - Minor fix → StrategyWriterTool
   - New research → ResearchTool
   - Finalize → stop loop
5. Repeat loop until stopping criteria met.
6. Log progress and decisions at each step.
7. Gradually replace placeholders with real logic.
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