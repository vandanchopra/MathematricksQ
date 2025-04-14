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
import json as pyjson
import re
import random

# Define LangChain tool wrappers for each agent
async def research_tool_func(query: str = "momentum trading", max_results: int = 3) -> dict:
    """Returns research ideas as a dictionary."""
    agent = IdeaResearcherAgent()
    await agent.run(query=query, max_results=max_results)
    
    # Load research ideas from JSON
    ideas_path = "AgenticDeveloper/research_ideas/research_ideas.json"
    with open(ideas_path, 'r') as f:
        ideas = pyjson.load(f)
    
    return {
        "query": query,
        "ideas": ideas
    }

async def strategy_writer_tool_func(instructions: str, strategy_dir: str, previous_strategy_path: str = None) -> str:
    agent = StrategyDeveloperAgent()
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, agent.run, instructions, strategy_dir, previous_strategy_path)
    return f"Strategy saved at: {path}"

async def backtester_tool_func(strategy_path: str, mode: str = "local") -> str:
    agent = BacktesterAgent()
    result = await agent.run(strategy_path, mode)
    return f"Backtest result: {result}"

async def backtest_analyzer_tool_func(backtest_dir: str) -> str:
    agent = BacktestAnalyzerAgent()
    result = await agent.run(backtest_dir)
    return f"Backtest analysis: {result}"

research_tool = Tool.from_function(
    research_tool_func,
    name="ResearchTool",
    description="Conducts research based on a query and saves ideas."
)

strategy_writer_tool = Tool.from_function(
    strategy_writer_tool_func,
    name="StrategyWriterTool",
    description="Implements or modifies trading strategies based on instructions."
)

backtester_tool = Tool.from_function(
    backtester_tool_func,
    name="BacktesterTool",
    description="Runs backtests on strategies."
)

backtest_analyzer_tool = Tool.from_function(
    backtest_analyzer_tool_func,
    name="BacktestAnalyzerTool",
    description="Analyzes backtest results and provides insights."
)

tools = [research_tool, strategy_writer_tool, backtester_tool, backtest_analyzer_tool]

system_prompt = SystemMessage(
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
)

prompt = ChatPromptTemplate.from_messages([
    system_prompt,
    MessagesPlaceholder(variable_name="chat_history"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

import shutil

class AlphaSeekerMetaAgent(BaseAgent):
    def __init__(self, config_path: str = "AgenticDeveloper/config/system_config.yaml", config=None):
        super().__init__(config_path=config_path, config=config)
        self.logger = get_logger("AlphaSeekerMetaAgent")
        
    async def generate_new_strategy_name(self, human_input: str) -> str:
        """
        Generate a new strategy name using the LLM: "adjective" "adjective" "noun" (e.g., SleepyTanHippo).
        Names are stored in strategy_names.json and validated against existing strategies.
        """
        import json
        import os
        
        names_file = "AgenticDeveloper/strategy_names.json"
        names = []
        
        # Try to load existing names from file
        if os.path.exists(names_file):
            try:
                with open(names_file, 'r') as f:
                    data = json.load(f)
                    names = data.get('names', [])
            except Exception as e:
                self.logger.error(f"Failed to load strategy names from file: {e}")

        # If no names available, generate new ones using LLM
        if not names:
            prompt = (
                "Give me a python list of 10 examples with the following logic: "
                "\"adjective\" \"adjective\" \"noun\" (eg. SleepyTanHippo). "
                "Return only a valid python list of strings, no explanation."
            )
            response = await self.call_llm(prompt, llm_destination="thinking")
            
            # Try to extract a python list from the response
            import ast
            try:
                # Find the first [ ... ] block in the response
                start = response.find("[")
                end = response.find("]", start)
                if start != -1 and end != -1:
                    list_str = response[start:end+1]
                    names = ast.literal_eval(list_str)
                else:
                    # Fallback: try to parse the whole response
                    names = ast.literal_eval(response)
            except Exception as e:
                self.logger.error(f"Failed to parse LLM response for strategy names: {e}\nResponse: {response}")
                from datetime import datetime
                return "Strategy_" + datetime.now().strftime("%Y%m%d_%H%M%S")
                
            if not names or not isinstance(names, list):
                from datetime import datetime
                return "Strategy_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Filter out names that already exist in Strategies/AgenticDev or Strategies
        valid_names = []
        for name in names:
            agenticdev_path = os.path.join("Strategies/AgenticDev", name)
            strategies_path = os.path.join("Strategies", name)
            if not os.path.exists(agenticdev_path) and not os.path.exists(strategies_path):
                valid_names.append(name)
        
        # If no valid names left, generate a timestamp-based name
        if not valid_names:
            from datetime import datetime
            return "Strategy_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Choose a random valid name
        new_name = random.choice(valid_names)
        
        # Remove the chosen name and save remaining valid names back to file
        valid_names.remove(new_name)
        try:
            with open(names_file, 'w') as f:
                json.dump({'names': valid_names}, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save strategy names to file: {e}")
        
        return new_name

    def fetch_strategy_code(self, strategy_path: str) -> str:
        """
        Fetch the code of the strategy from the given file path.
        """
        try:
            with open(strategy_path, "r") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to fetch strategy code from {strategy_path}: {e}")
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
                self.logger.error(f"Failed to fetch version history from {version_history_path}: {e}")
                return ""
        return ""
    
    async def run(
        self,
        new_strategy: bool,
        human_input: str = "",
        strategy_start_point_filepath: str = None,
    ):
        """
        Run AlphaSeeker meta-agent with explicit inputs.

        Parameters:
        - new_strategy: True for new strategy mode, False for existing strategy
        - human_input: Initial guidance or requirements from user
        - strategy_code, version_control_history, backtest_results, analysis: used if new_strategy is False
        """
        iteration = 0
        self.human_input = human_input

        # For existing strategy, fetch code and version history
        strategy_code = ""
        version_history = ""
        if not new_strategy:
            if not strategy_start_point_filepath or not os.path.exists(strategy_start_point_filepath):
                raise ValueError("A valid strategy_start_point_filepath must be provided for existing strategy mode.")
            strategy_code = self.fetch_strategy_code(strategy_start_point_filepath)
            version_history = self.fetch_version_history(strategy_start_point_filepath)

        if new_strategy:
            strategy_name = await self.generate_new_strategy_name(self.human_input)
        else:
            strategy_name = os.path.splitext(os.path.basename(strategy_start_point_filepath))[0]
        
        # Initialize state tracking
        state = {
            "mode": "new_strategy" if new_strategy else "existing_strategy",
            "strategy_name": strategy_name,
            "human_input": human_input,
            "strategy_code": strategy_code,
            "version_history": version_history,
            "iteration": 0,
            "research_outputs": [],
            "strategy_updates": [],
            "last_action": None,
            "tested_ideas": [],  # Keep track of which ideas have been tested (as a list for JSON serialization)
            "current_idea": None    # Currently being tested idea
        }
        
        while True:
            iteration += 1
            state["iteration"] = iteration
            # self.logger.info(f"--- AlphaSeeker Iteration {iteration} ---")

            try:
                # Let LLM decide next action
                # self.logger.info("Deciding next action based on current state...")
                decision = await self.decide_next_action(state)
                self.logger.info(f"--- AlphaSeeker Iteration {iteration} --- Decision made: {decision}")
                input("Press Enter to continue...")  # Pause for user to read logs
                
                tool = decision.get("tool")
                prompt = decision.get("prompt")
                
                if tool == "STOP":
                    self.logger.info("LLM decided to stop iterations.")
                    break
                
                # Execute the chosen tool
                self.logger.info(f"Executing {tool} with generated prompt...")
                
                if tool == "ResearchTool":
                    result = await research_tool_func(query=prompt)
                    if isinstance(result, dict):
                        state["research_outputs"].append(result["ideas"])
                        self.logger.info(f"Added {len(result['ideas'])} research ideas to state")
                    
                elif tool == "StrategyWriterTool":
                    # --- NEW STRATEGY DIRECTORY LOGIC ---
                    if new_strategy:
                        # Generate a new strategy name using LLM
                        strategy_name = state["strategy_name"]
                        base_dir = "Strategies/AgenticDev"
                        strategy_dir = os.path.join(base_dir, strategy_name)
                        # Ensure directory does not exist
                        attempt = 1
                        while os.path.exists(strategy_dir):
                            strategy_name = await self.generate_new_strategy_name(self.human_input + f"_{attempt}")
                            strategy_dir = os.path.join(base_dir, strategy_name)
                            attempt += 1
                        os.makedirs(strategy_dir, exist_ok=True)
                    else:
                        # Existing strategy mode: require strategy_start_point_filepath
                        if not hasattr(self, "strategy_start_point_filepath") or not self.strategy_start_point_filepath:
                            raise ValueError("strategy_start_point_filepath is required when new_strategy == False.")
                        if not os.path.exists(self.strategy_start_point_filepath):
                            raise FileNotFoundError(f"strategy_start_point_filepath does not exist: {self.strategy_start_point_filepath}")
                        # Copy the existing strategy to a new working directory
                        strategy_name = os.path.splitext(os.path.basename(self.strategy_start_point_filepath))[0]
                        base_dir = "Strategies/AgenticDev"
                        strategy_dir = os.path.join(base_dir, strategy_name)
                        if not os.path.exists(strategy_dir):
                            os.makedirs(strategy_dir, exist_ok=True)
                        shutil.copy2(self.strategy_start_point_filepath, os.path.join(strategy_dir, os.path.basename(self.strategy_start_point_filepath)))

                    result = await strategy_writer_tool_func(
                        instructions=prompt,
                        strategy_dir=strategy_dir
                    )
                    state["strategy_updates"].append(result)
                    state["strategy_code"] = result  # Update current strategy
                    
                    # Extract strategy path from result
                    strategy_path_match = re.search(r"Strategy saved at: (.+\.py)", str(result))
                    if strategy_path_match:
                        state["current_strategy_path"] = strategy_path_match.group(1)
                    
                elif tool == "BacktesterTool":
                    if "current_strategy_path" in state:
                        result = await backtester_tool_func(state["current_strategy_path"])
                        state["backtest_results"] = result
                    else:
                        raise ValueError("No strategy path available for backtesting")
                    
                    # Update version history with backtest results
                    if state["current_idea"]:
                        # Get directory from current strategy path
                        if "current_strategy_path" in state:
                            strategy_dir = os.path.dirname(state["current_strategy_path"])
                            history_path = os.path.join(strategy_dir, "version_history.json")
                            if os.path.exists(history_path):
                                with open(history_path, 'r') as f:
                                    history = pyjson.load(f)
                                    if history:
                                        # Add test results to latest version
                                        history[-1]["test_results"] = result
                                        history[-1]["tested_idea"] = state["current_idea"]["name"]
                                with open(history_path, 'w') as f:
                                    pyjson.dump(history, f, indent=2)
                        
                        # Update research ideas with test results
                        ideas_path = "AgenticDeveloper/research_ideas/research_ideas.json"
                        if os.path.exists(ideas_path):
                            with open(ideas_path, 'r') as f:
                                ideas = pyjson.load(f)
                                idea_name = state["current_idea"]["name"]
                                if idea_name in ideas:
                                    # Fix KeyError for 'learnings_from_testing'
                                    if "learnings_from_testing" not in ideas[idea_name]:
                                        ideas[idea_name]["learnings_from_testing"] = []
                                    ideas[idea_name]["learnings_from_testing"].append({
                                        "timestamp": datetime.now().isoformat(),
                                        "backtest_results": result,
                                        "strategy_path": state.get("current_strategy_path", "")
                                    })
                            with open(ideas_path, 'w') as f:
                                pyjson.dump(ideas, f, indent=2)
                    
                elif tool == "BacktestAnalyzerTool":
                    result = await backtest_analyzer_tool_func(prompt)
                    state["analysis"] = result
                
                state["last_action"] = {"tool": tool, "result": result}
                # self.logger.info(f"{tool} output: {result}")

            except KeyboardInterrupt:
                try:
                    user_input = input("\nHuman input (type STOP to exit): ")
                except KeyboardInterrupt:
                    self.logger.info("KeyboardInterrupt received again. Exiting AlphaSeeker.")
                    break
                if user_input.strip().upper() == "STOP":
                    self.logger.info("STOP command received. Exiting AlphaSeeker.")
                    break
                else:
                    # Update human input in state for next LLM decision
                    self.human_input = user_input
                    state["human_input"] = user_input
                    # self.logger.info(f"Human input saved: {self.human_input}")
                    continue

        self.logger.info("AlphaSeeker orchestration complete.")
        return state  # Return final state for analysis

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
                self.logger.warning(f"Failed to parse JSON from matched content: {e}")
        
        # If no JSON found between backticks, try parsing the whole response
        try:
            decision = pyjson.loads(response)
            return decision
        except Exception:
            self.logger.warning(f"Failed to parse LLM decision, defaulting to STOP. Response: {response}")
            return {"tool": "STOP", "prompt": ""}