import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

load_dotenv()

from services.vector_store import VectorStoreService

def run_query():
    print("🧠 Initializing ChromaDB and Embeddings...")
    try:
        vector_store = VectorStoreService()
    except Exception as e:
        print(f"Error initializing VectorDB: {e}")
        return

    print("\n✅ Ready! Type your semantic search query below (or type 'exit' to quit).")
    print("Example: 'Show me calls where the customer was really angry about fees'")
    
    while True:
        query = input("\n🔍 Search Query: ")
        if query.lower() in ['exit', 'quit']:
            break
            
        if not query.strip():
            continue
            
        print("\nSearching...")
        try:
            results = vector_store.search(query=query, limit=3)
            
            if not results:
                print("No results found.")
                continue
                
            for i, result in enumerate(results):
                meta = result["metadata"]
                print(f"\n--- Result {i+1} (Similarity Score: {result['similarity_score']:.4f}) ---")
                print(f"Client: {meta.get('client')}")
                print(f"Topic: {meta.get('topic')}")
                print(f"Resolved: {meta.get('issue_resolved')}")
                print(f"Escalated: {meta.get('escalated')}")
                print(f"\nTranscript Snippet:\n{result['transcript_snippet']}")
                print("-" * 60)
                
        except Exception as e:
            print(f"Error running search: {e}")

if __name__ == "__main__":
    run_query()
