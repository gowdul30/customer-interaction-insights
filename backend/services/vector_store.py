import os
import json
# pyrefly: ignore [missing-import]
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from models import CallExtraction

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class VectorStoreService:
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or os.path.join(BASE_DIR, "data", "chroma_db")
        
        # Use Google's free embedding API instead of local HuggingFace model.
        # This avoids loading torch + sentence-transformers (~400MB RAM)
        # which exceeds Render's free tier 512MB limit.
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=api_key,
            )
        else:
            self.embeddings = None
            print("[WARN] GEMINI_API_KEY not set. VectorStoreService embeddings unavailable.")
            
        # Initialize Chroma
        if self.embeddings:
            self.vectorstore = Chroma(
                collection_name="customer_calls",
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
        else:
            self.vectorstore = None

    def embed_and_store(self, call_data: CallExtraction, raw_transcript: str):
        if not self.embeddings:
            raise ValueError("Embeddings not configured.")
            
        # We store the raw transcript as the page content for semantic search
        # and attach the rich JSON metadata extracted by our agents
        
        metadata = {
            "client": call_data.client,
            "topic": call_data.topic,
            "issue_resolved": call_data.issue_resolved,
            "root_cause_category": call_data.root_cause.category,
            "escalated": call_data.escalation.escalated,
            "sentiment_score": call_data.customer_tone.sentiment_score,
            "empathy_score": call_data.agent_performance.empathy_score,
            # We dump the full JSON into a single metadata field for easy retrieval of complex nested objects
            "full_analysis_json": json.dumps(call_data.model_dump())
        }
        
        doc = Document(page_content=raw_transcript, metadata=metadata)
        
        self.vectorstore.add_documents([doc])
        print(f"[INFO] Successfully embedded and stored call for {call_data.client}")

    def search(self, query: str, client: str = None, limit: int = 5):
        if not self.embeddings:
            raise ValueError("Embeddings not configured.")
            
        # Optional metadata filtering by client
        filter_dict = {}
        if client and client.lower() != "all":
            filter_dict["client"] = client
            
        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=limit,
            filter=filter_dict if filter_dict else None
        )
        
        # Return formatted results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "transcript_snippet": doc.page_content[:500] + "...", 
                "metadata": doc.metadata,
                "similarity_score": score
            })
            
        return formatted_results
