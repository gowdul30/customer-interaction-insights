"""
Process new synthetic calls through the Agentic AI pipeline.
Extracts structured insights via LangGraph specialists, embeds into ChromaDB,
and appends results to the main calls.json dataset.
"""
import os
import json
import glob
import sys
import time
from dotenv import load_dotenv

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from agents.orchestrator import create_agentic_pipeline
from services.vector_store import VectorStoreService

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio")
MAIN_DATASET = os.path.join(BASE_DIR, "data", "calls.json")
PROCESSED_LOG = os.path.join(BASE_DIR, "data", "processed_calls.json")


def load_existing_ids():
    """Load IDs of already-processed synthetic calls to avoid duplicates."""
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, "r") as f:
            try:
                return {c["call_id"] for c in json.load(f)}
            except json.JSONDecodeError:
                return set()
    return set()


def main():
    print("[INFO] Starting Agentic Pipeline Processing...")
    
    # Initialize services
    pipeline = create_agentic_pipeline()
    vector_store = VectorStoreService()
    
    # Find all generated transcripts
    transcript_files = glob.glob(os.path.join(AUDIO_DIR, "*.json"))
    if not transcript_files:
        print(f"[WARN] No transcripts found in {AUDIO_DIR}")
        return
        
    print(f"[INFO] Found {len(transcript_files)} transcripts.")
    
    existing_ids = load_existing_ids()
    processed_this_run = []
    
    for file_path in transcript_files:
        call_id = os.path.basename(file_path).replace(".json", "")
        
        if call_id in existing_ids:
            print(f"[SKIP] {call_id} already processed.")
            continue
            
        print(f"\n[Processing] {call_id}...")
        
        with open(file_path, "r") as f:
            data = json.load(f)
            
        # Build transcript text
        transcript_text = ""
        for msg in data.get("messages", []):
            transcript_text += f"{msg.get('speaker')}: {msg.get('text')}\n"
            
        # Run through LangGraph Agentic Pipeline
        initial_state = {
            "transcript_text": transcript_text,
            "client": data.get("client", "Unknown"),
            "topic": data.get("topic", "General Inquiry")
        }
        
        print("  -> Routing to Specialist Agents...")
        
        # Retry logic for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result_state = pipeline.invoke(initial_state)
                break
            except Exception as e:
                if "RESOURCE_EXHAUSTED" in str(e) and attempt < max_retries - 1:
                    wait_time = 30 * (attempt + 1)
                    print(f"  [RATE LIMITED] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"  [ERROR] Pipeline failed: {e}")
                    result_state = {}
                    break
        
        final_extraction = result_state.get("final_extraction")
        if not final_extraction:
            print(f"  [ERROR] Pipeline failed to extract data for {call_id}")
            continue
            
        print("  -> Extraction Successful. Embedding and Storing...")
        
        # Store in VectorDB
        try:
            vector_store.embed_and_store(final_extraction, transcript_text)
        except Exception as e:
            print(f"  [ERROR] Failed to store in Vector DB: {e}")
            
        # Convert to dashboard-compatible format
        call_dict = final_extraction.model_dump()
        raw_date = call_id.split("_")[1] if len(call_id.split("_")) > 1 else "20240101"
        formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
        
        formatted_call = {
            "call_id": call_id,
            "client": call_dict["client"],
            "call_metadata": {
                "date": formatted_date,
                "duration_seconds": len(transcript_text.split()) * 0.5,
                "agent_id": "AGT-101",
                "agent_name": "Alex",
                "issue_resolved": call_dict["issue_resolved"]
            },
            "transcript_summary": call_dict["summary"],
            "nlp_analysis": {
                "root_cause": {
                    "category": call_dict["root_cause"]["category"],
                    "detected_cause": call_dict["root_cause"]["detected_cause"]
                },
                "escalation": {
                    "escalated": call_dict["escalation"]["escalated"],
                    "escalation_signals": call_dict["escalation"]["escalation_signals"]
                },
                "customer_tone": {
                    "overall": call_dict["customer_tone"]["overall"],
                    "sentiment_score": call_dict["customer_tone"]["sentiment_score"]
                },
                "callback_intent": {
                    "callback_requested": any("callback" in item["task"].lower() for item in call_dict.get("action_items", []))
                }
            },
            "feedback": {
                "post_call_survey_completed": True,
                "csat_score": 5 if call_dict["issue_resolved"] else (2 if call_dict["escalation"]["escalated"] else 3)
            }
        }
        
        processed_this_run.append(formatted_call)
        print(f"  ✓ {call_id} processed successfully.")
        
        # Pause between calls to respect rate limits
        time.sleep(8)
        
    # Save processing log
    all_processed = list(existing_ids)
    log_data = []
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, "r") as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = []
    log_data.extend(processed_this_run)
    with open(PROCESSED_LOG, "w") as f:
        json.dump(log_data, f, indent=2)
    
    # Also append to main dataset so they show up on the dashboard
    if processed_this_run:
        main_calls = []
        if os.path.exists(MAIN_DATASET):
            with open(MAIN_DATASET, "r") as f:
                main_calls = json.load(f)
        main_calls.extend(processed_this_run)
        with open(MAIN_DATASET, "w") as f:
            json.dump(main_calls, f, indent=2)
        print(f"\n[INFO] Appended {len(processed_this_run)} calls to {MAIN_DATASET}")
        
    print(f"\n[DONE] Processed {len(processed_this_run)} new calls.")

if __name__ == "__main__":
    main()
