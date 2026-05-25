"""FastAPI main application for Customer Interaction Insights."""
import os
from dotenv import load_dotenv
load_dotenv()  # Load .env before any other imports that read env vars

import json
import asyncio
import random
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager

from services.analytics_service import AnalyticsService
from services.chat_service import ChatService
from services.db import DatabaseService
from services.vector_store import VectorStoreService
from agents.orchestrator import create_agentic_pipeline
from models import CallExtraction
import data.generate_data as generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "calls.json")

# Initialize persistent database service (MongoDB)
db_service = DatabaseService()

# Seed MongoDB if empty and we are running in MongoDB mode, or in memory
if db_service.count() == 0:
    print("[INFO] Database is empty. Seeding from local calls.json...")
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Primary dataset not found at {DATA_PATH}")
    with open(DATA_PATH, "r") as f:
        local_calls = json.load(f)
    db_service.insert_many_calls(local_calls)

# Load calls list
CALLS = db_service.get_all_calls()
print(f"[INFO] Loaded {len(CALLS)} call records from database.")

analytics_service = AnalyticsService(CALLS)
chat_service = ChatService(analytics_service=analytics_service)

# Initialize vector store service for embedding live ingested calls
try:
    vector_store = VectorStoreService()
except Exception as e:
    print(f"[WARN] VectorStore init failed: {e}.")
    vector_store = None

# === WebSocket Manager ===
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Database is already initialized
    yield
    # Shutdown


app = FastAPI(title="Customer Interaction Insights API", version="1.0.0", lifespan=lifespan)

# CORS: allow local dev + production frontend URL
_cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
_frontend_url = os.environ.get("FRONTEND_URL")
if _frontend_url:
    _cors_origins.append(_frontend_url)
else:
    _cors_origins.append("*")  # Fallback for local dev

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# === Models ===
class ChatRequest(BaseModel):
    message: str
    client: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    client_detected: Optional[str] = None

class IngestRequest(BaseModel):
    transcript: str
    client: str
    agent_name: Optional[str] = None
    agent_id: Optional[str] = None


def format_extraction_to_call(
    extraction: CallExtraction,
    call_id: str,
    date_str: str,
    time_str: str,
    duration: int,
    agent_id: str,
    agent_name: str
) -> dict:
    # Scale empathy_score (0.0 - 1.0) to CSAT (1 - 5)
    csat = int(round(extraction.agent_performance.empathy_score * 4)) + 1
    
    return {
        "call_id": call_id,
        "client": extraction.client,
        "call_metadata": {
            "date": date_str,
            "time": time_str,
            "duration_seconds": duration,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "channel": "inbound",
            "queue": "customer_support",
            "issue_resolved": extraction.issue_resolved
        },
        "transcript_summary": extraction.summary,
        "nlp_analysis": {
            "customer_intent": {
                "primary_intent": extraction.topic,
                "secondary_intent": "",
                "confidence": 0.9
            },
            "root_cause": {
                "detected_cause": extraction.root_cause.detected_cause,
                "category": extraction.root_cause.category,
                "confidence": extraction.root_cause.confidence_score
            },
            "escalation": {
                "escalated": extraction.escalation.escalated,
                "escalation_trigger": "",
                "escalation_signals": extraction.escalation.escalation_signals,
                "confidence": extraction.escalation.escalation_risk_score
            },
            "callback_intent": {
                "callback_requested": False,
                "reason": "",
                "callback_type": "",
                "confidence": 0.0
            },
            "customer_tone": {
                "overall": extraction.customer_tone.overall,
                "tone_progression": [extraction.customer_tone.overall],
                "sentiment_score": extraction.customer_tone.sentiment_score
            },
            "call_summary": extraction.summary
        },
        "feedback": {
            "post_call_survey_completed": True,
            "csat_score": csat,
            "customer_comment": "Automated QA feedback based on agent empathy and professionalism."
        }
    }



# === Health Check (for Render / load balancer) ===

@app.get("/health")
def health_check():
    return {"status": "healthy", "calls_loaded": len(CALLS)}


# === Routes ===

@app.get("/api/clients")
def get_clients():
    return analytics_service.get_clients()

@app.get("/view-db", response_class=HTMLResponse)
def view_chromadb():
    """Built-in browser viewer for the ChromaDB Vector Database."""
    try:
        import chromadb
        db_path = os.path.join(BASE_DIR, "data", "chroma_db")
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection("customer_calls")
        count = collection.count()
        results = collection.peek(limit=50)
        
        html = f"""
        <html>
        <head>
            <title>ChromaDB Viewer</title>
            <style>
                body {{ font-family: system-ui, sans-serif; padding: 20px; background: #1e1e2e; color: #cdd6f4; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background: #181825; }}
                th, td {{ border: 1px solid #45475a; padding: 12px; text-align: left; }}
                th {{ background-color: #313244; color: #f38ba8; }}
                h1 {{ color: #89b4fa; }}
                .badge {{ background: #313244; padding: 4px 10px; border-radius: 12px; color: #a6e3a1; font-size: 0.85em; }}
                .meta {{ font-family: monospace; color: #a6e3a1; font-size: 0.9em; }}
                .doc {{ color: #bac2de; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <h1>🧠 ChromaDB Vector Store Viewer</h1>
            <p>Collection: <b>customer_calls</b> — <span class="badge">{count} documents embedded</span></p>
            <table>
                <tr>
                    <th>#</th>
                    <th>ID</th>
                    <th>Client / Topic (Metadata)</th>
                    <th>Document Preview</th>
                </tr>
        """
        
        for i in range(len(results.get('ids', []))):
            doc_id = results['ids'][i]
            document = results['documents'][i] if results['documents'] else "N/A"
            metadata = results['metadatas'][i] if results['metadatas'] else {}
            
            client_name = metadata.get('client', 'Unknown')
            topic = metadata.get('topic', 'N/A')
            
            html += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{doc_id}</td>
                    <td class="meta"><b>Client:</b> {client_name}<br><b>Topic:</b> {topic}</td>
                    <td class="doc">{str(document)[:300]}...</td>
                </tr>
            """
            
        html += """
            </table>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"<html><body style='background:#1e1e2e;color:#cdd6f4;padding:40px;font-family:sans-serif'><h1>ChromaDB Not Ready</h1><p>{e}</p><p>Run <code>python scripts/seed_vectordb.py</code> to populate the vector database.</p></body></html>"

@app.get("/api/calls")
def get_calls(
    client: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
):
    filtered = analytics_service._filter(client, start_date, end_date)
    if search:
        search_lower = search.lower()
        filtered = [c for c in filtered if search_lower in c.get("transcript_summary", "").lower()
                    or search_lower in c.get("call_id", "").lower()
                    or search_lower in c.get("call_metadata", {}).get("agent_name", "").lower()
                    or search_lower in c.get("nlp_analysis", {}).get("root_cause", {}).get("category", "").lower()]

    total = len(filtered)
    start = (page - 1) * limit
    end = start + limit
    return {"calls": filtered[start:end], "total": total, "page": page, "pages": (total + limit - 1) // limit}

@app.get("/api/calls/{call_id}")
def get_call(call_id: str):
    for c in CALLS:
        if c["call_id"] == call_id:
            return c
    return {"error": "Call not found"}

@app.get("/api/analytics/overview")
def get_overview(client: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    return analytics_service.get_overview(client, start_date, end_date)

@app.get("/api/analytics/root-causes")
def get_root_causes(client: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    return analytics_service.get_root_causes(client, start_date, end_date)

@app.get("/api/analytics/escalations")
def get_escalations(client: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    return analytics_service.get_escalations(client, start_date, end_date)

@app.get("/api/analytics/sentiment")
def get_sentiment(client: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    return analytics_service.get_sentiment(client, start_date, end_date)

@app.get("/api/analytics/agents")
def get_agents(client: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    return analytics_service.get_agents(client, start_date, end_date)
@app.post("/api/ingest")
async def ingest_transcript(req: IngestRequest):
    # 1. Run through LangGraph Agentic Pipeline (5 specialist agents)
    pipeline = create_agentic_pipeline()
    result = pipeline.invoke({
        "transcript_text": req.transcript,
        "client": req.client,
        "topic": "Customer Service Call"
    })
    
    # Extract structural CallExtraction model
    extraction = result.get("final_extraction")
    if not extraction:
        raise ValueError("Agentic extraction failed to yield a result.")
    
    # 2. Format into dashboard-compatible call record
    agent_id = req.agent_id
    agent_name = req.agent_name
    if not agent_id or not agent_name:
        agent_id, agent_name = random.choice(generator.AGENTS)
        
    call_seq = len(CALLS) + 1
    client_code = "".join([w[0] for w in req.client.split()]).upper()
    if not client_code:
        client_code = "EXT"
    date_now = datetime.now()
    date_str = date_now.strftime("%Y-%m-%d")
    time_str = date_now.strftime("%H:%M:%S")
    call_id = f"{client_code}-{date_now.strftime('%Y')}-{call_seq:05d}"
    
    duration = random.randint(120, 600)
    
    call_record = format_extraction_to_call(
        extraction=extraction,
        call_id=call_id,
        date_str=date_str,
        time_str=time_str,
        duration=duration,
        agent_id=agent_id,
        agent_name=agent_name
    )
    
    # 3. Store in MongoDB database
    db_service.insert_call(call_record)
    
    # 4. Embed in ChromaDB for RAG search
    if vector_store and vector_store.embeddings:
        try:
            vector_store.embed_and_store(extraction, req.transcript)
        except Exception as e:
            print(f"[ERROR] Failed to embed call: {e}")
            
    # 5. Update in-memory state + broadcast via WebSocket
    CALLS.append(call_record)
    analytics_service.calls = CALLS
    
    await manager.broadcast(json.dumps({
        "type": "NEW_CALLS", "count": 1, "total": len(CALLS)
    }))
    
    return call_record

@app.post("/api/chat")
async def chat(req: ChatRequest):
    response = await chat_service.chat(req.message, req.client)
    detected = chat_service._detect_client(req.message)
    return ChatResponse(response=response, client_detected=detected)



if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
