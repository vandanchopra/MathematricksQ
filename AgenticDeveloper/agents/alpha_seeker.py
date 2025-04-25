import concurrent.futures
import sys
import time
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool
from datetime import datetime

from .base import BaseAgent
from AgenticDeveloper.logger import get_logger
import os
from .research_agent import IdeaResearcherAgent
from .strategy_developer import StrategyDeveloperAgent
from .backtester import BacktesterAgent
from .backtest_analyzer import BacktestAnalyzerAgent
import asyncio
import json
import re
import random
import shutil

class AlphaSeekerMetaAgent(BaseAgent):
    async def research_tool_func(self, query: str = "momentum trading", max_results: int = 3) -> dict:
        """Returns research ideas as a dictionary."""
        agent = IdeaResearcherAgent()
        await agent.run(query=query, max_results=max_results)
        
        # Load research ideas from JSON
        ideas_path = "AgenticDeveloper/research_ideas/research_ideas.json"
        with open(ideas_path, 'r') as f:
            ideas = json.load(f)
        
        return {
            "query": query,
            "ideas": ideas
        }

    async def strategy_writer_tool_func(self, instructions: str, strategy_dir: str, previous_strategy_path: str = None) -> str:
        agent = StrategyDeveloperAgent()
        loop = asyncio.get_event_loop()
        new_strategy_path = await loop.run_in_executor(None, agent.run, instructions, strategy_dir, previous_strategy_path)
        
        return new_strategy_path

    async def backtester_tool_func(self, strategy_path: str, mode: str = "local") -> str:
        agent = BacktesterAgent()
        backtest_results = await agent.run(strategy_path, mode)
        return backtest_results

    async def backtest_analyzer_tool_func(self, backtest_dir: str) -> str:
        agent = BacktestAnalyzerAgent()
        backtest_analysis = await agent.run(backtest_dir)
        return backtest_analysis

    def _initialize_tools(self):
        """Initialize LangChain tools"""
        research_tool = Tool.from_function(
            self.research_tool_func,
            name="ResearchTool",
            description="Conducts research based on a query and saves ideas."
        )

        strategy_writer_tool = Tool.from_function(
            self.strategy_writer_tool_func,
            name="StrategyWriterTool",
            description="Implements or modifies trading strategies based on instructions."
        )

        backtester_tool = Tool.from_function(
            self.backtester_tool_func,
            name="BacktesterTool",
            description="Runs backtests on strategies."
        )

        backtest_analyzer_tool = Tool.from_function(
            self.backtest_analyzer_tool_func,
            name="BacktestAnalyzerTool",
            description="Analyzes backtest results and provides insights."
        )

        self.tools = [research_tool, strategy_writer_tool, backtester_tool, backtest_analyzer_tool]
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(
                content="""You are AlphaSeeker, an autonomous trading strategy meta-agent.
You dynamically call tools to research, develop, backtest, and analyze strategies.
You continuously improve strategies by looping through these tools.

Key principles:
1. One idea at a time: Test each research idea separately to understand its individual performance.
2. Scientific method: Develop, test, analyze before moving to the next idea.
3. Keep detailed records: Track performance of each idea and strategy version.

After each backtest:
1. Analyze the results thoroughly
2. Record learnings
3. Only then consider moving to a new idea or improving the current one.
"""
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def __init__(self, config_path: str = "AgenticDeveloper/config/system_config.yaml", config=None):
        super().__init__(config_path=config_path, config=config)
        self.logger = get_logger("AlphaSeeker")
        self._initialize_tools()
    
    def fetch_strategy_code(self, strategy_path: str) -> str:
        """
        Fetch the code of the strategy from the given file path.
        """
        try:
            with open(strategy_path, "r") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"[AlphaSeeker] Strategy code fetch failed - {e}")
            return ""

    def fetch_version_history(self, strategy_path: str) -> str:
        """
        Fetch the version history for the strategy, if available.
        Looks for version_history.json in the same directory as the strategy file.
        """
        import json
        dir_path = os.path.dirname(strategy_path)
        version_history_path = os.path.join(dir_path, "version_history.json")
        if os.path.exists(version_history_path):
            try:
                with open(version_history_path, "r") as f:
                    return json.dumps(json.load(f))
            except Exception as e:
                self.logger.error(f"[AlphaSeeker] Version history fetch failed - {e}")
                return ""
        return ""

    def _get_latest_version_number(self, strategy_path: str) -> int:
        """
        Extract the last number from a strategy filename to determine if it's odd or even.
        Example: strategy_v1_3_2_1_1_2.py returns 2
        """
        filename = os.path.basename(strategy_path)
        # Remove file extension and split by underscores
        parts = os.path.splitext(filename)[0].split('_')
        # Find the last numeric part
        for part in reversed(parts):
            if part.isdigit():
                return int(part)
        return 1  # Default to 1 if no version number found
    
    def _calculate_performance_delta(self, current_results: dict, parent_results: dict) -> float:
        """
        Calculate performance delta between current and parent version.
        Delta = CAGR * Sharpe ratio
        """
        try:
            current_performance = float(current_results.get('CAGR', 0)) * float(current_results.get('Sharpe', 0))
            if parent_results:
                parent_performance = float(parent_results.get('CAGR', 0)) * float(parent_results.get('Sharpe', 0))
                return current_performance - parent_performance
            return current_performance  # For new strategies, return absolute performance
        except (ValueError, TypeError) as e:
            self.logger.error(f"[AlphaSeeker] Delta calculation failed - {e}")
            return 0.0
            
    def determine_scenario(self, state: dict) -> str:
        """Determine which improvement scenario applies"""
        # SCENARIO 1: Check for errors first
        if state["parent_strategy_errors"]:
            return "error"
        
        # SCENARIO 2: Check trade count
        total_orders = state["parent_strategy_performance"].get("Total Orders", 0)
        try:
            total_orders = int(str(total_orders).replace(",", ""))
        except (ValueError, TypeError):
            total_orders = 0
            
        if total_orders < 100:
            return "low_trades"
            
        # SCENARIO 3: Need performance improvement
        return "improvement_needed"

    def create_improvement_prompt(self, scenario: str, state: dict) -> str:
        """Generate appropriate prompt based on scenario"""
        if scenario == "error":
            return f"Fix the following errors in the strategy:\n{state['parent_strategy_errors']}"
            
        elif scenario == "low_trades":
            total_orders = state["parent_strategy_performance"].get("Total Orders", 0)
            return (f"The current strategy only generated {total_orders} orders. "
                   "Modify the strategy to generate more trading opportunities by:\n"
                   "1. Adjusting entry/exit conditions\n"
                   "2. Adding more trading pairs\n"
                   "3. Reducing minimum trade thresholds")
                   
        else:  # improvement_needed
            return self.create_strategy_performance_improvement_prompt(state)

    def create_strategy_performance_improvement_prompt(self, state: dict) -> str:
        """Create a prompt for improving strategy performance based on current metrics"""
        metrics = state["parent_strategy_performance"]
        parent_strategy_performance_analysis = state["parent_strategy_performance_analysis"]
        self.logger.debug({'parent_strategy_performance_analysis': parent_strategy_performance_analysis})
        self.logger.debug({'state': state})
        self.logger.debug({'state.keys()': state.keys()})
        input("Press Enter to continue...")
        sharpe_ratio = metrics.get("Sharpe Ratio", "0")
        drawdown = metrics.get("Drawdown", "0%")
        
        prompt = "Improve the strategy performance with focus on:\n"
        
        if float(str(sharpe_ratio).replace("-", "0")) < 1.0:
            prompt += f"1. Improve risk-adjusted returns (current Sharpe Ratio: {sharpe_ratio})\n"
            
        if float(str(drawdown).replace("%", "").replace("-", "0")) > 15.0:
            prompt += f"2. Reduce maximum drawdown (current: {drawdown})\n"
            
        prompt += "\nMake targeted improvements while maintaining the core strategy logic."
        return prompt

    def calculate_performance_delta(self, child_performance: dict, parent_performance: dict) -> float:
        """Calculate delta between child and parent strategies"""
        try:
            child_sharpe = float(child_performance.get("Sharpe Ratio", 0))
            parent_sharpe = float(parent_performance.get("Sharpe Ratio", 0))
            return child_sharpe - parent_sharpe
        except (ValueError, TypeError):
            return 0.0

    def should_keep_child(self, state: dict, child_performance: dict) -> bool:
        """Determine if child strategy shows enough improvement to replace parent"""
        delta = self.calculate_performance_delta(
            child_performance,
            state["parent_strategy_performance"]
        )
        return delta > 0

    def sleeper(self, total_seconds: int, message: str = "System Sleeping") -> None:
        """Display a countdown timer while waiting.
        
        Args:
            total_seconds (int): Total time to wait in seconds
            message (str): Message to display while waiting
        """
        for remaining in range(total_seconds, 0, -1):
            days = remaining // (24 * 60 * 60)
            hours = (remaining % (24 * 60 * 60)) // (60 * 60)
            minutes = (remaining % (60 * 60)) // 60
            seconds = remaining % 60
            
            time_str = ""
            if days > 0:
                time_str += "{:2d} days,".format(days)
            if hours > 0:
                time_str += "{:2d} hours,".format(hours)
            if minutes > 0:
                time_str += "{:2d} minutes,".format(minutes)
            if seconds > 0:
                time_str += "{:2d} seconds".format(seconds)
            
            sys.stdout.write("\r")
            sys.stdout.write(f"{message}: " + time_str + " remaining.")
            sys.stdout.flush()
            time.sleep(1)  # Sleep for 1 second
        sys.stdout.write("\r" + " " * 100)  # Clear the line
        sys.stdout.write("\r")

    def _input_with_timeout(self, prompt: str = "") -> str:
        """Get input with a timeout using signals"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError()
        
        # Set the timeout handler
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(1)  # Will raise TimeoutError if no input after 1 second
        
        try:
            return input(prompt)
        except TimeoutError:
            return None
        finally:
            signal.alarm(0)  # Disable the alarm

    async def wait_for_human_input(self, timeout_seconds: int = 15) -> str:
        """Wait for human input with a timeout.
        Returns the input if received, otherwise None."""
        
        try:
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Start the sleeper
                sleeper_future = loop.run_in_executor(
                    executor,
                    self.sleeper,
                    timeout_seconds,
                    "Waiting for human input"
                )
                
                # Try to get input for the duration
                start_time = time.time()
                while time.time() - start_time < timeout_seconds:
                    # Check for input with a 1-second timeout
                    try:
                        result = await loop.run_in_executor(executor, self._input_with_timeout)
                        if result is not None:
                            # Cancel the sleeper
                            sleeper_future.cancel()
                            return result.strip()
                    except Exception:
                        pass
                    
                    # Sleep briefly to prevent CPU spinning
                    await asyncio.sleep(0.1)
                
                # If we get here, we timed out
                print("\n[AlphaSeeker] Timeout - continuing with current prompt")
                return None
                
        except Exception as e:
            self.logger.error(f"[AlphaSeeker] Input error - {e}")
            return None

    async def _update_google_sheets(self, metrics: dict):
        """
        Update strategy performance metrics to Google Sheets.
        Metrics include: CAGR, Sharpe, Burke, Max DD, Sortino, Win %, Avg Win, Avg Loss, Total Orders
        """
        try:
            if not os.getenv('GOOGLE_SHEETS_CREDENTIALS'):
                self.logger.warning("[AlphaSeeker] Missing Google Sheets credentials")
                return
                
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            creds_dict = json.loads(os.getenv('GOOGLE_SHEETS_CREDENTIALS'))
            creds = Credentials.from_authorized_user_info(creds_dict)
            
            service = build('sheets', 'v4', credentials=creds)
            spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
            range_name = os.getenv('GOOGLE_SHEETS_WORKSHEET_NAME')
            
            values = [[
                metrics.get('CAGR', ''),
                metrics.get('Sharpe', ''),
                metrics.get('Burke', ''),
                metrics.get('MaxDD', ''),
                metrics.get('Sortino', ''),
                metrics.get('WinRate', ''),
                metrics.get('AvgWin', ''),
                metrics.get('AvgLoss', ''),
                metrics.get('TotalTrades', '')
            ]]
            
            body = {'values': values}
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
        except Exception as e:
            self.logger.error(f"[AlphaSeeker] Failed to update sheets - {e}")

    async def run(
        self,
        new_strategy: bool,
        human_input: str = "",
        start_point_filepath: str = None,
    ):
        """
        Main entry point for AlphaSeeker's strategy development process.
        
        Args:
            new_strategy (bool): True to create new strategy, False to modify existing
            human_input (str): Initial guidance from user
            start_point_filepath (str): Path to existing strategy file if new_strategy is False
        """

        
        # Initialize state
        state = {
            "mode": "new_strategy" if new_strategy else "existing_strategy",
            "version_history_path": None,  # Path to version_history.json
            "parent_strategy_path": start_point_filepath,
            "parent_strategy_backtest_path": None,  # Path to parent strategy backtest results
            "parent_strategy_errors": None,  # Errors from parent strategy
            "parent_strategy_performance": None,  # Performance metrics of parent strategy
            "parent_strategy_performance_analysis": None,  # Analysis of parent strategy performance

            "current_strategy_version": None,  # Current version number (e.g., v1_2_3)
            "current_strategy_backtest_path": None,  # Path to parent strategy backtest results
            "current_strategy_errors": None,  # Errors from parent strategy
            "current_strategy_performance": None,  # Performance metrics of parent strategy
            "current_strategy_performance_analysis": None,  # Analysis of parent strategy performance
            "current_strategy_delta": None,  # Performance delta from parent
            "current_idea": None,  # Current trading idea being tested
            "iteration": 0
        }
        self.logger.debug(f"Initial state created. Everything set to None.")
        
        # If starting from existing strategy, initialize parent details
        if not new_strategy and start_point_filepath:
            strategy_dir = os.path.dirname(start_point_filepath)
            state["version_history_path"] = os.path.join(strategy_dir, "version_history.json")
            self.logger.debug(f"Starting from an existing strategy. Version history updated to state.")
    
        while True:
            state["iteration"] += 1
            print('--' * 40)
            self.logger.debug(f"Iteration {state['iteration']} started.")
            
            # Get parent strategy results if this is first iteration and not a new strategy
            if state["iteration"] == 1 and not new_strategy and state["version_history_path"]:
                # First get the latest backtest folder path from version history
                with open(state["version_history_path"], 'r') as f:
                    history = json.load(f)
                    
                # Find latest backtest folder
                for entry in reversed(history):
                    if "backtests" in entry and entry["backtests"]:
                        latest_backtest = entry["backtests"][-1]
                        backtest_folder = latest_backtest.get("backtest_folder")
                        if backtest_folder and os.path.exists(backtest_folder):
                            # Load results using BaseAgent's method
                            backtest_output = self._load_backtest_results(backtest_folder)
                            state["parent_strategy_performance"] = backtest_output.get("performance", {})
                            state["parent_strategy_errors"] = backtest_output.get("errors", [])
                            state["parent_strategy_backtest_path"] = backtest_folder
                            state["parent_strategy_performance_analysis"] = backtest_output.get("analysis", {})
                            self.logger.debug(f"Parent strategy performance loaded from backtest folder.")
                            break
            
            
            try:
                # Initial setup for new strategy if needed
                if new_strategy and state["iteration"] == 1:
                    idea = await self._get_next_research_idea(state)
                    prompt = self._create_strategy_prompt(idea)
                    strategy_path = await self.strategy_writer_tool_func(prompt, "Strategies/AgenticDev")
                    self.logger.debug(f"New strategy created at {strategy_path}")
                    state["parent_strategy_path"] = strategy_path
                                
                # 1. Determine current scenario
                scenario = self.determine_scenario(state)
                self.logger.debug(f"Scenario determined: {scenario}")
                
                # 2. Generate appropriate prompt
                prompt = self.create_improvement_prompt(scenario, state)
                self.logger.debug(f"Prompt for New Strategy generated: {prompt}")
                # 3. Give human 15 seconds to review/modify prompt
                human_input = await self.wait_for_human_input(15)
                if human_input:
                    prompt = human_input
            
                # 4. Create new strategy version
                strategy_dev = StrategyDeveloperAgent()
                new_strategy_path = await strategy_dev.run(
                    instructions=prompt,
                    start_point_filepath=state["parent_strategy_path"]
                )
                self.logger.debug(f"New strategy version created at {new_strategy_path}")
                
                # 5. Run backtest
                backtester = BacktesterAgent()
                backtest_result = await backtester.run(
                    strategy_path=new_strategy_path,
                    mode="cloud"
                )
                self.logger.debug(f"Backtest completed for new strategy version: {new_strategy_path}")
                
                # 6. Update metrics and check performance
                if backtest_result["backtest_success"]:
                    if self.should_keep_child(state, backtest_result["performance"]):
                        self.logger.debug(f"Decided to keep child strategy based on performance. {new_strategy_path}")
                        # Run analysis on successful child strategy
                        analyzer = BacktestAnalyzerAgent()
                        self.logger.debug(f"Running analysis on new strategy version: {new_strategy_path} with backtest result: {backtest_result['backtest_folder_path']}")
                        analysis_result = await analyzer.run(backtest_result["backtest_folder_path"])
                        
                        # Update parent with child's info
                        state["parent_strategy_path"] = new_strategy_path
                        state["parent_strategy_performance"] = backtest_result["performance"]
                        state["parent_strategy_errors"] = backtest_result["errors"]
                        state["parent_strategy_performance_analysis"] = analysis_result
                        state["current_strategy_delta"] = self.calculate_performance_delta(
                            backtest_result["performance"],
                            state["parent_strategy_performance"]
                        )
                    else:
                        self.logger.debug(f"Child strategy dropped due to poor performance: {new_strategy_path}")
                        pass
                
            except Exception as e:
                self.logger.error(f"[AlphaSeeker] Error in iteration {state['iteration']} - {e}")
                break

        return state
    
    async def decide_next_action(self, context: dict) -> dict:
        """
        Use the LLM to decide the next tool and prompt based on current context.
        Returns a dict with 'tool' and 'prompt'.
        """
        import json as pyjson
        
        # If we have research outputs but no current idea selected
        if context["research_outputs"] and not context["current_idea"]:
            # Get all ideas from research outputs
            all_ideas = {}
            for output in context["research_outputs"]:
                all_ideas.update(output)
            
            # Find untested ideas
            tested_ideas_set = set(context["tested_ideas"])
            untested_ideas = set(all_ideas.keys()) - tested_ideas_set
            if untested_ideas:
                # Select the first untested idea
                idea_name = list(untested_ideas)[0]
                idea = all_ideas[idea_name]
                context["current_idea"] = {
                    "name": idea_name,
                    "details": idea
                }
                # Mark this idea as being tested
                context["tested_ideas"].append(idea_name)
                
                # Create a focused prompt for this single idea
                return {
                    "tool": "StrategyWriterTool",
                    "prompt": f"Implement a trading strategy based on this specific idea:\n\nIdea: {idea_name}\nDescription: {idea['description']}\nPseudo-code:\n{idea['pseudo_code']}\n\nImplement only this idea without adding other concepts yet. This allows us to test each component's performance individually."
                }
        
        # For other cases, let the LLM decide
        prompt = (
            "Given the following context, decide which tool to call next and what prompt to use.\n"
            "Context:\n"
            f"{pyjson.dumps(context, indent=2)}\n"
            "Return a JSON with:\n"
            "{\n"
            "  \"tool\": \"ResearchTool\" | \"StrategyWriterTool\" | \"BacktesterTool\" | \"BacktestAnalyzerTool\" | \"STOP\",\n"
            "  \"prompt\": \"...\"\n"
            "}\n"
            "\nNotes:\n"
            "- If no research has been done, start with ResearchTool\n"
            "- After BacktesterTool has run on an idea, use BacktestAnalyzerTool to evaluate its performance\n"
            "- Only move to a new idea after fully testing the current one\n"
        )
        response = await self.call_llm(prompt, llm_destination="thinking")
        
        # Try to extract JSON between triple backticks
        import re
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        
        if json_match:
            try:
                decision = pyjson.loads(json_match.group(1))
                return decision
            except Exception as e:
                self.logger.warning(f"[AlphaSeeker] Failed to parse decision JSON - {e}")
        
        # If no JSON found between backticks, try parsing the whole response
        try:
            decision = pyjson.loads(response)
            return decision
        except Exception:
            self.logger.warning("[AlphaSeeker] Invalid decision - defaulting to stop")
            return {"tool": "STOP", "prompt": ""}

if __name__ == "__main__":
    import argparse
    import asyncio
    from AgenticDeveloper.logger import get_logger

    logger = get_logger("AlphaSeekerMain")

    parser = argparse.ArgumentParser(description="AlphaSeeker Meta Agent CLI")
    parser.add_argument("--new", action="store_true", help="Create a new strategy")
    parser.add_argument("--modify", action="store_true", help="Modify existing strategy")
    parser.add_argument("--strategy-path", type=str, help="Path to existing strategy (required for --modify)")
    parser.add_argument("--input", type=str, default="", help="Initial guidance for the agent")

    args = parser.parse_args()

    if args.new and args.modify:
        logger.error("Cannot specify both --new and --modify")
        exit(1)

    if args.modify and not args.strategy_path:
        logger.error("--strategy-path is required when using --modify")
        exit(1)

    async def main():
        agent = AlphaSeekerMetaAgent()
        try:
            state = await agent.run(
                new_strategy=args.new,
                human_input=args.input,
                start_point_filepath=args.strategy_path if args.modify else None
            )
            # logger.info("Final state:")
            # logger.info(json.dumps(state, indent=2))
        except Exception as e:
            logger.error(f"Error running AlphaSeeker: {e}")
            exit(1)

    asyncio.run(main())