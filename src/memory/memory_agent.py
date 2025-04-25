"""Memory Agent for managing the hybrid memory system."""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid

from src.memory import HybridMemory

class MemoryAgent:
    """Agent responsible for managing the hybrid memory system."""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", 
                 neo4j_user: str = "neo4j", 
                 neo4j_password: str = "password",
                 patann_url: str = "http://localhost:9200",
                 model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the memory agent.
        
        Args:
            neo4j_uri: URI for the Neo4j server
            neo4j_user: Username for the Neo4j server
            neo4j_password: Password for the Neo4j server
            patann_url: URL for the PatANN server
            model_name: Name of the sentence transformer model
        """
        # Initialize the memory system
        self.memory = HybridMemory(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            patann_url=patann_url,
            model_name=model_name
        )
        
        print("Hybrid memory system initialized")
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """Run the memory agent with the specified action.
        
        Args:
            action: The action to perform (store_idea, store_backtest, query_similar, etc.)
            **kwargs: Additional arguments for the action
            
        Returns:
            Dict containing the results of the action
        """
        print(f"Running memory agent with action: {action}")
        
        if action == "store_idea":
            return self.store_idea(**kwargs)
        elif action == "store_scenario":
            return self.store_scenario(**kwargs)
        elif action == "store_context":
            return self.store_context(**kwargs)
        elif action == "store_backtest":
            return self.store_backtest(**kwargs)
        elif action == "query_similar_ideas":
            return self.query_similar_ideas(**kwargs)
        elif action == "query_top_ideas":
            return self.query_top_ideas(**kwargs)
        elif action == "recommend_ideas":
            return self.recommend_ideas(**kwargs)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def store_idea(self, idea_name: str, description: str, context_ids: List[str], 
                   source_info: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Store a trading idea in the memory system.
        
        Args:
            idea_name: Name of the idea
            description: Description of the idea
            context_ids: List of context IDs the idea applies to
            source_info: Source information for the idea (optional)
            
        Returns:
            Dict containing the stored idea information
        """
        print(f"Storing idea: {idea_name}")
        
        # Generate a unique ID for the idea
        idea_id = str(uuid.uuid4())
        
        # Create a full description including source info if available
        full_description = description
        if source_info:
            source_text = f"\n\nSource: {source_info.get('title', '')}"
            if 'url' in source_info:
                source_text += f" ({source_info['url']})"
            full_description += source_text
        
        # Store the idea in the memory system
        self.memory.store_idea(idea_id, full_description, context_ids)
        
        return {
            "id": idea_id,
            "name": idea_name,
            "description": description,
            "contexts": context_ids,
            "source_info": source_info
        }
    
    def store_scenario(self, scenario_name: str, description: str, parent_idea_id: str, 
                      context_ids: List[str]) -> Dict[str, Any]:
        """Store a trading scenario in the memory system.
        
        Args:
            scenario_name: Name of the scenario
            description: Description of the scenario
            parent_idea_id: ID of the parent idea
            context_ids: List of context IDs the scenario applies to
            
        Returns:
            Dict containing the stored scenario information
        """
        print(f"Storing scenario: {scenario_name}")
        
        # Generate a unique ID for the scenario
        scenario_id = str(uuid.uuid4())
        
        # Store the scenario in the memory system
        self.memory.store_scenario(scenario_id, description, parent_idea_id, context_ids)
        
        return {
            "id": scenario_id,
            "name": scenario_name,
            "description": description,
            "parent_idea_id": parent_idea_id,
            "contexts": context_ids
        }
    
    def store_context(self, context_id: str, market: str, timeframe: str) -> Dict[str, Any]:
        """Store a trading context in the memory system.
        
        Args:
            context_id: ID of the context
            market: Market name
            timeframe: Timeframe
            
        Returns:
            Dict containing the stored context information
        """
        print(f"Storing context: {context_id} ({market}, {timeframe})")
        
        # Store the context in the memory system
        self.memory.store_context(context_id, market, timeframe)
        
        return {
            "id": context_id,
            "market": market,
            "timeframe": timeframe
        }
    
    def store_backtest(self, backtest_id: str, metrics: Dict[str, float], 
                      idea_id: str, context_id: str) -> Dict[str, Any]:
        """Store backtest results in the memory system.
        
        Args:
            backtest_id: ID of the backtest
            metrics: Dictionary of backtest metrics
            idea_id: ID of the idea being tested
            context_id: ID of the context the backtest was run in
            
        Returns:
            Dict containing the stored backtest information
        """
        print(f"Storing backtest: {backtest_id} for idea {idea_id} in context {context_id}")
        
        # Convert metrics to the expected format
        formatted_metrics = {}
        for key, value in metrics.items():
            # Try to convert string values to float
            if isinstance(value, str):
                try:
                    formatted_metrics[key] = float(value.replace('%', '').strip())
                except ValueError:
                    formatted_metrics[key] = value
            else:
                formatted_metrics[key] = value
        
        # Store the backtest in the memory system
        self.memory.store_backtest(backtest_id, formatted_metrics, idea_id, context_id)
        
        return {
            "id": backtest_id,
            "metrics": formatted_metrics,
            "idea_id": idea_id,
            "context_id": context_id
        }
    
    def query_similar_ideas(self, query_text: str, context_id: Optional[str] = None, 
                           top_k: int = 5) -> Dict[str, Any]:
        """Query similar ideas from the memory system.
        
        Args:
            query_text: Text to query
            context_id: Context ID to filter by (optional)
            top_k: Number of results to return
            
        Returns:
            Dict containing the query results
        """
        print(f"Querying similar ideas: {query_text}")
        
        # Generate embedding for the query text
        embedding = self.memory.vector_backend._get_embedding(query_text)
        
        # Query similar ideas
        similar_ideas = self.memory.query_similar_ideas(embedding, context_id, top_k)
        
        return {
            "query": query_text,
            "context_id": context_id,
            "results": similar_ideas
        }
    
    def query_top_ideas(self, context_id: Optional[str] = None, metric: str = "Sharpe", 
                       weights: Optional[Dict[str, float]] = None, 
                       limit: int = 10) -> Dict[str, Any]:
        """Query top ideas by metrics from the memory system.
        
        Args:
            context_id: Context ID to filter by (optional)
            metric: Metric to sort by
            weights: Dictionary of metric weights for custom scoring
            limit: Number of results to return
            
        Returns:
            Dict containing the query results
        """
        print(f"Querying top ideas by {metric}")
        
        # Query top ideas
        top_ideas = self.memory.query_top_ideas_by_metrics(context_id, metric, weights, limit)
        
        return {
            "metric": metric,
            "context_id": context_id,
            "weights": weights,
            "results": top_ideas
        }
    
    def recommend_ideas(self, strategy_text: str, context_id: str, 
                       top_k: int = 5) -> Dict[str, Any]:
        """Recommend ideas for a given strategy and context.
        
        Args:
            strategy_text: Text description of the current strategy
            context_id: Context ID to filter by
            top_k: Number of results to return
            
        Returns:
            Dict containing the recommendations
        """
        print(f"Recommending ideas for context: {context_id}")
        
        # Generate embedding for the strategy text
        embedding = self.memory.vector_backend._get_embedding(strategy_text)
        
        # Get recommendations
        recommendations = self.memory.recommend_ideas(embedding, context_id, top_k)
        
        return {
            "strategy": strategy_text,
            "context_id": context_id,
            "recommendations": recommendations
        }
    
    def process_research_ideas(self, ideas_json_path: str) -> Dict[str, Any]:
        """Process research ideas from the research agent.
        
        Args:
            ideas_json_path: Path to the research ideas JSON file
            
        Returns:
            Dict containing the processed ideas
        """
        print(f"Processing research ideas from: {ideas_json_path}")
        
        # Load the research ideas
        with open(ideas_json_path, 'r') as f:
            ideas = json.load(f)
        
        # Process each idea
        processed_ideas = {}
        for idea_id, idea_data in ideas.items():
            # Skip ideas that have already been processed
            if idea_data.get("memory_processed", False):
                continue
            
            # Extract idea information
            idea_name = idea_data.get("idea_name", "Unnamed Idea")
            description = idea_data.get("description", "")
            
            # Extract context information from the idea
            # This is a simple heuristic - in a real system, you would use NLP to extract contexts
            context_ids = []
            markets = ["BTC", "ETH", "NASDAQ", "S&P", "SPX", "SPY", "QQQ", "FOREX", "USD", "EUR", "JPY"]
            timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1D", "daily", "weekly", "monthly"]
            
            # Check for markets in the description
            for market in markets:
                if market.lower() in description.lower():
                    # Create context ID for this market with daily timeframe as default
                    context_id = f"{market.lower()}_daily"
                    if context_id not in context_ids:
                        context_ids.append(context_id)
                        # Ensure the context exists in the memory system
                        self.store_context(context_id, market, "1d")
            
            # If no contexts were found, use a default context
            if not context_ids:
                context_ids = ["default_context"]
                self.store_context("default_context", "Default", "1d")
            
            # Store the idea in the memory system
            source_info = idea_data.get("source_info", {})
            stored_idea = self.store_idea(idea_name, description, context_ids, source_info)
            
            # Mark the idea as processed
            idea_data["memory_processed"] = True
            idea_data["memory_id"] = stored_idea["id"]
            processed_ideas[idea_id] = idea_data
        
        # Save the updated ideas
        with open(ideas_json_path, 'w') as f:
            json.dump(ideas, f, indent=2)
        
        return {
            "processed_count": len(processed_ideas),
            "processed_ideas": processed_ideas
        }
    
    def process_backtest_results(self, backtest_dir: str) -> Dict[str, Any]:
        """Process backtest results from the backtester agent.
        
        Args:
            backtest_dir: Path to the backtest directory
            
        Returns:
            Dict containing the processed backtest results
        """
        print(f"Processing backtest results from: {backtest_dir}")
        
        # Load the backtest results
        backtest_output_path = os.path.join(backtest_dir, "backtest_output.json")
        if not os.path.exists(backtest_output_path):
            raise ValueError(f"Backtest output file not found: {backtest_output_path}")
        
        with open(backtest_output_path, 'r') as f:
            backtest_output = json.load(f)
        
        # Check if the backtest has already been processed
        if backtest_output.get("memory_processed", False):
            print(f"Backtest already processed: {backtest_dir}")
            return {
                "status": "already_processed",
                "backtest_id": backtest_output.get("memory_backtest_id", "")
            }
        
        # Extract backtest information
        backtest_id = backtest_output.get("backtest_id", str(uuid.uuid4()))
        metrics = backtest_output.get("performance", {})
        
        # Extract strategy information
        strategy_filename = backtest_output.get("strategy_filename", "")
        
        # Find the corresponding idea in the memory system
        # This is a placeholder - in a real system, you would have a mapping from strategy to idea
        idea_id = backtest_output.get("memory_idea_id", "")
        
        # If no idea ID is found, create a new idea from the strategy
        if not idea_id:
            # Read the strategy file
            strategy_path = os.path.join(backtest_dir, "code", strategy_filename)
            if os.path.exists(strategy_path):
                with open(strategy_path, 'r') as f:
                    strategy_code = f.read()
                
                # Extract a description from the strategy code
                description = self._extract_description_from_code(strategy_code)
                
                # Store the idea in the memory system
                idea_result = self.store_idea(
                    idea_name=os.path.splitext(strategy_filename)[0],
                    description=description,
                    context_ids=["default_context"],
                    source_info={"type": "strategy", "path": strategy_path}
                )
                
                idea_id = idea_result["id"]
                backtest_output["memory_idea_id"] = idea_id
            else:
                # If we can't find the strategy file, use a default idea
                idea_id = "default_idea"
                self.store_idea(
                    idea_name="Default Idea",
                    description="Default idea for backtest results without a strategy",
                    context_ids=["default_context"]
                )
        
        # Store the backtest in the memory system
        context_id = "default_context"  # Default context
        stored_backtest = self.store_backtest(backtest_id, metrics, idea_id, context_id)
        
        # Mark the backtest as processed
        backtest_output["memory_processed"] = True
        backtest_output["memory_backtest_id"] = stored_backtest["id"]
        
        # Save the updated backtest output
        with open(backtest_output_path, 'w') as f:
            json.dump(backtest_output, f, indent=2)
        
        return {
            "status": "processed",
            "backtest_id": stored_backtest["id"],
            "idea_id": idea_id
        }
    
    def _extract_description_from_code(self, code: str) -> str:
        """Extract a description from the strategy code.
        
        Args:
            code: The strategy code
            
        Returns:
            A description of the strategy
        """
        # Look for docstrings or comments
        import re
        
        # Try to find a class or module docstring
        docstring_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1).strip()
        
        # Try to find a comment block
        comment_block = ""
        for line in code.split('\n'):
            if line.strip().startswith('#'):
                comment_block += line.strip()[1:].strip() + " "
            elif comment_block:
                break
        
        if comment_block:
            return comment_block.strip()
        
        # If no description is found, return a generic description
        return "Trading strategy extracted from code"
