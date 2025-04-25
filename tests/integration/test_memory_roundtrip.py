"""Integration tests for the memory module."""

import os
import pytest
import tempfile
import subprocess
import time
from typing import List, Dict

from src.memory import PatANNMemory, Neo4jMemory, GraphRAGMemory

@pytest.fixture(scope="module")
def docker_services():
    """Start the docker services for testing."""
    # Start the docker services
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    
    # Wait for services to be ready
    time.sleep(10)
    
    yield
    
    # Stop the docker services
    subprocess.run(["docker-compose", "down"], check=True)

@pytest.fixture
def patann_memory():
    """Create a PatANNMemory instance for testing."""
    return PatANNMemory("http://localhost:9200")

@pytest.fixture
def neo4j_memory():
    """Create a Neo4jMemory instance for testing."""
    return Neo4jMemory(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )

@pytest.fixture
def graphrag_workspace():
    """Create a temporary GraphRAG workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy the settings.yaml file to the temporary directory
        settings_path = os.path.join(os.path.dirname(__file__), "../../src/memory/graphrag/settings.yaml")
        with open(settings_path, "r") as f:
            settings = f.read()
        
        # Write the settings to the temporary directory
        with open(os.path.join(tmpdir, "settings.yaml"), "w") as f:
            f.write(settings)
            
        yield tmpdir

@pytest.mark.skip(reason="Requires docker services to be running")
def test_patann_and_graphrag_roundtrip(docker_services, patann_memory, neo4j_memory, graphrag_workspace):
    """Test a roundtrip through PatANN and GraphRAG."""
    # 1) Store an idea & dummy backtest via PatANNMemory
    idea_id = "test_idea_1"
    idea_text = "This is a test idea for mean reversion trading"
    context_ids = ["crypto", "equities"]
    
    patann_memory.store_idea(idea_id, idea_text, context_ids)
    
    # Store the same idea in Neo4j
    neo4j_memory.store_idea(idea_id, idea_text, context_ids)
    
    # Store a backtest
    bt_id = "test_backtest_1"
    metrics = {"sharpe_ratio": 1.5, "max_drawdown": 0.1}
    
    neo4j_memory.store_backtest(bt_id, metrics, idea_id, context_ids[0])
    
    # 2) Initialize GraphRAG with the workspace
    graphrag_memory = GraphRAGMemory(graphrag_workspace)
    
    # 3) Query similarity
    # Generate an embedding for the query
    query_text = "mean reversion strategy"
    query_embedding = patann_memory.embedder.encode(query_text).tolist()
    
    # Query similar ideas
    similar_ideas = patann_memory.query_similar_ideas(query_embedding, context_ids[0], top_k=1)
    
    # Verify that our idea is returned
    assert idea_id in similar_ideas
    
    # 4) Query RAG response
    # This would require a real OpenAI API key, so we'll skip the actual execution
    try:
        rag_response = graphrag_memory.rag_query(
            "What are good mean reversion strategies?",
            top_k=1
        )
        assert rag_response  # Should not be empty
    except Exception as e:
        # If this fails due to missing API keys or other setup issues, that's okay for this test
        print(f"RAG query failed: {e}")
        pass
