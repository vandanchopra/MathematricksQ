import argparse
import asyncio
import json
from AgenticDeveloper.agents.alpha_seeker import AlphaSeekerMetaAgent

async def run_new_strategy(human_input: str):
    agent = AlphaSeekerMetaAgent("AgenticDeveloper/config/system_config.yaml")
    print("\n--- Running AlphaSeeker in NewStrategy mode ---")
    print(f"Initial human guidance: {human_input}\n")
    result = await agent.run(
        new_strategy=True,
        human_input=human_input
    )
    print("\nFinal State:")
    print(json.dumps(result, indent=2))

async def run_existing_strategy(human_input: str, strategy_start_point_filepath: str):
    agent = AlphaSeekerMetaAgent("AgenticDeveloper/config/system_config.yaml")
    print("\n--- Running AlphaSeeker in ExistingStrategy mode ---")
    print(f"Initial human guidance: {human_input}\n")
    result = await agent.run(
        new_strategy=False,
        human_input=human_input,
        strategy_start_point_filepath=strategy_start_point_filepath
    )
    print("\nFinal State:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser(description="Test AlphaSeeker Meta-Agent")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--new_strategy", action="store_true", help="If present, run in new strategy mode.")
    group.add_argument("--strategy_start_point_filepath", type=str, help="Path to an existing strategy to start from (required if not using --new_strategy).")
    parser.add_argument("--human_input", type=str, default="Create a profitable trading strategy", help="Initial guidance for AlphaSeeker")
    args = parser.parse_args()

    # Validate strategy_start_point_filepath if provided
    if args.strategy_start_point_filepath:
        import os
        if not os.path.exists(args.strategy_start_point_filepath):
            print(f"Error: Provided strategy_start_point_filepath does not exist: {args.strategy_start_point_filepath}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Using existing strategy from: {args.strategy_start_point_filepath}")

    if args.new_strategy:
        asyncio.run(run_new_strategy(args.human_input))
    else:
        asyncio.run(run_existing_strategy(args.human_input, args.strategy_start_point_filepath))