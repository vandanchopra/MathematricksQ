# src/memory/patann_backend.py
import requests
import json
import os
from typing import List, Dict, Any, Optional, Union, cast
from datetime import datetime
from sentence_transformers import SentenceTransformer
from .interface import MemoryBackend, IdeaDict, ScenarioDict, ContextDict, BacktestDict, MetricsDict

import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PatANN-Client")

class PatANN:
    """Client for interacting with PatAnn vector database using HTTP API."""

    def __init__(self, url: str = "http://localhost:9200"):
        """Initialize the PatAnn client.

        Args:
            url: The URL of the PatAnn server
        """
        self.url = url.rstrip('/')
        self.headers = {"Content-Type": "application/json"}

        # Initialize metadata storage for fallback
        self.metadata = {}

        # Test connection
        try:
            response = requests.get(f"{self.url}/health")
            if response.status_code == 200:
                logger.info(f"Connected to PatANN server at {self.url}")
                self.server_available = True
            else:
                logger.warning(f"PatANN server at {self.url} returned status code {response.status_code}")
                self.server_available = False
        except Exception as e:
            logger.warning(f"Could not connect to PatANN server at {self.url}: {str(e)}")
            logger.info("Using local fallback implementation for testing purposes.")
            self.server_available = False

    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]):
        """Insert or update a vector in the database.

        Args:
            id: Unique identifier for the vector
            vector: The vector to insert
            metadata: Optional metadata to store with the vector
        """
        # Always store metadata locally for fallback
        self.metadata[id] = {
            "vector": vector,
            "metadata": metadata
        }

        if not self.server_available:
            return {"id": id, "status": "stored_locally"}

        try:
            # Prepare the request payload
            payload = {
                "id": id,
                "vector": vector,
                "metadata": metadata
            }

            # Send the request to the PatANN server
            response = requests.post(
                f"{self.url}/vectors",
                headers=self.headers,
                json=payload
            )

            # Check if the request was successful
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to upsert vector {id}: {response.status_code} {response.text}")
                return {"id": id, "status": "stored_locally"}
        except Exception as e:
            logger.error(f"Error upserting vector: {str(e)}")
            return {"id": id, "status": "stored_locally"}

    def search(self, vector: List[float], filter: Optional[Dict[str, Any]] = None, k: int = 5):
        """Search for similar vectors in the database.

        Args:
            vector: Query vector
            filter: Optional filter to apply to the search
            k: Number of results to return
        """
        if not self.server_available:
            return self._local_search(vector, filter, k)

        try:
            # Prepare the request payload
            payload = {
                "vector": vector,
                "k": k
            }

            if filter:
                payload["filter"] = filter

            # Send the request to the PatANN server
            response = requests.post(
                f"{self.url}/search",
                headers=self.headers,
                json=payload
            )

            # Check if the request was successful
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                logger.warning(f"Failed to search vectors: {response.status_code} {response.text}")
                return self._local_search(vector, filter, k)
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return self._local_search(vector, filter, k)

    def _local_search(self, vector: List[float], filter: Optional[Dict[str, Any]] = None, k: int = 5):
        """Perform a local search when the PatANN server is unavailable."""
        logger.info("Using local fallback search implementation")
        results = []

        # Convert vector to numpy array for faster computation
        query_vector = np.array(vector)

        # Calculate distances for all vectors in the local metadata store
        for id, data in self.metadata.items():
            # Apply filter if provided
            if filter:
                # Check if all filter conditions are met
                metadata = data["metadata"]
                match = True
                for key, value in filter.items():
                    if key == "id":
                        if id != value:
                            match = False
                            break
                    elif key not in metadata or metadata[key] != value:
                        match = False
                        break
                if not match:
                    continue

            # Calculate Euclidean distance
            stored_vector = np.array(data["vector"])
            distance = np.sum((query_vector - stored_vector) ** 2)

            results.append({
                "id": id,
                "distance": float(distance),
                "metadata": data["metadata"]
            })

        # Sort by distance (ascending) and take top k
        results.sort(key=lambda x: x["distance"])
        return results[:k]

class PatANNMemory(MemoryBackend):
    def __init__(self, patann_url: str = "http://localhost:9200", model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the PatANN memory backend.

        Args:
            patann_url: URL of the PatAnn server
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name

        # Initialize the embedding model
        self.embedder = SentenceTransformer(model_name)

        # Initialize the PatANN client
        self.client = PatANN(url=patann_url)

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for the given text."""
        return self.embedder.encode(text).tolist()

    def store_idea(self, idea_id: str, description: str, context_ids: List[str]) -> None:
        """Store a trading idea with links to relevant contexts."""
        vec = self._get_embedding(description)
        created_at = datetime.now().isoformat()

        self.client.upsert(
            id=idea_id,
            vector=vec,
            metadata={
                "type": "idea",
                "description": description,
                "contexts": context_ids,
                "created_at": created_at
            }
        )

    def store_scenario(self, scenario_id: str, description: str, parent_idea_id: str, context_ids: List[str]) -> None:
        """Store a trading scenario with links to parent idea and relevant contexts."""
        vec = self._get_embedding(description)
        created_at = datetime.now().isoformat()

        self.client.upsert(
            id=scenario_id,
            vector=vec,
            metadata={
                "type": "scenario",
                "description": description,
                "parent_idea_id": parent_idea_id,
                "contexts": context_ids,
                "created_at": created_at
            }
        )

    def store_context(self, context_id: str, market: str, timeframe: str) -> None:
        """Store a trading context (market and timeframe)."""
        # Create a text representation of the context for embedding
        context_text = f"Market: {market}, Timeframe: {timeframe}"
        vec = self._get_embedding(context_text)

        self.client.upsert(
            id=context_id,
            vector=vec,
            metadata={
                "type": "context",
                "market": market,
                "timeframe": timeframe
            }
        )

    def store_backtest(self, backtest_id: str, metrics: MetricsDict, idea_id: str, context_id: str) -> None:
        """Store backtest results with links to the idea and context."""
        # We don't store backtests in the vector DB, as they're better suited for the graph DB
        # However, we could store a text representation of the backtest results if needed
        pass

    def get_idea(self, idea_id: str) -> Optional[IdeaDict]:
        """Retrieve a specific idea by ID."""
        # PatANN doesn't have a direct get by ID method, so we use a search with a filter
        results = self.client.search(
            vector=[0.0] * 768,  # Dummy vector, we're filtering by ID
            filter={"id": idea_id},
            k=1
        )

        if not results:
            return None

        metadata = results[0]["metadata"]
        return {
            "id": idea_id,
            "description": metadata["description"],
            "created_at": datetime.fromisoformat(metadata["created_at"])
        }

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioDict]:
        """Retrieve a specific scenario by ID."""
        results = self.client.search(
            vector=[0.0] * 768,  # Dummy vector, we're filtering by ID
            filter={"id": scenario_id},
            k=1
        )

        if not results:
            return None

        metadata = results[0]["metadata"]
        return {
            "id": scenario_id,
            "description": metadata["description"],
            "created_at": datetime.fromisoformat(metadata["created_at"]),
            "parent_idea_id": metadata.get("parent_idea_id")
        }

    def get_context(self, context_id: str) -> Optional[ContextDict]:
        """Retrieve a specific context by ID."""
        results = self.client.search(
            vector=[0.0] * 768,  # Dummy vector, we're filtering by ID
            filter={"id": context_id},
            k=1
        )

        if not results:
            return None

        metadata = results[0]["metadata"]
        return {
            "id": context_id,
            "market": metadata["market"],
            "timeframe": metadata["timeframe"]
        }

    def get_backtest(self, backtest_id: str) -> Optional[BacktestDict]:
        """Retrieve a specific backtest by ID."""
        # We don't store backtests in the vector DB
        return None

    def query_similar_ideas(self, embedding: List[float], context_id: Optional[str] = None, top_k: int = 10) -> List[IdeaDict]:
        """Find similar ideas using vector similarity."""
        filter_dict = {"type": "idea"}
        if context_id:
            filter_dict["contexts"] = context_id

        results = self.client.search(
            vector=embedding,
            filter=filter_dict,
            k=top_k
        )

        return [
            {
                "id": r["id"],
                "description": r["metadata"]["description"],
                "created_at": datetime.fromisoformat(r["metadata"]["created_at"])
            }
            for r in results
        ]

    def query_top_ideas_by_metrics(self, context_id: Optional[str] = None, metric: str = "Sharpe", weights: Optional[Dict[str, float]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Find top ideas based on backtest metrics, optionally with custom weighting."""
        # Vector DB doesn't store metrics, so we delegate this to the graph DB
        return []

    def query_scenarios_for_idea(self, idea_id: str) -> List[ScenarioDict]:
        """Find all scenarios derived from a specific idea."""
        results = self.client.search(
            vector=[0.0] * 768,  # Dummy vector, we're filtering by parent_idea_id
            filter={"type": "scenario", "parent_idea_id": idea_id},
            k=100  # Get all scenarios for this idea
        )

        return [
            {
                "id": r["id"],
                "description": r["metadata"]["description"],
                "created_at": datetime.fromisoformat(r["metadata"]["created_at"]),
                "parent_idea_id": r["metadata"]["parent_idea_id"]
            }
            for r in results
        ]

    def query_backtests_for_idea(self, idea_id: str, context_id: Optional[str] = None) -> List[BacktestDict]:
        """Find all backtests for a specific idea, optionally filtered by context."""
        # Vector DB doesn't store backtests, so we delegate this to the graph DB
        return []

    def query_ideas_for_context(self, context_id: str) -> List[IdeaDict]:
        """Find all ideas that apply to a specific context."""
        results = self.client.search(
            vector=[0.0] * 768,  # Dummy vector, we're filtering by context
            filter={"type": "idea", "contexts": context_id},
            k=100  # Get all ideas for this context
        )

        return [
            {
                "id": r["id"],
                "description": r["metadata"]["description"],
                "created_at": datetime.fromisoformat(r["metadata"]["created_at"])
            }
            for r in results
        ]

    def rag_query(self, prompt: str, context_id: Optional[str] = None, top_k: int = 5) -> str:
        """Perform a RAG query to get insights from the knowledge graph."""
        # PatANN doesn't handle RAG directly
        raise NotImplementedError("Use GraphRAG for RAG queries")

    def recommend_ideas(self, current_strategy_embedding: List[float], context_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Recommend ideas for a given strategy embedding and context using the hybrid approach."""
        # This is the core vector similarity search functionality
        similar_ideas = self.query_similar_ideas(
            embedding=current_strategy_embedding,
            context_id=context_id,
            top_k=top_k * 2  # Get more than we need for re-ranking
        )

        # In a real hybrid system, we would now pass these to the graph DB for re-ranking
        # For now, we'll just return the vector similarity results
        return [
            {
                "id": idea["id"],
                "description": idea["description"],
                "created_at": idea["created_at"],
                "similarity_score": 0.9 - (i * 0.1)  # Mock similarity score
            }
            for i, idea in enumerate(similar_ideas[:top_k])
        ]
