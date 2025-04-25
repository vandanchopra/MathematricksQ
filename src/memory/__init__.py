"""Memory module for storing and retrieving trading ideas, strategies, and backtest results."""

# Original memory system
from .interface import MemoryBackend
from .patann_backend import PatANNMemory
from .graph_backend import Neo4jMemory
from .rag_backend import GraphRAGMemory
from .hybrid_backend import HybridMemory
from .memory_agent import MemoryAgent

# New graph memory system
from .kg_builder import (
    setup_schema, store_idea, store_scenario, store_context, store_backtest,
    get_description, clear_database
)
from .patann_indexer import (
    PatANNClient, index_idea, index_scenario, search_similar, rank_next_ideas
)
from .graph_memory import GraphMemory
from .graph_memory_agent import GraphMemoryAgent

__all__ = [
    # Original memory system
    "MemoryBackend", "PatANNMemory", "Neo4jMemory", "GraphRAGMemory", "HybridMemory", "MemoryAgent",

    # New graph memory system
    "setup_schema", "store_idea", "store_scenario", "store_context", "store_backtest",
    "get_description", "clear_database", "PatANNClient", "index_idea", "index_scenario",
    "search_similar", "rank_next_ideas", "GraphMemory", "GraphMemoryAgent"
]
