import pytest
import os
import logging
import json
import asyncio
from agents.backtester import BacktesterAgent
from agents.strategy_developer import StrategyDeveloperAgent
from agents.backtest_analyzer import BacktestAnalyzerAgent
from AgenticDeveloper.agents.alpha_seeker import AlphaSeekerMetaAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test fixtures
@pytest.fixture
def backtester_agent():
    agent = BacktesterAgent()
    agent.logger.setLevel(logging.INFO)
    for handler in agent.logger.handlers:
        agent.logger.removeHandler(handler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    agent.logger.addHandler(console_handler)
    return agent

@pytest.fixture
async def strategy_developer_agent():
    return StrategyDeveloperAgent()

@pytest.fixture
def backtest_analyzer_agent():
    return BacktestAnalyzerAgent("AgenticDeveloper/config/system_config.yaml")

@pytest.fixture
def alpha_seeker_agent():
    return AlphaSeekerMetaAgent("AgenticDeveloper/config/system_config.yaml")

# Test Backtester
@pytest.mark.asyncio
async def test_backtester_local(backtester_agent):
    """Test backtesting in local mode"""
    strategy_path = "Strategies/AgenticDev/AncientStoneGolem/strategy_v1_3_1.py"
    assert os.path.exists(strategy_path), f"Strategy file not found: {strategy_path}"
    
    result = await backtester_agent.run(strategy_path, mode="local")
    assert result is not None
    assert isinstance(result, dict), "Result should be a dictionary"
    assert all(key in result for key in ["backtest_successful", "folder_path", "results-summary"]), \
        "Result missing required keys"
    print({'result': result})

@pytest.mark.asyncio
async def test_backtester_cloud(backtester_agent):
    """Test backtesting in cloud mode"""
    strategy_path = "Strategies/AgenticDev/AncientStoneGolem/strategy_v1_3_1.py"
    assert os.path.exists(strategy_path), f"Strategy file not found: {strategy_path}"
    
    logger.info(f"Starting cloud backtest for {strategy_path}")
    result = await backtester_agent.run(strategy_path, mode="cloud")
    
    # Validate result structure
    assert result is not None, "Result should not be None"
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "backtest_successful" in result, "Result missing 'backtest_successful' key"
    assert "folder_path" in result, "Result missing 'folder_path' key"
    assert "results-summary" in result, "Result missing 'results-summary' key"
    
    # Verify backtest files were created
    assert os.path.exists(result["folder_path"]), "Backtest folder was not created"
    assert os.path.exists(os.path.join(result["folder_path"], "summary.json")), "summary.json not found"
    
    print('\nCloud Backtest Result:')
    print(f'Success: {result["backtest_successful"]}')
    print(f'Folder: {result["folder_path"]}')

# Test Strategy Developer
@pytest.mark.asyncio
async def test_strategy_developer(strategy_developer_agent):
    """Test strategy development"""
    # Test setup
    start_point_filepath = "Strategies/AgenticDev/AncientStoneGolem/strategy_v1_3_2_1_1.py"
    instructions = "Improve the sharpe ratio and the compoundingAnnualReturn"
    backtest_dir = "Strategies/AgenticDev/AncientStoneGolem/backtests/2025-04-19_19-55-29"
    
    # Pre-test validations
    assert os.path.exists(start_point_filepath), "Start point strategy file not found"
    assert os.path.exists(backtest_dir), "Backtest directory not found"
    
    # Run strategy development
    result_path = await strategy_developer_agent.run(
        instructions=instructions,
        start_point_filepath=start_point_filepath,
        backtest_dir=backtest_dir
    )
    
    # Validate strategy file creation
    assert os.path.exists(result_path), "Strategy file was not created"
    assert result_path.endswith(".py"), "Strategy file should be a Python file"
    
    # Check file content
    with open(result_path, "r") as f:
        strategy_content = f.read()
        assert "class" in strategy_content, "Strategy should contain a class definition"
        assert "def Initialize(self)" in strategy_content, "Strategy should have Initialize method"
        assert "QCAlgorithm" in strategy_content, "Strategy should inherit from QCAlgorithm"
    
    # Validate version history
    strategy_dir = os.path.dirname(result_path)
    history_path = os.path.join(strategy_dir, "version_history.json")
    assert os.path.exists(history_path), "version_history.json not created"
    
    with open(history_path, "r") as f:
        history = json.load(f)
        assert isinstance(history, list), "Version history should be a list"
        assert len(history) >= 1, "Version history should have at least one entry"
        
        # Check latest version entry
        latest_version = history[-1]
        required_keys = ["version", "file", "timestamp", "description"]
        assert all(key in latest_version for key in required_keys), \
            f"Latest version missing required keys. Found: {list(latest_version.keys())}"
        assert latest_version["file"] == result_path, "Version history file path doesn't match"
        
        # Verify version numbering
        version_numbers = [entry["version"] for entry in history]
        assert len(version_numbers) == len(set(version_numbers)), "Duplicate version numbers found"

# Test Backtest Analyzer
@pytest.mark.asyncio
async def test_backtest_analyzer(backtest_analyzer_agent):
    """Test backtest analysis"""
    backtest_dir = "Strategies/AgenticDev/LazyYellowCat/backtests/2025-04-23_12-14-31"
    
    # Pre-test validations
    assert os.path.exists(backtest_dir), "Backtest directory not found"
    assert os.path.exists(os.path.join(backtest_dir, "summary.json")), "summary.json not found"
    
    # Run analysis
    result = await backtest_analyzer_agent.run(backtest_dir)
    assert result is not None, "Result should not be None"
    assert "analysis" in result, "Result should contain 'analysis' key"
    
    # Validate analysis structure
    analysis = result["analysis"]
    required_sections = ["metrics_analysis", "trade_analysis", "strategy_analysis", "improvement_suggestions"]
    assert all(section in analysis for section in required_sections), \
        f"Analysis missing required sections. Found: {list(analysis.keys())}"
    
    # Validate metrics analysis
    metrics = analysis["metrics_analysis"]
    assert isinstance(metrics, dict), "Metrics analysis should be a dictionary"
    required_metrics = ["CAGR", "Sharpe", "MaxDrawdown"]
    assert all(metric in metrics for metric in required_metrics), \
        f"Metrics analysis missing required metrics. Found: {list(metrics.keys())}"
    
    # Validate trade analysis
    trades = analysis["trade_analysis"]
    assert isinstance(trades, dict), "Trade analysis should be a dictionary"
    required_trade_metrics = ["win_rate", "average_win", "average_loss"]
    assert all(metric in trades for metric in required_trade_metrics), \
        f"Trade analysis missing required metrics. Found: {list(trades.keys())}"
    
    # Validate strategy analysis
    strategy = analysis["strategy_analysis"]
    assert isinstance(strategy, dict), "Strategy analysis should be a dictionary"
    assert "strengths" in strategy and "weaknesses" in strategy, \
        "Strategy analysis should include strengths and weaknesses"
    
    # Validate improvement suggestions
    suggestions = analysis["improvement_suggestions"]
    assert isinstance(suggestions, list), "Improvement suggestions should be a list"
    assert len(suggestions) > 0, "Should have at least one improvement suggestion"
    
    # Check analysis file creation
    analysis_file = os.path.join(backtest_dir, "BacktestAnalyzerAgent_analysis.json")
    assert os.path.exists(analysis_file), "Analysis file not created"
    with open(analysis_file, 'r') as f:
        saved_analysis = json.load(f)
        assert saved_analysis == result["analysis"], "Saved analysis doesn't match returned analysis"

# Test Alpha Seeker
@pytest.mark.asyncio
async def test_alpha_seeker_new_strategy(alpha_seeker_agent):
    """Test AlphaSeeker with new strategy"""
    # Run with new strategy
    result = await alpha_seeker_agent.run(
        new_strategy=True,
        human_input="Create a profitable momentum trading strategy"
    )
    
    # Validate result structure
    assert result is not None, "Result should not be None"
    assert isinstance(result, dict), "Result should be a dictionary"
    
    # Check required state fields
    required_fields = [
        "mode", "strategy_name", "current_strategy_path",
        "current_strategy_version", "current_strategy_results",
        "current_strategy_analysis", "current_strategy_delta",
        "current_idea", "iteration"
    ]
    assert all(field in result for field in required_fields), \
        f"Result missing required fields. Found: {list(result.keys())}"
    
    # Verify mode and strategy creation
    assert result["mode"] == "new_strategy", "Mode should be new_strategy"
    if result["current_strategy_path"]:
        assert os.path.exists(result["current_strategy_path"]), "Strategy file should exist"
        assert result["current_strategy_path"].endswith('.py'), "Strategy should be a Python file"
        
        # Check strategy content
        with open(result["current_strategy_path"], 'r') as f:
            content = f.read()
            assert 'class' in content, "Strategy should define a class"
            assert 'Initialize' in content, "Strategy should have Initialize method"
            assert 'QCAlgorithm' in content, "Strategy should inherit from QCAlgorithm"

@pytest.mark.asyncio
async def test_alpha_seeker_existing_strategy(alpha_seeker_agent):
    """Test AlphaSeeker with existing strategy"""
    strategy_path = "Strategies/AgenticDev/LazyYellowCat/strategy_v1.py"
    assert os.path.exists(strategy_path), f"Strategy file not found: {strategy_path}"
    
    # Run with existing strategy
    result = await alpha_seeker_agent.run(
        new_strategy=False,
        human_input="Improve the strategy's Sharpe ratio",
        start_point_filepath=strategy_path
    )
    
    # Validate result structure
    assert result is not None, "Result should not be None"
    assert isinstance(result, dict), "Result should be a dictionary"
    
    # Check required state fields
    required_fields = [
        "mode", "strategy_name", "current_strategy_path",
        "parent_name", "parent_results", "parent_errors",
        "current_strategy_version", "current_strategy_results",
        "current_strategy_analysis", "current_strategy_delta",
        "version_history_path"
    ]
    assert all(field in result for field in required_fields), \
        f"Result missing required fields. Found: {list(result.keys())}"
    
    # Verify mode and paths
    assert result["mode"] == "existing_strategy", "Mode should be existing_strategy"
    assert result["parent_name"] == os.path.basename(strategy_path), \
        "Parent name should match input file"
    
    # Check version history
    if result["version_history_path"]:
        assert os.path.exists(result["version_history_path"]), \
            "Version history should exist"
        with open(result["version_history_path"], 'r') as f:
            history = json.load(f)
            assert isinstance(history, list), "Version history should be a list"
            assert len(history) > 0, "Version history should not be empty"
    
    # Check parent results
    if result["parent_results"]:
        assert isinstance(result["parent_results"], dict), \
            "Parent results should be a dictionary"
        assert "compoundingAnnualReturn" in result["parent_results"], \
            "Parent results should include CAGR"
        assert "sharpeRatio" in result["parent_results"], \
            "Parent results should include Sharpe ratio"

def display_json_section(title: str, content: dict, indent: int = 2):
    """Helper function to display JSON sections nicely"""
    print(f"\n{title}:")
    print("-" * 40)
    if isinstance(content, dict):
        for key, value in content.items():
            if isinstance(value, list):
                print(f"{' ' * indent}{key}:")
                for item in value:
                    print(f"{' ' * (indent * 2)}- {item}")
            else:
                print(f"{' ' * indent}{key}: {value}")
    else:
        print(json.dumps(content, indent=2))
