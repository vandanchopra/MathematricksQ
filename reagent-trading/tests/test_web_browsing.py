#!/usr/bin/env python3
"""
Tests for the web browsing capabilities in the ReAgent trading system.
These tests verify that the web browsing functionality works correctly.
"""

import os
import sys
import json
import time
import unittest
import subprocess
import requests
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

class WebBrowsingTests(unittest.TestCase):
    """Tests for the web browsing capabilities in the ReAgent trading system."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        cls.base_dir = Path(__file__).parent.parent
        cls.docker_dir = cls.base_dir / "docker"
        
        # Start the browser container
        print("Starting browser container...")
        subprocess.run(
            ["docker-compose", "up", "-d", "puppeteer"], 
            cwd=str(cls.docker_dir), 
            check=True
        )
        
        # Wait for the container to be ready
        print("Waiting for browser container to be ready...")
        time.sleep(10)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment."""
        # Stop the browser container
        print("Stopping browser container...")
        subprocess.run(
            ["docker-compose", "down"], 
            cwd=str(cls.docker_dir), 
            check=True
        )
    
    def test_01_browser_running(self):
        """Test that the browser container is running."""
        result = subprocess.run(
            ["docker-compose", "ps"], 
            cwd=str(self.docker_dir), 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Check that the browser container is running
        self.assertIn("puppeteer", result.stdout, "Browser container is not running")
        self.assertIn("Up", result.stdout, "Browser container is not running")
        
        print("Browser container is running")
    
    def test_02_browser_accessible(self):
        """Test that the browser is accessible."""
        try:
            response = requests.get("http://localhost:3000/")
            self.assertEqual(response.status_code, 200, "Browser is not accessible")
            print("Browser is accessible")
        except requests.exceptions.ConnectionError:
            self.fail("Browser is not accessible")
    
    def test_03_browser_functionality(self):
        """Test the browser functionality."""
        # Create a simple HTML file to test the browser
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Browser Test</title>
        </head>
        <body>
            <h1>Browser Test</h1>
            <p>This is a test of the browser functionality.</p>
        </body>
        </html>
        """
        
        test_html_path = self.base_dir / "browser_test.html"
        with open(test_html_path, "w") as f:
            f.write(test_html)
        
        try:
            # Start a simple HTTP server to serve the test HTML
            server_process = subprocess.Popen(
                ["python3", "-m", "http.server", "8000"],
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for the server to start
            time.sleep(5)
            
            # Test that the server is running
            try:
                response = requests.get("http://localhost:8000/browser_test.html")
                self.assertEqual(response.status_code, 200, "HTTP server is not running")
                print("HTTP server is running")
            except requests.exceptions.ConnectionError:
                self.fail("HTTP server is not running")
            
            # Test the browser functionality
            # This is a simplified test - in a real test, we would use the WebSearchAgent
            # to search for information and verify the results
            print("Testing browser functionality...")
            
            # Use curl to test the browser API
            result = subprocess.run(
                [
                    "curl", "-X", "POST", 
                    "http://localhost:3000/content", 
                    "-H", "Content-Type: application/json", 
                    "-d", '{"url": "http://localhost:8000/browser_test.html"}'
                ], 
                capture_output=True, 
                text=True
            )
            
            # Print the output for debugging
            print("Browser API output:")
            print(result.stdout)
            
            # Check that the browser API returned the expected content
            self.assertEqual(result.returncode, 0, "Browser API request failed")
            self.assertIn("Browser Test", result.stdout, "Browser API did not return the expected content")
            
            print("Browser functionality works correctly")
            
        finally:
            # Stop the HTTP server
            server_process.terminate()
            server_process.wait()
            
            # Remove the test HTML file
            if test_html_path.exists():
                os.remove(test_html_path)
    
    def test_04_web_search_agent(self):
        """Test the WebSearchAgent."""
        # Build the TypeScript code
        print("Building TypeScript code...")
        subprocess.run(["npm", "run", "build"], cwd=str(self.base_dir), check=True)
        
        # Run the WebSearchAgent
        print("Running WebSearchAgent...")
        result = subprocess.run(
            ["node", "dist/cli.js", "search", "SMA crossover strategy"], 
            cwd=str(self.base_dir), 
            capture_output=True, 
            text=True
        )
        
        # Print the output for debugging
        print("WebSearchAgent output:")
        print(result.stdout)
        
        if result.returncode != 0:
            print("WebSearchAgent error:")
            print(result.stderr)
        
        # Check that the WebSearchAgent ran successfully
        self.assertEqual(result.returncode, 0, "WebSearchAgent failed")
        self.assertIn("Searching for: SMA crossover strategy", result.stdout, "WebSearchAgent did not run correctly")
        
        print("WebSearchAgent ran successfully")

if __name__ == "__main__":
    unittest.main()
