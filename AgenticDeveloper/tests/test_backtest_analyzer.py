import sys
import os
import asyncio
import json
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.backtest_analyzer import BacktestAnalyzerAgent

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

import pytest
import pytest_asyncio

@pytest_asyncio.fixture
async def analyzer():
    """Fixture to provide a BacktestAnalyzerAgent instance"""
    return BacktestAnalyzerAgent()

@pytest.mark.asyncio
async def test_analyze_backtest_results(analyzer):
    """Test analyzing backtest results using backtest_output.json format"""
    # Use a backtest directory with known backtest_output.json
    backtest_dir = "Strategies/AgenticDev/LazyYellowCat/backtests/2025-04-23_12-14-31"
    
    # Run analysis
    result = await analyzer.run(backtest_dir)
    
    # Verify expected keys in result
    assert "timestamp" in result, "Result should include timestamp"
    assert "backtest_path" in result, "Result should include backtest path"
    assert "analysis" in result, "Result should include analysis"
    
    # Verify analysis structure
    analysis = result["analysis"]
    assert "metrics_analysis" in analysis, "Analysis should include metrics analysis"
    assert "trade_analysis" in analysis, "Analysis should include trade analysis"
    assert "strategy_analysis" in analysis, "Analysis should include strategy analysis"
    assert "improvement_suggestions" in analysis, "Analysis should include improvement suggestions"
    
    # Verify standalone analysis file was created
    standalone_file = os.path.join(backtest_dir, "BacktestAnalyzerAgent_analysis.json")
    assert os.path.exists(standalone_file), "Standalone analysis file should be created"
    
    # Verify backtest_output.json was updated with analysis
    output_json_path = os.path.join(backtest_dir, "backtest_output.json")
    with open(output_json_path, 'r') as f:
        backtest_output = json.load(f)
        
    assert "analysis" in backtest_output, "backtest_output.json should have analysis field"
    assert backtest_output["analysis"] == result["analysis"], "Analysis in backtest_output.json should match result"

@pytest.mark.asyncio
async def test_analyze_backtest_with_invalid_path(analyzer):
    """Test analyzer handles invalid backtest directory"""
    with pytest.raises(ValueError, match="Backtest directory not found"):
        await analyzer.run("invalid/path")