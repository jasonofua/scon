#!/usr/bin/env python3
"""
Simple script to create the Qdrant collection for SCONIA.
"""
import requests
import json

# Configuration
QDRANT_URL = "https://6b71346c-f2c7-4515-a743-6adf2e81ea31.us-east4-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.0b5XGbJR1rGa2uIQmf2sL9BuJjz_6E8vhrEQTLEWcxE"
COLLECTION_NAME = "sconia_legal_documents"
EMBEDDING_SIZE = 1536

def create_collection():
    """Create the Qdrant collection."""
    headers = {
        "Content-Type": "application/json",
        "api-key": QDRANT_API_KEY
    }
    
    # Check if collection exists
    print(f"Checking if collection '{COLLECTION_NAME}' exists...")
    response = requests.get(f"{QDRANT_URL}/collections", headers=headers)
    
    if response.status_code == 200:
        collections = response.json()
        collection_names = [col["name"] for col in collections.get("result", {}).get("collections", [])]
        
        if COLLECTION_NAME in collection_names:
            print(f"✅ Collection '{COLLECTION_NAME}' already exists!")
            return True
        else:
            print(f"Collection '{COLLECTION_NAME}' does not exist. Creating...")
    else:
        print(f"Error checking collections: {response.status_code} - {response.text}")
        return False
    
    # Create collection
    collection_config = {
        "vectors": {
            "size": EMBEDDING_SIZE,
            "distance": "Cosine"
        }
    }
    
    response = requests.put(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
        headers=headers,
        json=collection_config
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Successfully created collection '{COLLECTION_NAME}'!")
        return True
    else:
        print(f"❌ Error creating collection: {response.status_code} - {response.text}")
        return False

def main():
    """Main function."""
    print("🏛️  SCONIA Qdrant Collection Setup")
    print("=" * 40)
    
    success = create_collection()
    
    if success:
        print("\n✅ Collection setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. The collection is ready to receive documents")
        print("   2. Use the add_constitution.py script to populate it")
        print("   3. Test the API with constitutional queries")
    else:
        print("\n❌ Collection setup failed!")

if __name__ == "__main__":
    main()
