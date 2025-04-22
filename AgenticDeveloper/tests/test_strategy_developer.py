import os
import json
import asyncio
import pytest
from unittest.mock import patch
from AgenticDeveloper.agents.strategy_developer import StrategyDeveloperAgent

@pytest.fixture
async def agent():
    return StrategyDeveloperAgent()

async def test_run_creates_strategy_file():
    start_point_filepath = "Strategies/AgenticDev/AncientStoneGolem/strategy_v1_3_2_1_1.py"
    strategy_dir = os.path.dirname(start_point_filepath)
    # instructions = "Increase the number of trades by increasing the number of assets it's trading. Add SPY, AAPL, MSFT, NVDA"
    # instructions = "Increase the performance of the strategy by increasing the sharpe ratio"
    instructions = "Improve the sharpe ratio and the compoundingAnnualReturn"
    backtest_dir = "Strategies/AgenticDev/AncientStoneGolem/backtests/2025-04-19_19-55-29"
    
    # # # # New Strategy
    # start_point_filepath = None
    # backtest_dir = None
    # instructions = "Write a profitable long/short strategy that trades SPY, AAPL, MSFT, NVDA"
    
    agent_inst = StrategyDeveloperAgent()
    result_path = await agent_inst.run(instructions=instructions, start_point_filepath=start_point_filepath, backtest_dir=backtest_dir)
    
    # Check that the strategy file was created
    assert os.path.exists(result_path), "Strategy file was not created"
    with open(result_path, "r") as f:
        content = f.read()
        
    # Check that version_history.json was created and contains an entry
    strategy_dir = os.path.dirname(result_path)
    history_path = os.path.join(strategy_dir, "version_history.json")
    assert os.path.exists(history_path), f"version_history.json was not created in {strategy_dir}"
    with open(history_path, "r") as f:
        history = json.load(f)
    assert isinstance(history, list)
    assert len(history) >= 1
    assert any("version" in entry and "file" in entry for entry in history)

if __name__ == "__main__":
    asyncio.run(test_run_creates_strategy_file())