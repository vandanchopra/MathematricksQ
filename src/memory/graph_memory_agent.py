#!/usr/bin/env python3
"""
Graph Memory Agent

This module provides a simplified interface for working with the graph memory system.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

from .graph_memory import GraphMemory

# Load environment variables
load_dotenv()

class GraphMemoryAgent:
    """
    Agent for interacting with the graph memory system.
    """
    
    def __init__(self):
        """
        Initialize the memory agent.
        """
        self.memory = GraphMemory()
    
    def remember_idea(self, description, tags=None):
        """
        Remember an idea.
        
        Args:
            description (str): Description of the idea
            tags (list): List of tags for the idea
        
        Returns:
            str: ID of the created idea
        """
        if tags is None:
            tags = []
        
        return self.memory.add_idea(
            description=description,
            tags=tags,
            created_at=datetime.now().isoformat()
        )
    
    def remember_scenario(self, description, parent_idea_id, tags=None):
        """
        Remember a scenario.
        
        Args:
            description (str): Description of the scenario
            parent_idea_id (str): ID of the parent idea
            tags (list): List of tags for the scenario
        
        Returns:
            str: ID of the created scenario
        """
        if tags is None:
            tags = []
        
        return self.memory.add_scenario(
            description=description,
            parent_idea_id=parent_idea_id,
            tags=tags,
            created_at=datetime.now().isoformat()
        )
    
    def remember_context(self, market, timeframe, description=None):
        """
        Remember a context.
        
        Args:
            market (str): Market identifier (e.g., "BTC/USD")
            timeframe (str): Timeframe (e.g., "1d", "4h")
            description (str): Description of the context
        
        Returns:
            str: ID of the created context
        """
        return self.memory.add_context(
            market=market,
            timeframe=timeframe,
            description=description
        )
    
    def remember_backtest(self, idea_id, context_id, metrics, scenario_id=None, notes=None):
        """
        Remember a backtest.
        
        Args:
            idea_id (str): ID of the idea being tested
            context_id (str): ID of the context in which the backtest was executed
            metrics (dict): Dictionary of metrics (e.g., Sharpe, CAGR, MaxDrawdown)
            scenario_id (str): ID of the scenario to which the backtest applies (optional)
            notes (str): Additional notes about the backtest
        
        Returns:
            str: ID of the created backtest
        """
        return self.memory.add_backtest(
            idea_id=idea_id,
            context_id=context_id,
            metrics=metrics,
            scenario_id=scenario_id,
            notes=notes,
            date=datetime.now().isoformat()
        )
    
    def recall_similar_ideas(self, description, k=5):
        """
        Recall ideas similar to the given description.
        
        Args:
            description (str): Description to search for
            k (int): Number of results to return
        
        Returns:
            list: List of similar ideas
        """
        return self.memory.find_similar_ideas(text=description, k=k)
    
    def recall_best_ideas(self, metric="Sharpe", k=5):
        """
        Recall the best ideas based on a specific metric.
        
        Args:
            metric (str): Metric to use for ranking (e.g., "Sharpe", "CAGR")
            k (int): Number of results to return
        
        Returns:
            list: List of best ideas
        """
        return self.memory.get_best_ideas(metric=metric, k=k)
    
    def recommend_ideas(self, current_idea_ids, k=5):
        """
        Recommend ideas to explore next based on the current ideas.
        
        Args:
            current_idea_ids (list): List of current idea IDs
            k (int): Number of recommendations to return
        
        Returns:
            list: List of recommended ideas
        """
        return self.memory.recommend_next_ideas(current_idea_ids, k=k)
    
    def get_idea_performance(self, idea_id):
        """
        Get the performance of an idea across all backtests.
        
        Args:
            idea_id (str): ID of the idea
        
        Returns:
            dict: Performance metrics for the idea
        """
        backtests = self.memory.get_idea_backtests(idea_id)
        
        if not backtests:
            return {
                "idea_id": idea_id,
                "num_backtests": 0,
                "metrics": {}
            }
        
        # Aggregate metrics
        all_metrics = {}
        for backtest in backtests:
            for metric, value in backtest["metrics"].items():
                if metric not in all_metrics:
                    all_metrics[metric] = []
                all_metrics[metric].append(value)
        
        # Calculate statistics
        metrics = {}
        for metric, values in all_metrics.items():
            metrics[metric] = {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "count": len(values)
            }
        
        return {
            "idea_id": idea_id,
            "num_backtests": len(backtests),
            "metrics": metrics
        }
    
    def compare_ideas(self, idea_ids, metric="Sharpe"):
        """
        Compare multiple ideas based on a specific metric.
        
        Args:
            idea_ids (list): List of idea IDs to compare
            metric (str): Metric to use for comparison (e.g., "Sharpe", "CAGR")
        
        Returns:
            list: List of ideas with their performance metrics
        """
        results = []
        
        for idea_id in idea_ids:
            performance = self.get_idea_performance(idea_id)
            
            # Get idea description
            with self.memory.driver.session() as session:
                result = session.run("""
                    MATCH (i:Idea {id: $idea_id})
                    RETURN i.description AS description
                """, idea_id=idea_id)
                
                record = result.single()
                description = record["description"] if record else ""
            
            # Extract the specific metric
            metric_stats = performance["metrics"].get(metric, {
                "min": 0,
                "max": 0,
                "mean": 0,
                "count": 0
            })
            
            results.append({
                "id": idea_id,
                "description": description,
                "num_backtests": performance["num_backtests"],
                "metric": metric,
                "min": metric_stats["min"],
                "max": metric_stats["max"],
                "mean": metric_stats["mean"]
            })
        
        # Sort by mean metric value (descending)
        results.sort(key=lambda x: x["mean"], reverse=True)
        
        return results
    
    def get_context_performance(self, context_id):
        """
        Get the performance of all ideas in a specific context.
        
        Args:
            context_id (str): ID of the context
        
        Returns:
            dict: Performance metrics for all ideas in the context
        """
        backtests = self.memory.get_context_backtests(context_id)
        
        if not backtests:
            return {
                "context_id": context_id,
                "num_backtests": 0,
                "ideas": []
            }
        
        # Group by idea
        ideas = {}
        for backtest in backtests:
            idea_id = backtest["idea"]["id"]
            if idea_id not in ideas:
                ideas[idea_id] = {
                    "id": idea_id,
                    "description": backtest["idea"]["description"],
                    "backtests": []
                }
            ideas[idea_id]["backtests"].append(backtest)
        
        # Calculate statistics for each idea
        for idea_id, idea in ideas.items():
            all_metrics = {}
            for backtest in idea["backtests"]:
                for metric, value in backtest["metrics"].items():
                    if metric not in all_metrics:
                        all_metrics[metric] = []
                    all_metrics[metric].append(value)
            
            metrics = {}
            for metric, values in all_metrics.items():
                metrics[metric] = {
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "count": len(values)
                }
            
            idea["metrics"] = metrics
            idea["num_backtests"] = len(idea["backtests"])
            del idea["backtests"]  # Remove raw backtest data
        
        # Get context details
        with self.memory.driver.session() as session:
            result = session.run("""
                MATCH (c:Context {id: $context_id})
                RETURN c.market AS market, c.timeframe AS timeframe
            """, context_id=context_id)
            
            record = result.single()
            market = record["market"] if record else ""
            timeframe = record["timeframe"] if record else ""
        
        return {
            "context_id": context_id,
            "market": market,
            "timeframe": timeframe,
            "num_backtests": len(backtests),
            "ideas": list(ideas.values())
        }
    
    def compare_contexts(self, context_ids, metric="Sharpe"):
        """
        Compare multiple contexts based on a specific metric.
        
        Args:
            context_ids (list): List of context IDs to compare
            metric (str): Metric to use for comparison (e.g., "Sharpe", "CAGR")
        
        Returns:
            list: List of contexts with their performance metrics
        """
        results = []
        
        for context_id in context_ids:
            performance = self.get_context_performance(context_id)
            
            # Calculate average metric across all ideas
            if performance["ideas"]:
                metric_values = []
                for idea in performance["ideas"]:
                    if metric in idea["metrics"]:
                        metric_values.append(idea["metrics"][metric]["mean"])
                
                avg_metric = sum(metric_values) / len(metric_values) if metric_values else 0
            else:
                avg_metric = 0
            
            results.append({
                "id": context_id,
                "market": performance["market"],
                "timeframe": performance["timeframe"],
                "num_backtests": performance["num_backtests"],
                "num_ideas": len(performance["ideas"]),
                "metric": metric,
                "avg_value": avg_metric
            })
        
        # Sort by average metric value (descending)
        results.sort(key=lambda x: x["avg_value"], reverse=True)
        
        return results
    
    def get_visualization_data(self, context_id=None, idea_id=None):
        """
        Get data for visualizing the memory graph.
        
        Args:
            context_id (str): ID of the context to filter by (optional)
            idea_id (str): ID of the idea to filter by (optional)
        
        Returns:
            dict: Graph data for visualization
        """
        return self.memory.get_full_subgraph(context_id=context_id, idea_id=idea_id)
    
    def export_to_json(self, file_path):
        """
        Export the memory graph to a JSON file.
        
        Args:
            file_path (str): Path to the output file
        
        Returns:
            bool: True if successful, False otherwise
        """
        graph = self.memory.get_full_subgraph()
        
        try:
            with open(file_path, "w") as f:
                json.dump(graph, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def import_from_json(self, file_path):
        """
        Import the memory graph from a JSON file.
        
        Args:
            file_path (str): Path to the input file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, "r") as f:
                graph = json.load(f)
            
            # Clear existing data
            self.memory.clear()
            
            # Import nodes
            for node in graph["nodes"]:
                if node["type"] == "Idea":
                    self.memory.add_idea(
                        id=node["id"],
                        description=node["label"],
                        **node["properties"]
                    )
                elif node["type"] == "Scenario":
                    # We'll add scenarios after all ideas are added
                    pass
                elif node["type"] == "Context":
                    self.memory.add_context(
                        id=node["id"],
                        market=node["properties"].get("market", ""),
                        timeframe=node["properties"].get("timeframe", ""),
                        **{k: v for k, v in node["properties"].items() if k not in ["id", "market", "timeframe"]}
                    )
                elif node["type"] == "Backtest":
                    # We'll add backtests after all ideas, scenarios, and contexts are added
                    pass
            
            # Import scenarios
            for node in graph["nodes"]:
                if node["type"] == "Scenario":
                    # Find parent idea
                    parent_idea_id = None
                    for edge in graph["edges"]:
                        if edge["source"] == node["id"] and edge["type"] == "SUBIDEA_OF":
                            parent_idea_id = edge["target"]
                            break
                    
                    if parent_idea_id:
                        self.memory.add_scenario(
                            id=node["id"],
                            description=node["label"],
                            parent_idea_id=parent_idea_id,
                            **node["properties"]
                        )
            
            # Import backtests
            for node in graph["nodes"]:
                if node["type"] == "Backtest":
                    # Find idea, context, and scenario
                    idea_id = None
                    context_id = None
                    scenario_id = None
                    
                    for edge in graph["edges"]:
                        if edge["target"] == node["id"] and edge["type"] == "TESTED_IN":
                            idea_id = edge["source"]
                        elif edge["source"] == node["id"] and edge["type"] == "EXECUTED_IN":
                            context_id = edge["target"]
                        elif edge["source"] == node["id"] and edge["type"] == "APPLIES_TO":
                            scenario_id = edge["target"]
                    
                    if idea_id and context_id:
                        metrics = node.get("metrics", {})
                        self.memory.add_backtest(
                            id=node["id"],
                            idea_id=idea_id,
                            context_id=context_id,
                            scenario_id=scenario_id,
                            metrics=metrics,
                            **{k: v for k, v in node["properties"].items() if k not in ["id", "metrics"]}
                        )
            
            return True
        except Exception as e:
            print(f"Error importing from JSON: {e}")
            return False

if __name__ == "__main__":
    # Example usage
    agent = GraphMemoryAgent()
    
    # Remember an idea
    idea_id = agent.remember_idea(
        description="Using Internal Bar Strength (IBS) for mean reversion trading",
        tags=["mean-reversion", "technical-indicator", "IBS"]
    )
    
    # Remember a scenario
    scenario_id = agent.remember_scenario(
        description="IBS applied to country ETFs",
        parent_idea_id=idea_id,
        tags=["ETF", "country", "global"]
    )
    
    # Remember a context
    context_id = agent.remember_context(
        market="ETF-Basket",
        timeframe="1d",
        description="Daily timeframe for a basket of country ETFs"
    )
    
    # Remember a backtest
    backtest_id = agent.remember_backtest(
        idea_id=idea_id,
        context_id=context_id,
        scenario_id=scenario_id,
        metrics={
            "Sharpe": 1.85,
            "CAGR": 0.12,
            "MaxDrawdown": 0.15,
            "WinRate": 0.58,
            "ProfitFactor": 1.65,
            "TotalTrades": 250
        },
        notes="Initial test of IBS strategy on country ETFs"
    )
    
    # Recall similar ideas
    similar_ideas = agent.recall_similar_ideas(
        description="mean reversion trading strategies",
        k=5
    )
    
    print("Similar ideas:")
    for idea in similar_ideas:
        print(f"ID: {idea['id']}, Score: {idea['score']}")
        print(f"Text: {idea['metadata'].get('text', '')}")
        print()
    
    # Get idea performance
    performance = agent.get_idea_performance(idea_id)
    
    print(f"Performance of idea {idea_id}:")
    print(f"Number of backtests: {performance['num_backtests']}")
    for metric, stats in performance["metrics"].items():
        print(f"{metric}: min={stats['min']}, max={stats['max']}, mean={stats['mean']}")
    print()
    
    # Export to JSON
    agent.export_to_json("memory_graph.json")
    print("Memory graph exported to memory_graph.json")
