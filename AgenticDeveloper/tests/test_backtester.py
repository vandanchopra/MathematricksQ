import pytest
import os
import logging
from agents.backtester import BacktesterAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.fixture
def backtester_agent():
    agent = BacktesterAgent()
    # Configure agent's logger for console output
    agent.logger.setLevel(logging.INFO)
    for handler in agent.logger.handlers:
        agent.logger.removeHandler(handler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    agent.logger.addHandler(console_handler)
    return agent

@pytest.mark.asyncio
async def test_run_backtest_local(backtester_agent):
    strategy_path = "Strategies/AgenticDev/AncientStoneGolem/strategy_v1_1.py"
    backtest_output = await backtester_agent.run(strategy_path, mode="local")
    print('\nLocal Backtest Output:')
    print(f'Success: {backtest_output["backtest_success"]}')
    print(f'Folder: {backtest_output["backtest_folder_path"]}')
    # Check for errors
    if backtest_output.get('errors'):
        print('\nErrors:')
        for error in backtest_output['errors']:
            print(f'- {error}')
            
    # Check performance metrics
    if backtest_output.get('performance'):
        print('\nPerformance Metrics:')
        for key, value in backtest_output['performance'].items():
            print(f'{key}: {value}')

@pytest.mark.asyncio
async def test_run_backtest_cloud(backtester_agent):
    strategy_path = "Strategies/AgenticDev/AncientStoneGolem/strategy_v1_1.py"
    
    """Test cloud backtesting with AncientStoneGolem strategy."""
    logger.info(f"Starting cloud backtest for {strategy_path}")
    
    # Check if strategy exists
    if not os.path.exists(strategy_path):
        logger.error(f"Strategy file not found: {strategy_path}")
        return
    
    logger.info("Running cloud backtest...")
    backtest_output = await backtester_agent.run(strategy_path, mode="cloud")
    
    print('\nCloud Backtest Output:')
    print(f'Success: {backtest_output["backtest_success"]}')
    print(f'Folder: {backtest_output["backtest_folder_path"]}')
    
    # Check if main.py was created
    strategy_dir = os.path.dirname(strategy_path)
    main_path = os.path.join(strategy_dir, "main.py")
    if os.path.exists(main_path):
        logger.info("main.py was created successfully")
        if os.path.exists(strategy_path):
            logger.info("Original strategy file was preserved")
    else:
        logger.error("main.py was not created")
    
    # Check for errors
    if backtest_output.get('errors'):
        print('\nErrors:')
        for error in backtest_output['errors']:
            print(f'- {error}')
    
    # Check performance metrics
    if backtest_output.get('performance'):
        print('\nPerformance Metrics:')
        for key, value in backtest_output['performance'].items():
            print(f'{key}: {value}')