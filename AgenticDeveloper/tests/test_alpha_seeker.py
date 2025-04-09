import argparse
import asyncio
import json
from AgenticDeveloper.agents.alpha_seeker import AlphaSeekerMetaAgent

async def run_new_strategy():
    agent = AlphaSeekerMetaAgent("AgenticDeveloper/config/system_config.yaml")
    print("\n--- Running AlphaSeeker in NewStrategy mode ---")
    result = await agent.run(
        new_strategy=True
    )
    print("AlphaSeeker output:\n", result)

async def run_existing_strategy():
    agent = AlphaSeekerMetaAgent("AgenticDeveloper/config/system_config.yaml")
    print("\n--- Running AlphaSeeker in ExistingStrategy mode ---")
    result = await agent.run(
        new_strategy=False,
        strategy_code="def existing_strategy(): pass",
        version_control_history="dummy version history",
        backtest_results="dummy backtest results",
        analysis="dummy analysis"
    )
    print("AlphaSeeker output:\n", result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test AlphaSeeker Meta-Agent")
    parser.add_argument("--new_strategy", type=bool, default=True, help="Set to True for new strategy mode, False for existing strategy mode")
    args = parser.parse_args()

    if args.new_strategy:
        asyncio.run(run_new_strategy())
    else:
        asyncio.run(run_existing_strategy())