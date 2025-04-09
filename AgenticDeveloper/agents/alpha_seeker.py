from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_core.tools import Tool, AsyncTool

from .base import BaseAgent
from .research_agent import IdeaResearcherAgent
from .strategy_developer import StrategyDeveloperAgent
from .backtester import BacktesterAgent
from .backtest_analyzer import BacktestAnalyzerAgent
import asyncio

# Define LangChain tool wrappers for each agent
async def research_tool_func(query: str = "momentum trading", max_results: int = 3) -> str:
    agent = IdeaResearcherAgent()
    await agent.run(query=query, max_results=max_results)
    return f"Research completed for query: {query}"

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
Decide after each cycle whether to fix, research, or finalize.
"""
)

prompt = ChatPromptTemplate.from_messages([
    system_prompt,
    MessagesPlaceholder(variable_name="chat_history"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

class AlphaSeekerMetaAgent(BaseAgent):
    def __init__(self, config_path: str = "AgenticDeveloper/config/system_config.yaml", config=None):
        super().__init__(config_path=config_path, config=config)

        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt,
        )

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            verbose=True,
        )

    async def run(
        self,
        new_strategy: bool,
        strategy_code: str = "",
        version_control_history: str = "",
        backtest_results: str = "",
        analysis: str = "",
    ):
        """
        Run AlphaSeeker meta-agent with explicit inputs.

        Parameters:
        - new_strategy: True for new strategy mode, False for existing strategy
        - strategy_code, version_control_history, backtest_results, analysis: used if new_strategy is False
        """
        if new_strategy:
            input_text = f"NewStrategy: True"
        else:
            input_text = (
                f"NewStrategy: False\n"
                f"Strategy Code:\n{strategy_code}\n"
                f"Version Control History:\n{version_control_history}\n"
                f"Backtest Results:\n{backtest_results}\n"
                f"Analysis:\n{analysis}\n"
            )

        return await self.executor.ainvoke({"input": input_text})