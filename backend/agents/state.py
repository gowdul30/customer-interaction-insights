from typing import TypedDict, Optional, List, Dict, Any
from models import CallExtraction

class AgentState(TypedDict):
    transcript_text: str
    client: str
    topic: str
    
    # Partial outputs from specialists
    root_cause_analysis: Optional[Dict[str, Any]]
    escalation_analysis: Optional[Dict[str, Any]]
    sentiment_analysis: Optional[Dict[str, Any]]
    action_items_analysis: Optional[List[Dict[str, Any]]]
    qa_analysis: Optional[Dict[str, Any]]
    
    # Final combined output
    final_extraction: Optional[CallExtraction]
