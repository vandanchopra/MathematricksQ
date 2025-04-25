#!/usr/bin/env python3
"""
Script to build a knowledge graph with proper relationships
"""

import os
import sys
import logging
from typing import Dict, List, Any
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from neo4j import GraphDatabase
from src.memory.hybrid_backend import HybridMemory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("KnowledgeGraphBuilder")

def build_knowledge_graph():
    """Build a knowledge graph with proper relationships."""
    # Initialize the memory system
    memory = HybridMemory(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        patann_url="http://localhost:9200",
        model_name="all-MiniLM-L6-v2"
    )
    
    # Clear the database
    with memory.graph_backend.driver.session() as session:
        session.run("""
        MATCH (n)
        DETACH DELETE n
        """)
        logger.info("Database cleared")
    
    # Store contexts
    contexts = [
        {"id": "btc_daily", "market": "BTC/USD", "timeframe": "1d"},
        {"id": "eth_daily", "market": "ETH/USD", "timeframe": "1d"},
        {"id": "btc_hourly", "market": "BTC/USD", "timeframe": "1h"},
        {"id": "eth_hourly", "market": "ETH/USD", "timeframe": "1h"},
        {"id": "btc_4h", "market": "BTC/USD", "timeframe": "4h"},
        {"id": "eth_4h", "market": "ETH/USD", "timeframe": "4h"},
        {"id": "btc_15m", "market": "BTC/USD", "timeframe": "15m"},
        {"id": "eth_15m", "market": "ETH/USD", "timeframe": "15m"},
        {"id": "sol_daily", "market": "SOL/USD", "timeframe": "1d"},
        {"id": "sol_hourly", "market": "SOL/USD", "timeframe": "1h"},
        {"id": "sol_4h", "market": "SOL/USD", "timeframe": "4h"},
        {"id": "sol_15m", "market": "SOL/USD", "timeframe": "15m"},
        {"id": "bnb_daily", "market": "BNB/USD", "timeframe": "1d"},
        {"id": "bnb_hourly", "market": "BNB/USD", "timeframe": "1h"},
        {"id": "bnb_4h", "market": "BNB/USD", "timeframe": "4h"}
    ]
    
    for context in contexts:
        memory.store_context(context["id"], context["market"], context["timeframe"])
        logger.info(f"Stored context: {context['id']}")
    
    # Store ideas
    ideas = [
        {"id": "idea1", "description": "Buy when RSI is below 30", "contexts": ["btc_daily", "eth_daily", "sol_daily", "bnb_daily"]},
        {"id": "idea2", "description": "Sell when RSI is above 70", "contexts": ["btc_daily", "eth_daily", "sol_daily", "bnb_daily"]},
        {"id": "idea3", "description": "Buy on golden cross (50 SMA crosses above 200 SMA)", "contexts": ["btc_daily", "eth_daily"]},
        {"id": "idea4", "description": "Sell on death cross (50 SMA crosses below 200 SMA)", "contexts": ["btc_daily", "eth_daily"]},
        {"id": "idea5", "description": "Buy when price is 10% below 20-day moving average", "contexts": ["btc_hourly", "eth_hourly"]},
        {"id": "idea6", "description": "Buy when MACD crosses above signal line", "contexts": ["btc_4h", "eth_4h", "sol_4h", "bnb_4h"]},
        {"id": "idea7", "description": "Sell when MACD crosses below signal line", "contexts": ["btc_4h", "eth_4h", "sol_4h", "bnb_4h"]},
        {"id": "idea8", "description": "Buy when Bollinger Bands squeeze and price breaks out", "contexts": ["btc_hourly", "eth_hourly", "sol_hourly"]},
        {"id": "idea9", "description": "Buy when price breaks above resistance level", "contexts": ["btc_daily", "eth_daily", "sol_daily"]},
        {"id": "idea10", "description": "Sell when price breaks below support level", "contexts": ["btc_daily", "eth_daily", "sol_daily"]},
        {"id": "idea11", "description": "Buy when 3 consecutive green candles form", "contexts": ["btc_15m", "eth_15m", "sol_15m"]},
        {"id": "idea12", "description": "Sell when 3 consecutive red candles form", "contexts": ["btc_15m", "eth_15m", "sol_15m"]},
        {"id": "idea13", "description": "Buy on bullish engulfing pattern", "contexts": ["btc_daily", "eth_daily", "sol_daily", "bnb_daily"]},
        {"id": "idea14", "description": "Sell on bearish engulfing pattern", "contexts": ["btc_daily", "eth_daily", "sol_daily", "bnb_daily"]},
        {"id": "idea15", "description": "Buy when price crosses above 50-day EMA", "contexts": ["btc_daily", "eth_daily"]},
        {"id": "idea16", "description": "Sell when price crosses below 50-day EMA", "contexts": ["btc_daily", "eth_daily"]},
        {"id": "idea17", "description": "Buy when Stochastic oscillator crosses above 20", "contexts": ["btc_4h", "eth_4h"]},
        {"id": "idea18", "description": "Sell when Stochastic oscillator crosses below 80", "contexts": ["btc_4h", "eth_4h"]},
        {"id": "idea19", "description": "Buy when OBV is increasing while price is flat", "contexts": ["btc_hourly", "eth_hourly"]},
        {"id": "idea20", "description": "Sell when OBV is decreasing while price is flat", "contexts": ["btc_hourly", "eth_hourly"]},
        {"id": "idea21", "description": "Buy when ADX is above 25 and +DI crosses above -DI", "contexts": ["btc_4h", "eth_4h"]},
        {"id": "idea22", "description": "Sell when ADX is above 25 and -DI crosses above +DI", "contexts": ["btc_4h", "eth_4h"]}
    ]
    
    for idea in ideas:
        memory.store_idea(idea["id"], idea["description"], idea["contexts"])
        logger.info(f"Stored idea: {idea['id']}")
    
    # Store backtests with proper relationships
    backtests = [
        {"id": "bt1", "metrics": {"Sharpe": 1.5, "CAGR": 0.25, "MaxDrawdown": 0.15, "WinRate": 0.65}, "idea_id": "idea1", "context_id": "btc_daily"},
        {"id": "bt2", "metrics": {"Sharpe": 1.2, "CAGR": 0.20, "MaxDrawdown": 0.18, "WinRate": 0.60}, "idea_id": "idea2", "context_id": "btc_daily"},
        {"id": "bt3", "metrics": {"Sharpe": 0.8, "CAGR": 0.15, "MaxDrawdown": 0.25, "WinRate": 0.55}, "idea_id": "idea3", "context_id": "btc_daily"},
        {"id": "bt4", "metrics": {"Sharpe": 1.0, "CAGR": 0.18, "MaxDrawdown": 0.20, "WinRate": 0.58}, "idea_id": "idea4", "context_id": "btc_daily"},
        {"id": "bt5", "metrics": {"Sharpe": 1.8, "CAGR": 0.30, "MaxDrawdown": 0.12, "WinRate": 0.70}, "idea_id": "idea5", "context_id": "btc_hourly"},
        {"id": "bt6", "metrics": {"Sharpe": 1.3, "CAGR": 0.22, "MaxDrawdown": 0.16, "WinRate": 0.62}, "idea_id": "idea6", "context_id": "btc_4h"},
        {"id": "bt7", "metrics": {"Sharpe": 1.1, "CAGR": 0.19, "MaxDrawdown": 0.19, "WinRate": 0.59}, "idea_id": "idea7", "context_id": "btc_4h"},
        {"id": "bt8", "metrics": {"Sharpe": 1.6, "CAGR": 0.28, "MaxDrawdown": 0.14, "WinRate": 0.68}, "idea_id": "idea8", "context_id": "btc_hourly"},
        {"id": "bt9", "metrics": {"Sharpe": 1.4, "CAGR": 0.24, "MaxDrawdown": 0.17, "WinRate": 0.64}, "idea_id": "idea9", "context_id": "btc_daily"},
        {"id": "bt10", "metrics": {"Sharpe": 1.2, "CAGR": 0.21, "MaxDrawdown": 0.18, "WinRate": 0.61}, "idea_id": "idea10", "context_id": "btc_daily"},
        {"id": "bt11", "metrics": {"Sharpe": 1.3, "CAGR": 0.23, "MaxDrawdown": 0.16, "WinRate": 0.63}, "idea_id": "idea1", "context_id": "eth_daily"},
        {"id": "bt12", "metrics": {"Sharpe": 1.1, "CAGR": 0.19, "MaxDrawdown": 0.19, "WinRate": 0.59}, "idea_id": "idea2", "context_id": "eth_daily"},
        {"id": "bt13", "metrics": {"Sharpe": 1.7, "CAGR": 0.29, "MaxDrawdown": 0.13, "WinRate": 0.69}, "idea_id": "idea8", "context_id": "eth_hourly"},
        {"id": "bt14", "metrics": {"Sharpe": 1.2, "CAGR": 0.21, "MaxDrawdown": 0.18, "WinRate": 0.61}, "idea_id": "idea6", "context_id": "eth_4h"},
        {"id": "bt15", "metrics": {"Sharpe": 1.0, "CAGR": 0.18, "MaxDrawdown": 0.20, "WinRate": 0.58}, "idea_id": "idea7", "context_id": "eth_4h"},
        {"id": "bt16", "metrics": {"Sharpe": 1.5, "CAGR": 0.26, "MaxDrawdown": 0.15, "WinRate": 0.66}, "idea_id": "idea11", "context_id": "btc_15m"},
        {"id": "bt17", "metrics": {"Sharpe": 1.3, "CAGR": 0.22, "MaxDrawdown": 0.17, "WinRate": 0.62}, "idea_id": "idea12", "context_id": "btc_15m"},
        {"id": "bt18", "metrics": {"Sharpe": 1.6, "CAGR": 0.27, "MaxDrawdown": 0.14, "WinRate": 0.67}, "idea_id": "idea13", "context_id": "btc_daily"},
        {"id": "bt19", "metrics": {"Sharpe": 1.4, "CAGR": 0.24, "MaxDrawdown": 0.16, "WinRate": 0.64}, "idea_id": "idea14", "context_id": "btc_daily"},
        {"id": "bt20", "metrics": {"Sharpe": 1.2, "CAGR": 0.21, "MaxDrawdown": 0.18, "WinRate": 0.61}, "idea_id": "idea15", "context_id": "btc_daily"},
        {"id": "bt21", "metrics": {"Sharpe": 1.1, "CAGR": 0.19, "MaxDrawdown": 0.19, "WinRate": 0.59}, "idea_id": "idea16", "context_id": "btc_daily"},
        {"id": "bt22", "metrics": {"Sharpe": 1.3, "CAGR": 0.23, "MaxDrawdown": 0.17, "WinRate": 0.63}, "idea_id": "idea17", "context_id": "btc_4h"},
        {"id": "bt23", "metrics": {"Sharpe": 1.2, "CAGR": 0.21, "MaxDrawdown": 0.18, "WinRate": 0.61}, "idea_id": "idea18", "context_id": "btc_4h"},
        {"id": "bt24", "metrics": {"Sharpe": 1.4, "CAGR": 0.24, "MaxDrawdown": 0.16, "WinRate": 0.64}, "idea_id": "idea19", "context_id": "btc_hourly"},
        {"id": "bt25", "metrics": {"Sharpe": 1.3, "CAGR": 0.22, "MaxDrawdown": 0.17, "WinRate": 0.62}, "idea_id": "idea20", "context_id": "btc_hourly"}
    ]
    
    for backtest in backtests:
        memory.store_backtest(backtest["id"], backtest["metrics"], backtest["idea_id"], backtest["context_id"])
        logger.info(f"Stored backtest: {backtest['id']}")
    
    # Store scenarios
    scenarios = [
        {"id": "scenario1", "description": "RSI(14) < 30 on 4h timeframe", "parent_idea_id": "idea1", "contexts": ["btc_daily"]},
        {"id": "scenario2", "description": "RSI(7) < 25 with volume confirmation", "parent_idea_id": "idea1", "contexts": ["btc_daily"]},
        {"id": "scenario3", "description": "RSI(14) > 70 on 4h timeframe", "parent_idea_id": "idea2", "contexts": ["btc_daily"]},
        {"id": "scenario4", "description": "RSI(7) > 75 with volume confirmation", "parent_idea_id": "idea2", "contexts": ["btc_daily"]},
        {"id": "scenario5", "description": "50 SMA crosses above 200 SMA with increasing volume", "parent_idea_id": "idea3", "contexts": ["btc_daily"]},
        {"id": "scenario6", "description": "50 SMA crosses below 200 SMA with increasing volume", "parent_idea_id": "idea4", "contexts": ["btc_daily"]},
        {"id": "scenario7", "description": "Price is 10% below 20-day MA with bullish candlestick pattern", "parent_idea_id": "idea5", "contexts": ["btc_hourly"]},
        {"id": "scenario8", "description": "MACD crosses above signal line with histogram increasing", "parent_idea_id": "idea6", "contexts": ["btc_4h"]},
        {"id": "scenario9", "description": "MACD crosses below signal line with histogram decreasing", "parent_idea_id": "idea7", "contexts": ["btc_4h"]},
        {"id": "scenario10", "description": "Bollinger Bands width at 6-month low and price breaks above upper band", "parent_idea_id": "idea8", "contexts": ["btc_hourly"]}
    ]
    
    for scenario in scenarios:
        memory.store_scenario(scenario["id"], scenario["description"], scenario["parent_idea_id"], scenario["contexts"])
        logger.info(f"Stored scenario: {scenario['id']}")
    
    # Verify the database state
    with memory.graph_backend.driver.session() as session:
        # Count nodes by label
        result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] AS label, count(n) AS count
        ORDER BY count DESC
        """)
        
        logger.info("Node counts by label:")
        for record in result:
            logger.info(f"  {record['label']}: {record['count']}")
        
        # Count relationships by type
        result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) AS rel, count(r) AS count
        ORDER BY count DESC
        """)
        
        logger.info("Relationship counts by type:")
        for record in result:
            logger.info(f"  {record['rel']}: {record['count']}")
        
        # Check for Idea-Backtest-Context paths
        result = session.run("""
        MATCH p=(i:Idea)-[:TESTED_IN]->(b:Backtest)-[:EXECUTED_IN]->(c:Context)
        RETURN count(p) AS path_count
        """)
        
        logger.info(f"Idea-Backtest-Context path count: {result.single()['path_count']}")
    
    logger.info("Knowledge graph built successfully!")

if __name__ == "__main__":
    build_knowledge_graph()
