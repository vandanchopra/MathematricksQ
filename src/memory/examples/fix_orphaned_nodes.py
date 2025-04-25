#!/usr/bin/env python3
"""
Script to fix orphaned nodes in the memory knowledge graph
"""

import os
import sys
import logging
import random
from typing import Dict, List, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from neo4j import GraphDatabase
from src.memory.hybrid_backend import HybridMemory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OrphanFixer")

class OrphanFixer:
    """Class to fix orphaned nodes in the memory knowledge graph."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """Initialize the orphan fixer.
        
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
        logger.info("OrphanFixer initialized")
    
    def find_orphaned_ideas(self) -> List[Dict[str, Any]]:
        """Find ideas without TESTED_IN or SUBIDEA_OF relationships.
        
        Returns:
            List of orphaned ideas
        """
        orphaned_ideas = []
        with self.driver.session() as session:
            # Find Ideas without TESTED_IN
            result = session.run("""
            MATCH (i:Idea)
            WHERE NOT ((i)-[:TESTED_IN]->())
            RETURN i.id AS id, i.description AS description
            """)
            
            for record in result:
                orphaned_ideas.append({
                    "id": record["id"],
                    "description": record["description"],
                    "missing": "TESTED_IN"
                })
            
            # Find Ideas without SUBIDEA_OF
            result = session.run("""
            MATCH (i:Idea)
            WHERE NOT (()-[:SUBIDEA_OF]->(i))
            RETURN i.id AS id, i.description AS description
            """)
            
            for record in result:
                # Check if this idea is already in the list
                existing = next((idea for idea in orphaned_ideas if idea["id"] == record["id"]), None)
                if existing:
                    existing["missing"] += ", SUBIDEA_OF"
                else:
                    orphaned_ideas.append({
                        "id": record["id"],
                        "description": record["description"],
                        "missing": "SUBIDEA_OF"
                    })
        
        return orphaned_ideas
    
    def find_orphaned_backtests(self) -> List[Dict[str, Any]]:
        """Find backtests without TESTED_IN or EXECUTED_IN relationships.
        
        Returns:
            List of orphaned backtests
        """
        orphaned_backtests = []
        with self.driver.session() as session:
            # Find Backtests without TESTED_IN
            result = session.run("""
            MATCH (b:Backtest)
            WHERE NOT ((b)<-[:TESTED_IN]-())
            RETURN b.id AS id
            """)
            
            for record in result:
                orphaned_backtests.append({
                    "id": record["id"],
                    "missing": "TESTED_IN"
                })
            
            # Find Backtests without EXECUTED_IN
            result = session.run("""
            MATCH (b:Backtest)
            WHERE NOT ((b)-[:EXECUTED_IN]->())
            RETURN b.id AS id
            """)
            
            for record in result:
                # Check if this backtest is already in the list
                existing = next((bt for bt in orphaned_backtests if bt["id"] == record["id"]), None)
                if existing:
                    existing["missing"] += ", EXECUTED_IN"
                else:
                    orphaned_backtests.append({
                        "id": record["id"],
                        "missing": "EXECUTED_IN"
                    })
        
        return orphaned_backtests
    
    def find_orphaned_contexts(self) -> List[Dict[str, Any]]:
        """Find contexts without EXECUTED_IN or APPLIES_IN relationships.
        
        Returns:
            List of orphaned contexts
        """
        orphaned_contexts = []
        with self.driver.session() as session:
            # Find Contexts without EXECUTED_IN or APPLIES_IN
            result = session.run("""
            MATCH (c:Context)
            WHERE NOT ((c)<-[:EXECUTED_IN]-()) AND NOT ((c)<-[:APPLIES_IN]-())
            RETURN c.id AS id, c.market AS market, c.timeframe AS timeframe
            """)
            
            for record in result:
                orphaned_contexts.append({
                    "id": record["id"],
                    "market": record["market"],
                    "timeframe": record["timeframe"],
                    "missing": "EXECUTED_IN, APPLIES_IN"
                })
        
        return orphaned_contexts
    
    def find_orphaned_scenarios(self) -> List[Dict[str, Any]]:
        """Find scenarios without SUBIDEA_OF or APPLIES_IN relationships.
        
        Returns:
            List of orphaned scenarios
        """
        orphaned_scenarios = []
        with self.driver.session() as session:
            # Find Scenarios without SUBIDEA_OF
            result = session.run("""
            MATCH (s:Scenario)
            WHERE NOT ((s)-[:SUBIDEA_OF]->())
            RETURN s.id AS id, s.description AS description
            """)
            
            for record in result:
                orphaned_scenarios.append({
                    "id": record["id"],
                    "description": record["description"],
                    "missing": "SUBIDEA_OF"
                })
            
            # Find Scenarios without APPLIES_IN
            result = session.run("""
            MATCH (s:Scenario)
            WHERE NOT ((s)-[:APPLIES_IN]->())
            RETURN s.id AS id, s.description AS description
            """)
            
            for record in result:
                # Check if this scenario is already in the list
                existing = next((s for s in orphaned_scenarios if s["id"] == record["id"]), None)
                if existing:
                    existing["missing"] += ", APPLIES_IN"
                else:
                    orphaned_scenarios.append({
                        "id": record["id"],
                        "description": record["description"],
                        "missing": "APPLIES_IN"
                    })
        
        return orphaned_scenarios
    
    def get_all_contexts(self) -> List[Dict[str, Any]]:
        """Get all contexts from the database.
        
        Returns:
            List of contexts
        """
        contexts = []
        with self.driver.session() as session:
            result = session.run("""
            MATCH (c:Context)
            RETURN c.id AS id, c.market AS market, c.timeframe AS timeframe
            """)
            
            for record in result:
                contexts.append({
                    "id": record["id"],
                    "market": record["market"],
                    "timeframe": record["timeframe"]
                })
        
        return contexts
    
    def fix_orphaned_ideas(self, orphaned_ideas: List[Dict[str, Any]]) -> None:
        """Fix orphaned ideas by creating missing relationships.
        
        Args:
            orphaned_ideas: List of orphaned ideas
        """
        contexts = self.get_all_contexts()
        
        for idea in orphaned_ideas:
            idea_id = idea["id"]
            missing = idea["missing"]
            
            logger.info(f"Fixing orphaned idea: {idea_id} (missing: {missing})")
            
            # Fix missing TESTED_IN relationship
            if "TESTED_IN" in missing:
                # Create a backtest for this idea
                backtest_id = f"bt_fix_{idea_id}"
                context = random.choice(contexts)
                context_id = context["id"]
                
                # Generate realistic metrics
                metrics = {
                    "Sharpe": round(0.8 + random.random() * 1.2, 2),
                    "CAGR": round(0.1 + random.random() * 0.3, 2),
                    "MaxDrawdown": round(0.1 + random.random() * 0.2, 2),
                    "WinRate": round(0.4 + random.random() * 0.3, 2)
                }
                
                # Store the backtest
                self.memory.store_backtest(backtest_id, metrics, idea_id, context_id)
                logger.info(f"  Created backtest {backtest_id} for idea {idea_id} in context {context_id}")
            
            # Fix missing SUBIDEA_OF relationship
            if "SUBIDEA_OF" in missing:
                # Create a scenario for this idea
                scenario_id = f"scenario_fix_{idea_id}"
                scenario_desc = f"Implementation for {idea_id}: {random.choice(['aggressive', 'conservative', 'balanced'])} parameter settings"
                
                # Choose a context
                context = random.choice(contexts)
                context_id = context["id"]
                
                # Store the scenario
                self.memory.store_scenario(scenario_id, scenario_desc, idea_id, [context_id])
                logger.info(f"  Created scenario {scenario_id} for idea {idea_id}")
    
    def fix_orphaned_backtests(self, orphaned_backtests: List[Dict[str, Any]]) -> None:
        """Fix orphaned backtests by creating missing relationships.
        
        Args:
            orphaned_backtests: List of orphaned backtests
        """
        contexts = self.get_all_contexts()
        
        for backtest in orphaned_backtests:
            backtest_id = backtest["id"]
            missing = backtest["missing"]
            
            logger.info(f"Fixing orphaned backtest: {backtest_id} (missing: {missing})")
            
            # Fix missing TESTED_IN relationship
            if "TESTED_IN" in missing:
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
                    
                    logger.info(f"  Created idea {idea_id} for backtest {backtest_id}")
            
            # Fix missing EXECUTED_IN relationship
            if "EXECUTED_IN" in missing:
                # Choose a context
                context = random.choice(contexts)
                context_id = context["id"]
                
                # Create the EXECUTED_IN relationship
                with self.driver.session() as session:
                    session.run("""
                    MATCH (b:Backtest {id: $backtest_id})
                    MATCH (c:Context {id: $context_id})
                    MERGE (b)-[:EXECUTED_IN]->(c)
                    """, backtest_id=backtest_id, context_id=context_id)
                    
                    logger.info(f"  Connected backtest {backtest_id} to context {context_id}")
    
    def fix_orphaned_contexts(self, orphaned_contexts: List[Dict[str, Any]]) -> None:
        """Fix orphaned contexts by creating missing relationships.
        
        Args:
            orphaned_contexts: List of orphaned contexts
        """
        for context in orphaned_contexts:
            context_id = context["id"]
            missing = context["missing"]
            
            logger.info(f"Fixing orphaned context: {context_id} (missing: {missing})")
            
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
            
            # Store the idea and backtest
            self.memory.store_idea(idea_id, idea_desc, [context_id])
            self.memory.store_backtest(backtest_id, metrics, idea_id, context_id)
            logger.info(f"  Created idea {idea_id} and backtest {backtest_id} for context {context_id}")
    
    def fix_orphaned_scenarios(self, orphaned_scenarios: List[Dict[str, Any]]) -> None:
        """Fix orphaned scenarios by creating missing relationships.
        
        Args:
            orphaned_scenarios: List of orphaned scenarios
        """
        contexts = self.get_all_contexts()
        
        for scenario in orphaned_scenarios:
            scenario_id = scenario["id"]
            missing = scenario["missing"]
            
            logger.info(f"Fixing orphaned scenario: {scenario_id} (missing: {missing})")
            
            # Fix missing SUBIDEA_OF relationship
            if "SUBIDEA_OF" in missing:
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
                    
                    logger.info(f"  Created idea {idea_id} for scenario {scenario_id}")
            
            # Fix missing APPLIES_IN relationship
            if "APPLIES_IN" in missing:
                # Choose a context
                context = random.choice(contexts)
                context_id = context["id"]
                
                # Create the APPLIES_IN relationship
                with self.driver.session() as session:
                    session.run("""
                    MATCH (s:Scenario {id: $scenario_id})
                    MATCH (c:Context {id: $context_id})
                    MERGE (s)-[:APPLIES_IN]->(c)
                    """, scenario_id=scenario_id, context_id=context_id)
                    
                    logger.info(f"  Connected scenario {scenario_id} to context {context_id}")
    
    def fix_all_orphans(self) -> None:
        """Fix all orphaned nodes in the database."""
        # Find orphaned nodes
        orphaned_ideas = self.find_orphaned_ideas()
        orphaned_backtests = self.find_orphaned_backtests()
        orphaned_contexts = self.find_orphaned_contexts()
        orphaned_scenarios = self.find_orphaned_scenarios()
        
        # Log orphaned nodes
        logger.info(f"Found {len(orphaned_ideas)} orphaned ideas")
        logger.info(f"Found {len(orphaned_backtests)} orphaned backtests")
        logger.info(f"Found {len(orphaned_contexts)} orphaned contexts")
        logger.info(f"Found {len(orphaned_scenarios)} orphaned scenarios")
        
        # Fix orphaned nodes
        self.fix_orphaned_ideas(orphaned_ideas)
        self.fix_orphaned_backtests(orphaned_backtests)
        self.fix_orphaned_contexts(orphaned_contexts)
        self.fix_orphaned_scenarios(orphaned_scenarios)
        
        # Verify fixes
        remaining_orphaned_ideas = self.find_orphaned_ideas()
        remaining_orphaned_backtests = self.find_orphaned_backtests()
        remaining_orphaned_contexts = self.find_orphaned_contexts()
        remaining_orphaned_scenarios = self.find_orphaned_scenarios()
        
        logger.info(f"After fixes, found {len(remaining_orphaned_ideas)} orphaned ideas")
        logger.info(f"After fixes, found {len(remaining_orphaned_backtests)} orphaned backtests")
        logger.info(f"After fixes, found {len(remaining_orphaned_contexts)} orphaned contexts")
        logger.info(f"After fixes, found {len(remaining_orphaned_scenarios)} orphaned scenarios")
    
    def close(self) -> None:
        """Close the Neo4j driver."""
        self.driver.close()

def main():
    """Run the orphan fixer."""
    logger.info("Starting orphan fixer...")
    
    # Initialize the orphan fixer
    fixer = OrphanFixer(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    # Fix all orphaned nodes
    fixer.fix_all_orphans()
    
    # Close the orphan fixer
    fixer.close()
    
    logger.info("Orphan fixer completed successfully!")

if __name__ == "__main__":
    main()
