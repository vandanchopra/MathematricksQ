"""Unit tests for the memory interface."""

import pytest
from typing import List, Dict, Protocol, runtime_checkable

# Import the memory backends
from src.memory import MemoryBackend, PatANNMemory, Neo4jMemory, GraphRAGMemory

def test_memory_backend_protocol():
    """Test that MemoryBackend is a valid Protocol."""
    assert isinstance(MemoryBackend, type)
    assert issubclass(MemoryBackend, Protocol)

def test_patann_memory_implements_protocol():
    """Test that PatANNMemory implements the MemoryBackend protocol."""
    # Check method signatures
    assert hasattr(PatANNMemory, 'store_idea')
    assert hasattr(PatANNMemory, 'store_backtest')
    assert hasattr(PatANNMemory, 'query_similar_ideas')
    assert hasattr(PatANNMemory, 'rag_query')

def test_neo4j_memory_implements_protocol():
    """Test that Neo4jMemory implements the MemoryBackend protocol."""
    # Check method signatures
    assert hasattr(Neo4jMemory, 'store_idea')
    assert hasattr(Neo4jMemory, 'store_backtest')
    assert hasattr(Neo4jMemory, 'query_similar_ideas')
    assert hasattr(Neo4jMemory, 'rag_query')

def test_graphrag_memory_implements_protocol():
    """Test that GraphRAGMemory implements the MemoryBackend protocol."""
    # Check method signatures
    assert hasattr(GraphRAGMemory, 'store_idea')
    assert hasattr(GraphRAGMemory, 'store_backtest')
    assert hasattr(GraphRAGMemory, 'query_similar_ideas')
    assert hasattr(GraphRAGMemory, 'rag_query')
