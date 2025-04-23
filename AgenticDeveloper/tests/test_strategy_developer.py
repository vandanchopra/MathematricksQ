import os
import json
import pytest
import pytest_asyncio
from AgenticDeveloper.agents.strategy_developer import StrategyDeveloperAgent

@pytest_asyncio.fixture
async def agent():
    """Fixture that provides a StrategyDeveloperAgent instance"""
    return StrategyDeveloperAgent()

@pytest_asyncio.fixture
async def test_strategy_path():
    """Fixture that provides test strategy path"""
    return "Strategies/AgenticDev/AncientStoneGolem/strategy_v2.py"

@pytest_asyncio.fixture
async def test_backtest_dir():
    """Fixture that provides test backtest directory"""
    return None

@pytest.mark.asyncio
async def test_improve_strategy(agent, test_strategy_path, test_backtest_dir):
    """Test improving existing strategy with specific instructions"""
    instructions = "Improve the sharpe ratio and the compoundingAnnualReturn"
    
    result_path = await agent.run(
        instructions=instructions,
        start_point_filepath=test_strategy_path,
        backtest_dir=test_backtest_dir
    )
    
    # Verify strategy file creation
    assert os.path.exists(result_path), "Strategy file was not created"
    
    # Verify file content exists
    with open(result_path, "r") as f:
        content = f.read()
        assert content.strip(), "Strategy file is empty"

    # Verify version history
    strategy_dir = os.path.dirname(result_path)
    history_path = os.path.join(strategy_dir, "version_history.json")
    assert os.path.exists(history_path), f"version_history.json not found in {strategy_dir}"
    
    with open(history_path, "r") as f:
        history = json.load(f)
        assert isinstance(history, list), "Version history should be a list"
        assert len(history) >= 1, "Version history should have at least one entry"
        assert any("version" in entry and "file" in entry for entry in history), \
            "Version history entries should contain version and file fields"

@pytest.mark.asyncio
async def test_create_new_strategy(agent):
    """Test creating a new strategy from scratch"""
    instructions = "Write a profitable long/short strategy that trades SPY, AAPL, MSFT, NVDA"
    
    result_path = await agent.run(
        instructions=instructions,
        start_point_filepath=None,
        backtest_dir=None
    )
    
    assert os.path.exists(result_path), "New strategy file was not created"
    
    strategy_dir = os.path.dirname(result_path)
    history_path = os.path.join(strategy_dir, "version_history.json")
    assert os.path.exists(history_path), "Version history not created for new strategy"