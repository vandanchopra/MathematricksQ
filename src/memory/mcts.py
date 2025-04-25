"""
Monte Carlo Tree Search (MCTS) implementation for trading strategy optimization.

This module implements MCTS to systematically explore and optimize trading strategies
by treating each idea as a node in a tree and using UCB to balance exploration and exploitation.
"""

import os
import math
import logging
import random
import uuid
from typing import List, Dict, Optional, Tuple, Any
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mcts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MCTS")

# Load environment variables
load_dotenv()

# Neo4j connection parameters
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7688")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "trading123")

# Create a driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# Import your existing backtester agent
# This is a placeholder - replace with your actual import
import sys
import os as _os

# Add the current directory to the path so we can import the backtester_agent module
sys.path.append(_os.path.dirname(_os.path.abspath(__file__)))
from backtester_agent import run_backtest

class MCTSNode:
    """
    Node in the Monte Carlo Tree Search.
    
    Attributes:
        idea_id (str): ID of the idea represented by this node
        parent (MCTSNode): Parent node
        children (List[MCTSNode]): Child nodes
        N (int): Number of visits
        W (float): Total reward
        context (Dict): Context information (market, timeframe, etc.)
        params (Dict): Parameters for the idea
        backtest_id (str): ID of the backtest associated with this node
        description (str): Description of the idea
    """
    
    def __init__(self, idea_id: str, parent: Optional['MCTSNode'] = None, 
                 context: Optional[Dict] = None, params: Optional[Dict] = None,
                 description: Optional[str] = None):
        self.idea_id = idea_id
        self.parent = parent
        self.children: List['MCTSNode'] = []
        self.N = 0  # visit count
        self.W = 0.0  # total reward
        self.context = context or {"market": "BTC", "timeframe": "DAILY"}
        self.params = params or {}
        self.backtest_id = None
        self.description = description
    
    @property
    def Q(self) -> float:
        """Average reward."""
        return self.W / self.N if self.N else 0
    
    @property
    def is_leaf(self) -> bool:
        """Check if the node is a leaf node (has no children)."""
        return len(self.children) == 0
    
    def __str__(self) -> str:
        return f"MCTSNode(idea_id={self.idea_id}, N={self.N}, W={self.W:.2f}, Q={self.Q:.2f})"
    
    def __repr__(self) -> str:
        return self.__str__()


def compute_score(metrics: Dict) -> float:
    """
    Compute a composite score for a backtest based on its metrics.
    
    Args:
        metrics (dict): Dictionary containing backtest metrics
        
    Returns:
        float: Composite score
    """
    # Default values in case metrics are missing
    sharpe = metrics.get("metric_Sharpe", 0)
    cagr = metrics.get("metric_CAGR", 0)
    max_drawdown = metrics.get("metric_MaxDrawdown", 0)
    
    # Compute score using the formula: 0.5*Sharpe + 0.3*CAGR - 0.2*MaxDrawdown
    score = 0.5 * sharpe + 0.3 * cagr - 0.2 * max_drawdown
    
    return score


def select(node: MCTSNode, exploration_constant: float = 1.0) -> MCTSNode:
    """
    Select a child node using UCB1 formula.
    
    Args:
        node (MCTSNode): Parent node
        exploration_constant (float): Controls exploration vs. exploitation
        
    Returns:
        MCTSNode: Selected child node
    """
    # If node is a leaf node, return it
    if node.is_leaf:
        return node
    
    # Select child with highest UCB value
    best_child = None
    best_ucb = float('-inf')
    
    for child in node.children:
        # UCB1 formula: Q + c * sqrt(ln(N_parent) / N_child)
        if child.N == 0:
            # If child has not been visited, prioritize it
            ucb = float('inf')
        else:
            ucb = child.Q + exploration_constant * math.sqrt(math.log(node.N) / child.N)
        
        if ucb > best_ucb:
            best_ucb = ucb
            best_child = child
    
    # Recursively select from the best child
    return select(best_child, exploration_constant)


def expand(node: MCTSNode) -> MCTSNode:
    """
    Expand the node by creating a new child node.
    
    Args:
        node (MCTSNode): Node to expand
        
    Returns:
        MCTSNode: New child node
    """
    # Get the idea details from Neo4j
    with driver.session() as session:
        result = session.run("""
        MATCH (i:Idea {id: $idea_id})
        RETURN i.description AS description
        """, idea_id=node.idea_id)
        
        record = result.single()
        if record:
            description = record["description"]
        else:
            description = f"Variation of {node.idea_id}"
    
    # Generate a new idea ID
    new_idea_id = str(uuid.uuid4())
    
    # Create variations of the context or parameters
    variation_type = random.choice(["context", "params"])
    
    if variation_type == "context":
        # Vary the context (market, timeframe)
        markets = ["BTC", "ETH", "SOL", "AAPL", "MSFT", "SPY"]
        timeframes = ["DAILY", "HOURLY", "15MIN", "5MIN", "1MIN"]
        
        new_context = {
            "market": random.choice(markets),
            "timeframe": random.choice(timeframes)
        }
        new_params = node.params.copy()
    else:
        # Vary the parameters
        new_context = node.context.copy()
        new_params = node.params.copy()
        
        # Add or modify a random parameter
        param_keys = ["lookback", "threshold", "stop_loss", "take_profit", "position_size"]
        param_key = random.choice(param_keys)
        
        if param_key == "lookback":
            new_params[param_key] = random.randint(5, 200)
        elif param_key == "threshold":
            new_params[param_key] = random.uniform(0.1, 5.0)
        elif param_key == "stop_loss":
            new_params[param_key] = random.uniform(0.01, 0.1)
        elif param_key == "take_profit":
            new_params[param_key] = random.uniform(0.02, 0.2)
        elif param_key == "position_size":
            new_params[param_key] = random.uniform(0.1, 1.0)
    
    # Create a new description for the variation
    new_description = f"Variation of {description[:100]}... with {variation_type} changes"
    
    # Create a new child node
    child = MCTSNode(
        idea_id=new_idea_id,
        parent=node,
        context=new_context,
        params=new_params,
        description=new_description
    )
    
    # Add the child to the parent's children
    node.children.append(child)
    
    # Store the new idea in Neo4j
    with driver.session() as session:
        session.run("""
        CREATE (i:Idea {id: $idea_id, description: $description, testCount: 0, totalScore: 0.0})
        """, idea_id=new_idea_id, description=new_description)
    
    logger.info(f"Created new idea: {new_idea_id} as a variation of {node.idea_id}")
    
    return child


def simulate(node: MCTSNode) -> float:
    """
    Run a backtest for the node and return the score.
    
    Args:
        node (MCTSNode): Node to simulate
        
    Returns:
        float: Score of the backtest
    """
    logger.info(f"Simulating backtest for idea: {node.idea_id}")
    
    try:
        # Run the backtest using your existing backtester agent
        metrics = run_backtest(node.description, node.context, node.params)
        
        # Compute the score
        score = compute_score(metrics)
        logger.info(f"Backtest complete. Score: {score:.4f}")
        
        # Generate a unique ID for the backtest
        backtest_id = f"bt_{str(uuid.uuid4())}"
        node.backtest_id = backtest_id
        
        # Store the backtest results in Neo4j
        with driver.session() as session:
            # Create Backtest node
            session.run("""
            MERGE (b:Backtest {id: $bt_id})
            SET b.metric_Sharpe = $Sharpe,
                b.metric_CAGR = $CAGR,
                b.metric_MaxDrawdown = $MaxDrawdown,
                b.metric_WinRate = $WinRate,
                b.metric_TotalTrades = $TotalTrades,
                b.metric_ProfitFactor = $ProfitFactor,
                b.date = datetime()
            """, {
                "bt_id": backtest_id,
                "Sharpe": metrics.get("metric_Sharpe", 0),
                "CAGR": metrics.get("metric_CAGR", 0),
                "MaxDrawdown": metrics.get("metric_MaxDrawdown", 0),
                "WinRate": metrics.get("metric_WinRate", 0),
                "TotalTrades": metrics.get("metric_TotalTrades", 0),
                "ProfitFactor": metrics.get("metric_ProfitFactor", 0)
            })
            
            # Create TESTED_IN relationship
            session.run("""
            MATCH (i:Idea {id: $idea_id}), (b:Backtest {id: $bt_id})
            MERGE (i)-[r:TESTED_IN]->(b)
            """, {
                "idea_id": node.idea_id,
                "bt_id": backtest_id
            })
            
            # Update idea counters
            session.run("""
            MATCH (i:Idea {id: $idea_id})
            SET i.testCount = COALESCE(i.testCount, 0) + 1,
                i.totalScore = COALESCE(i.totalScore, 0.0) + $score
            """, {
                "idea_id": node.idea_id,
                "score": score
            })
            
            # Connect to a Context
            context_id = f"context_{node.context['market']}_{node.context['timeframe']}"
            session.run("""
            MATCH (b:Backtest {id: $bt_id})
            MERGE (c:Context {id: $context_id, market: $market, timeframe: $timeframe})
            MERGE (b)-[:EXECUTED_IN]->(c)
            """, {
                "bt_id": backtest_id,
                "context_id": context_id,
                "market": node.context["market"],
                "timeframe": node.context["timeframe"]
            })
            
            # Create a Scenario node for the parameters
            if node.params:
                scenario_id = f"scenario_{str(uuid.uuid4())}"
                scenario_desc = f"Parameters: {str(node.params)}"
                session.run("""
                MATCH (b:Backtest {id: $bt_id})
                MERGE (s:Scenario {id: $scenario_id, description: $description})
                MERGE (b)-[:APPLIES_TO]->(s)
                """, {
                    "bt_id": backtest_id,
                    "scenario_id": scenario_id,
                    "description": scenario_desc
                })
            
            logger.info(f"Stored backtest results in Neo4j. Backtest ID: {backtest_id}")
        
        return score
        
    except Exception as e:
        logger.error(f"Error simulating backtest for idea {node.idea_id}: {e}")
        return 0.0


def backpropagate(node: MCTSNode, score: float) -> None:
    """
    Backpropagate the score up the tree.
    
    Args:
        node (MCTSNode): Node to start backpropagation from
        score (float): Score to backpropagate
    """
    current = node
    while current:
        current.N += 1
        current.W += score
        current = current.parent


def selection_phase(root: MCTSNode, exploration_constant: float = 1.0) -> MCTSNode:
    """
    Selection phase of MCTS.
    
    Args:
        root (MCTSNode): Root node
        exploration_constant (float): Controls exploration vs. exploitation
        
    Returns:
        MCTSNode: Selected leaf node
    """
    return select(root, exploration_constant)


def run_mcts(root_idea_id: str, iterations: int = 10, exploration_constant: float = 1.0) -> MCTSNode:
    """
    Run Monte Carlo Tree Search.
    
    Args:
        root_idea_id (str): ID of the root idea
        iterations (int): Number of iterations to run
        exploration_constant (float): Controls exploration vs. exploitation
        
    Returns:
        MCTSNode: Root node of the search tree
    """
    logger.info(f"Starting MCTS with root idea: {root_idea_id}, iterations: {iterations}")
    
    # Get the idea description from Neo4j
    with driver.session() as session:
        result = session.run("""
        MATCH (i:Idea {id: $idea_id})
        RETURN i.description AS description
        """, idea_id=root_idea_id)
        
        record = result.single()
        if record:
            description = record["description"]
        else:
            description = f"Root idea {root_idea_id}"
    
    # Create the root node
    root = MCTSNode(idea_id=root_idea_id, description=description)
    
    # Run the specified number of iterations
    for i in range(iterations):
        logger.info(f"Iteration {i+1}/{iterations}")
        
        # 1. Selection: Find a leaf node
        leaf = selection_phase(root, exploration_constant)
        
        # 2. Expansion: Create a new child node
        child = expand(leaf)
        
        # 3. Simulation: Run a backtest and get the score
        score = simulate(child)
        
        # 4. Backpropagation: Update the statistics up the tree
        backpropagate(child, score)
    
    # Return the root node
    logger.info(f"MCTS complete. Root node: {root}")
    
    return root


def get_best_child(node: MCTSNode) -> Optional[MCTSNode]:
    """
    Get the child with the highest Q value.
    
    Args:
        node (MCTSNode): Parent node
        
    Returns:
        MCTSNode: Best child node
    """
    if not node.children:
        return None
    
    return max(node.children, key=lambda child: child.Q)


def visualize_mcts_tree(root: MCTSNode) -> None:
    """
    Visualize the MCTS tree in the Neo4j database.
    
    Args:
        root (MCTSNode): Root node of the tree
    """
    # This function is not needed as the tree is already stored in Neo4j
    # through the simulate function
    pass


if __name__ == "__main__":
    # Example usage
    root_idea_id = "759cd9df-0859-4749-b634-7b8638fa5881"  # Replace with an actual idea ID
    root = run_mcts(root_idea_id, iterations=5)
    
    # Get the best child
    best_child = get_best_child(root)
    if best_child:
        logger.info(f"Best child: {best_child}")
        logger.info(f"Best child idea ID: {best_child.idea_id}")
        logger.info(f"Best child score: {best_child.Q:.4f}")
    else:
        logger.info("No children found")
    
    # Close the Neo4j driver
    driver.close()
