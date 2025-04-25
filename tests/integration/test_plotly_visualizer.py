#!/usr/bin/env python3
"""
Integration tests for the PlotlyVisualizer using real Neo4j data
"""

import os
import sys
import unittest
import logging
import time

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# Import the necessary modules
from src.memory.hybrid_backend import HybridMemory
from src.memory.plotly_visualizer import PlotlyVisualizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PlotlyVisualizerTest")

class TestPlotlyVisualizer(unittest.TestCase):
    """Integration tests for the PlotlyVisualizer class using real Neo4j data."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment once for all tests."""
        logger.info("Setting up test environment...")

        # Initialize the memory system
        cls.memory = HybridMemory(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            patann_url="http://localhost:9200",
            model_name="all-MiniLM-L6-v2"
        )

        # Clear the database
        with cls.memory.graph_backend.driver.session() as session:
            session.run("""
            MATCH (n)
            DETACH DELETE n
            """)

        # Set up test data
        cls._setup_test_data()

        # Initialize the visualizer
        cls.visualizer = PlotlyVisualizer(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )

    @classmethod
    def _setup_test_data(cls):
        """Set up test data in Neo4j."""
        # Store contexts
        contexts = [
            {"id": "btc_daily", "market": "BTC/USD", "timeframe": "1d"},
            {"id": "eth_daily", "market": "ETH/USD", "timeframe": "1d"},
            {"id": "btc_hourly", "market": "BTC/USD", "timeframe": "1h"}
        ]

        for context in contexts:
            cls.memory.store_context(context["id"], context["market"], context["timeframe"])
            logger.info(f"Stored context: {context['id']}")

        # Store ideas
        ideas = [
            {"id": "idea1", "description": "Buy when RSI is below 30", "contexts": ["btc_daily", "eth_daily"]},
            {"id": "idea2", "description": "Sell when RSI is above 70", "contexts": ["btc_daily", "eth_daily"]},
            {"id": "idea3", "description": "Buy on golden cross (50 SMA crosses above 200 SMA)", "contexts": ["btc_daily"]},
            {"id": "idea4", "description": "Sell on death cross (50 SMA crosses below 200 SMA)", "contexts": ["btc_daily"]},
            {"id": "idea5", "description": "Buy when price is 10% below 20-day moving average", "contexts": ["btc_hourly"]}
        ]

        for idea in ideas:
            cls.memory.store_idea(idea["id"], idea["description"], idea["contexts"])
            logger.info(f"Stored idea: {idea['id']}")

        # Store backtests
        backtests = [
            {"id": "bt1", "metrics": {"Sharpe": 1.5, "CAGR": 0.25, "MaxDrawdown": 0.15}, "idea_id": "idea1", "context_id": "btc_daily"},
            {"id": "bt2", "metrics": {"Sharpe": 1.2, "CAGR": 0.20, "MaxDrawdown": 0.18}, "idea_id": "idea2", "context_id": "btc_daily"},
            {"id": "bt3", "metrics": {"Sharpe": 0.8, "CAGR": 0.15, "MaxDrawdown": 0.25}, "idea_id": "idea3", "context_id": "btc_daily"},
            {"id": "bt4", "metrics": {"Sharpe": 1.0, "CAGR": 0.18, "MaxDrawdown": 0.20}, "idea_id": "idea4", "context_id": "btc_daily"},
            {"id": "bt5", "metrics": {"Sharpe": 1.8, "CAGR": 0.30, "MaxDrawdown": 0.12}, "idea_id": "idea5", "context_id": "btc_hourly"}
        ]

        for backtest in backtests:
            cls.memory.store_backtest(backtest["id"], backtest["metrics"], backtest["idea_id"], backtest["context_id"])
            logger.info(f"Stored backtest: {backtest['id']}")

        # Store scenarios
        scenarios = [
            {"id": "scenario1", "description": "RSI(14) < 30 on 4h timeframe", "parent_idea_id": "idea1", "contexts": ["btc_daily"]},
            {"id": "scenario2", "description": "RSI(7) < 25 with volume confirmation", "parent_idea_id": "idea1", "contexts": ["btc_daily"]}
        ]

        for scenario in scenarios:
            cls.memory.store_scenario(scenario["id"], scenario["description"], scenario["parent_idea_id"], scenario["contexts"])
            logger.info(f"Stored scenario: {scenario['id']}")

        # Wait a moment for Neo4j to process all the data
        time.sleep(1)

        logger.info("Test data setup complete!")

    def test_fetch_edges(self):
        """Test the fetch_edges method with real Neo4j data."""
        # Call the method
        edges = self.visualizer.fetch_edges(limit=10)

        # Check that edges were returned
        self.assertTrue(len(edges) > 0, "No edges were returned")

        # Check that the expected edges are present
        edge_pairs = set(edges)
        self.assertIn(("idea1", "bt1"), edge_pairs, "Expected edge (idea1, bt1) not found")
        self.assertIn(("bt1", "btc_daily"), edge_pairs, "Expected edge (bt1, btc_daily) not found")

    def test_fetch_scenario_edges(self):
        """Test the fetch_scenario_edges method with real Neo4j data."""
        # Initialize node_labels
        self.visualizer.node_labels = {}

        # Call the method
        edges = self.visualizer.fetch_scenario_edges(limit=10)

        # Check that edges were returned
        self.assertTrue(len(edges) > 0, "No scenario edges were returned")

        # Check that the expected edges are present
        edge_pairs = set(edges)
        self.assertIn(("scenario1", "idea1"), edge_pairs, "Expected edge (scenario1, idea1) not found")

    def test_get_node_types(self):
        """Test the get_node_types method with real node labels."""
        # Set up node labels by fetching edges first
        self.visualizer.node_labels = {}
        self.visualizer.fetch_edges(limit=10)
        self.visualizer.fetch_scenario_edges(limit=10)

        # Call the method
        node_types = self.visualizer.get_node_types()

        # Check that node types were returned
        self.assertTrue(len(node_types) > 0, "No node types were returned")

        # Check that the expected node types are present
        self.assertIn("idea1", node_types, "Node idea1 not found in node_types")
        self.assertIn("bt1", node_types, "Node bt1 not found in node_types")
        self.assertIn("btc_daily", node_types, "Node btc_daily not found in node_types")

    def test_visualize(self):
        """Test the visualize method with real Neo4j data."""
        # Call the method
        fig = self.visualizer.visualize(limit=10, output_file="test_knowledge_graph.html")

        # Check that a figure was returned
        self.assertIsNotNone(fig, "No figure was returned")

        # Check that the output file was created
        self.assertTrue(os.path.exists("test_knowledge_graph.html"), "Output file was not created")

    def test_visualize_metrics(self):
        """Test the visualize_metrics method with real Neo4j data."""
        # Call the method
        fig = self.visualizer.visualize_metrics(metric="Sharpe", limit=5, output_file="test_metrics.html")

        # Check that a figure was returned
        self.assertIsNotNone(fig, "No figure was returned")

        # Check that the output file was created
        self.assertTrue(os.path.exists("test_metrics.html"), "Output file was not created")

    def test_visualize_context_performance(self):
        """Test the visualize_context_performance method with real Neo4j data."""
        # Call the method
        fig = self.visualizer.visualize_context_performance(
            context_id="btc_daily",
            metric="Sharpe",
            limit=5,
            output_file="test_context_performance.html"
        )

        # Check that a figure was returned
        self.assertIsNotNone(fig, "No figure was returned")

        # Check that the output file was created
        self.assertTrue(os.path.exists("test_context_performance.html"), "Output file was not created")

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Close the visualizer
        cls.visualizer.close()

        # Clean up output files
        for file in ["test_knowledge_graph.html", "test_metrics.html", "test_context_performance.html"]:
            if os.path.exists(file):
                os.remove(file)

        logger.info("Test environment cleaned up.")

if __name__ == '__main__':
    unittest.main()
