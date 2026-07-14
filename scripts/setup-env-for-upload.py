#!/usr/bin/env python3
"""
Setup environment variables for document upload to new Qdrant instance.
This script ensures all required environment variables are set correctly.
"""
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

def setup_environment():
    """Setup environment variables for the new Qdrant configuration."""
    
    # New Qdrant configuration
    os.environ["QDRANT_URL"] = "https://46d164a0-aa9f-48c0-8ffc-1b0d1b60a591.us-east4-0.gcp.cloud.qdrant.io:6333"
    os.environ["QDRANT_API_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.SPNWCGECEkm2mU5cVWGJxS_ImkZpahtae08n7N27u_Q"
    os.environ["VECTOR_DB_TYPE"] = "qdrant"
    
    # OpenAI configuration (required for embeddings)
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Please set it for embedding generation.")
        print("   export OPENAI_API_KEY='your-openai-api-key'")
        return False
    
    # Other required settings
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "True"
    
    print("✅ Environment variables configured for new Qdrant instance")
    print(f"📊 Qdrant URL: {os.environ['QDRANT_URL']}")
    print(f"🔑 API Key: {'*' * 20}...{os.environ['QDRANT_API_KEY'][-10:]}")
    
    return True

def check_documents():
    """Check if all required documents are available."""
    
    documents = [
        "constitution.txt",
        "nigeria_electoral_act_2022.txt",
        "nigeria_constitution_provisions.txt",
        "nigeria_court_hierarchy_and_judges.txt",
        "nigeria_criminal_code_provisions.txt",
        "nigeria_current_judges_profiles.txt",
        "nigeria_supreme_court_landmark_cases.txt"
    ]
    
    print("\n📄 Checking document availability:")
    
    available_docs = []
    missing_docs = []
    
    for doc in documents:
        if os.path.exists(doc):
            size_kb = os.path.getsize(doc) / 1024
            print(f"   ✅ {doc} ({size_kb:.1f} KB)")
            available_docs.append(doc)
        else:
            print(f"   ❌ {doc} (missing)")
            missing_docs.append(doc)
    
    print(f"\n📊 Summary: {len(available_docs)}/{len(documents)} documents available")
    
    if missing_docs:
        print(f"⚠️  Missing documents: {', '.join(missing_docs)}")
    
    return len(available_docs) > 0

if __name__ == "__main__":
    print("🔧 SCONIA Environment Setup for Document Upload")
    print("=" * 50)
    
    # Setup environment
    env_ok = setup_environment()
    
    # Check documents
    docs_ok = check_documents()
    
    print("\n" + "=" * 50)
    
    if env_ok and docs_ok:
        print("✅ Ready for document upload!")
        print("\nNext steps:")
        print("1. Run: python scripts/upload-to-new-qdrant.py")
        print("2. Wait for upload to complete")
        print("3. Deploy the updated API")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        
        if not env_ok:
            print("   - Set OPENAI_API_KEY environment variable")
        if not docs_ok:
            print("   - Ensure document files are in the project root")
