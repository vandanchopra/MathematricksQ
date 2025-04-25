#!/usr/bin/env python3
"""
PatANN HTTP Server - A FastAPI wrapper for PatANN vector database
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import uvicorn

# Add the patann directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'patann')))

# Import PatANN
import patann

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PatANN-Server")

# Constants
VECTOR_DIM = 384  # Default dimension for sentence embeddings
SEARCH_RADIUS = 100
CONSTELLATION_SIZE = 16

app = FastAPI(title="PatANN Vector Database API")

# Initialize PatANN
ann = patann.createInstance(VECTOR_DIM)
if ann is None:
    raise RuntimeError("Failed to create PatANN instance")

# Configure the index
ann.this_is_preproduction_software(True)
ann.setDistanceType(2)  # L2_SQUARE distance
ann.setRadius(SEARCH_RADIUS)
ann.setConstellationSize(CONSTELLATION_SIZE)

# Store metadata separately since PatANN doesn't support it natively
metadata_store = {}

# Define request/response models
class UpsertItem(BaseModel):
    id: str
    vector: List[float]
    metadata: Dict[str, Any]

class SearchRequest(BaseModel):
    vector: List[float]
    k: int = 10
    filter: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    id: str
    distance: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    results: List[SearchResult]

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the server is healthy"""
    return {
        "status": "ok",
        "version": "0.1.0"
    }

@app.post("/vectors")
async def upsert_vector(item: UpsertItem):
    """Insert or update a vector in the database"""
    try:
        # Convert vector to numpy array
        vector = np.array(item.vector, dtype=np.float32)
        
        # Check vector dimension
        if len(vector) != VECTOR_DIM:
            raise HTTPException(status_code=400, detail=f"Vector dimension must be {VECTOR_DIM}")
        
        # Add vector to PatANN
        vector_id = ann.addVector(vector)
        
        # Store metadata
        metadata_store[item.id] = {
            "vector_id": vector_id,
            "metadata": item.metadata
        }
        
        return {"id": item.id, "status": "success"}
    except Exception as e:
        logger.error(f"Error upserting vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_vectors(req: SearchRequest):
    """Search for similar vectors"""
    try:
        # Convert query vector to numpy array
        query_vector = np.array(req.vector, dtype=np.float32)
        
        # Check vector dimension
        if len(query_vector) != VECTOR_DIM:
            raise HTTPException(status_code=400, detail=f"Vector dimension must be {VECTOR_DIM}")
        
        # Wait for the index to be ready
        ann.waitForIndexReady()
        
        # Create query session
        query = ann.createQuerySession(SEARCH_RADIUS, req.k)
        
        # Perform search
        query.query(query_vector, req.k)
        
        # Get results
        result_ids = query.getResults(0)
        result_distances = query.getResultDists()
        
        # Map PatANN vector IDs to user IDs and apply filters
        results = []
        for i in range(len(result_ids)):
            # Find the user ID for this vector ID
            user_id = None
            for id, data in metadata_store.items():
                if data["vector_id"] == result_ids[i]:
                    user_id = id
                    metadata = data["metadata"]
                    break
            
            if user_id is None:
                continue
                
            # Apply filter if provided
            if req.filter:
                match = True
                for key, value in req.filter.items():
                    if key == "id":
                        if user_id != value:
                            match = False
                            break
                    elif key not in metadata or metadata[key] != value:
                        match = False
                        break
                
                if not match:
                    continue
            
            results.append({
                "id": user_id,
                "distance": float(result_distances[i]),
                "metadata": metadata
            })
        
        # Clean up
        query.destroy()
        
        return {"results": results}
    except Exception as e:
        logger.error(f"Error searching vectors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info(f"Starting PatANN server with vector dimension {VECTOR_DIM}")
    uvicorn.run(app, host="0.0.0.0", port=9200)
