import os
import json
import pytest
from unittest.mock import patch
from AgenticDeveloper.agents.strategy_developer import StrategyDeveloperAgent

@pytest.fixture
def agent():
    return StrategyDeveloperAgent()

def test_run_creates_strategy_file(agent):
    strategy_dir = "Strategies/AgenticDev/FirstAutoStrategy"
    os.makedirs("Strategies/AgenticDev", exist_ok=True)

    result_path = agent.run("write a momentum strategy for AAPL", strategy_dir)

    # Check that the strategy file was created
    assert os.path.exists(result_path), "Strategy file was not created"
    with open(result_path, "r") as f:
        content = f.read()

    # Check that version_history.json was created and contains an entry
    history_path = os.path.join(strategy_dir, "version_history.json")
    assert os.path.exists(history_path), "version_history.json was not created"
    with open(history_path, "r") as f:
        history = json.load(f)
    assert isinstance(history, list)
    assert len(history) >= 1
    assert any("version" in entry and "file" in entry for entry in history)