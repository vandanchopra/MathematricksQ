# src/memory/graph_backend.py
import os
from typing import Dict, List, Any, Optional, Union, cast
from datetime import datetime
from neo4j import GraphDatabase
from .interface import MemoryBackend, IdeaDict, ScenarioDict, ContextDict, BacktestDict, MetricsDict

class Neo4jMemory(MemoryBackend):
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.close()

    def clear_database(self):
        """Clear all data from the database."""
        with self.driver.session() as session:
            session.run("""
            MATCH (n)
            DETACH DELETE n
            """)

    def store_idea(self, idea_id: str, description: str, context_ids: List[str]) -> None:
        with self.driver.session() as session:
            # Create idea node
            session.run(
                """
                MERGE (i:Idea {id: $idea_id})
                SET i.description = $description,
                    i.created_at = datetime()
                """,
                idea_id=idea_id, description=description
            )

            # Create relationships to contexts
            for context_id in context_ids:
                session.run(
                    """
                    MATCH (i:Idea {id: $idea_id})
                    MERGE (c:Context {id: $context_id})
                    MERGE (i)-[r:APPLIES_IN]->(c)
                    """,
                    idea_id=idea_id, context_id=context_id
                )

    def store_backtest(self, backtest_id: str, metrics: MetricsDict, idea_id: str, context_id: str) -> None:
        with self.driver.session() as session:
            # Create backtest node
            # Neo4j doesn't support nested properties, so we need to flatten the metrics
            # Store each metric as a separate property
            properties = {f"metric_{k}": v for k, v in metrics.items()}
            properties["id"] = backtest_id
            properties["date"] = datetime.now().isoformat()

            # Create the Cypher query dynamically
            property_string = ", ".join([f"b.{k} = ${k}" for k in properties.keys()])
            query = f"""
            MERGE (b:Backtest {{id: $id}})
            SET {property_string}
            """

            session.run(query, **properties)

            # Link to idea
            session.run(
                """
                MATCH (b:Backtest {id: $backtest_id})
                MATCH (i:Idea {id: $idea_id})
                MERGE (i)-[r:TESTED_IN]->(b)
                """,
                backtest_id=backtest_id, idea_id=idea_id
            )

            # Link to context
            session.run(
                """
                MATCH (b:Backtest {id: $backtest_id})
                MATCH (c:Context {id: $context_id})
                MERGE (b)-[r:EXECUTED_IN]->(c)
                """,
                backtest_id=backtest_id, context_id=context_id
            )

    def store_scenario(self, scenario_id: str, description: str, parent_idea_id: str, context_ids: List[str]) -> None:
        with self.driver.session() as session:
            # Create scenario node
            session.run(
                """
                MERGE (s:Scenario {id: $scenario_id})
                SET s.description = $description,
                    s.created_at = datetime()
                """,
                scenario_id=scenario_id, description=description
            )

            # Link to parent idea
            session.run(
                """
                MATCH (s:Scenario {id: $scenario_id})
                MATCH (i:Idea {id: $parent_idea_id})
                MERGE (s)-[r:SUBIDEA_OF]->(i)
                """,
                scenario_id=scenario_id, parent_idea_id=parent_idea_id
            )

            # Create relationships to contexts
            for context_id in context_ids:
                session.run(
                    """
                    MATCH (s:Scenario {id: $scenario_id})
                    MERGE (c:Context {id: $context_id})
                    MERGE (s)-[r:APPLIES_IN]->(c)
                    """,
                    scenario_id=scenario_id, context_id=context_id
                )

    def store_context(self, context_id: str, market: str, timeframe: str) -> None:
        with self.driver.session() as session:
            session.run(
                """
                MERGE (c:Context {id: $context_id})
                SET c.market = $market,
                    c.timeframe = $timeframe
                """,
                context_id=context_id, market=market, timeframe=timeframe
            )

    def get_idea(self, idea_id: str) -> Optional[IdeaDict]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (i:Idea {id: $idea_id})
                RETURN i.id AS id, i.description AS description, i.created_at AS created_at
                """,
                idea_id=idea_id
            )
            record = result.single()
            if not record:
                return None

            return {
                "id": record["id"],
                "description": record["description"],
                "created_at": record["created_at"]
            }

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioDict]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Scenario {id: $scenario_id})
                OPTIONAL MATCH (s)-[:SUBIDEA_OF]->(i:Idea)
                RETURN s.id AS id, s.description AS description, s.created_at AS created_at, i.id AS parent_idea_id
                """,
                scenario_id=scenario_id
            )
            record = result.single()
            if not record:
                return None

            return {
                "id": record["id"],
                "description": record["description"],
                "created_at": record["created_at"],
                "parent_idea_id": record["parent_idea_id"]
            }

    def get_context(self, context_id: str) -> Optional[ContextDict]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Context {id: $context_id})
                RETURN c.id AS id, c.market AS market, c.timeframe AS timeframe
                """,
                context_id=context_id
            )
            record = result.single()
            if not record:
                return None

            return {
                "id": record["id"],
                "market": record["market"],
                "timeframe": record["timeframe"]
            }

    def get_backtest(self, backtest_id: str) -> Optional[BacktestDict]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (b:Backtest {id: $backtest_id})
                MATCH (i:Idea)-[:TESTED_IN]->(b)
                MATCH (b)-[:EXECUTED_IN]->(c:Context)
                RETURN b, i.id AS idea_id, c.id AS context_id
                """,
                backtest_id=backtest_id
            )
            record = result.single()
            if not record:
                return None

            # Extract backtest node properties
            backtest_node = record["b"]

            # Extract metrics from flattened properties
            metrics = {}
            for key, value in backtest_node.items():
                if key.startswith("metric_"):
                    metric_name = key[7:]  # Remove "metric_" prefix
                    metrics[metric_name] = value

            return {
                "id": backtest_node["id"],
                "date": backtest_node["date"],
                "metrics": metrics,
                "idea_id": record["idea_id"],
                "context_id": record["context_id"]
            }

    def query_similar_ideas(self, embedding: List[float], context_id: Optional[str] = None, top_k: int = 10) -> List[IdeaDict]:
        # Neo4j doesn't handle vector similarity directly
        # This is a placeholder - in practice, use PatANN for this
        with self.driver.session() as session:
            query = """
            MATCH (i:Idea)
            """

            if context_id:
                query += "MATCH (i)-[:APPLIES_IN]->(c:Context {id: $context_id})\n"

            query += """
            RETURN i.id AS id, i.description AS description, i.created_at AS created_at
            LIMIT $top_k
            """

            params = {"top_k": top_k}
            if context_id:
                params["context_id"] = context_id

            result = session.run(query, **params)

            return [
                {
                    "id": record["id"],
                    "description": record["description"],
                    "created_at": record["created_at"]
                }
                for record in result
            ]

    def query_top_ideas_by_metrics(self, context_id: Optional[str] = None, metric: str = "Sharpe", weights: Optional[Dict[str, float]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            # Base query to match ideas and backtests
            query = """
            MATCH (i:Idea)-[:TESTED_IN]->(b:Backtest)
            """

            if context_id:
                query += "MATCH (b)-[:EXECUTED_IN]->(c:Context {id: $context_id})\n"

            # If weights are provided, use a weighted formula
            if weights:
                # Adjust for flattened metrics
                weight_terms = []
                for m, w in weights.items():
                    weight_terms.append(f"b.metric_{m} * {w}")

                weight_formula = " + ".join(weight_terms)
                query += f"""
                RETURN i.id AS id, i.description AS description, i.created_at AS created_at, b AS backtest_node,
                       {weight_formula} AS score
                ORDER BY score DESC
                """
            else:
                # Otherwise, sort by the specified metric
                query += f"""
                RETURN i.id AS id, i.description AS description, i.created_at AS created_at, b AS backtest_node
                ORDER BY b.metric_{metric} DESC
                """

            query += "LIMIT $limit"

            params = {"limit": limit}
            if context_id:
                params["context_id"] = context_id

            result = session.run(query, **params)

            return_list = []
            for record in result:
                # Extract backtest node properties
                backtest_node = record["backtest_node"]

                # Extract metrics from flattened properties
                metrics = {}
                for key, value in backtest_node.items():
                    if key.startswith("metric_"):
                        metric_name = key[7:]  # Remove "metric_" prefix
                        metrics[metric_name] = value

                # Calculate score if not provided
                if "score" in record:
                    score = record["score"]
                else:
                    score = metrics.get(metric, 0)

                return_list.append({
                    "id": record["id"],
                    "description": record["description"],
                    "created_at": record["created_at"],
                    "metrics": metrics,
                    "score": score
                })

            return return_list

    def query_scenarios_for_idea(self, idea_id: str) -> List[ScenarioDict]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Scenario)-[:SUBIDEA_OF]->(i:Idea {id: $idea_id})
                RETURN s.id AS id, s.description AS description, s.created_at AS created_at, i.id AS parent_idea_id
                """,
                idea_id=idea_id
            )

            return [
                {
                    "id": record["id"],
                    "description": record["description"],
                    "created_at": record["created_at"],
                    "parent_idea_id": record["parent_idea_id"]
                }
                for record in result
            ]

    def query_backtests_for_idea(self, idea_id: str, context_id: Optional[str] = None) -> List[BacktestDict]:
        with self.driver.session() as session:
            query = """
            MATCH (i:Idea {id: $idea_id})-[:TESTED_IN]->(b:Backtest)
            """

            if context_id:
                query += "MATCH (b)-[:EXECUTED_IN]->(c:Context {id: $context_id})\n"
            else:
                query += "MATCH (b)-[:EXECUTED_IN]->(c:Context)\n"

            query += """
            RETURN b AS backtest_node, i.id AS idea_id, c.id AS context_id
            """

            params = {"idea_id": idea_id}
            if context_id:
                params["context_id"] = context_id

            result = session.run(query, **params)

            return_list = []
            for record in result:
                # Extract backtest node properties
                backtest_node = record["backtest_node"]

                # Extract metrics from flattened properties
                metrics = {}
                for key, value in backtest_node.items():
                    if key.startswith("metric_"):
                        metric_name = key[7:]  # Remove "metric_" prefix
                        metrics[metric_name] = value

                return_list.append({
                    "id": backtest_node["id"],
                    "date": backtest_node["date"],
                    "metrics": metrics,
                    "idea_id": record["idea_id"],
                    "context_id": record["context_id"]
                })

            return return_list

    def query_ideas_for_context(self, context_id: str) -> List[IdeaDict]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (i:Idea)-[:APPLIES_IN]->(c:Context {id: $context_id})
                RETURN i.id AS id, i.description AS description, i.created_at AS created_at
                """,
                context_id=context_id
            )

            return [
                {
                    "id": record["id"],
                    "description": record["description"],
                    "created_at": record["created_at"]
                }
                for record in result
            ]

    def rag_query(self, prompt: str, context_id: Optional[str] = None, top_k: int = 5) -> str:
        # Neo4j doesn't handle RAG directly
        # This is a placeholder - in practice, use GraphRAG for this
        raise NotImplementedError("Use GraphRAG for RAG queries")

    def recommend_ideas(self, current_strategy_embedding: List[float], context_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # This is a hybrid approach that would combine vector similarity from PatANN with graph re-ranking
        # For now, we'll implement a simplified version that just returns ideas for the context
        # In a real implementation, this would first query PatANN for similar ideas, then re-rank using Neo4j

        # Step 1: Get ideas for the context (this would normally come from PatANN)
        ideas = self.query_ideas_for_context(context_id)

        # Step 2: Re-rank based on backtest metrics
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (i:Idea)-[:APPLIES_IN]->(c:Context {id: $context_id})
                MATCH (i)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c)
                WHERE i.id IN $idea_ids
                RETURN i.id AS id, i.description AS description, i.created_at AS created_at, b AS backtest_node,
                       (b.metric_Sharpe * 0.5 + b.metric_CAGR * 0.3 - b.metric_MaxDrawdown * 0.2) AS score
                ORDER BY score DESC
                LIMIT $top_k
                """,
                context_id=context_id, idea_ids=[idea["id"] for idea in ideas], top_k=top_k
            )

            return_list = []
            for record in result:
                # Extract backtest node properties
                backtest_node = record["backtest_node"]

                # Extract metrics from flattened properties
                metrics = {}
                for key, value in backtest_node.items():
                    if key.startswith("metric_"):
                        metric_name = key[7:]  # Remove "metric_" prefix
                        metrics[metric_name] = value

                return_list.append({
                    "id": record["id"],
                    "description": record["description"],
                    "created_at": record["created_at"],
                    "metrics": metrics,
                    "score": record["score"]
                })

            return return_list
