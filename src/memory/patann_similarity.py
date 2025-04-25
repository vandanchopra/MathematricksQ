"""
PatANN-based similarity search for the memory module.
This module uses PatANN to find similar ideas based on their descriptions.
"""

import os
import sys
import json
import logging
import asyncio
import uuid
import time
import random
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("patann_similarity.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PatANNSimilarity")

# Load environment variables
load_dotenv()

# Neo4j connection parameters
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7688")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "trading123")

# Create a driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# Try to import PatANN
try:
    import patann
    PATANN_AVAILABLE = True
    logger.info("PatANN imported successfully")
except ImportError:
    PATANN_AVAILABLE = False
    logger.warning("PatANN not available. Using fallback mode.")

# Try to import sentence-transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("Sentence Transformers imported successfully")
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("Sentence Transformers not available. Using fallback mode.")

class PatANNSimilarity:
    """
    PatANN-based similarity search for the memory module.
    This class uses PatANN to find similar ideas based on their descriptions.
    """
    
    def __init__(self, index_path: str = "patann_index", embedding_dim: int = 384):
        """
        Initialize the PatANN similarity search.
        
        Args:
            index_path: Path to the PatANN index
            embedding_dim: Dimension of the embeddings
        """
        self.index_path = index_path
        self.embedding_dim = embedding_dim
        self.patann_index = None
        self.embedding_model = None
        
        # Initialize PatANN
        if PATANN_AVAILABLE:
            try:
                # Create the index directory if it doesn't exist
                os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
                
                # Initialize the PatANN index
                self.patann_index = patann.Index(self.index_path, self.embedding_dim)
                logger.info(f"PatANN index initialized at {self.index_path}")
            except Exception as e:
                logger.error(f"Error initializing PatANN index: {e}")
                self.patann_index = None
        
        # Initialize the embedding model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Embedding model initialized")
            except Exception as e:
                logger.error(f"Error initializing embedding model: {e}")
                self.embedding_model = None
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get the embedding for a text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding as a numpy array
        """
        if self.embedding_model is not None:
            try:
                embedding = self.embedding_model.encode(text)
                return embedding
            except Exception as e:
                logger.error(f"Error getting embedding: {e}")
        
        # Fallback: Generate a random embedding
        logger.warning("Using fallback random embedding")
        return np.random.randn(self.embedding_dim).astype(np.float32)
    
    def index_idea(self, idea_id: str, description: str) -> bool:
        """
        Index an idea in PatANN.
        
        Args:
            idea_id: ID of the idea
            description: Description of the idea
            
        Returns:
            True if successful, False otherwise
        """
        if self.patann_index is None:
            logger.warning("PatANN index not available")
            return False
        
        try:
            # Get the embedding
            embedding = self.get_embedding(description)
            
            # Add the embedding to the index
            self.patann_index.add(idea_id, embedding)
            logger.info(f"Indexed idea {idea_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error indexing idea {idea_id}: {e}")
            return False
    
    def find_similar_ideas(self, description: str, k: int = 5) -> List[Tuple[str, float]]:
        """
        Find similar ideas to a description.
        
        Args:
            description: Description to find similar ideas for
            k: Number of similar ideas to return
            
        Returns:
            List of (idea_id, similarity) tuples
        """
        if self.patann_index is None:
            logger.warning("PatANN index not available")
            return []
        
        try:
            # Get the embedding
            embedding = self.get_embedding(description)
            
            # Search for similar embeddings
            results = self.patann_index.search(embedding, k)
            
            # Convert to list of (idea_id, similarity) tuples
            similar_ideas = [(result.id, result.score) for result in results]
            
            return similar_ideas
        except Exception as e:
            logger.error(f"Error finding similar ideas: {e}")
            return []
    
    def index_all_ideas(self) -> int:
        """
        Index all ideas in Neo4j.
        
        Returns:
            Number of ideas indexed
        """
        count = 0
        
        try:
            with driver.session() as session:
                # Get all ideas
                result = session.run("""
                MATCH (i:Idea)
                RETURN i.id as id, i.description as description
                """)
                
                # Index each idea
                for record in result:
                    idea_id = record["id"]
                    description = record["description"]
                    
                    if description:
                        success = self.index_idea(idea_id, description)
                        if success:
                            count += 1
            
            logger.info(f"Indexed {count} ideas")
            return count
        except Exception as e:
            logger.error(f"Error indexing all ideas: {e}")
            return count
    
    def find_similar_ideas_for_idea(self, idea_id: str, k: int = 5) -> List[Tuple[str, float]]:
        """
        Find similar ideas to an existing idea.
        
        Args:
            idea_id: ID of the idea to find similar ideas for
            k: Number of similar ideas to return
            
        Returns:
            List of (idea_id, similarity) tuples
        """
        try:
            with driver.session() as session:
                # Get the idea description
                result = session.run("""
                MATCH (i:Idea {id: $idea_id})
                RETURN i.description as description
                """, idea_id=idea_id)
                
                record = result.single()
                if not record:
                    logger.warning(f"Idea {idea_id} not found")
                    return []
                
                description = record["description"]
                if not description:
                    logger.warning(f"Idea {idea_id} has no description")
                    return []
                
                # Find similar ideas
                return self.find_similar_ideas(description, k)
        except Exception as e:
            logger.error(f"Error finding similar ideas for idea {idea_id}: {e}")
            return []
    
    def create_subidea_relationships(self, idea_id: str, k: int = 3, similarity_threshold: float = 0.7) -> int:
        """
        Create SUBIDEA_OF relationships between similar ideas.
        
        Args:
            idea_id: ID of the idea to find similar ideas for
            k: Number of similar ideas to consider
            similarity_threshold: Minimum similarity score to create a relationship
            
        Returns:
            Number of relationships created
        """
        count = 0
        
        try:
            # Find similar ideas
            similar_ideas = self.find_similar_ideas_for_idea(idea_id, k)
            
            # Filter by similarity threshold
            similar_ideas = [(id, score) for id, score in similar_ideas if score >= similarity_threshold and id != idea_id]
            
            # Create relationships
            with driver.session() as session:
                for similar_id, similarity in similar_ideas:
                    # Create SUBIDEA_OF relationship
                    result = session.run("""
                    MATCH (i1:Idea {id: $idea_id}), (i2:Idea {id: $similar_id})
                    MERGE (i1)-[r:SUBIDEA_OF {similarity: $similarity}]->(i2)
                    RETURN r
                    """, idea_id=idea_id, similar_id=similar_id, similarity=similarity)
                    
                    if result.single():
                        count += 1
                        logger.info(f"Created SUBIDEA_OF relationship from {idea_id} to {similar_id} with similarity {similarity:.4f}")
            
            return count
        except Exception as e:
            logger.error(f"Error creating SUBIDEA_OF relationships for idea {idea_id}: {e}")
            return count
    
    def create_all_subidea_relationships(self, k: int = 3, similarity_threshold: float = 0.7) -> int:
        """
        Create SUBIDEA_OF relationships between all similar ideas.
        
        Args:
            k: Number of similar ideas to consider
            similarity_threshold: Minimum similarity score to create a relationship
            
        Returns:
            Number of relationships created
        """
        count = 0
        
        try:
            with driver.session() as session:
                # Get all ideas
                result = session.run("""
                MATCH (i:Idea)
                RETURN i.id as id
                """)
                
                # Create relationships for each idea
                for record in result:
                    idea_id = record["id"]
                    count += self.create_subidea_relationships(idea_id, k, similarity_threshold)
            
            logger.info(f"Created {count} SUBIDEA_OF relationships")
            return count
        except Exception as e:
            logger.error(f"Error creating all SUBIDEA_OF relationships: {e}")
            return count
    
    def find_and_create_new_ideas(self, idea_id: str, num_variations: int = 3) -> List[str]:
        """
        Find similar ideas and create new variations.
        
        Args:
            idea_id: ID of the idea to find similar ideas for
            num_variations: Number of variations to create
            
        Returns:
            List of new idea IDs
        """
        new_idea_ids = []
        
        try:
            with driver.session() as session:
                # Get the idea description
                result = session.run("""
                MATCH (i:Idea {id: $idea_id})
                RETURN i.description as description
                """, idea_id=idea_id)
                
                record = result.single()
                if not record:
                    logger.warning(f"Idea {idea_id} not found")
                    return []
                
                description = record["description"]
                if not description:
                    logger.warning(f"Idea {idea_id} has no description")
                    return []
                
                # Find similar ideas
                similar_ideas = self.find_similar_ideas_for_idea(idea_id, k=5)
                
                # Create variations
                for i in range(num_variations):
                    # Generate a new idea ID
                    new_idea_id = str(uuid.uuid4())
                    
                    # Create a variation of the description
                    variation_description = self._create_variation(description, similar_ideas)
                    
                    # Create the new idea
                    session.run("""
                    CREATE (i:Idea {id: $id, description: $description, testCount: 0, totalScore: 0.0})
                    """, id=new_idea_id, description=variation_description)
                    
                    # Create SUBIDEA_OF relationship
                    session.run("""
                    MATCH (i1:Idea {id: $new_id}), (i2:Idea {id: $parent_id})
                    MERGE (i1)-[r:SUBIDEA_OF]->(i2)
                    """, new_id=new_idea_id, parent_id=idea_id)
                    
                    # Index the new idea
                    self.index_idea(new_idea_id, variation_description)
                    
                    new_idea_ids.append(new_idea_id)
                    logger.info(f"Created new idea {new_idea_id} as a variation of {idea_id}")
            
            return new_idea_ids
        except Exception as e:
            logger.error(f"Error creating variations for idea {idea_id}: {e}")
            return new_idea_ids
    
    def _create_variation(self, description: str, similar_ideas: List[Tuple[str, float]]) -> str:
        """
        Create a variation of a description.
        
        Args:
            description: Original description
            similar_ideas: List of (idea_id, similarity) tuples
            
        Returns:
            Variation of the description
        """
        # In a real implementation, you would use an LLM to create a variation
        # For now, we'll just use a simple template
        
        # Get descriptions of similar ideas
        similar_descriptions = []
        for idea_id, _ in similar_ideas:
            try:
                with driver.session() as session:
                    result = session.run("""
                    MATCH (i:Idea {id: $idea_id})
                    RETURN i.description as description
                    """, idea_id=idea_id)
                    
                    record = result.single()
                    if record and record["description"]:
                        similar_descriptions.append(record["description"])
            except Exception as e:
                logger.error(f"Error getting description for idea {idea_id}: {e}")
        
        # Create a variation
        if similar_descriptions:
            # Pick a random similar description
            similar_desc = random.choice(similar_descriptions)
            
            # Create a simple variation
            variation = f"Variation of original idea: {description[:100]}...\n\nIncorporating elements from: {similar_desc[:100]}..."
        else:
            variation = f"Variation of: {description}"
        
        return variation

# Singleton instance
_instance = None

def get_patann_similarity() -> PatANNSimilarity:
    """
    Get the singleton instance of the PatANNSimilarity.
    
    Returns:
        PatANNSimilarity instance
    """
    global _instance
    if _instance is None:
        _instance = PatANNSimilarity()
    return _instance

def index_all_ideas() -> int:
    """
    Index all ideas in Neo4j.
    
    Returns:
        Number of ideas indexed
    """
    similarity = get_patann_similarity()
    return similarity.index_all_ideas()

def create_all_subidea_relationships(k: int = 3, similarity_threshold: float = 0.7) -> int:
    """
    Create SUBIDEA_OF relationships between all similar ideas.
    
    Args:
        k: Number of similar ideas to consider
        similarity_threshold: Minimum similarity score to create a relationship
        
    Returns:
        Number of relationships created
    """
    similarity = get_patann_similarity()
    return similarity.create_all_subidea_relationships(k, similarity_threshold)

def find_and_create_new_ideas(idea_id: str, num_variations: int = 3) -> List[str]:
    """
    Find similar ideas and create new variations.
    
    Args:
        idea_id: ID of the idea to find similar ideas for
        num_variations: Number of variations to create
        
    Returns:
        List of new idea IDs
    """
    similarity = get_patann_similarity()
    return similarity.find_and_create_new_ideas(idea_id, num_variations)

if __name__ == "__main__":
    # Test the PatANN similarity search
    similarity = get_patann_similarity()
    
    # Index all ideas
    count = similarity.index_all_ideas()
    print(f"Indexed {count} ideas")
    
    # Create SUBIDEA_OF relationships
    count = similarity.create_all_subidea_relationships()
    print(f"Created {count} SUBIDEA_OF relationships")
