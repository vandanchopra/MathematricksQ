import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

from .base import BaseAgent
from AgenticDeveloper.logger import get_logger

class StrategyDeveloperAgent(BaseAgent):
    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(config_path, config)
        self.logger = get_logger("StrategyDeveloperAgent")
    """
    Agent responsible for generating or modifying QuantConnect Lean strategy code
    based on instructions (ideas, pseudocode, errors, etc.) using an LLM.
    """

    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(config_path, config)

    def run(self, instructions: str, strategy_dir: str, previous_strategy_path: str = None) -> str:
        """
        Main entry point to generate or modify a strategy based on instructions.
        Optionally provide a previous strategy file path to include its code in the prompt.
        Returns the path to the saved strategy file.
        """
        import asyncio
        from AgenticDeveloper.agents.backtester import BacktesterAgent

        base_instruction = 'Write Quantconnect Lean compatible code in python, that does the follwing:'
        instructions = base_instruction + instructions + ' | Do not forget to check your code and debug it before you return it.'
        self._create_project_if_needed(strategy_dir)

        previous_code = ""
        if previous_strategy_path and os.path.exists(previous_strategy_path):
            with open(previous_strategy_path, "r") as f:
                previous_code = f.read()

        max_retries = 3
        attempt = 0
        errors = []
        final_path = None

        while attempt < max_retries:
            attempt += 1
            print(f"[StrategyDeveloperAgent] Attempt {attempt} to generate and test strategy")

            # Prepare prompt: original instructions + previous errors if any
            if errors:
                error_text = "\n".join(errors)
                prompt = f"{instructions}"
                if previous_code:
                    prompt += f"\n\nHere is the code previously written by you:\n{previous_code}"
                prompt += f"\n\nThe above code has errors. Please look at all the errors, then create a plan for how you want to make fixes, and only then write fresh code:\n{error_text}\n\nPlease look at all the errors, then create a plan for how you want to make fixes, and only then write fresh code:"
            else:
                prompt = instructions
                if previous_code:
                    prompt += f"\n\nHere is the previous strategy code:\n{previous_code}"
            
            # Generate strategy code
            extracted_code, full_response = self.generate_strategy_code(prompt)
            
            # Save strategy version (overwrite or new version)
            final_path = self.save_strategy_version(extracted_code, strategy_dir, llm_full_response=full_response)
            self.logger.info(f"Saved strategy version at: {final_path}")
            
            # Run backtest
            result = self.test_generated_code(final_path)
            self.logger.info(f"Backtest result: {result}")
            
            if result.get("backtest_successful"):
                self.logger.info("Backtest successful.")
                break
            else:
                self.logger.info("Backtest failed. Errors:")
                errors = result.get("errors", [])
                previous_code = extracted_code  # Use the latest code for next attempt
            
        if attempt == max_retries and errors:
            self.logger.info("Max retries reached. Last errors:")
            for err in errors:
                self.logger.info(f" - {err}")

        return final_path

    def test_generated_code(self, python_file_path: str) -> dict:
        """
        Run a lean backtest on the specified python file.
        Returns a dict with backtest results.
        """
        import asyncio
        from AgenticDeveloper.agents.backtester import BacktesterAgent

        backtester = BacktesterAgent()
        result = asyncio.run(backtester.run(python_file_path))
        return result


    def generate_strategy_code(self, instructions: str) -> (str):
        """
        Generate QuantConnect Lean strategy code from instructions using LLM.
        Returns a tuple: (extracted_code, full_response)
        """
        import re

        max_attempts = 3
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            prompt = self._create_strategy_prompt(instructions)
            # self.logger.info(f"LLM prompt:\n{prompt}")
            response = self.strategy_writer_llm.invoke(prompt)

            # Extract python code block
            code_blocks = re.findall(r"```python(.*?)```", response, re.DOTALL | re.IGNORECASE)
            if code_blocks:
                code = code_blocks[0].strip()
                return code, response
            else:
                print(f"[StrategyDeveloperAgent] No python code block found in LLM response, retrying ({attempt}/{max_attempts})...")

        raise ValueError("LLM did not return a valid python code block after multiple attempts.")

    def save_strategy_version(self, strategy_code: str, strategy_dir: str, llm_full_response: str = None) -> str:
        """
        Save the generated strategy code with a new version number.
        Also update version_history.json metadata.
        """
        os.makedirs(strategy_dir, exist_ok=True)
        version = self._get_new_version(strategy_dir)
        filename = f"strategy_v{version}.py"
        path = os.path.join(strategy_dir, filename)
        with open(path, "w") as f:
            f.write(strategy_code)

        # Update version history metadata
        history_path = os.path.join(strategy_dir, "version_history.json")
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                history = json.load(f)
        else:
            history = []

        entry = {
            "version": version,
            "file": filename,
            "timestamp": datetime.now().isoformat(),
            "description": "Generated by StrategyDeveloperAgent"
        }
        if llm_full_response:
            entry["llm_full_response"] = llm_full_response

        history.append(entry)

        with open(history_path, "w") as f:
            json.dump(history, f, indent=2)

        return path

    def _get_new_version(self, strategy_dir: str) -> str:
        """
        Determine the next version number based on existing files.
        """
        existing_versions = []
        for fname in os.listdir(strategy_dir):
            if fname.startswith("strategy_v") and fname.endswith(".py"):
                try:
                    ver = fname[len("strategy_v"):-3]
                    existing_versions.append(ver)
                except:
                    continue
        # Sort versions
        if not existing_versions:
            return "1_0_0"
        else:
            # Assuming semantic versioning major_minor_patch with underscores
            latest = sorted(existing_versions, key=lambda s: list(map(int, s.split('_'))))[-1]
            major, minor, patch = map(int, latest.split('_'))
            patch += 1
            return f"{major}_{minor}_{patch}"

    def _create_project_if_needed(self, strategy_dir: str):
        """
        If the strategy directory does not exist or does not contain main.py and config.json,
        create a new QuantConnect Lean project using 'lean project-create'.
        """
        main_py = os.path.join(strategy_dir, "main.py")
        config_json = os.path.join(strategy_dir, "config.json")

        if os.path.isdir(strategy_dir) and os.path.exists(main_py) and os.path.exists(config_json):
            print(f"[StrategyDeveloperAgent] Existing Lean project detected at {strategy_dir}, skipping creation.")
            return  # Project already exists and is valid

        # Extract strategy name
        strategy_name = os.path.basename(strategy_dir.rstrip("/"))
        strategies_root = os.path.dirname(strategy_dir.rstrip("/"))

        # Ensure Strategies root exists
        os.makedirs(strategies_root, exist_ok=True)

        # Run lean project-create inside Strategies root
        cmd = f'cd "{strategies_root}" && lean project-create "{strategy_name}" --language python'
        os.system(cmd)
        print("[StrategyDeveloperAgent] Project created.")

    def _create_strategy_prompt(self, instructions: str) -> str:
        """
        Create a prompt for the LLM to generate strategy code.
        """
        prompt = f"Given the following instructions, generate a QuantConnect Lean compatible trading strategy in Python:\n\n{instructions}\n\n# Strategy Code:\n"
        return prompt
    
if __name__ == "__main__":
    agent = StrategyDeveloperAgent()
    agent.test_generated_code("/Users/vandanchopra/Vandan_Personal_Folder/CODE_STUFF/Projects/MathematricksQ/Strategies/AgenticDev/FirstAutoStrategy/strategy_v1_0_3.py")