import asyncio
import os
import re
import sys
from datetime import datetime
from typing import Dict
import json

from .base import BaseAgent
from AgenticDeveloper.logger import get_logger

class BacktesterAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.logger = get_logger("BacktesterAgent")

    async def _prepare_backtest(self, strategy_path: str, mode: str) -> tuple[str, str]:
        """Prepare for backtest based on mode. Returns (strategy_path, command)."""
        if mode == "local":
            command = f"lean backtest '{strategy_path}'"
            return strategy_path, command
        elif mode == "cloud":
            strategy_folder = os.path.dirname(strategy_path)
            
            new_path = await self._rename_to_main(strategy_path)
            if not await self._cloud_push(strategy_folder):
                raise RuntimeError("Failed to push to cloud")
            else:
                command = "lean cloud backtest " + str(strategy_folder)
                return new_path, command
        elif mode == "random_data":
            raise NotImplementedError("Random data backtesting is not implemented yet.")
        else:
            raise ValueError(f"Unsupported mode: {mode}")

    async def _rename_to_main(self, strategy_path: str) -> str:
        """Copy strategy file to main.py in its directory while preserving original."""
        import shutil
        strategy_dir = os.path.dirname(strategy_path)
        new_path = os.path.join(strategy_dir, "main.py")
        try:
            if os.path.exists(new_path):
                os.remove(new_path)
            shutil.copy2(strategy_path, new_path)
            return new_path
        except Exception as e:
            self.logger.error(f"[Backtester] Copy failed - {e}")
            raise RuntimeError(f"Failed to copy strategy file to main.py: {e}")

    async def _cloud_push(self, strategy_folder: str) -> bool:
        """Push strategy to cloud. Returns success status."""
        try:
            cmd = "lean cloud push --project " + str(strategy_folder)
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # Store complete output while displaying in real-time
            stdout_chunks = []
            stderr_chunks = []
            
            # Read output in real-time
            async def read_stream(stream, chunks):
                try:
                    while True:
                        chunk = await stream.read(1)
                        if not chunk:
                            break
                        chunks.append(chunk)
                        # Print in real-time without buffering
                        sys.stdout.buffer.write(chunk)
                        sys.stdout.buffer.flush()
                except Exception as e:
                    self.logger.error(f"[Backtester] Stream error - {e}")
            
            # Run both readers concurrently and wait for completion
            await asyncio.gather(
                read_stream(process.stdout, stdout_chunks),
                read_stream(process.stderr, stderr_chunks)
            )
            
            # Wait for process to complete
            await process.wait()
            
            # Combine chunks into complete output
            stdout_str = b''.join(stdout_chunks).decode()
            stderr_str = b''.join(stderr_chunks).decode()
            
            # Check for errors in output
            if process.returncode != 0 or "error" in stdout_str.lower():
                self.logger.error("[Backtester] Push failed")
                if stdout_str:
                    self.logger.error(f"Output: {stdout_str}")
                if stderr_str:
                    self.logger.error(f"Error: {stderr_str}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"[Backtester] Push error - {e}")
            return False

    async def _execute_backtest(self, command: str) -> tuple[asyncio.subprocess.Process, str, str]:
        """Execute backtest command and return process, stdout, and stderr."""
        print(f"\n{command}\n")
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ
        )
        
        try:
            # Collect output while displaying real-time
            stdout_chunks = []
            stderr_chunks = []
            
            async def read_stream(stream, chunks):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    chunks.append(line)
                    # Print in real-time
                    sys.stdout.buffer.write(line)
                    sys.stdout.buffer.flush()
            
            # Read both streams concurrently
            await asyncio.gather(
                read_stream(process.stdout, stdout_chunks),
                read_stream(process.stderr, stderr_chunks)
            )
            
            # Wait for process completion
            await process.wait()
            
            # Combine chunks into strings
            stdout_str = b''.join(stdout_chunks).decode()
            stderr_str = b''.join(stderr_chunks).decode()
            
            if process.returncode != 0:
                self.logger.error(f"[Backtester] Command failed - code {process.returncode}")
            
            return process, stdout_str, stderr_str
            
        except asyncio.TimeoutError:
            self.logger.warning("[Backtester] Timeout after 5 minutes")
            process.terminate()
            await process.wait()
            return process, "", "Timeout after 5 minutes"
        except Exception as e:
            self.logger.error(f"[Backtester] Execution failed - {e}")
            return process, "", str(e)

    async def _read_lean_output(self) -> str:
        """Read output from lean CLI's latest output file"""
        try:
            # Get backtest folder path from lean CLI output
            output_locations = [
                "backtests/latest/log.txt",
                "backtests/latest/output.txt",
                os.path.join("Strategies", "AgenticDev", "AncientStoneGolem", "backtests", "latest", "log.txt"),
                os.path.join("Strategies", "AgenticDev", "AncientStoneGolem", "backtests", "latest", "output.txt")
            ]
            
            # Try reading from each possible location
            for location in output_locations:
                if os.path.exists(location):
                    with open(location, 'r') as f:
                        return f.read()
            
            self.logger.warning("[Backtester] No output files found")
            return ""
        except Exception as e:
            self.logger.error(f"[Backtester] Output read failed - {e}")
            return ""

    def _get_process_output(self, process_result: tuple[asyncio.subprocess.Process, str, str]) -> str:
        """Get stdout from process result and log any errors."""
        process, stdout_str, stderr_str = process_result
        
        if process.returncode != 0:
            self.logger.error(f"[Backtester] Process failed - code {process.returncode}")
            
        return stdout_str

    async def _create_backtest_folder(self, command_output: str, strategy_path: str, mode: str) -> tuple[str, str]:
        """Create or find backtest folder and return its path and timestamp"""
        strategy_dir = os.path.dirname(strategy_path)
        backtests_dir = os.path.join(strategy_dir, "backtests")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        if mode == "cloud":
            # For cloud mode, first check if Lean CLI already created a backtest folder
            latest_backtest = None
            if os.path.exists(backtests_dir):
                backtest_folders = [os.path.join(backtests_dir, d) for d in os.listdir(backtests_dir) if os.path.isdir(os.path.join(backtests_dir, d))]
                if backtest_folders:
                    latest_backtest = max(backtest_folders, key=os.path.getctime)
                    creation_time = os.path.getctime(latest_backtest)
                    time_diff = datetime.now().timestamp() - creation_time
                    # Use the latest folder if it was created in the last minute
                    if time_diff < 60:
                        return latest_backtest, os.path.basename(latest_backtest)

        backtest_folder = os.path.join(backtests_dir, timestamp)
        os.makedirs(backtests_dir, exist_ok=True)
        os.makedirs(backtest_folder, exist_ok=True)
        
        code_dir = os.path.join(backtest_folder, "code")
        os.makedirs(code_dir, exist_ok=True)
        
        strategy_filename = os.path.basename(strategy_path)
        if strategy_filename == "main.py":
            strategy_filename = [f for f in os.listdir(strategy_dir) if f.startswith("strategy_") and f.endswith(".py")][0]
            strategy_path = os.path.join(strategy_dir, strategy_filename)
            
        strategy_copy_path = os.path.join(code_dir, strategy_filename)
        import shutil
        shutil.copy2(strategy_path, strategy_copy_path)
        return backtest_folder, timestamp
    
    def _get_performance_data(self, mode: str, stdout_str: str, backtest_folder: str) -> Dict[str, str]:
        """Get performance data based on mode from appropriate source"""
        performance_data = {}
        
        if mode == "cloud":
            # For cloud mode, parse from console output
            performance_data = self._parse_performance_table(stdout_str)
        else:
            summary_files = [f for f in os.listdir(backtest_folder) if f.endswith('-summary.json')]
            if summary_files:
                summary_path = os.path.join(backtest_folder, summary_files[0])
                with open(summary_path, 'r') as f:
                    summary_data = json.load(f)
                    if 'totalPerformance' in summary_data:
                        performance_data = {
                            **summary_data['totalPerformance'].get('tradeStatistics', {}),
                            **summary_data['totalPerformance'].get('portfolioStatistics', {})
                        }
            else:
                self.logger.warning("[Backtester] No summary file found")
        
        return performance_data

    def _parse_performance_table(self, stdout_str: str) -> Dict[str, str]:
        """Parse performance table and statistics from output"""
        performance_data = {}
        
        # First try to parse STATISTICS:: format
        for line in stdout_str.splitlines():
            if 'STATISTICS::' in line:
                try:
                    parts = line.split('STATISTICS::', 1)[1].strip()
                    stat_name, stat_value = parts.split(':', 1)
                    stat_name = stat_name.strip()
                    stat_value = stat_value.strip()
                    if stat_name and stat_value:
                        performance_data[stat_name] = stat_value
                except Exception as e:
                    pass
        
        # Then try to parse table format
        try:
            in_table = False
            for line in stdout_str.splitlines():
                if '┌' in line:
                    in_table = True
                    continue
                if '└' in line:
                    in_table = False
                    continue
                
                if in_table and '│' in line and '──' not in line:
                    try:
                        parts = line.split('│')
                        parts = [p.strip() for p in parts if p.strip()]
                        for i in range(0, len(parts), 2):
                            if i + 1 < len(parts):
                                stat_name = parts[i].strip()
                                stat_value = parts[i + 1].strip()
                                if stat_name and stat_value:
                                    performance_data[stat_name] = stat_value
                    except Exception as e:
                        pass
        except Exception as e:
            self.logger.error(f"Error parsing performance table: {e}")
        return performance_data

    async def _create_backtest_output(self, stdout_str: str, strategy_path: str, mode: str) -> Dict:
        """Create consolidated backtest output"""
        try:
            backtest_folder = None
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            if mode == "local":
                backtest_folder = self._extract_backtest_folder_from_output(stdout_str)
                if backtest_folder:
                    timestamp = os.path.basename(backtest_folder)
            if not backtest_folder:
                strategy_dir = os.path.dirname(strategy_path)
                backtests_dir = os.path.join(strategy_dir, "backtests")
                backtest_folder = os.path.join(backtests_dir, timestamp)
                os.makedirs(backtests_dir, exist_ok=True)
                os.makedirs(backtest_folder, exist_ok=True)

            self._cleanup_code_directory(backtest_folder, strategy_path)
            
            # Initialize backtest output
            strategy_filename = os.path.basename(strategy_path)
            backtest_id = self._extract_backtest_id(stdout_str)
            backtest_output = self.get_backtest_output_template(strategy_filename, backtest_id)
            
            # Update basic fields
            backtest_output["backtest_success"] = ("┌────────────────────────────┬" in stdout_str) or ("STATISTICS::" in stdout_str)
            backtest_output["backtest_folder_path"] = backtest_folder
            backtest_output["backtest_console_output"] = stdout_str
            
            # Get performance data
            performance_data = self._get_performance_data(mode, stdout_str, backtest_folder)
            backtest_output["performance"] = performance_data
            error_messages, warning_messages = self.check_errors_in_console_output(stdout_str)
            
            if "warnings" not in backtest_output:
                backtest_output["warnings"] = []
            backtest_output["warnings"].extend(warning_messages)
            
            if error_messages:
                backtest_output["errors"].extend(error_messages)
                backtest_output["backtest_success"] = False
            
            # Extract and add metadata
            name = self._extract_backtest_name(stdout_str)
            url = self._extract_backtest_url(stdout_str)
            
            # Add metadata to output
            backtest_output["backtest_raw_data"].update({
                "timestamp": timestamp,
                "backtest_name": name,
                "backtest_url": url,
                "strategy_code_filepath": strategy_path.replace("main.py", "strategy_v1.py") if mode == "cloud" else strategy_path
            })
            # Save output files
            try:
                output_json_path = os.path.join(backtest_folder, 'backtest_output.json')
                with open(output_json_path, 'w') as f:
                    json.dump(backtest_output, f, indent=4)
                output_txt_path = os.path.join(backtest_folder, 'output.txt')
                with open(output_txt_path, 'w') as f:
                    f.write(stdout_str)
                
                
            except Exception as e:
                self.logger.error(f"[Backtester] Save failed - {e}")
            
            # Update version history
            self._update_version_history(strategy_path, backtest_folder, backtest_output["backtest_success"],
                                    backtest_output["errors"], backtest_output["warnings"], backtest_output["failed_data_requests"])
            
            return backtest_output
            
        except Exception as e:
            self.logger.error(f"[Backtester] Output creation failed - {e}")
            error_results = self.get_backtest_output_template(os.path.basename(strategy_path), "")
            error_results["errors"].append(str(e))
            return error_results

    async def run(self, strategy_path: str, mode: str = "local") -> Dict:
        """
        Run a backtest for the given strategy.
        mode: 'local', 'cloud', or 'random_data'
        Returns: dict with standardized backtest results
        """
        try:
            _strategy_path, command = await self._prepare_backtest(strategy_path, mode)
            process, stdout_str, stderr_str = await self._execute_backtest(command)
            original_strategy_path = _strategy_path.replace("main.py", os.path.basename(strategy_path)) if mode == "cloud" else strategy_path
            backtest_output = await self._create_backtest_output(stdout_str, original_strategy_path, mode)
            return backtest_output
            
        except Exception as e:
            self.logger.error(f"[Backtester] Run failed - {e}")
            error_results = self.get_backtest_output_template(os.path.basename(strategy_path), "")
            error_results["errors"].append(str(e))
            return error_results

    def _update_version_history(self, strategy_path: str, backtest_folder: str, backtest_successful: bool, errors: list, warnings: list, failed_data_requests: list) -> None:
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
                self.logger.error("[Backtester] AgenticDev dir not found")
                return
                
            # Get path to version_history.json
            version_history_path = os.path.join(strategy_dir,
                                              os.path.basename(os.path.dirname(abs_strategy_path)),
                                              "version_history.json")
            
            if not os.path.exists(version_history_path):
                self.logger.warning("[Backtester] Version history missing")
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
            
            
            # Get version from original strategy file name, not main.py
            strategy_filename = os.path.basename(strategy_path)
            if strategy_filename == "main.py":
                # Get original strategy file name from version history or error data
                if errors:
                    strategy_filename = os.path.basename(error_data["strategy_code_filepath"])
                else:
                    return  # Skip version history update if we can't determine the original file
                
            version_match = re.search(r'strategy_v(\d+(?:_\d+)*)\.py$', strategy_filename)
            if not version_match:
                self.logger.error(f"Could not extract version from original strategy filename: {strategy_filename}")
                return
                
            version = version_match.group(1)
            
            # Find matching version in version history
            version_entry = None
            for entry in version_history:
                # Extract version number from the stored version filename
                stored_version_match = re.search(r'strategy_v(\d+(?:_\d+)*)\.py$', entry.get('version', ''))
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
                'warnings': warnings,
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
            self.logger.error(f"[Backtester] History update failed - {e}")

    def _cleanup_code_directory(self, backtest_folder: str, strategy_path: str) -> None:
        """Clean up code directory by recreating it with only the target strategy."""
        import shutil
        code_dir = os.path.join(backtest_folder, "code")
        
        # Step 1: Delete code folder if it exists
        if os.path.exists(code_dir):
            shutil.rmtree(code_dir)
        
        os.makedirs(code_dir)
        
        strategy_filename = os.path.basename(strategy_path)
        if strategy_filename == "main.py":
            strategy_filename = os.path.basename(strategy_path.replace("main.py", os.path.basename(strategy_path)))
        
        strategy_copy_path = os.path.join(code_dir, strategy_filename)
        shutil.copy2(strategy_path, strategy_copy_path)
    
    def _extract_backtest_folder_from_output(self, stdout_str: str) -> str:
        """Extract backtest folder path from Lean CLI output"""
        for line in stdout_str.splitlines():
            if "Successfully ran" in line and "stored the output in" in line:
                match = re.search(r"stored the output in '([^']*)'", line)
                if match:
                    backtest_folder = match.group(1)
                    if os.path.exists(backtest_folder):
                        return backtest_folder
                    else:
                        self.logger.warning(f"Found folder path but it doesn't exist: {backtest_folder}")
        self.logger.warning("No valid backtest folder found in output")
        return None

    def _extract_backtest_id(self, output: str) -> str:
        """Extract backtest ID from the output."""
        match = re.search(r'Backtest id: ([a-f0-9]+)', output)
        return match.group(1) if match else ""

    def _extract_backtest_name(self, output: str) -> str:
        """Extract backtest name from the output."""
        match = re.search(r'Backtest name: (.+)$', output, re.MULTILINE)
        return match.group(1) if match else ""

    def _extract_backtest_url(self, output: str) -> str:
        """Extract backtest URL from the output."""
        match = re.search(r'Backtest url: (https://[^\s]+)', output)
        return match.group(1) if match else ""

    def check_errors_in_console_output(self, console_output: str) -> tuple[list, list]:
        """Check for error messages and warnings in the console output and extract multi-line blocks."""
        errors = []
        warnings = []
        lines = console_output.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            is_warning = "warning" in line.lower()
            is_error = (
                ("error" in line.lower() and "tracking error" not in line.lower())
                or ("syntaxerror" in line.lower())
                or ("traceback" in line.lower())
                or ("exception" in line.lower())
                or ("failed" in line.lower() and "failed data requests" not in line.lower())
                or ("could not" in line.lower())
                or ("unable to" in line.lower())
                or "compiler error" in line.lower()
            )
            
            if is_warning or is_error:
                message_block = [line.rstrip()]
                i += 1
                # Capture any related context (indented lines, stack traces, etc.)
                while i < len(lines) and (
                    lines[i].startswith(" ")
                    or lines[i].startswith("\t")
                    or lines[i].startswith("***")
                    or lines[i].strip() == ""
                    or "at line" in lines[i].lower()
                    or "file" in lines[i].lower()
                ):
                    message_block.append(lines[i].rstrip())
                    i += 1
                if is_warning:
                    warnings.append("\n".join(message_block))
                else:
                    errors.append("\n".join(message_block))
            else:
                i += 1
                
        return errors, warnings

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