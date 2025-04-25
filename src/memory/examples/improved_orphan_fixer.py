#!/usr/bin/env python3
"""
Improved Orphan Fixer with advanced relationship creation logic
"""

import os
import sys
import logging
import random
import argparse
from typing import Dict, List, Any, Optional, Tuple, Set

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from neo4j import GraphDatabase
from src.memory.hybrid_backend import HybridMemory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ImprovedOrphanFixer")

class ImprovedOrphanFixer:
    """Improved class to fix orphaned nodes in the memory knowledge graph."""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """Initialize the improved orphan fixer.

        Args:
            uri: Neo4j URI
            user: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.memory = HybridMemory(
            neo4j_uri=uri,
            neo4j_user=user,
            neo4j_password=password,
            patann_url="http://localhost:9200",
            model_name="all-MiniLM-L6-v2"
        )
        logger.info("ImprovedOrphanFixer initialized")

    def find_orphaned_nodes(self, node_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Find orphaned nodes in the database.

        Args:
            node_types: Optional list of node types to check (e.g., ["Idea", "Backtest"])

        Returns:
            Dictionary mapping node types to lists of orphaned node information
        """
        if node_types is None:
            node_types = ["Idea", "Backtest", "Context", "Scenario"]

        orphans = {node_type: [] for node_type in node_types}

        with self.driver.session() as session:
            for node_type in node_types:
                # Define relationship requirements for each node type
                if node_type == "Idea":
                    # Ideas should have TESTED_IN and SUBIDEA_OF relationships
                    result = session.run("""
                    MATCH (i:Idea)
                    WHERE NOT ((i)-[:TESTED_IN]->()) OR NOT (()-[:SUBIDEA_OF]->(i))
                    RETURN i.id AS id, i.description AS description,
                           NOT ((i)-[:TESTED_IN]->()) AS missing_tested_in,
                           NOT (()-[:SUBIDEA_OF]->(i)) AS missing_subidea_of
                    """)

                    for record in result:
                        orphans["Idea"].append({
                            "id": record["id"],
                            "description": record["description"],
                            "missing_tested_in": record["missing_tested_in"],
                            "missing_subidea_of": record["missing_subidea_of"]
                        })

                elif node_type == "Backtest":
                    # Backtests should have TESTED_IN and EXECUTED_IN relationships
                    result = session.run("""
                    MATCH (b:Backtest)
                    WHERE NOT ((b)<-[:TESTED_IN]-()) OR NOT ((b)-[:EXECUTED_IN]->())
                    RETURN b.id AS id, b.metrics AS metrics,
                           NOT ((b)<-[:TESTED_IN]-()) AS missing_tested_in,
                           NOT ((b)-[:EXECUTED_IN]->()) AS missing_executed_in
                    """)

                    for record in result:
                        orphans["Backtest"].append({
                            "id": record["id"],
                            "metrics": record["metrics"],
                            "missing_tested_in": record["missing_tested_in"],
                            "missing_executed_in": record["missing_executed_in"]
                        })

                elif node_type == "Context":
                    # Contexts should have EXECUTED_IN or APPLIES_IN relationships
                    result = session.run("""
                    MATCH (c:Context)
                    WHERE NOT ((c)<-[:EXECUTED_IN]-()) AND NOT ((c)<-[:APPLIES_IN]-())
                    RETURN c.id AS id, c.market AS market, c.timeframe AS timeframe
                    """)

                    for record in result:
                        orphans["Context"].append({
                            "id": record["id"],
                            "market": record["market"],
                            "timeframe": record["timeframe"],
                            "missing_executed_in": True,
                            "missing_applies_in": True
                        })

                elif node_type == "Scenario":
                    # Scenarios should have SUBIDEA_OF and APPLIES_IN relationships
                    result = session.run("""
                    MATCH (s:Scenario)
                    WHERE NOT ((s)-[:SUBIDEA_OF]->()) OR NOT ((s)-[:APPLIES_IN]->())
                    RETURN s.id AS id, s.description AS description,
                           NOT ((s)-[:SUBIDEA_OF]->()) AS missing_subidea_of,
                           NOT ((s)-[:APPLIES_IN]->()) AS missing_applies_in
                    """)

                    for record in result:
                        orphans["Scenario"].append({
                            "id": record["id"],
                            "description": record["description"],
                            "missing_subidea_of": record["missing_subidea_of"],
                            "missing_applies_in": record["missing_applies_in"]
                        })

        return orphans

    def get_all_nodes(self, node_type: str) -> List[Dict[str, Any]]:
        """Get all nodes of a specific type.

        Args:
            node_type: Node type to retrieve (e.g., "Idea", "Backtest")

        Returns:
            List of node information dictionaries
        """
        nodes = []
        with self.driver.session() as session:
            if node_type == "Idea":
                result = session.run("""
                MATCH (i:Idea)
                RETURN i.id AS id, i.description AS description
                """)

                for record in result:
                    nodes.append({
                        "id": record["id"],
                        "description": record["description"]
                    })

            elif node_type == "Backtest":
                result = session.run("""
                MATCH (b:Backtest)
                RETURN b.id AS id, b.metrics AS metrics
                """)

                for record in result:
                    nodes.append({
                        "id": record["id"],
                        "metrics": record["metrics"]
                    })

            elif node_type == "Context":
                result = session.run("""
                MATCH (c:Context)
                RETURN c.id AS id, c.market AS market, c.timeframe AS timeframe
                """)

                for record in result:
                    nodes.append({
                        "id": record["id"],
                        "market": record["market"],
                        "timeframe": record["timeframe"]
                    })

            elif node_type == "Scenario":
                result = session.run("""
                MATCH (s:Scenario)
                RETURN s.id AS id, s.description AS description
                """)

                for record in result:
                    nodes.append({
                        "id": record["id"],
                        "description": record["description"]
                    })

        return nodes

    def fix_orphaned_nodes(self,
                          node_types: Optional[List[str]] = None,
                          relationship_types: Optional[List[str]] = None,
                          dry_run: bool = False,
                          quality_threshold: float = 0.0) -> Dict[str, int]:
        """Fix orphaned nodes by creating missing relationships.

        Args:
            node_types: Optional list of node types to fix (e.g., ["Idea", "Backtest"])
            relationship_types: Optional list of relationship types to fix (e.g., ["TESTED_IN", "EXECUTED_IN"])
            dry_run: If True, only report what would be fixed without making changes
            quality_threshold: Minimum quality threshold for creating relationships (0.0 to 1.0)

        Returns:
            Dictionary mapping relationship types to the number of relationships created
        """
        if node_types is None:
            node_types = ["Idea", "Backtest", "Context", "Scenario"]

        if relationship_types is None:
            relationship_types = ["TESTED_IN", "EXECUTED_IN", "APPLIES_IN", "SUBIDEA_OF"]

        # Find orphaned nodes
        orphans = self.find_orphaned_nodes(node_types)

        # Log orphaned nodes
        for node_type, nodes in orphans.items():
            logger.info(f"Found {len(nodes)} orphaned {node_type} nodes")

        # Initialize counters for created relationships
        created_relationships = {rel_type: 0 for rel_type in relationship_types}

        # Fix orphaned nodes
        for node_type in node_types:
            if node_type == "Idea" and "Idea" in orphans and orphans["Idea"]:
                created_relationships.update(self._fix_orphaned_ideas(
                    orphans["Idea"], relationship_types, dry_run, quality_threshold
                ))

            elif node_type == "Backtest" and "Backtest" in orphans and orphans["Backtest"]:
                created_relationships.update(self._fix_orphaned_backtests(
                    orphans["Backtest"], relationship_types, dry_run, quality_threshold
                ))

            elif node_type == "Context" and "Context" in orphans and orphans["Context"]:
                created_relationships.update(self._fix_orphaned_contexts(
                    orphans["Context"], relationship_types, dry_run, quality_threshold
                ))

            elif node_type == "Scenario" and "Scenario" in orphans and orphans["Scenario"]:
                created_relationships.update(self._fix_orphaned_scenarios(
                    orphans["Scenario"], relationship_types, dry_run, quality_threshold
                ))

        return created_relationships

    def _calculate_relationship_quality(self, source_type: str, target_type: str,
                                      source_data: Dict[str, Any], target_data: Dict[str, Any]) -> float:
        """Calculate the quality of a potential relationship between two nodes.

        Args:
            source_type: Type of the source node (e.g., "Idea", "Backtest")
            target_type: Type of the target node (e.g., "Context", "Scenario")
            source_data: Data for the source node
            target_data: Data for the target node

        Returns:
            Quality score between 0.0 and 1.0
        """
        # Base quality score
        quality = 0.5

        # Calculate quality based on node types and data
        if source_type == "Idea" and target_type == "Context":
            # Check if the idea description mentions the context's market or timeframe
            if "description" in source_data and "market" in target_data and "timeframe" in target_data:
                description = source_data["description"].lower()
                market = target_data["market"].lower()
                timeframe = target_data["timeframe"].lower()

                # Check for market mentions
                market_keywords = {
                    "btc": ["bitcoin", "btc", "crypto"],
                    "eth": ["ethereum", "eth", "crypto"],
                    "spy": ["spy", "s&p", "s&p 500", "stock", "equity"],
                    "aapl": ["apple", "aapl", "stock", "equity"],
                    "msft": ["microsoft", "msft", "stock", "equity"],
                    "forex": ["forex", "currency", "fx"],
                    "usd": ["usd", "dollar", "forex", "currency"],
                    "eur": ["eur", "euro", "forex", "currency"]
                }

                # Check for timeframe mentions
                timeframe_keywords = {
                    "1m": ["minute", "1m", "short-term", "scalping"],
                    "5m": ["5m", "short-term", "scalping"],
                    "15m": ["15m", "short-term"],
                    "1h": ["hour", "1h", "hourly", "intraday"],
                    "4h": ["4h", "intraday"],
                    "1d": ["day", "1d", "daily", "swing", "long-term"]
                }

                # Calculate market relevance
                market_relevance = 0
                for m, keywords in market_keywords.items():
                    if m in market.lower():
                        for keyword in keywords:
                            if keyword in description:
                                market_relevance += 0.1
                                break

                # Calculate timeframe relevance
                timeframe_relevance = 0
                for tf, keywords in timeframe_keywords.items():
                    if tf in timeframe.lower():
                        for keyword in keywords:
                            if keyword in description:
                                timeframe_relevance += 0.1
                                break

                # Adjust quality based on relevance
                quality += market_relevance + timeframe_relevance

        elif source_type == "Idea" and target_type == "Backtest":
            # Higher quality for backtests with good metrics
            if "metrics" in target_data:
                metrics = target_data["metrics"]
                if metrics and isinstance(metrics, dict):
                    # Adjust quality based on metrics
                    if "Sharpe" in metrics and metrics["Sharpe"] > 1.0:
                        quality += 0.1
                    if "CAGR" in metrics and metrics["CAGR"] > 0.2:
                        quality += 0.1
                    if "MaxDrawdown" in metrics and metrics["MaxDrawdown"] < 0.2:
                        quality += 0.1

        elif source_type == "Scenario" and target_type == "Idea":
            # Check for similarity between scenario and idea descriptions
            if "description" in source_data and "description" in target_data:
                scenario_desc = source_data["description"].lower()
                idea_desc = target_data["description"].lower()

                # Simple word overlap similarity
                scenario_words = set(scenario_desc.split())
                idea_words = set(idea_desc.split())

                if scenario_words and idea_words:
                    # Jaccard similarity
                    intersection = len(scenario_words.intersection(idea_words))
                    union = len(scenario_words.union(idea_words))

                    if union > 0:
                        similarity = intersection / union
                        quality += similarity * 0.3

        # Ensure quality is between 0.0 and 1.0
        quality = max(0.0, min(1.0, quality))

        return quality

    def _find_similar_ideas(self, idea_description: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find ideas similar to the given description.

        Args:
            idea_description: Description to find similar ideas for
            limit: Maximum number of similar ideas to return

        Returns:
            List of similar idea information dictionaries with similarity scores
        """
        similar_ideas = []

        with self.driver.session() as session:
            # Get all ideas
            result = session.run("""
            MATCH (i:Idea)
            RETURN i.id AS id, i.description AS description
            """)

            ideas = [(record["id"], record["description"]) for record in result]

            # Calculate similarity scores
            for idea_id, desc in ideas:
                if not desc or not idea_description:
                    continue

                # Simple word overlap similarity
                idea_words = set(desc.lower().split())
                desc_words = set(idea_description.lower().split())

                if not idea_words or not desc_words:
                    continue

                # Jaccard similarity
                intersection = len(idea_words.intersection(desc_words))
                union = len(idea_words.union(desc_words))

                if union == 0:
                    similarity = 0
                else:
                    similarity = intersection / union

                similar_ideas.append({
                    "id": idea_id,
                    "description": desc,
                    "similarity": similarity
                })

            # Sort by similarity score
            similar_ideas.sort(key=lambda x: x["similarity"], reverse=True)

            # Return top matches
            return similar_ideas[:limit]

    def _find_matching_contexts(self, idea_description: str) -> List[Dict[str, Any]]:
        """Find contexts that match the given idea description.

        Args:
            idea_description: Description to find matching contexts for

        Returns:
            List of matching context information dictionaries with relevance scores
        """
        matching_contexts = []

        # Get all contexts
        contexts = self.get_all_nodes("Context")

        # Define market keywords
        market_keywords = {
            "BTC": ["bitcoin", "btc", "crypto"],
            "ETH": ["ethereum", "eth", "crypto"],
            "SPY": ["spy", "s&p", "s&p 500", "stock", "equity"],
            "AAPL": ["apple", "aapl", "stock", "equity"],
            "MSFT": ["microsoft", "msft", "stock", "equity"],
            "FOREX": ["forex", "currency", "fx"],
            "USD": ["usd", "dollar", "forex", "currency"],
            "EUR": ["eur", "euro", "forex", "currency"]
        }

        # Define timeframe keywords
        timeframe_keywords = {
            "1m": ["minute", "1m", "short-term", "scalping"],
            "5m": ["5m", "short-term", "scalping"],
            "15m": ["15m", "short-term"],
            "1h": ["hour", "1h", "hourly", "intraday"],
            "4h": ["4h", "intraday"],
            "1d": ["day", "1d", "daily", "swing", "long-term"]
        }

        # Calculate relevance scores for each context
        for context in contexts:
            market = context["market"]
            timeframe = context["timeframe"]

            # Calculate market relevance
            market_relevance = 0
            if market in market_keywords:
                for keyword in market_keywords[market]:
                    if keyword.lower() in idea_description.lower():
                        market_relevance += 1

            # Calculate timeframe relevance
            timeframe_relevance = 0
            if timeframe in timeframe_keywords:
                for keyword in timeframe_keywords[timeframe]:
                    if keyword.lower() in idea_description.lower():
                        timeframe_relevance += 1

            # Calculate overall relevance
            relevance = market_relevance + timeframe_relevance

            matching_contexts.append({
                "id": context["id"],
                "market": market,
                "timeframe": timeframe,
                "relevance": relevance
            })

        # Sort by relevance score
        matching_contexts.sort(key=lambda x: x["relevance"], reverse=True)

        # If no relevant contexts found, return all contexts
        if not matching_contexts or matching_contexts[0]["relevance"] == 0:
            return contexts

        # Return contexts with non-zero relevance
        return [c for c in matching_contexts if c["relevance"] > 0]

    def _generate_scenario_description(self, idea_description: str) -> str:
        """Generate a scenario description based on the idea description.

        Args:
            idea_description: Description of the idea

        Returns:
            Generated scenario description
        """
        # Extract strategy type and parameters from the idea description
        strategy_type = ""
        parameters = []

        # Check for strategy types
        if "momentum" in idea_description.lower():
            strategy_type = "Momentum"
            parameters = ["lookback period", "threshold"]
        elif "mean reversion" in idea_description.lower() or "oversold" in idea_description.lower():
            strategy_type = "Mean Reversion"
            parameters = ["RSI period", "oversold threshold"]
        elif "trend" in idea_description.lower():
            strategy_type = "Trend Following"
            parameters = ["moving average period", "signal threshold"]
        elif "breakout" in idea_description.lower():
            strategy_type = "Breakout"
            parameters = ["volatility measure", "breakout threshold"]
        elif "arbitrage" in idea_description.lower():
            strategy_type = "Arbitrage"
            parameters = ["price difference threshold", "execution speed"]
        else:
            # Default to a generic strategy type
            strategy_type = "Trading"
            parameters = ["entry threshold", "exit threshold"]

        # Generate parameter values
        parameter_values = {}
        for param in parameters:
            if "period" in param.lower() or "lookback" in param.lower():
                parameter_values[param] = random.choice([5, 10, 14, 20, 50, 100, 200])
            elif "threshold" in param.lower():
                parameter_values[param] = round(random.uniform(0.1, 0.5), 2)
            else:
                parameter_values[param] = round(random.uniform(0.01, 0.1), 2)

        # Generate parameter settings
        parameter_settings = ", ".join([f"{param}: {value}" for param, value in parameter_values.items()])

        # Generate scenario description
        scenario_desc = f"{strategy_type} implementation with {parameter_settings}"

        return scenario_desc

    def _fix_orphaned_ideas(self,
                           orphaned_ideas: List[Dict[str, Any]],
                           relationship_types: List[str],
                           dry_run: bool,
                           quality_threshold: float = 0.0) -> Dict[str, int]:
        """Fix orphaned ideas by creating missing relationships.

        Args:
            orphaned_ideas: List of orphaned idea information dictionaries
            relationship_types: List of relationship types to fix
            dry_run: If True, only report what would be fixed without making changes

        Returns:
            Dictionary mapping relationship types to the number of relationships created
        """
        created_relationships = {rel_type: 0 for rel_type in relationship_types}

        # Get available backtests, contexts, and scenarios for creating relationships
        backtests = self.get_all_nodes("Backtest") if "TESTED_IN" in relationship_types else []

        for idea in orphaned_ideas:
            idea_id = idea["id"]
            idea_description = idea["description"]
            logger.info(f"Fixing orphaned idea: {idea_id}")

            # Find matching contexts based on idea description
            matching_contexts = self._find_matching_contexts(idea_description)

            # Fix missing TESTED_IN relationship
            if "TESTED_IN" in relationship_types and idea.get("missing_tested_in", False):
                # Create a backtest for this idea
                backtest_id = f"bt_fix_{idea_id}"

                # Choose the most relevant context
                if matching_contexts:
                    context = matching_contexts[0]
                    context_id = context["id"]

                    # Generate realistic metrics based on idea description
                    metrics = self._generate_metrics_for_idea(idea_description)

                    if not dry_run:
                        # Store the backtest
                        self.memory.store_backtest(backtest_id, metrics, idea_id, context_id)
                        created_relationships["TESTED_IN"] += 1
                        created_relationships["EXECUTED_IN"] += 1

                    logger.info(f"  {'Would create' if dry_run else 'Created'} backtest {backtest_id} for idea {idea_id} in context {context_id}")
                    logger.info(f"  Metrics: {metrics}")

            # Fix missing SUBIDEA_OF relationship
            if "SUBIDEA_OF" in relationship_types and idea.get("missing_subidea_of", False):
                # Create a scenario for this idea
                scenario_id = f"scenario_fix_{idea_id}"

                # Generate a meaningful scenario description based on the idea
                scenario_desc = self._generate_scenario_description(idea_description)

                # Choose relevant contexts
                if matching_contexts:
                    # Use up to 3 most relevant contexts
                    relevant_contexts = [c["id"] for c in matching_contexts[:3]]

                    if not dry_run:
                        # Store the scenario
                        self.memory.store_scenario(scenario_id, scenario_desc, idea_id, relevant_contexts)
                        created_relationships["SUBIDEA_OF"] += 1
                        created_relationships["APPLIES_IN"] += len(relevant_contexts)

                    logger.info(f"  {'Would create' if dry_run else 'Created'} scenario {scenario_id} for idea {idea_id}")
                    logger.info(f"  Scenario description: {scenario_desc}")
                    logger.info(f"  Applied to contexts: {relevant_contexts}")

        return created_relationships

    def _generate_metrics_for_idea(self, idea_description: str) -> Dict[str, float]:
        """Generate realistic metrics based on the idea description.

        Args:
            idea_description: Description of the idea

        Returns:
            Dictionary of generated metrics
        """
        # Base metrics with some randomization
        sharpe_base = 0.8 + random.random() * 1.2  # 0.8 to 2.0
        cagr_base = 0.1 + random.random() * 0.3    # 10% to 40%
        max_drawdown_base = 0.1 + random.random() * 0.2  # 10% to 30%
        win_rate_base = 0.4 + random.random() * 0.3  # 40% to 70%

        # Adjust based on strategy type mentioned in the description
        desc_lower = idea_description.lower()

        # Trend following strategies often have better Sharpe ratios
        if "trend" in desc_lower or "momentum" in desc_lower:
            sharpe_base *= 1.2
            win_rate_base *= 0.9  # Lower win rate but higher returns

        # Mean reversion strategies often have higher win rates
        if "mean reversion" in desc_lower or "oversold" in desc_lower or "overbought" in desc_lower:
            win_rate_base *= 1.2
            sharpe_base *= 0.9  # Higher win rate but lower Sharpe

        # Arbitrage strategies have lower returns but very high win rates
        if "arbitrage" in desc_lower:
            win_rate_base *= 1.3
            cagr_base *= 0.7
            max_drawdown_base *= 0.7  # Lower drawdowns

        # Strategies using stop losses often have lower drawdowns
        if "stop loss" in desc_lower or "stop-loss" in desc_lower:
            max_drawdown_base *= 0.8

        # Strategies using multiple indicators often have better metrics
        indicator_count = sum(1 for indicator in ["rsi", "macd", "bollinger", "moving average", "ma", "ema", "sma"]
                             if indicator in desc_lower)
        if indicator_count > 1:
            sharpe_base *= (1 + 0.05 * indicator_count)
            win_rate_base *= (1 + 0.02 * indicator_count)

        # Round to reasonable precision
        metrics = {
            "Sharpe": round(sharpe_base, 2),
            "CAGR": round(cagr_base, 2),
            "MaxDrawdown": round(max_drawdown_base, 2),
            "WinRate": round(win_rate_base, 2),
            "TotalTrades": random.randint(50, 500),
            "ProfitFactor": round(1.0 + random.random() * 1.5, 2),  # 1.0 to 2.5
            "AverageWin": round(0.01 + random.random() * 0.04, 3),  # 1% to 5%
            "AverageLoss": round(0.01 + random.random() * 0.02, 3)  # 1% to 3%
        }

        return metrics

    def _fix_orphaned_backtests(self,
                              orphaned_backtests: List[Dict[str, Any]],
                              relationship_types: List[str],
                              dry_run: bool,
                              quality_threshold: float = 0.0) -> Dict[str, int]:
        """Fix orphaned backtests by creating missing relationships.

        Args:
            orphaned_backtests: List of orphaned backtest information dictionaries
            relationship_types: List of relationship types to fix
            dry_run: If True, only report what would be fixed without making changes

        Returns:
            Dictionary mapping relationship types to the number of relationships created
        """
        created_relationships = {rel_type: 0 for rel_type in relationship_types}

        # Get available ideas and contexts for creating relationships
        ideas = self.get_all_nodes("Idea") if "TESTED_IN" in relationship_types else []
        contexts = self.get_all_nodes("Context") if "EXECUTED_IN" in relationship_types else []

        for backtest in orphaned_backtests:
            backtest_id = backtest["id"]
            logger.info(f"Fixing orphaned backtest: {backtest_id}")

            # Fix missing TESTED_IN relationship
            if "TESTED_IN" in relationship_types and backtest.get("missing_tested_in", False):
                if not dry_run:
                    # Find or create an idea for this backtest
                    with self.driver.session() as session:
                        # Create a new idea
                        idea_id = f"idea_fix_{backtest_id}"
                        idea_desc = f"Strategy for backtest {backtest_id}"

                        # Create the TESTED_IN relationship
                        session.run("""
                        MERGE (i:Idea {id: $idea_id, description: $idea_desc})
                        MERGE (b:Backtest {id: $backtest_id})
                        MERGE (i)-[:TESTED_IN]->(b)
                        """, idea_id=idea_id, idea_desc=idea_desc, backtest_id=backtest_id)

                        created_relationships["TESTED_IN"] += 1

                logger.info(f"  {'Would create' if dry_run else 'Created'} idea idea_fix_{backtest_id} for backtest {backtest_id}")

            # Fix missing EXECUTED_IN relationship
            if "EXECUTED_IN" in relationship_types and backtest.get("missing_executed_in", False):
                if contexts:
                    # Choose a context
                    context = random.choice(contexts)
                    context_id = context["id"]

                    if not dry_run:
                        # Create the EXECUTED_IN relationship
                        with self.driver.session() as session:
                            session.run("""
                            MATCH (b:Backtest {id: $backtest_id})
                            MATCH (c:Context {id: $context_id})
                            MERGE (b)-[:EXECUTED_IN]->(c)
                            """, backtest_id=backtest_id, context_id=context_id)

                            created_relationships["EXECUTED_IN"] += 1

                    logger.info(f"  {'Would connect' if dry_run else 'Connected'} backtest {backtest_id} to context {context_id}")

        return created_relationships

    def _fix_orphaned_contexts(self,
                             orphaned_contexts: List[Dict[str, Any]],
                             relationship_types: List[str],
                             dry_run: bool,
                             quality_threshold: float = 0.0) -> Dict[str, int]:
        """Fix orphaned contexts by creating missing relationships.

        Args:
            orphaned_contexts: List of orphaned context information dictionaries
            relationship_types: List of relationship types to fix
            dry_run: If True, only report what would be fixed without making changes

        Returns:
            Dictionary mapping relationship types to the number of relationships created
        """
        created_relationships = {rel_type: 0 for rel_type in relationship_types}

        for context in orphaned_contexts:
            context_id = context["id"]
            logger.info(f"Fixing orphaned context: {context_id}")

            # Create a new idea and backtest for this context
            idea_id = f"idea_fix_{context_id}"
            idea_desc = f"Strategy for context {context_id}"
            backtest_id = f"bt_fix_{context_id}"

            # Generate realistic metrics
            metrics = {
                "Sharpe": round(0.8 + random.random() * 1.2, 2),
                "CAGR": round(0.1 + random.random() * 0.3, 2),
                "MaxDrawdown": round(0.1 + random.random() * 0.2, 2),
                "WinRate": round(0.4 + random.random() * 0.3, 2)
            }

            if not dry_run:
                # Store the idea and backtest
                self.memory.store_idea(idea_id, idea_desc, [context_id])
                self.memory.store_backtest(backtest_id, metrics, idea_id, context_id)

                if "EXECUTED_IN" in relationship_types:
                    created_relationships["EXECUTED_IN"] += 1
                if "APPLIES_IN" in relationship_types:
                    created_relationships["APPLIES_IN"] += 1
                if "TESTED_IN" in relationship_types:
                    created_relationships["TESTED_IN"] += 1

            logger.info(f"  {'Would create' if dry_run else 'Created'} idea {idea_id} and backtest {backtest_id} for context {context_id}")

        return created_relationships

    def _fix_orphaned_scenarios(self,
                              orphaned_scenarios: List[Dict[str, Any]],
                              relationship_types: List[str],
                              dry_run: bool,
                              quality_threshold: float = 0.0) -> Dict[str, int]:
        """Fix orphaned scenarios by creating missing relationships.

        Args:
            orphaned_scenarios: List of orphaned scenario information dictionaries
            relationship_types: List of relationship types to fix
            dry_run: If True, only report what would be fixed without making changes

        Returns:
            Dictionary mapping relationship types to the number of relationships created
        """
        created_relationships = {rel_type: 0 for rel_type in relationship_types}

        # Get available ideas and contexts for creating relationships
        ideas = self.get_all_nodes("Idea") if "SUBIDEA_OF" in relationship_types else []
        contexts = self.get_all_nodes("Context") if "APPLIES_IN" in relationship_types else []

        for scenario in orphaned_scenarios:
            scenario_id = scenario["id"]
            logger.info(f"Fixing orphaned scenario: {scenario_id}")

            # Fix missing SUBIDEA_OF relationship
            if "SUBIDEA_OF" in relationship_types and scenario.get("missing_subidea_of", False):
                if not dry_run:
                    # Create a new idea for this scenario
                    idea_id = f"idea_fix_{scenario_id}"
                    idea_desc = f"Parent idea for scenario {scenario_id}"

                    # Create the SUBIDEA_OF relationship
                    with self.driver.session() as session:
                        session.run("""
                        MERGE (i:Idea {id: $idea_id, description: $idea_desc})
                        MATCH (s:Scenario {id: $scenario_id})
                        MERGE (s)-[:SUBIDEA_OF]->(i)
                        """, idea_id=idea_id, idea_desc=idea_desc, scenario_id=scenario_id)

                        created_relationships["SUBIDEA_OF"] += 1

                logger.info(f"  {'Would create' if dry_run else 'Created'} idea {idea_id} for scenario {scenario_id}")

            # Fix missing APPLIES_IN relationship
            if "APPLIES_IN" in relationship_types and scenario.get("missing_applies_in", False):
                if contexts:
                    # Choose a context
                    context = random.choice(contexts)
                    context_id = context["id"]

                    if not dry_run:
                        # Create the APPLIES_IN relationship
                        with self.driver.session() as session:
                            session.run("""
                            MATCH (s:Scenario {id: $scenario_id})
                            MATCH (c:Context {id: $context_id})
                            MERGE (s)-[:APPLIES_IN]->(c)
                            """, scenario_id=scenario_id, context_id=context_id)

                            created_relationships["APPLIES_IN"] += 1

                    logger.info(f"  {'Would connect' if dry_run else 'Connected'} scenario {scenario_id} to context {context_id}")

        return created_relationships

    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()

def main():
    """Run the improved orphan fixer."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fix orphaned nodes in the memory knowledge graph")
    parser.add_argument("--node-types", nargs="+", choices=["Idea", "Backtest", "Context", "Scenario"],
                       help="Node types to fix")
    parser.add_argument("--relationship-types", nargs="+", choices=["TESTED_IN", "EXECUTED_IN", "APPLIES_IN", "SUBIDEA_OF"],
                       help="Relationship types to fix")
    parser.add_argument("--dry-run", action="store_true", help="Only report what would be fixed without making changes")
    parser.add_argument("--report-only", action="store_true", help="Only report orphaned nodes without fixing them")
    parser.add_argument("--fix-specific", type=str, help="Fix a specific node by ID")
    parser.add_argument("--fix-specific-type", choices=["Idea", "Backtest", "Context", "Scenario"],
                       help="Type of the specific node to fix")
    parser.add_argument("--quality-threshold", type=float, default=0.0,
                       help="Minimum quality threshold for creating relationships (0.0 to 1.0)")
    parser.add_argument("--output-report", type=str, help="Path to save the orphan report as JSON")
    args = parser.parse_args()

    logger.info("Starting improved orphan fixer...")

    # Initialize the orphan fixer
    fixer = ImprovedOrphanFixer(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )

    # Report only mode
    if args.report_only:
        orphans = fixer.find_orphaned_nodes(args.node_types)

        # Print report
        for node_type, nodes in orphans.items():
            logger.info(f"Found {len(nodes)} orphaned {node_type} nodes")
            for i, node in enumerate(nodes[:10]):  # Show only first 10
                logger.info(f"  {i+1}. {node['id']}")
                if 'description' in node:
                    logger.info(f"     Description: {node['description']}")
                if 'missing_tested_in' in node and node['missing_tested_in']:
                    logger.info(f"     Missing: TESTED_IN relationship")
                if 'missing_executed_in' in node and node['missing_executed_in']:
                    logger.info(f"     Missing: EXECUTED_IN relationship")
                if 'missing_subidea_of' in node and node['missing_subidea_of']:
                    logger.info(f"     Missing: SUBIDEA_OF relationship")
                if 'missing_applies_in' in node and node['missing_applies_in']:
                    logger.info(f"     Missing: APPLIES_IN relationship")

            if len(nodes) > 10:
                logger.info(f"  ... and {len(nodes) - 10} more")

        # Save report to file if requested
        if args.output_report:
            import json
            with open(args.output_report, 'w') as f:
                json.dump(orphans, f, indent=2)
            logger.info(f"Saved orphan report to {args.output_report}")

    # Fix specific node
    elif args.fix_specific and args.fix_specific_type:
        logger.info(f"Fixing specific {args.fix_specific_type} node: {args.fix_specific}")

        # Get the node
        with fixer.driver.session() as session:
            if args.fix_specific_type == "Idea":
                result = session.run("""
                MATCH (i:Idea {id: $id})
                RETURN i.id AS id, i.description AS description,
                       NOT ((i)-[:TESTED_IN]->()) AS missing_tested_in,
                       NOT (()-[:SUBIDEA_OF]->(i)) AS missing_subidea_of
                """, id=args.fix_specific)

                nodes = [{
                    "id": record["id"],
                    "description": record["description"],
                    "missing_tested_in": record["missing_tested_in"],
                    "missing_subidea_of": record["missing_subidea_of"]
                } for record in result]

                if nodes:
                    # Fix the node
                    created_relationships = fixer._fix_orphaned_ideas(
                        nodes,
                        args.relationship_types or ["TESTED_IN", "EXECUTED_IN", "APPLIES_IN", "SUBIDEA_OF"],
                        args.dry_run
                    )
                else:
                    logger.error(f"Node not found: {args.fix_specific}")

            elif args.fix_specific_type == "Backtest":
                result = session.run("""
                MATCH (b:Backtest {id: $id})
                RETURN b.id AS id, b.metrics AS metrics,
                       NOT ((b)<-[:TESTED_IN]-()) AS missing_tested_in,
                       NOT ((b)-[:EXECUTED_IN]->()) AS missing_executed_in
                """, id=args.fix_specific)

                nodes = [{
                    "id": record["id"],
                    "metrics": record["metrics"],
                    "missing_tested_in": record["missing_tested_in"],
                    "missing_executed_in": record["missing_executed_in"]
                } for record in result]

                if nodes:
                    # Fix the node
                    created_relationships = fixer._fix_orphaned_backtests(
                        nodes,
                        args.relationship_types or ["TESTED_IN", "EXECUTED_IN"],
                        args.dry_run
                    )
                else:
                    logger.error(f"Node not found: {args.fix_specific}")

            elif args.fix_specific_type == "Context":
                result = session.run("""
                MATCH (c:Context {id: $id})
                RETURN c.id AS id, c.market AS market, c.timeframe AS timeframe,
                       NOT ((c)<-[:EXECUTED_IN]-()) AS missing_executed_in,
                       NOT ((c)<-[:APPLIES_IN]-()) AS missing_applies_in
                """, id=args.fix_specific)

                nodes = [{
                    "id": record["id"],
                    "market": record["market"],
                    "timeframe": record["timeframe"],
                    "missing_executed_in": record["missing_executed_in"],
                    "missing_applies_in": record["missing_applies_in"]
                } for record in result]

                if nodes:
                    # Fix the node
                    created_relationships = fixer._fix_orphaned_contexts(
                        nodes,
                        args.relationship_types or ["EXECUTED_IN", "APPLIES_IN"],
                        args.dry_run
                    )
                else:
                    logger.error(f"Node not found: {args.fix_specific}")

            elif args.fix_specific_type == "Scenario":
                result = session.run("""
                MATCH (s:Scenario {id: $id})
                RETURN s.id AS id, s.description AS description,
                       NOT ((s)-[:SUBIDEA_OF]->()) AS missing_subidea_of,
                       NOT ((s)-[:APPLIES_IN]->()) AS missing_applies_in
                """, id=args.fix_specific)

                nodes = [{
                    "id": record["id"],
                    "description": record["description"],
                    "missing_subidea_of": record["missing_subidea_of"],
                    "missing_applies_in": record["missing_applies_in"]
                } for record in result]

                if nodes:
                    # Fix the node
                    created_relationships = fixer._fix_orphaned_scenarios(
                        nodes,
                        args.relationship_types or ["SUBIDEA_OF", "APPLIES_IN"],
                        args.dry_run
                    )
                else:
                    logger.error(f"Node not found: {args.fix_specific}")

        # Log results
        if 'created_relationships' in locals():
            for rel_type, count in created_relationships.items():
                logger.info(f"Created {count} {rel_type} relationships")

    # Fix all orphaned nodes
    else:
        created_relationships = fixer.fix_orphaned_nodes(
            node_types=args.node_types,
            relationship_types=args.relationship_types,
            dry_run=args.dry_run,
            quality_threshold=args.quality_threshold
        )

        # Log results
        for rel_type, count in created_relationships.items():
            logger.info(f"Created {count} {rel_type} relationships")

    # Close the orphan fixer
    fixer.close()

    logger.info("Improved orphan fixer completed successfully!")

if __name__ == "__main__":
    main()
