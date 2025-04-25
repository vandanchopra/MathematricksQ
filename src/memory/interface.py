# src/memory/interface.py
from typing import Protocol, List, Dict, Any, Optional, Union, TypedDict
from datetime import datetime

class MetricsDict(TypedDict, total=False):
    """Dictionary of backtest metrics."""
    CAGR: float
    Sharpe: float
    MaxDrawdown: float
    WinRate: float
    ProfitFactor: float
    ExpectedValue: float
    # Add any other metrics you want to track

class ContextDict(TypedDict):
    """Dictionary representing a trading context."""
    id: str
    market: str
    timeframe: str

class IdeaDict(TypedDict):
    """Dictionary representing a trading idea."""
    id: str
    description: str
    created_at: datetime

class ScenarioDict(TypedDict):
    """Dictionary representing a trading scenario."""
    id: str
    description: str
    created_at: datetime
    parent_idea_id: Optional[str]

class BacktestDict(TypedDict):
    """Dictionary representing a backtest result."""
    id: str
    date: datetime
    metrics: MetricsDict
    idea_id: str
    context_id: str

class MemoryBackend(Protocol):
    """Protocol for memory backends that store and retrieve trading ideas, scenarios, backtests, and contexts."""

    # Storage methods
    def store_idea(self, idea_id: str, description: str, context_ids: List[str]) -> None:
        """Store a trading idea with links to relevant contexts."""
        ...

    def store_scenario(self, scenario_id: str, description: str, parent_idea_id: str, context_ids: List[str]) -> None:
        """Store a trading scenario with links to parent idea and relevant contexts."""
        ...

    def store_context(self, context_id: str, market: str, timeframe: str) -> None:
        """Store a trading context (market and timeframe)."""
        ...

    def store_backtest(self, backtest_id: str, metrics: MetricsDict, idea_id: str, context_id: str) -> None:
        """Store backtest results with links to the idea and context."""
        ...

    # Retrieval methods
    def get_idea(self, idea_id: str) -> Optional[IdeaDict]:
        """Retrieve a specific idea by ID."""
        ...

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioDict]:
        """Retrieve a specific scenario by ID."""
        ...

    def get_context(self, context_id: str) -> Optional[ContextDict]:
        """Retrieve a specific context by ID."""
        ...

    def get_backtest(self, backtest_id: str) -> Optional[BacktestDict]:
        """Retrieve a specific backtest by ID."""
        ...

    # Query methods
    def query_similar_ideas(self, embedding: List[float], context_id: Optional[str] = None, top_k: int = 10) -> List[IdeaDict]:
        """Find similar ideas using vector similarity."""
        ...

    def query_top_ideas_by_metrics(self, context_id: Optional[str] = None, metric: str = "Sharpe", weights: Optional[Dict[str, float]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Find top ideas based on backtest metrics, optionally with custom weighting."""
        ...

    def query_scenarios_for_idea(self, idea_id: str) -> List[ScenarioDict]:
        """Find all scenarios derived from a specific idea."""
        ...

    def query_backtests_for_idea(self, idea_id: str, context_id: Optional[str] = None) -> List[BacktestDict]:
        """Find all backtests for a specific idea, optionally filtered by context."""
        ...

    def query_ideas_for_context(self, context_id: str) -> List[IdeaDict]:
        """Find all ideas that apply to a specific context."""
        ...

    # Hybrid query methods
    def rag_query(self, prompt: str, context_id: Optional[str] = None, top_k: int = 5) -> str:
        """Perform a RAG query to get insights from the knowledge graph."""
        ...

    def recommend_ideas(self, current_strategy_embedding: List[float], context_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Recommend ideas for a given strategy embedding and context using the hybrid approach."""
        ...
