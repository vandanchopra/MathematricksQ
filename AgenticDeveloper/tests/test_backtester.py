import pytest
import os
from agents.backtester import BacktesterAgent

@pytest.fixture
def backtester_agent():
    return BacktesterAgent()

@pytest.mark.asyncio
async def test_run_backtest_local(backtester_agent):
    result = await backtester_agent.run("Strategies/AgenticDev/ShinyGoldenOtter/strategy_v1_0_2.py", mode="local")
    print({'result': result})