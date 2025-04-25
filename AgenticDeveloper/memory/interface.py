from typing import Protocol, List, Dict, Optional, Any
from datetime import datetime

class MemoryBackend(Protocol):
    """Protocol defining the interface for graph-based memory backends."""
    
    def store_idea(self, 
                  idea_id: str, 
                  content: Dict[str, Any], 
                  metadata: Dict[str, Any],
                  relationships: Optional[List[Dict[str, str]]] = None) -> None:
        """
        Store a trading idea in the graph memory.
        
        Args:
            idea_id: Unique identifier for the idea
            content: Dictionary containing idea content (description, edge, pseudo_code etc.)
            metadata: Dictionary containing metadata about the idea (source, timestamp, etc.)
            relationships: Optional list of relationships to other nodes
        """
        ...
        
    def store_backtest(self,
                      backtest_id: str,
                      metrics: Dict[str, Any],
                      strategy_id: str,
                      idea_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Store backtest results in the graph memory.
        
        Args:
            backtest_id: Unique identifier for the backtest
            metrics: Dictionary containing backtest metrics and performance data
            strategy_id: ID of the strategy that was tested
            idea_id: Optional ID of the research idea that led to this strategy
            metadata: Optional additional metadata about the backtest
        """
        ...
        
    def store_strategy(self,
                      strategy_id: str,
                      code: str,
                      version: str,
                      idea_id: Optional[str] = None,
                      parent_strategy_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Store a strategy version in the graph memory.
        
        Args:
            strategy_id: Unique identifier for the strategy
            code: The strategy's source code
            version: Version string for this strategy
            idea_id: Optional ID of the research idea this implements
            parent_strategy_id: Optional ID of the parent strategy this was derived from
            metadata: Optional additional metadata about the strategy
        """
        ...
        
    def query_similar_ideas(self,
                          text: str,
                          top_k: int = 5,
                          filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Find similar ideas based on semantic search.
        
        Args:
            text: Text to search for similar ideas
            top_k: Number of similar ideas to return
            filters: Optional filters to apply to the search
            
        Returns:
            List of similar ideas with their content and metadata
        """
        ...
        
    def query_strategy_history(self,
                             strategy_id: str,
                             include_backtests: bool = True) -> Dict[str, Any]:
        """
        Get the full history of a strategy including its evolution and performance.
        
        Args:
            strategy_id: ID of the strategy to query
            include_backtests: Whether to include backtest results
            
        Returns:
            Dictionary containing the strategy's history
        """
        ...
        
    def find_top_strategies(self,
                          metric: str,
                          timeframe: Optional[str] = None,
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find top performing strategies based on a specific metric.
        
        Args:
            metric: Performance metric to sort by (e.g. "sharpe_ratio")
            timeframe: Optional timeframe to consider
            filters: Optional filters to apply
            limit: Maximum number of strategies to return
            
        Returns:
            List of top strategies with their metrics
        """
        ...
        
    def get_related_nodes(self,
                         node_id: str,
                         relationship_types: Optional[List[str]] = None,
                         max_depth: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get nodes related to a given node in the graph.
        
        Args:
            node_id: ID of the node to start from
            relationship_types: Optional list of relationship types to traverse
            max_depth: Maximum depth to traverse in the graph
            
        Returns:
            Dictionary of related nodes grouped by relationship type
        """
        ...