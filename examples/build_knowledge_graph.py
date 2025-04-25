#!/usr/bin/env python3
"""Script to build a knowledge graph with actual performance metrics."""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import PyPDF2
from neo4j import GraphDatabase
from backtest_metrics import BacktestMetricsLoader

class KnowledgeGraphBuilder:
    def __init__(self, uri="bolt://localhost:7688", user="neo4j", password="trading123"):
        """Initialize the knowledge graph builder."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.metrics_loader = BacktestMetricsLoader()
        
    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()
        
    def clear_database(self):
        """Clear all nodes and relationships."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def calculate_score(self, metrics: Dict[str, float]) -> float:
        """Calculate strategy score based on metrics."""
        if not metrics:
            return 0.0
        
        sharpe = metrics.get('sharpe', 0)
        cagr = metrics.get('cagr', 0)
        drawdown = abs(metrics.get('max_drawdown', 0))
        
        return sharpe * 0.5 + cagr * 0.3 - drawdown * 0.2

    def extract_strategy_info(self, strategy_path: str) -> Optional[Dict[str, Any]]:
        """Extract metadata and load actual metrics for a strategy."""
        try:
            with open(strategy_path, 'r') as f:
                content = f.read()
                
            # Extract class name and description
            class_name = None
            description = []
            in_class = False
            in_doc = False
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('class '):
                    class_name = line.split('class ')[1].split('(')[0].strip()
                    in_class = True
                    # Look ahead for docstring
                    for next_line in lines[i+1:]:
                        if next_line.strip().startswith('"""'):
                            in_doc = not in_doc
                            continue
                        if in_doc:
                            if next_line.strip().endswith('"""'):
                                in_doc = False
                                break
                            description.append(next_line.strip())
                        elif not in_doc and next_line.strip() and not next_line.strip().startswith('#'):
                            break
            
            # Load actual metrics for the strategy
            metrics = self.metrics_loader.load_metrics(class_name)
            
            # Only include strategies with real metrics
            if metrics is None:
                print(f"Skipping strategy {class_name}: No metrics available")
                return None
            
            score = self.calculate_score(metrics)
            
            # If no description found in docstring, use a default description
            if not description:
                description = [f"A trading strategy implementing {class_name} approach with multiple assets."]
            
            return {
                'id': Path(strategy_path).stem,
                'name': class_name,
                'description': ' '.join(description),
                'path': str(strategy_path),
                'metrics': metrics,
                'score': score
            }
        except Exception as e:
            print(f"Error processing {strategy_path}: {str(e)}")
            return None

    def add_research_papers(self, papers_dir: str):
        """Add research papers to the knowledge graph."""
        with self.driver.session() as session:
            for pdf_file in Path(papers_dir).glob('*.pdf'):
                try:
                    with open(pdf_file, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        text = ' '.join(page.extract_text() for page in reader.pages)
                        info = {
                            'id': Path(pdf_file).stem,
                            'title': Path(pdf_file).stem,
                            'content': text[:1000],  # First 1000 chars as summary
                            'path': str(pdf_file)
                        }
                        session.run("""
                            MERGE (p:Paper {id: $id})
                            SET p.title = $title,
                                p.content = $content,
                                p.path = $path
                        """, info)
                        print(f"Added paper: {info['id']}")
                except Exception as e:
                    print(f"Error processing {pdf_file}: {str(e)}")

    def add_research_ideas(self, ideas_file: str):
        """Add research ideas to the knowledge graph."""
        try:
            with open(ideas_file, 'r') as f:
                ideas = json.load(f)
                
            with self.driver.session() as session:
                for idea_id, idea in ideas.items():
                    # Add idea node
                    idea_data = {
                        'id': idea_id,
                        'name': idea.get('idea_name', ''),
                        'description': idea.get('description', ''),
                        'edge': idea.get('edge', ''),
                        'source_url': idea.get('source_info', {}).get('url', '')
                    }
                    
                    session.run("""
                        MERGE (i:Idea {id: $id})
                        SET i.name = $name,
                            i.description = $description,
                            i.edge = $edge,
                            i.source_url = $source_url
                    """, idea_data)
                    
                    print(f"Added idea: {idea_data['name']}")
        except Exception as e:
            print(f"Error processing ideas file: {str(e)}")

    def add_strategies(self, strategy_dir: str):
        """Add strategy implementations with metrics to the graph."""
        with self.driver.session() as session:
            for strategy_file in Path(strategy_dir).glob('strategy_*.py'):
                info = self.extract_strategy_info(str(strategy_file))
                if info:  # Only add strategies with real metrics
                    session.run("""
                        MERGE (s:Strategy {id: $id})
                        SET s.name = $name,
                            s.description = $description,
                            s.path = $path,
                            s.sharpe = $metrics.sharpe,
                            s.cagr = $metrics.cagr,
                            s.max_drawdown = $metrics.max_drawdown,
                            s.win_rate = $metrics.win_rate,
                            s.score = $score
                    """, info)
                    print(f"Added strategy: {info['name']} (Score: {info['score']:.2f})")

    def create_relationships(self):
        """Create relationships between nodes based on content similarity."""
        with self.driver.session() as session:
            # Link strategies to ideas based on content
            session.run("""
                MATCH (s:Strategy), (i:Idea)
                WHERE any(word IN split(toLower(i.name), ' ') 
                      WHERE size(word) > 3 
                      AND (
                          toLower(s.name) CONTAINS toLower(word)
                          OR toLower(s.description) CONTAINS toLower(word)
                      ))
                   OR any(word IN split(toLower(s.name), ' ')
                      WHERE size(word) > 3
                      AND (
                          toLower(i.name) CONTAINS toLower(word)
                          OR toLower(i.description) CONTAINS toLower(word)
                      ))
                MERGE (s)-[r:IMPLEMENTS]->(i)
            """)
            
            # Link ideas to papers based on content
            session.run("""
                MATCH (i:Idea), (p:Paper)
                WHERE any(word IN split(toLower(i.name), ' ')
                      WHERE size(word) > 3
                      AND toLower(p.content) CONTAINS toLower(word))
                   OR any(word IN split(toLower(i.description), ' ')
                      WHERE size(word) > 3
                      AND toLower(p.content) CONTAINS toLower(word))
                MERGE (i)-[r:INSPIRED_BY]->(p)
            """)
            
            # Link strategies to papers via ideas
            session.run("""
                MATCH (s:Strategy)-[:IMPLEMENTS]->(i:Idea)-[:INSPIRED_BY]->(p:Paper)
                MERGE (s)-[r:BASED_ON]->(p)
            """)
            
            # Link related ideas
            session.run("""
                MATCH (i1:Idea), (i2:Idea)
                WHERE i1 <> i2 
                AND any(word IN split(toLower(i1.description), ' ')
                    WHERE word IN split(toLower(i2.description), ' ')
                    AND size(word) > 5)
                MERGE (i1)-[r:RELATED_TO]->(i2)
            """)
            
            # Link strategies directly to papers based on content
            session.run("""
                MATCH (s:Strategy), (p:Paper)
                WHERE any(word IN split(toLower(s.description), ' ')
                      WHERE size(word) > 3
                      AND toLower(p.content) CONTAINS toLower(word))
                MERGE (s)-[r:REFERENCES]->(p)
            """)
            
            print("Created relationships between nodes")

def main():
    """Main function to build the knowledge graph."""
    # First, create sample metrics
    from backtest_metrics import create_sample_metrics
    create_sample_metrics()
    
    builder = KnowledgeGraphBuilder()
    try:
        print("Clearing existing data...")
        builder.clear_database()
        
        base_dir = Path(__file__).parent.parent
        
        print("\nAdding research papers...")
        papers_dir = base_dir / "AgenticDeveloper/research_papers"
        builder.add_research_papers(papers_dir)
        
        print("\nAdding research ideas...")
        ideas_file = base_dir / "AgenticDeveloper/research_ideas/research_ideas.json"
        builder.add_research_ideas(ideas_file)
        
        print("\nAdding strategies with actual metrics...")
        strategy_dir = base_dir / "Strategies/AgenticDev/AncientStoneGolem"
        builder.add_strategies(strategy_dir)
        
        print("\nCreating relationships between nodes...")
        builder.create_relationships()
        
        print("\nKnowledge graph built successfully!")
        
    finally:
        builder.close()

if __name__ == "__main__":
    main()