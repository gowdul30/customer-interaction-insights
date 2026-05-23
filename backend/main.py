"""FastAPI main application for Customer Interaction Insights."""
import json
import os
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
import data.generate_data as generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load call data — always use the rich 500+ record dataset
DATA_PATH = os.path.join(BASE_DIR, "data", "calls.json")
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Primary dataset not found at {DATA_PATH}")

with open(DATA_PATH, "r") as f:
    CALLS = json.load(f)
print(f"[INFO] Loaded {len(CALLS)} call records from {DATA_PATH}")

analytics_service = AnalyticsService(CALLS)
chat_service = ChatService(analytics_service=analytics_service)

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

# === Background Streaming Task ===
async def generate_realtime_calls():
    global CALLS
    print("[INFO] Started real-time call streaming task (generating data every 10s)")
    while True:
        await asyncio.sleep(10)
        num_new = random.randint(1, 3)
        now = datetime.now()
        new_calls = []
        for _ in range(num_new):
            new_call = generator.generate_call(len(CALLS) + 1, override_datetime=now)
            new_calls.append(new_call)
        
        CALLS.extend(new_calls)
        await manager.broadcast(json.dumps({"type": "NEW_CALLS", "count": num_new, "total": len(CALLS)}))
        print(f"[STREAM] {num_new} new calls generated. Total is now {len(CALLS)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background task
    task = asyncio.create_task(generate_realtime_calls())
    yield
    # Shutdown: Cancel the task
    task.cancel()

app = FastAPI(title="Customer Interaction Insights API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.post("/api/chat")
async def chat(req: ChatRequest):
    response = await chat_service.chat(req.message, req.client)
    detected = chat_service._detect_client(req.message)
    return ChatResponse(response=response, client_detected=detected)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
