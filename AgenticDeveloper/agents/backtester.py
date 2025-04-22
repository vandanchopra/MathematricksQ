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
        self.logger.info(f"Preparing backtest in {mode} mode for {strategy_path}")
        if mode == "local":
            command = f"lean backtest '{strategy_path}'"
            self.logger.info(f"Using local backtest command: {command}")
            return strategy_path, command
        elif mode == "cloud":
            self.logger.info("Starting cloud backtest preparation...")
            strategy_folder = os.path.dirname(strategy_path)
            self.logger.info(f"Strategy folder: {strategy_folder}")
            
            new_path = await self._rename_to_main(strategy_path)
            if not await self._cloud_push(strategy_folder):
                raise RuntimeError("Failed to push to cloud")
            else:
                self.logger.info(f"Cloud push successful for {strategy_folder}")
                
            command = "lean cloud backtest " + str(strategy_folder)
            self.logger.info(f"Using cloud backtest command: {command}")
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
        self.logger.info(f"Copying {strategy_path} to {new_path}")
        try:
            if os.path.exists(new_path):
                self.logger.info(f"Removing existing {new_path}")
                os.remove(new_path)
            shutil.copy2(strategy_path, new_path)
            self.logger.info("Successfully copied strategy to main.py")
            return new_path
        except Exception as e:
            self.logger.error(f"Failed to copy strategy file to main.py: {e}")
            raise RuntimeError(f"Failed to copy strategy file to main.py: {e}")

    async def _cloud_push(self, strategy_folder: str) -> bool:
        """Push strategy to cloud. Returns success status."""
        try:
            # Use --project option to specify the strategy folder
            cmd = "lean cloud push --project " + str(strategy_folder)
            self.logger.info(f"Executing: {cmd}")
            
            # Show real-time output but also capture for error checking
            # Set env var to disable output buffering
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
                    self.logger.error(f"Error reading stream: {e}")
            
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
                self.logger.error("Cloud push failed")
                if stdout_str:
                    self.logger.error(f"Output: {stdout_str}")
                if stderr_str:
                    self.logger.error(f"Error: {stderr_str}")
                return False
            
            self.logger.info("Cloud push completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to push to cloud: {e}")
            return False

    async def _execute_backtest(self, command: str) -> tuple[asyncio.subprocess.Process, str, str]:
        """Execute backtest command and return process, stdout, and stderr."""
        self.logger.info(f"Executing backtest command: {command}")
        
        # Show command being executed with visual separator
        separator = f"{'='*80}"
        print(f"\n{separator}")
        print(f"BACKTESTER: Executing command")
        print(f"COMMAND: {command}")
        print(f"{separator}\n")
        
        # Create process with pipes for stdout/stderr
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ
        )
        
        self.logger.info(f"Process started with PID: {process.pid}")
        
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
            
            self.logger.debug(f"Read {len(stdout_str)} bytes from log files")
            
            if process.returncode != 0:
                self.logger.error(f"Command failed with return code {process.returncode}")
            else:
                self.logger.info("Command completed successfully")
            
            return process, stdout_str, stderr_str
            
        except asyncio.TimeoutError:
            self.logger.warning("Backtest timed out after 5 minutes")
            process.terminate()
            await process.wait()
            return process, "", "Timeout after 5 minutes"
        except Exception as e:
            self.logger.error(f"Error during backtest: {e}")
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
                    self.logger.debug(f"Reading output from: {location}")
                    with open(location, 'r') as f:
                        content = f.read()
                        self.logger.debug(f"Read {len(content)} bytes from {location}")
                        return content
            
            self.logger.warning("No output files found in standard locations")
            return ""
        except Exception as e:
            self.logger.error(f"Error reading lean output: {e}")
            return ""

    def _get_process_output(self, process_result: tuple[asyncio.subprocess.Process, str, str]) -> str:
        """Get stdout from process result and log any errors."""
        process, stdout_str, stderr_str = process_result
        
        if process.returncode != 0:
            self.logger.error(f"Process failed with return code {process.returncode}")
            
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
                        self.logger.info(f"Using existing backtest folder: {latest_backtest}")
                        return latest_backtest, os.path.basename(latest_backtest)

        # Create new folder if needed
        backtest_folder = os.path.join(backtests_dir, timestamp)
        os.makedirs(backtests_dir, exist_ok=True)
        os.makedirs(backtest_folder, exist_ok=True)
        
        # Create standard folders
        code_dir = os.path.join(backtest_folder, "code")
        os.makedirs(code_dir, exist_ok=True)
        
        # Save strategy code
        strategy_filename = os.path.basename(strategy_path)
        if strategy_filename == "main.py":
            strategy_filename = [f for f in os.listdir(strategy_dir) if f.startswith("strategy_") and f.endswith(".py")][0]
            strategy_path = os.path.join(strategy_dir, strategy_filename)
            
        strategy_copy_path = os.path.join(code_dir, strategy_filename)
        self.logger.info(f"Saving strategy code to: {strategy_copy_path}")
        import shutil
        shutil.copy2(strategy_path, strategy_copy_path)
        
        self.logger.info(f"Created backtest folder at: {backtest_folder}")
        return backtest_folder, timestamp
    
    def _parse_performance_table(self, stdout_str: str) -> Dict[str, str]:
        """Parse performance table and statistics from output"""
        performance_data = {}
        
        # Log input for debugging
        self.logger.debug("Starting performance table parsing")
        self.logger.debug(f"Input string length: {len(stdout_str)}")
        
        # First try to parse STATISTICS:: format
        for line in stdout_str.splitlines():
            if 'STATISTICS::' in line:
                self.logger.debug(f"Found STATISTICS:: line: {line}")
                try:
                    # Split on STATISTICS:: and then on first colon
                    parts = line.split('STATISTICS::', 1)[1].strip()
                    stat_name, stat_value = parts.split(':', 1)
                    stat_name = stat_name.strip()
                    stat_value = stat_value.strip()
                    if stat_name and stat_value:
                        self.logger.debug(f"Added stat: {stat_name} = {stat_value}")
                        performance_data[stat_name] = stat_value
                except Exception as e:
                    self.logger.debug(f"Error parsing statistics line: {e}")
        
        # Then try to parse table format
        try:
            in_table = False
            for line in stdout_str.splitlines():
                if '┌' in line:
                    self.logger.debug("Found start of table")
                    in_table = True
                    continue
                if '└' in line:
                    self.logger.debug("Found end of table")
                    in_table = False
                    continue
                
                if in_table and '│' in line and '──' not in line:
                    self.logger.debug(f"Processing table row: {line}")
                    try:
                        parts = line.split('│')
                        # Skip empty parts and get pairs
                        parts = [p.strip() for p in parts if p.strip()]
                        for i in range(0, len(parts), 2):
                            if i + 1 < len(parts):
                                stat_name = parts[i].strip()
                                stat_value = parts[i + 1].strip()
                                if stat_name and stat_value:
                                    self.logger.debug(f"Added table stat: {stat_name} = {stat_value}")
                                    performance_data[stat_name] = stat_value
                    except Exception as e:
                        self.logger.debug(f"Error parsing table row: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing performance table: {e}")
        
        # Log results
        self.logger.debug(f"Parsed {len(performance_data)} performance metrics")
        self.logger.debug(f"Performance data: {performance_data}")
        
        self.logger.debug(f"Parsed performance data: {performance_data}")
        return performance_data

    async def _create_backtest_output(self, stdout_str: str, strategy_path: str, mode: str) -> Dict:
        """Create consolidated backtest output"""
        try:
            self.logger.debug("Creating backtest output...")
            
            # For local mode, try to extract backtest folder from output first
            backtest_folder = None
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.logger.info({'mode': mode})
            if mode == "local":
                backtest_folder = self._extract_backtest_folder_from_output(stdout_str)
                if backtest_folder:
                    timestamp = os.path.basename(backtest_folder)
                    self.logger.info(f"Using lean backtest folder: {backtest_folder}")
            
            # Create new folder if lean didn't create one
            if not backtest_folder:
                strategy_dir = os.path.dirname(strategy_path)
                backtests_dir = os.path.join(strategy_dir, "backtests")
                backtest_folder = os.path.join(backtests_dir, timestamp)
                os.makedirs(backtests_dir, exist_ok=True)
                os.makedirs(backtest_folder, exist_ok=True)
                self.logger.info(f"Created new backtest folder: {backtest_folder}")
            
            # Clean up the code directory after backtest completes
            code_dir = os.path.join(backtest_folder, "code")
            
            # Wait for files to be copied (max 10 seconds)
            max_wait = 10
            wait_interval = 0.5
            total_waited = 0
            last_file_count = 0
            stable_count = 0
            
            while total_waited < max_wait:
                if os.path.exists(code_dir):
                    current_files = os.listdir(code_dir)
                    current_count = len(current_files)
                    self.logger.info(f"Found {current_count} files after waiting {total_waited}s: {current_files}")
                    
                    if current_count == last_file_count:
                        stable_count += 1
                        if stable_count >= 4:  # Files stable for 2 seconds
                            break
                    else:
                        stable_count = 0
                        last_file_count = current_count
                        
                await asyncio.sleep(wait_interval)
                total_waited += wait_interval
            
            if os.path.exists(code_dir):
                self.logger.info(f"Starting code directory cleanup in {mode} mode")
                # Get target strategy filename
                target_strategy = os.path.basename(strategy_path)
                if target_strategy == "main.py":
                    target_strategy = os.path.basename(strategy_path.replace("main.py", os.path.basename(strategy_path)))
                self.logger.info(f"Target strategy to keep: {target_strategy}")
                
                # List files before cleanup
                before_files = os.listdir(code_dir)
                self.logger.info(f"Files before cleanup: {before_files}")
                
                # Remove all files except target strategy
                for file in before_files:
                    if file != target_strategy and file.endswith('.py'):
                        file_path = os.path.join(code_dir, file)
                        try:
                            os.remove(file_path)
                            self.logger.info(f"Removed: {file}")
                        except Exception as e:
                            self.logger.error(f"Error removing {file}: {e}")
                
                # Verify cleanup
                after_files = os.listdir(code_dir)
                self.logger.info(f"Files after cleanup: {after_files}")
                
                # Remove all files except target strategy
                for file in os.listdir(code_dir):
                    if file != target_strategy and file.endswith('.py'):
                        file_path = os.path.join(code_dir, file)
                        try:
                            os.remove(file_path)
                            self.logger.info(f"Removed: {file}")
                        except Exception as e:
                            self.logger.error(f"Error removing {file}: {e}")
                
                # Verify cleanup
                after_files = os.listdir(code_dir)
                self.logger.info(f"Files after cleanup: {after_files}")
            
            # Initialize backtest output
            strategy_filename = os.path.basename(strategy_path)
            backtest_id = self._extract_backtest_id(stdout_str)
            backtest_output = self.get_backtest_output_template(strategy_filename, backtest_id)
            
            # Update basic fields
            backtest_output["backtest_success"] = ("┌────────────────────────────┬" in stdout_str) or ("STATISTICS::" in stdout_str)
            backtest_output["backtest_folder_path"] = backtest_folder
            backtest_output["backtest_console_output"] = stdout_str
            
            # Parse performance table
            self.logger.debug("Parsing performance data from output...")
            self.logger.info("Parsing performance data from output...")
            performance_data = self._parse_performance_table(stdout_str)
            backtest_output["performance"] = performance_data
            self.logger.info(f"Found {len(performance_data)} performance metrics")
            for key, value in performance_data.items():
                self.logger.info(f"  {key}: {value}")
            
            # Check for errors
            self.logger.debug("Checking for errors in output...")
            error_messages = self.check_errors_in_console_output(stdout_str)
            if error_messages:
                backtest_output["errors"].extend(error_messages)
                backtest_output["backtest_success"] = False
                self.logger.debug(f"Found errors: {error_messages}")
            
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
            
            self.logger.debug(f"Metadata extracted - Name: {name}, URL: {url}")
            
            # Save both output files
            try:
                # Save backtest_output.json
                output_json_path = os.path.join(backtest_folder, 'backtest_output.json')
                self.logger.debug(f"Saving backtest output to: {output_json_path}")
                with open(output_json_path, 'w') as f:
                    json.dump(backtest_output, f, indent=4)
                
                # Save raw output
                output_txt_path = os.path.join(backtest_folder, 'output.txt')
                self.logger.debug(f"Saving raw output to: {output_txt_path}")
                with open(output_txt_path, 'w') as f:
                    f.write(stdout_str)
                
                self.logger.info(f"Results saved:")
                self.logger.info(f"  - JSON: {output_json_path}")
                self.logger.info(f"  - Output: {output_txt_path}")
                self.logger.info(f"Results saved in {backtest_folder}")
                
            except Exception as e:
                self.logger.error(f"Error saving output files: {e}")
            
            # Update version history
            self._update_version_history(strategy_path, backtest_folder, backtest_output["backtest_success"],
                                    backtest_output["errors"], backtest_output["failed_data_requests"])
            
            return backtest_output
            
        except Exception as e:
            self.logger.error(f"Failed to create backtest output: {e}")
            error_results = self.get_backtest_output_template(os.path.basename(strategy_path), "")
            error_results["errors"].append(str(e))
            return error_results

    async def run(self, strategy_path: str, mode: str = "local") -> Dict:
        """
        Run a backtest for the given strategy.
        mode: 'local', 'cloud', or 'random_data'
        Returns: dict with standardized backtest results
        """
        self.logger.info(f"Starting backtest for {strategy_path} in mode: {mode}")

        try:
            # 1. Mode-specific setup
            self.logger.info("Step 1: Preparing backtest setup...")
            _strategy_path, command = await self._prepare_backtest(strategy_path, mode)
            self.logger.info(f"Prepared strategy at {_strategy_path} with command: {command}")
            # 2. Execute backtest and process results
            self.logger.info("Step 2: Executing backtest...")
            process, stdout_str, stderr_str = await self._execute_backtest(command)
            # 3. Create and return backtest output
            self.logger.info("Step 3: Creating backtest output...")
            # In cloud mode, we need to convert from main.py path back to original strategy path
            original_strategy_path = _strategy_path.replace("main.py", os.path.basename(strategy_path)) if mode == "cloud" else strategy_path
            self.logger.info(f"Using path for output: {original_strategy_path}")
            backtest_output = await self._create_backtest_output(stdout_str, original_strategy_path, mode)
            self.logger.info(f"Backtest completed. Success: {backtest_output['backtest_success']}")
            return backtest_output
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {str(e)}")
            error_results = self.get_backtest_output_template(os.path.basename(strategy_path), "")
            error_results["errors"].append(str(e))
            return error_results

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

    def _extract_backtest_folder_from_output(self, stdout_str: str) -> str:
        """Extract backtest folder path from Lean CLI output"""
        self.logger.debug("Searching for backtest folder in output...")
        self.logger.info({'stdout_str': stdout_str[-1000:]})
        for line in stdout_str.splitlines():
            if "Successfully ran" in line and "stored the output in" in line:
                self.logger.debug(f"Found matching line: {line}")
                # Extract path between quotes after "stored the output in"
                match = re.search(r"stored the output in '([^']*)'", line)
                if match:
                    backtest_folder = match.group(1)
                    if os.path.exists(backtest_folder):
                        self.logger.info(f"Found and verified lean backtest folder: {backtest_folder}")
                        return backtest_folder
                    else:
                        self.logger.warning(f"Found folder path but it doesn't exist: {backtest_folder}")
                else:
                    self.logger.debug(f"Could not extract folder path from line: {line}")
            else:
                self.logger.debug(f"Line did not match pattern: {line}")
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

    def check_errors_in_console_output(self, console_output: str) -> list:
        """Check for error messages in the console output and extract multi-line error blocks."""
        errors = []
        lines = console_output.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            # Look for error indicators
            if (
                ("error" in line.lower() and "tracking error" not in line.lower())
                or ("syntaxerror" in line.lower())
                or ("traceback" in line.lower())
                or ("exception" in line.lower())
                or ("failed" in line.lower() and "failed data requests" not in line.lower())
                or ("could not" in line.lower())
                or ("unable to" in line.lower())
                or "warning" in line.lower()
                or "compiler error" in line.lower()
            ):
                error_block = [line.rstrip()]
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
                    error_block.append(lines[i].rstrip())
                    i += 1
                errors.append("\n".join(error_block))
            else:
                i += 1
                
        # Log found errors for debugging
        if errors:
            self.logger.debug(f"Found errors in console output: {errors}")
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