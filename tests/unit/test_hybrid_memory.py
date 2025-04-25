"""Tests for the hybrid memory backend."""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the memory backends
from src.memory import HybridMemory

class TestHybridMemory(unittest.TestCase):
    """Test the hybrid memory backend."""

    def setUp(self):
        """Set up the test environment."""
        # Mock the Neo4j and PatANN backends
        self.neo4j_patcher = patch('MathematricksQ.src.memory.hybrid_backend.Neo4jMemory')
        self.patann_patcher = patch('MathematricksQ.src.memory.hybrid_backend.PatANNMemory')

        self.mock_neo4j = self.neo4j_patcher.start()
        self.mock_patann = self.patann_patcher.start()

        # Create mock instances
        self.mock_neo4j_instance = MagicMock()
        self.mock_patann_instance = MagicMock()

        self.mock_neo4j.return_value = self.mock_neo4j_instance
        self.mock_patann.return_value = self.mock_patann_instance

        # Create the hybrid memory instance
        self.memory = HybridMemory(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            patann_url="http://localhost:9200"
        )

    def tearDown(self):
        """Clean up after the test."""
        self.neo4j_patcher.stop()
        self.patann_patcher.stop()

    def test_store_idea(self):
        """Test storing an idea."""
        # Arrange
        idea_id = "idea1"
        description = "Buy when RSI is below 30"
        context_ids = ["btc_daily", "eth_daily"]

        # Act
        self.memory.store_idea(idea_id, description, context_ids)

        # Assert
        self.mock_neo4j_instance.store_idea.assert_called_once_with(idea_id, description, context_ids)
        self.mock_patann_instance.store_idea.assert_called_once_with(idea_id, description, context_ids)

    def test_store_context(self):
        """Test storing a context."""
        # Arrange
        context_id = "btc_daily"
        market = "BTC/USD"
        timeframe = "1d"

        # Act
        self.memory.store_context(context_id, market, timeframe)

        # Assert
        self.mock_neo4j_instance.store_context.assert_called_once_with(context_id, market, timeframe)
        self.mock_patann_instance.store_context.assert_called_once_with(context_id, market, timeframe)

    def test_store_backtest(self):
        """Test storing a backtest."""
        # Arrange
        backtest_id = "bt1"
        metrics = {"Sharpe": 1.5, "CAGR": 0.25, "MaxDrawdown": 0.15}
        idea_id = "idea1"
        context_id = "btc_daily"

        # Act
        self.memory.store_backtest(backtest_id, metrics, idea_id, context_id)

        # Assert
        self.mock_neo4j_instance.store_backtest.assert_called_once_with(backtest_id, metrics, idea_id, context_id)
        # PatANN doesn't store backtests
        self.mock_patann_instance.store_backtest.assert_not_called()

    def test_query_similar_ideas(self):
        """Test querying similar ideas."""
        # Arrange
        embedding = [0.1, 0.2, 0.3]
        context_id = "btc_daily"
        top_k = 5

        mock_ideas = [
            {"id": "idea1", "description": "Buy when RSI is below 30", "created_at": datetime.now()},
            {"id": "idea2", "description": "Sell when RSI is above 70", "created_at": datetime.now()}
        ]
        self.mock_patann_instance.query_similar_ideas.return_value = mock_ideas

        # Act
        result = self.memory.query_similar_ideas(embedding, context_id, top_k)

        # Assert
        self.mock_patann_instance.query_similar_ideas.assert_called_once_with(embedding, context_id, top_k)
        self.assertEqual(result, mock_ideas)

    def test_query_top_ideas_by_metrics(self):
        """Test querying top ideas by metrics."""
        # Arrange
        context_id = "btc_daily"
        metric = "Sharpe"
        weights = {"Sharpe": 0.6, "CAGR": 0.4}
        limit = 5

        mock_ideas = [
            {"id": "idea1", "description": "Buy when RSI is below 30", "created_at": datetime.now(), "metrics": {"Sharpe": 1.5}},
            {"id": "idea2", "description": "Sell when RSI is above 70", "created_at": datetime.now(), "metrics": {"Sharpe": 1.2}}
        ]
        self.mock_neo4j_instance.query_top_ideas_by_metrics.return_value = mock_ideas

        # Act
        result = self.memory.query_top_ideas_by_metrics(context_id, metric, weights, limit)

        # Assert
        self.mock_neo4j_instance.query_top_ideas_by_metrics.assert_called_once_with(context_id, metric, weights, limit)
        self.assertEqual(result, mock_ideas)

    def test_recommend_ideas(self):
        """Test recommending ideas using the hybrid approach."""
        # Arrange
        embedding = [0.1, 0.2, 0.3]
        context_id = "btc_daily"
        top_k = 3

        # Mock vector similarity results
        mock_similar_ideas = [
            {"id": "idea1", "description": "Buy when RSI is below 30", "created_at": datetime.now()},
            {"id": "idea2", "description": "Sell when RSI is above 70", "created_at": datetime.now()},
            {"id": "idea3", "description": "Buy on golden cross", "created_at": datetime.now()},
            {"id": "idea4", "description": "Sell on death cross", "created_at": datetime.now()}
        ]
        self.mock_patann_instance.query_similar_ideas.return_value = mock_similar_ideas

        # Mock graph re-ranking results
        mock_ranked_ideas = [
            {"id": "idea2", "description": "Sell when RSI is above 70", "created_at": datetime.now(), "metrics": {"Sharpe": 1.5}},
            {"id": "idea1", "description": "Buy when RSI is below 30", "created_at": datetime.now(), "metrics": {"Sharpe": 1.2}}
        ]
        self.mock_neo4j_instance.query_top_ideas_by_metrics.return_value = mock_ranked_ideas

        # Act
        result = self.memory.recommend_ideas(embedding, context_id, top_k)

        # Assert
        self.mock_patann_instance.query_similar_ideas.assert_called_once_with(embedding=embedding, context_id=context_id, top_k=top_k*2)
        self.mock_neo4j_instance.query_top_ideas_by_metrics.assert_called_once()
        self.assertEqual(len(result), 3)  # Should return top_k results
        self.assertEqual(result[0]["id"], "idea2")  # First result should be the top ranked idea
        self.assertEqual(result[1]["id"], "idea1")  # Second result should be the second ranked idea
        # Third result should be from the vector similarity results (not in ranked ideas)
        self.assertTrue(result[2]["id"] in ["idea3", "idea4"])

if __name__ == "__main__":
    unittest.main()
