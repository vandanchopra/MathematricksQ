import asyncio
import os
import re
from datetime import datetime
from typing import Dict, Optional
import json

from .base import BaseAgent
from AgenticDeveloper.logger import get_logger

class BacktesterAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.logger = get_logger("BacktesterAgent")

    async def run(self, strategy_path: str, mode: str = "local") -> Dict:
        """
        Run a backtest for the given strategy.
        mode: 'local', 'cloud', or 'random_data'
        Returns: dict with 'folder_path', 'backtest_successful', and 'errors'
        """
        self.log_progress(f"Starting backtest for {strategy_path} in mode: {mode}")

        # Build command
        if mode == "local":
            command = f"lean backtest '{strategy_path}'"
        elif mode == "cloud":
            raise NotImplementedError("Cloud backtesting is not implemented yet.")
        elif mode == "random_data":
            raise NotImplementedError("Cloud backtesting is not implemented yet.")
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        self.log_progress(f"Running command: {command}")

        # Run command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="."
        )
        stdout, stderr = await process.communicate()
        stdout_str = stdout.decode() if stdout else ""
        stderr_str = stderr.decode() if stderr else ""

        filtered_stdout = "\n".join(
            line for line in stdout_str.splitlines()
            if "error" in line.lower() and "tracking error" not in line.lower()
        )
        filtered_stderr = "\n".join(
            line for line in stderr_str.splitlines()
            if "error" in line.lower() and "tracking error" not in line.lower()
        )
        if filtered_stdout:
            self.logger.error(f"Lean CLI stdout errors:\n{filtered_stdout}")
        if filtered_stderr:
            self.logger.error(f"Lean CLI stderr errors:\n{filtered_stderr}")

        # Parse output directory from CLI output or error output
        folder_path = None
        patterns = [
            r"output is stored in\s*'([^']+)'",
            r"stored the output in\s*'([^']+)'"
        ]
        for output in (stdout_str, stderr_str):
            for pattern in patterns:
                match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)
                if match:
                    folder_path = match.group(1)
                    break
            if folder_path:
                break
 
        errors = []
        backtest_successful = False
        if folder_path and os.path.exists(folder_path):
            backtest_successful, errors, failed_data_requests = self.backtest_success_check(folder_path=folder_path, console_output=stdout_str)
            # Save errors to json file in backtest folder
            os.makedirs(folder_path, exist_ok=True)
            with open(folder_path+'/errors.json', 'w') as f:
                json.dump({"backtest_successful": backtest_successful, "errors": errors, "strategy_code_filepath":strategy_path}, f, indent=4)
        else:
            backtest_successful = False
            errors = ["Backtest output folder not found"]
            
        # Delete all the files in the backtest/code/ folder that are not by the name strategy_path.split("/")[-1]
        # This is to avoid cluttering the backtest folder with old files
        strategy_filename = os.path.basename(strategy_path)
        backtest_code_folder = os.path.join(folder_path, "code")
        if os.path.exists(backtest_code_folder):
            for filename in os.listdir(backtest_code_folder):
                if filename != strategy_filename:
                    file_path = os.path.join(backtest_code_folder, filename)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        self.logger.error(f"Failed to delete {file_path}: {e}")
        else:
            self.logger.warning(f"Backtest code folder not found: {backtest_code_folder}")
        
        # Save results to errors.json in backtest folder
        result = {
            "folder_path": folder_path,
            "backtest_successful": backtest_successful,
            "errors": errors,
            "failed_data_requests":failed_data_requests
        }
        
        # Update version history
        self._update_version_history(strategy_path, folder_path, backtest_successful, errors, failed_data_requests)
        return result

    def _update_version_history(self, strategy_path: str, backtest_folder: str, backtest_successful: bool, errors: list, failed_data_requests: list) -> None:
        """Update version history with backtest results

        Args:
            strategy_path: Path to the strategy file
            backtest_folder: Path to the backtest results folder
            backtest_successful: Whether the backtest completed successfully
            errors: List of errors encountered during backtest
        """
        try:
            # Handle both full and relative strategy paths
            abs_strategy_path = os.path.abspath(strategy_path)
            strategy_dir = os.path.dirname(abs_strategy_path)
            
            # Navigate up to find Strategies/AgenticDev directory
            while strategy_dir and os.path.basename(strategy_dir) != "AgenticDev":
                strategy_dir = os.path.dirname(strategy_dir)
            
            if not strategy_dir:
                self.logger.error("Could not find AgenticDev directory in strategy path")
                return
                
            # Get path to version_history.json
            version_history_path = os.path.join(strategy_dir,
                                              os.path.basename(os.path.dirname(abs_strategy_path)),
                                              "version_history.json")
            
            if not os.path.exists(version_history_path):
                self.logger.warning(f"Version history file not found: {version_history_path}")
                return
                
            # Load version history
            with open(version_history_path, 'r') as f:
                version_history = json.load(f)
            
            # Find summary.json file in backtest folder
            backtest_files = os.listdir(backtest_folder)
            summary_file = None
            for file in backtest_files:
                if file.endswith('-summary.json'):
                    summary_file = file
                    break
            # Extract summary data with error handling
            results_summary = {
                'tradeStatistics': None,
                'portfolioStatistics': None,
                'error': None
            }
            
            if summary_file:
                try:
                    with open(os.path.join(backtest_folder, summary_file), 'r') as f:
                        summary_data = json.load(f)
                        if 'totalPerformance' in summary_data:
                            if 'tradeStatistics' in summary_data['totalPerformance']:
                                results_summary['tradeStatistics'] = summary_data['totalPerformance']['tradeStatistics']
                            if 'portfolioStatistics' in summary_data['totalPerformance']:
                                results_summary['portfolioStatistics'] = summary_data['totalPerformance']['portfolioStatistics']
                        else:
                            results_summary['error'] = "Missing totalPerformance in summary data"
                except Exception as e:
                    results_summary['error'] = f"Failed to parse summary file: {str(e)}"
            else:
                results_summary['error'] = "No summary file found in backtest folder"
            
            
            # Get version from strategy file name (e.g., "strategy_v1_0_2.py" -> "1_0_2")
            strategy_filename = os.path.basename(abs_strategy_path)
            version_match = re.search(r'strategy_v([\d_]+)\.py$', strategy_filename)
            if not version_match:
                self.logger.error(f"Could not extract version from strategy filename: {strategy_filename}")
                return
                
            version = version_match.group(1)
            
            # Find matching version in version history
            version_entry = None
            for entry in version_history:
                # Extract version number from the stored version filename
                stored_version_match = re.search(r'strategy_v([\d_]+)\.py$', entry.get('version', ''))
                if stored_version_match and stored_version_match.group(1) == version:
                    version_entry = entry
                    break
                    
            if not version_entry:
                self.logger.error(f"Version {version} not found in version history")
                return
                
            # Add new backtest result to the correct version
            if 'backtests' not in version_entry:
                version_entry['backtests'] = []
            
            # Store absolute paths for reference
            abs_backtest_folder = os.path.abspath(backtest_folder)
            
            version_entry['backtests'].append({
                'errors': errors,
                'backtest_successful': backtest_successful,
                'results-summary': results_summary,
                'backtest_folder': abs_backtest_folder,
                'timestamp': datetime.now().isoformat(),
                'failed_data_requests': failed_data_requests
            })
            
            # Save updated version history
            with open(version_history_path, 'w') as f:
                json.dump(version_history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to update version history: {str(e)}")


    def backtest_success_check(self, folder_path: str, console_output: str = ""):
        """
        Checks if the backtest was successful by analyzing console output, failed data requests, and log errors.
        Returns (success: bool, errors: list)
        """
        # First, check console output for errors
        console_errors = self.check_errors_in_console_output(console_output)
        if console_errors:
            return False, console_errors, []

        errors = []

        # Only if console output is clean, check other error sources
        failed_data_requests = self.check_for_failed_data_requests(folder_path)

        print(f"Checking backtest logs for errors in {folder_path}")
        errors += self.check_backtest_logs_for_errors(folder_path)
        print(f"Finished Checking backtest logs for errors in {folder_path}")

        # Only consider non-tracking-error messages when determining success
        real_errors = [err for err in errors if "STATISTICS:: TRACKING ERROR" not in err.upper()]
        success = len(real_errors) == 0
        return success, real_errors, failed_data_requests

    def check_errors_in_console_output(self, console_output: str) -> list:
        """
        Parse the Lean CLI console output and extract error messages.
        Returns a list of errors (empty if none).
        """
        errors = []
        lines = console_output.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if (
                ("error" in line.lower() and "tracking error" not in line.lower())
                or ("syntaxerror" in line.lower())
                or ("traceback" in line.lower())
            ):
                error_block = [line.rstrip()]
                i += 1
                # Capture indented traceback/code lines
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t") or lines[i].startswith("***") or lines[i].strip() == ""):
                    error_block.append(lines[i].rstrip())
                    i += 1
                errors.append("\n".join(error_block))
            else:
                i += 1
        return errors


    def check_backtest_logs_for_errors(self, folder_path: str) -> list:
        """
        Parse the backtest log.txt and extract multi-line error blocks.
        Returns a list of errors (empty if none).
        """
        import os

        log_path = os.path.join(folder_path, "log.txt")
        if not os.path.exists(log_path):
            return ["log.txt not found"]

        errors = []
        with open(log_path, "r") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i]
            # Only consider ERROR lines that aren't tracking error statistics
            if "ERROR" in line.upper() and "STATISTICS:: TRACKING ERROR" not in line.upper():
                error_block = [line.rstrip()]
                i += 1
                # Capture indented traceback lines
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                    error_block.append(lines[i].rstrip())
                    i += 1
                errors.append("\n".join(error_block))
            else:
                i += 1

        # Filter out any tracking error statistics that might have slipped through
        errors = [err for err in errors if "STATISTICS:: TRACKING ERROR" not in err.upper()]
        return errors


    def check_for_failed_data_requests(self, folder_path: str) -> list:
        """
        Checks for failed data requests files in the backtest output folder.
        Returns a list of failed data request entries.
        """
        failed_requests = []
        if not os.path.isdir(folder_path):
            return failed_requests

        for filename in os.listdir(folder_path):
            if filename.startswith("failed-data-requests-") and filename.endswith(".txt"):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, "r") as f:
                        lines = [line.strip() for line in f if line.strip()]
                        failed_requests.extend(lines)
                except Exception as e:
                    self.log_progress(f"Error reading {file_path}: {e}")
        return failed_requests