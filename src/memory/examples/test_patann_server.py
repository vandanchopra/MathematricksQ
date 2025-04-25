#!/usr/bin/env python3
"""
Test script for the PatANN server
"""

import os
import sys
import requests
import json
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

def test_patann_server(url: str = "http://localhost:9200"):
    """Test the PatANN server."""
    print(f"Testing PatANN server at {url}")
    
    # Check if the server is running
    try:
        response = requests.get(f"{url}/health")
        if response.status_code == 200:
            print(f"Server is running: {response.json()}")
        else:
            print(f"Server returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Error connecting to server: {str(e)}")
        return False
    
    # Load the sentence transformer model
    print("Loading sentence transformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Create some test data
    print("Creating test data...")
    texts = [
        "Buy when RSI is below 30",
        "Sell when RSI is above 70",
        "Buy on golden cross (50 SMA crosses above 200 SMA)",
        "Sell on death cross (50 SMA crosses below 200 SMA)",
        "Buy when price is 10% below 20-day moving average"
    ]
    
    # Get embeddings for the texts
    print("Getting embeddings...")
    embeddings = model.encode(texts)
    
    # Store the embeddings in the PatANN server
    print("Storing embeddings...")
    for i, (text, embedding) in enumerate(zip(texts, embeddings)):
        try:
            # Prepare the request payload
            payload = {
                "id": f"idea_{i}",
                "vector": embedding.tolist(),
                "metadata": {
                    "text": text,
                    "index": i
                }
            }
            
            # Send the request to the PatANN server
            response = requests.post(
                f"{url}/vectors",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                print(f"Stored embedding for '{text}'")
            else:
                print(f"Failed to store embedding: {response.status_code} {response.text}")
        except Exception as e:
            print(f"Error storing embedding: {str(e)}")
    
    # Search for similar vectors
    print("\nSearching for similar vectors...")
    query_text = "Buy when price is low"
    query_embedding = model.encode(query_text)
    
    try:
        # Prepare the request payload
        payload = {
            "vector": query_embedding.tolist(),
            "k": 3
        }
        
        # Send the request to the PatANN server
        response = requests.post(
            f"{url}/search",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            results = response.json().get("results", [])
            print(f"Found {len(results)} similar vectors for '{query_text}':")
            for i, result in enumerate(results):
                print(f"{i+1}. {result['metadata']['text']} (Distance: {result['distance']})")
        else:
            print(f"Failed to search vectors: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error searching vectors: {str(e)}")
    
    print("\nTest complete!")
    return True

if __name__ == "__main__":
    test_patann_server()
