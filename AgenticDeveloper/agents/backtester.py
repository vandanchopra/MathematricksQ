import asyncio
import os
import re
from datetime import datetime
from typing import Dict, Optional

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
            backtest_successful, errors = self.backtest_success_check(folder_path=folder_path, console_output=stdout_str)
        else:
            backtest_successful = False
            errors = ["Backtest output folder not found"]

        return {
            "folder_path": folder_path,
            "backtest_successful": backtest_successful,
            "errors": errors
        }

    def backtest_success_check(self, folder_path: str, console_output: str = "") -> (bool, list):
        """
        Checks if the backtest was successful by analyzing console output, failed data requests, and log errors.
        Returns (success: bool, errors: list)
        """
        # First, check console output for errors
        console_errors = self.check_errors_in_console_output(console_output)
        if console_errors:
            return False, console_errors

        errors = []

        # Only if console output is clean, check other error sources
        errors += self.check_for_failed_data_requests(folder_path)

        print(f"Checking backtest logs for errors in {folder_path}")
        errors += self.check_backtest_logs_for_errors(folder_path)
        print(f"Finished Checking backtest logs for errors in {folder_path}")

        # Only consider non-tracking-error messages when determining success
        real_errors = [err for err in errors if "STATISTICS:: TRACKING ERROR" not in err.upper()]
        success = len(real_errors) == 0
        return success, real_errors

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