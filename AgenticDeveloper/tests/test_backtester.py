import pytest
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from agents.backtester import BacktesterAgent

@pytest.fixture
def mock_config():
    return {
        "llm": {
            "provider": "ollama",
            "ollama": {
                "model": "llama2",
                "base_url": "http://localhost:11434"
            }
        },
        "agents": {
            "backtester": {
                "test_data": {
                    "min_period": "1Y",
                    "train_split": 0.7
                },
                "tools": ["lean_cli"]
            }
        },
        "tools": {
            "lean_cli": {
                "backtest_command": "lean backtest"
            }
        }
    }

@pytest.fixture
def backtester_agent(mock_config, tmp_path):
    agent = BacktesterAgent(config=mock_config)
    agent.logger = Mock()
    return agent

@pytest.mark.asyncio
async def test_select_data_periods(backtester_agent):
    """Test the data period selection logic"""
    train_period, test_period = backtester_agent._select_data_periods()
    
    # Verify period structure
    assert isinstance(train_period, dict)
    assert isinstance(test_period, dict)
    assert "start" in train_period and "end" in train_period
    assert "start" in test_period and "end" in test_period
    
    # Verify dates are properly formatted
    datetime.strptime(train_period["start"], "%Y-%m-%d")
    datetime.strptime(train_period["end"], "%Y-%m-%d")
    datetime.strptime(test_period["start"], "%Y-%m-%d")
    datetime.strptime(test_period["end"], "%Y-%m-%d")
    
    # Verify period relationships
    assert train_period["end"] == test_period["start"]
    assert test_period["end"] >= datetime.now().strftime("%Y-%m-%d")

@pytest.mark.asyncio
async def test_run_backtest_success(backtester_agent):
    """Test successful backtest execution"""
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(return_value=(
        b"Total Trades: 100\nSharpe Ratio: 1.5\nReturn: 15.5%",
        b""
    ))
    mock_process.returncode = 0
    
    with patch('asyncio.create_subprocess_shell', return_value=mock_process):
        result = await backtester_agent._run_backtest("test/strategy")
        
        assert isinstance(result, dict)
        assert "metrics" in result
        assert result["metrics"]["Total Trades"] == 100
        assert result["metrics"]["Sharpe Ratio"] == 1.5
        assert result["metrics"]["Return"] == 15.5

@pytest.mark.asyncio
async def test_run_backtest_failure(backtester_agent):
    """Test backtest execution failure"""
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(return_value=(b"", b"Error: Strategy not found"))
    mock_process.returncode = 1
    
    with patch('asyncio.create_subprocess_shell', return_value=mock_process):
        with pytest.raises(RuntimeError, match="Backtest failed"):
            await backtester_agent._run_backtest("test/strategy")

def test_store_results(backtester_agent, tmp_path):
    """Test results storage"""
    # Prepare test data
    result = {
        "metrics": {
            "Total Trades": 100,
            "Sharpe Ratio": 1.5,
            "Return": 15.5
        },
        "timestamp": "2025-03-25T16:00:00"
    }
    
    metadata = {
        "train_period": {"start": "2024-01-01", "end": "2024-06-30"},
        "test_period": {"start": "2024-07-01", "end": "2024-12-31"}
    }
    
    strategy_path = str(tmp_path / "test_strategy")
    os.makedirs(strategy_path)
    
    # Store results
    stored_result = backtester_agent._store_results(result, strategy_path, metadata)
    
    # Verify stored result structure
    assert isinstance(stored_result, dict)
    assert "metadata" in stored_result
    assert "metrics" in stored_result
    assert "strategy_path" in stored_result
    assert "timestamp" in stored_result
    
    # Verify file was created
    backtest_dirs = [d for d in os.listdir(os.path.join(strategy_path, "backtests"))]
    assert len(backtest_dirs) == 1
    
    results_file = os.path.join(strategy_path, "backtests", backtest_dirs[0], "results.json")
    assert os.path.exists(results_file)
    
    # Verify file contents
    with open(results_file, 'r') as f:
        saved_data = json.load(f)
        assert saved_data["metrics"] == result["metrics"]
        assert saved_data["metadata"] == metadata

@pytest.mark.asyncio
async def test_full_backtest_flow(backtester_agent, tmp_path):
    """Test the complete backtest flow"""
    strategy_path = str(tmp_path / "test_strategy")
    os.makedirs(strategy_path)
    
    # Mock subprocess
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(return_value=(
        b"Total Trades: 100\nSharpe Ratio: 1.5\nReturn: 15.5%",
        b""
    ))
    mock_process.returncode = 0
    
    # Mock wait_for_human_input
    backtester_agent.wait_for_human_input = AsyncMock(return_value=None)
    
    with patch('asyncio.create_subprocess_shell', return_value=mock_process):
        result = await backtester_agent.run(strategy_path)
        
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "metrics" in result
        assert result["metrics"]["Total Trades"] == 100
        assert os.path.exists(os.path.join(strategy_path, "backtests"))

def test_invalid_config():
    """Test agent initialization with invalid config"""
    invalid_config = {
        "llm": {
            "provider": "ollama",
            "ollama": {
                "model": "llama2"
            }
        },
        "agents": {
            "backtester": {
                "tools": ["lean_cli"]
            }
        }
    }
    
    with pytest.raises(KeyError):
        BacktesterAgent(config=invalid_config)