import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

from .base import BaseAgent
from AgenticDeveloper.logger import get_logger
import asyncio
from AgenticDeveloper.agents.backtester import BacktesterAgent
import re, random

class StrategyDeveloperAgent(BaseAgent):
    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(config_path, config)
        self.logger = get_logger("StrategyDeveloperAgent")
    """
    Agent responsible for generating or modifying QuantConnect Lean strategy code
    based on instructions (ideas, pseudocode, errors, etc.) using an LLM.
    """

    async def generate_new_strategy_name(self) -> str:
        """
        Generate a new strategy name using the LLM: "adjective" "adjective" "noun" (e.g., SleepyTanHippo).
        Names are stored in strategy_names.json and validated against existing strategies.
        """
        import json
        import os
        
        names_file = "AgenticDeveloper/strategy_names.json"
        names = []
        
        # Try to load existing names from file
        if os.path.exists(names_file):
            try:
                with open(names_file, 'r') as f:
                    data = json.load(f)
                    names = data.get('names', [])
            except Exception as e:
                self.logger.error(f"Failed to load strategy names from file: {e}")

        # If no names available, generate new ones using LLM
        if not names:
            prompt = (
                "Give me a python list of 10 examples with the following logic: "
                "\"adjective\" \"adjective\" \"noun\" (eg. SleepyTanHippo). "
                "Return only a valid python list of strings, no explanation."
            )
            response = await self.call_llm(prompt, llm_destination="thinking")
            
            # Try to extract a python list from the response
            import ast
            try:
                # Find the first [ ... ] block in the response
                start = response.find("[")
                end = response.find("]", start)
                if start != -1 and end != -1:
                    list_str = response[start:end+1]
                    names = ast.literal_eval(list_str)
                else:
                    # Fallback: try to parse the whole response
                    names = ast.literal_eval(response)
            except Exception as e:
                self.logger.error(f"Failed to parse LLM response for strategy names: {e}\nResponse: {response}")
                from datetime import datetime
                return "Strategy_" + datetime.now().strftime("%Y%m%d_%H%M%S")
                
            if not names or not isinstance(names, list):
                from datetime import datetime
                return "Strategy_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Filter out names that already exist in Strategies/AgenticDev or Strategies
        valid_names = []
        for name in names:
            agenticdev_path = os.path.join("Strategies/AgenticDev", name)
            strategies_path = os.path.join("Strategies", name)
            if not os.path.exists(agenticdev_path) and not os.path.exists(strategies_path):
                valid_names.append(name)
        
        # If no valid names left, generate a timestamp-based name
        if not valid_names:
            from datetime import datetime
            return "Strategy_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Choose a random valid name
        new_name = random.choice(valid_names)
        
        # Remove the chosen name and save remaining valid names back to file
        valid_names.remove(new_name)
        try:
            with open(names_file, 'w') as f:
                json.dump({'names': valid_names}, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save strategy names to file: {e}")
        
        return new_name

    async def run(self, instructions: str, start_point_filepath: str = None, backtest_dir: str=None) -> str:
        """
        Main entry point to generate or modify a strategy based on instructions.
        Optionally provide a previous strategy file path to include its code in the prompt.
        Returns the path to the saved strategy file.
        """

        max_retries = 10
        attempt = 0
        errors = []
        final_path = None
        
        parent_filepath = start_point_filepath
        new_strategy_version = start_point_filepath
        
        while attempt < max_retries:
            attempt += 1
            self.logger.info(f"Attempt {attempt} to generate and test strategy")
            
            previous_code = ""
            if parent_filepath and os.path.exists(parent_filepath):
                with open(parent_filepath, "r") as f:
                    previous_code = f.read()
                    
            # Prepare prompt: original instructions + previous errors if any
            if backtest_dir:
                results = self._load_backtest_results(backtest_dir)
            else:
                results = {}
            
            
            errors_dict = results.get("errors", None)
            errors_list = errors_dict['errors'] if errors_dict else []
            error_fix = False
            
            if errors_list:
                error_text = str(errors_list)
                previous_code_prompt = f"\n\nHere is the code previously written by you:\n{previous_code}. " if previous_code else ""
                fix_errors_prompt = f"\n\nThe above code has errors. Please look at all the errors, and rewrite the entire code so that these problems are fixed:\n{error_text[:1000]}. "
                base_instruction = "Write Quantconnect Lean compatible code in python, that fixes the errors. " 
                prompt = previous_code_prompt + fix_errors_prompt + base_instruction + instructions
                error_fix = True
            else:
                previous_code_prompt = f"\n\nHere is the code previously written by you:\n{previous_code}. " if previous_code else ""
                analysis_prompt = f"\n\nHere is the analysis of the previous strategy:\n{results['analysis']}" if 'analysis' in results else ""
                base_instruction = f'Write Quantconnect Lean compatible code in python, that does the following: {instructions}. '
                prompt = previous_code_prompt + analysis_prompt + base_instruction
            
            self.logger.info({'attempt':attempt, 'prompt': prompt, 'parent_filepath': parent_filepath, 'backtest_dir': backtest_dir})
            input("Press Enter to continue...")
            
            self.logger.info("Starting Code Generation...")
            # Generate strategy code
            extracted_code, full_response = self.generate_strategy_code(prompt)
            self.logger.info("Code Generation Complete.")
            ''' 
            if its a new start point, create a new project
            if it's old, let the new strategy_filename and path.
            
            '''
            
            if not parent_filepath:
                new_strategy_name = await self.generate_new_strategy_name()
                parent_filepath = os.path.join("Strategies/AgenticDev", new_strategy_name)
                self._create_new_project(parent_filepath)
            
            if not error_fix or attempt == 1:
                new_strategy_version = self._get_new_version(parent_filepath)
            else:
                new_strategy_version = parent_filepath
            
            # Save strategy version (overwrite or new version)
            
            final_path = self.save_strategy_version(extracted_code, new_strategy_version, llm_full_response=full_response)
            self.logger.info(f"Saved strategy version at: {final_path}")
            parent_filepath = final_path
            
            # Run backtest
            result = await self.test_generated_code(final_path)
            backtest_dir = result['folder_path']
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

    async def test_generated_code(self, python_file_path: str) -> dict:
        """
        Run a lean backtest on the specified python file.
        Returns a dict with backtest results.
        """

        backtester = BacktesterAgent()
        result = await backtester.run(python_file_path)
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
            prompt = instructions
            # self.paginate_output(prompt)
            # self.logger.info(f"LLM prompt:\n{prompt}")    
            response = self.strategy_writer_llm.invoke(prompt)
            self.logger.info(f"[StrategyDeveloperAgent] Raw LLM response:\n{response}\n")

            # Extract python code block
            code_blocks = re.findall(r"```python(.*?)```", response, re.DOTALL | re.IGNORECASE)
            if code_blocks:
                code = code_blocks[0].strip()
                return code, response
            else:
                self.logger.info(f"[StrategyDeveloperAgent] No python code block found in LLM response (looking for ```python ... ``` blocks), retrying ({attempt}/{max_attempts})...")

        raise ValueError("LLM did not return a valid python code block after multiple attempts.")

    def save_strategy_version(self, strategy_code: str, new_strategy_version: str, llm_full_response: str = None) -> str:
        """
        Save the generated strategy code with a new version number.
        Also update version_history.json metadata.
        """
        os.makedirs("Strategies/AgenticDev", exist_ok=True)
        
        with open(new_strategy_version, "w") as f:
            f.write(strategy_code)

        # Update version history metadata
        strategy_dir = os.path.dirname(new_strategy_version)
        history_path = os.path.join(strategy_dir, "version_history.json")
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                history = json.load(f)
        else:
            history = []
        model_used = self.strategy_writer_llm.model
        entry = {
            "version": new_strategy_version.split("/")[-1],
            "file": new_strategy_version,
            "timestamp": datetime.now().isoformat(),
            "description": f"Generated by {model_used}"
        }
        if llm_full_response:
            entry["llm_full_response"] = llm_full_response

        history.append(entry)

        with open(history_path, "w") as f:
            json.dump(history, f, indent=2)

        return new_strategy_version

    def _get_new_version(self, parent_filepath: str = None) -> tuple[str, str]:
        """
        Get parent's version and add _1, _2, etc. based on existing files.
        Args:
            parent_filepath: Path to parent strategy file (e.g., strategy_v1_0_1.py). If None, returns v1
        Returns:
            Tuple of (version number, full filepath) for the new file
        """
        # If no parent filepath provided, return v1 in current directory
        if parent_filepath is None:
            return "1", os.path.join(os.getcwd(), "strategy_v1.py")
            
        # Get directory and parent's version
        parent_dir = os.path.dirname(parent_filepath) if not os.path.isdir(parent_filepath) else parent_filepath
        parent_file = os.path.basename(parent_filepath)
        
        # Extract parent's version (e.g., from strategy_v1_0_1.py get 1_0_1)
        match = re.search(r'strategy_v(.+?)\.py', parent_file)
        if not match:
            new_version = "1"
            return os.path.join(parent_dir, f"strategy_v{new_version}.py")
        
        parent_version = match.group(1)  # e.g., "1_0_1"
        
        # Find all files with same base version but different trailing number
        existing_versions = []
        base_version = parent_version  # e.g., "1_0_1"
        base_prefix = f"strategy_v{base_version}_"  # e.g., "strategy_v1_0_1_"
        
        for fname in os.listdir(parent_dir):
            if fname.startswith(base_prefix) and fname.endswith(".py"):
                try:
                    # Extract trailing number (e.g., from strategy_v1_0_1_2.py get 2)
                    trailing = re.search(rf'{base_prefix}(\d+)\.py', fname)
                    if trailing:
                        existing_versions.append(int(trailing.group(1)))
                except:
                    continue
        
        # If no versions with trailing number exist, start with 1
        if not existing_versions:
            new_version = f"{base_version}_1"
        else:
            # Otherwise, use next available number
            next_num = max(existing_versions) + 1
            new_version = f"{base_version}_{next_num}"
        
        new_filepath = os.path.join(parent_dir, f"strategy_v{new_version}.py")
        return new_filepath
            
    def _create_new_project(self, strategy_dir: str):
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
    
if __name__ == "__main__":
    agent = StrategyDeveloperAgent()
    agent.test_generated_code("/Users/vandanchopra/Vandan_Personal_Folder/CODE_STUFF/Projects/MathematricksQ/Strategies/AgenticDev/FirstAutoStrategy/strategy_v1_0_3.py")