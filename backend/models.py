from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class RootCause(BaseModel):
    category: str = Field(description="The primary category of the issue (e.g., billing_error, service_outage, policy_confusion, agent_error, system_bug)")
    detected_cause: str = Field(description="A short, specific description of the root cause.")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)

class Escalation(BaseModel):
    escalated: bool = Field(description="True if the call was escalated to a supervisor or manager.")
    escalation_signals: List[str] = Field(default_factory=list, description="Specific phrases or signs indicating escalation risk (e.g., 'speak to a manager', 'cancel my account').")
    escalation_risk_score: float = Field(description="Score from 0.0 to 1.0 indicating the likelihood of future escalation based on this call.", ge=0.0, le=1.0)

class CustomerTone(BaseModel):
    overall: str = Field(description="Overall tone of the customer (e.g., satisfied, neutral, frustrated, angry).")
    sentiment_score: float = Field(description="Sentiment score from -1.0 (very negative) to 1.0 (very positive).", ge=-1.0, le=1.0)
    frustration_spikes: int = Field(description="Number of times the customer exhibited a spike in frustration during the call.")

class ActionItem(BaseModel):
    owner: str = Field(description="Who is responsible for the action item (e.g., Agent, Customer, Billing Department).")
    task: str = Field(description="Description of the action item.")
    deadline: Optional[str] = Field(None, description="Deadline or timeline for the action item if mentioned.")

class AgentPerformance(BaseModel):
    empathy_score: float = Field(description="Score from 0.0 to 1.0 evaluating the agent's empathy.", ge=0.0, le=1.0)
    professionalism_score: float = Field(description="Score from 0.0 to 1.0 evaluating the agent's professionalism.", ge=0.0, le=1.0)
    first_call_resolution_attempted: bool = Field(description="Did the agent try to resolve the issue on the first call?")
    missed_opportunities: List[str] = Field(default_factory=list, description="Any missed opportunities to resolve the issue better or up-sell.")

class CallExtraction(BaseModel):
    client: str = Field(description="The client or company the call is for (e.g., Verizon, AT&T, Wells Fargo).")
    topic: str = Field(description="A short 2-3 word topic of the call.")
    issue_resolved: bool = Field(description="Whether the issue was resolved during the call.")
    summary: str = Field(description="A concise 2-sentence summary of the interaction.")
    
    root_cause: RootCause
    escalation: Escalation
    customer_tone: CustomerTone
    action_items: List[ActionItem] = Field(default_factory=list)
    agent_performance: AgentPerformance
