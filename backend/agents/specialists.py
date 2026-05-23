import os
import json
from google import genai
from google.genai import types
from agents.state import AgentState
from models import RootCause, Escalation, CustomerTone, ActionItem, AgentPerformance

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def _invoke_structured_agent(prompt: str, schema_class, transcript: str):
    client = get_gemini_client()
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Transcript to analyze:\n\n{transcript}",
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                response_mime_type="application/json",
                response_schema=schema_class,
                temperature=0.1,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"[ERROR] Specialist agent failed: {e}")
        return None

def root_cause_node(state: AgentState) -> AgentState:
    print("[Agent] Running Root Cause Specialist...")
    prompt = "You are the Root Cause Specialist. Analyze the transcript and determine the primary category of the issue and a specific description. Assign a confidence score."
    result = _invoke_structured_agent(prompt, RootCause, state["transcript_text"])
    return {"root_cause_analysis": result}

def escalation_node(state: AgentState) -> AgentState:
    print("[Agent] Running Escalation Predictor...")
    prompt = "You are the Escalation Predictor. Determine if the call was escalated. Extract any specific phrases signaling escalation risk. Calculate a risk score for future escalation based on the customer's frustration level and agent handling."
    result = _invoke_structured_agent(prompt, Escalation, state["transcript_text"])
    return {"escalation_analysis": result}

def sentiment_node(state: AgentState) -> AgentState:
    print("[Agent] Running Sentiment Deep-Dive...")
    prompt = "You are the Sentiment Deep-Dive Agent. Evaluate the overall tone, calculate a specific sentiment score (-1.0 to 1.0), and count the exact number of times the customer exhibited a spike in frustration."
    result = _invoke_structured_agent(prompt, CustomerTone, state["transcript_text"])
    return {"sentiment_analysis": result}

def action_item_node(state: AgentState) -> AgentState:
    print("[Agent] Running Action Item Specialist...")
    # For lists, we define a wrapper schema inline
    from pydantic import BaseModel
    from typing import List
    class ActionItemWrapper(BaseModel):
        items: List[ActionItem]
        
    prompt = "You are the Action Item Specialist. Extract all commitments, follow-ups, or promised tasks mentioned in the transcript. Identify the owner and deadline if present."
    result = _invoke_structured_agent(prompt, ActionItemWrapper, state["transcript_text"])
    return {"action_items_analysis": result.get("items", []) if result else []}

def qa_node(state: AgentState) -> AgentState:
    print("[Agent] Running QA Specialist...")
    prompt = "You are the Quality Assurance Specialist. Score the agent's empathy and professionalism. Check if they attempted first call resolution. Identify any missed opportunities to resolve the issue better or de-escalate."
    result = _invoke_structured_agent(prompt, AgentPerformance, state["transcript_text"])
    return {"qa_analysis": result}
