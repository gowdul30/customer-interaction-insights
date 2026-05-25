"""
Seed the ChromaDB vector database with existing call data from calls.json.
Uses Google Generative AI embeddings (free API) — lightweight, no local model needed.
"""
import os
import sys
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "calls.json")
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma_db")


def main():
    print("🧠 Seeding ChromaDB with existing call data...")
    print(f"   Source: {DATA_PATH}")
    print(f"   Target: {CHROMA_DIR}\n")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not set. Cannot seed vector DB without embeddings.")
        sys.exit(1)
    
    # Load calls
    with open(DATA_PATH, "r") as f:
        calls = json.load(f)
    print(f"[INFO] Loaded {len(calls)} calls from dataset.")
    
    # Initialize Google embedding API (lightweight, no torch/local model needed)
    print("[INFO] Using Google Generative AI embeddings (models/text-embedding-004)...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key,
    )
    
    # Initialize Chroma
    vectorstore = Chroma(
        collection_name="customer_calls",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    
    # Check what's already embedded
    existing_count = vectorstore._collection.count()
    if existing_count > 0:
        print(f"[INFO] ChromaDB already has {existing_count} documents.")
        force = "--force" in sys.argv or os.environ.get("FORCE_SEED") == "true" or not sys.stdin.isatty()
        if force:
            vectorstore._collection.delete(where={})
            print("[INFO] Cleared existing documents (forced re-seed).")
        else:
            response = input("Do you want to clear and re-seed? (y/N): ").strip().lower()
            if response == 'y':
                vectorstore._collection.delete(where={})
                print("[INFO] Cleared existing documents.")
            else:
                print("[SKIP] Keeping existing data. Exiting.")
                return
    
    # Build documents for embedding
    documents = []
    for call in calls:
        # Build a rich text representation for semantic search
        nlp = call.get("nlp_analysis", {})
        text = (
            f"Client: {call.get('client', 'Unknown')}\n"
            f"Summary: {call.get('transcript_summary', '')}\n"
            f"Root Cause: {nlp.get('root_cause', {}).get('category', 'unknown')} — {nlp.get('root_cause', {}).get('detected_cause', '')}\n"
            f"Customer Tone: {nlp.get('customer_tone', {}).get('overall', 'neutral')}\n"
            f"Escalated: {nlp.get('escalation', {}).get('escalated', False)}\n"
            f"Resolved: {call.get('call_metadata', {}).get('issue_resolved', False)}"
        )
        
        metadata = {
            "client": call.get("client", "Unknown"),
            "topic": nlp.get("root_cause", {}).get("category", "unknown"),
            "issue_resolved": call.get("call_metadata", {}).get("issue_resolved", False),
            "escalated": nlp.get("escalation", {}).get("escalated", False),
            "sentiment_score": nlp.get("customer_tone", {}).get("sentiment_score", 0.0),
            "call_id": call.get("call_id", ""),
            "date": call.get("call_metadata", {}).get("date", ""),
        }
        
        documents.append(Document(page_content=text, metadata=metadata))
    
    # Batch embed in chunks to avoid rate limits
    BATCH_SIZE = 20
    total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
    
    import time
    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        print(f"[{batch_num}/{total_batches}] Embedding batch of {len(batch)} documents...")
        vectorstore.add_documents(batch)
        # Small delay to respect Google API rate limits
        if batch_num < total_batches:
            time.sleep(1)
    
    final_count = vectorstore._collection.count()
    print(f"\n✅ Done! ChromaDB now contains {final_count} embedded documents.")
    print(f"   You can view them at: http://localhost:8000/view-db")

if __name__ == "__main__":
    main()
