from langgraph.graph import StateGraph, START, END
from agents.state import AgentState
from agents.specialists import root_cause_node, escalation_node, sentiment_node, action_item_node, qa_node
from models import CallExtraction

def aggregator_node(state: AgentState) -> AgentState:
    print("[Agent] Aggregating results from all specialists...")
    
    final_output = CallExtraction(
        client=state.get("client", "Unknown"),
        topic=state.get("topic", "Customer Service Call"),
        issue_resolved=True, 
        summary="A customer interaction processed by the Agentic AI pipeline.",
        root_cause=state.get("root_cause_analysis") or {"category": "unknown", "detected_cause": "Failed to extract", "confidence_score": 0.0},
        escalation=state.get("escalation_analysis") or {"escalated": False, "escalation_signals": [], "escalation_risk_score": 0.0},
        customer_tone=state.get("sentiment_analysis") or {"overall": "neutral", "sentiment_score": 0.0, "frustration_spikes": 0},
        action_items=state.get("action_items_analysis", []),
        agent_performance=state.get("qa_analysis") or {"empathy_score": 0.5, "professionalism_score": 0.5, "first_call_resolution_attempted": False, "missed_opportunities": []}
    )
    
    return {"final_extraction": final_output}

def create_agentic_pipeline():
    # Define the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("root_cause_agent", root_cause_node)
    workflow.add_node("escalation_agent", escalation_node)
    workflow.add_node("sentiment_agent", sentiment_node)
    workflow.add_node("action_item_agent", action_item_node)
    workflow.add_node("qa_agent", qa_node)
    workflow.add_node("aggregator", aggregator_node)
    
    # Define the edges (Parallel execution)
    # Fan out from START
    workflow.add_edge(START, "root_cause_agent")
    workflow.add_edge(START, "escalation_agent")
    workflow.add_edge(START, "sentiment_agent")
    workflow.add_edge(START, "action_item_agent")
    workflow.add_edge(START, "qa_agent")
    
    # Fan in to aggregator
    workflow.add_edge("root_cause_agent", "aggregator")
    workflow.add_edge("escalation_agent", "aggregator")
    workflow.add_edge("sentiment_agent", "aggregator")
    workflow.add_edge("action_item_agent", "aggregator")
    workflow.add_edge("qa_agent", "aggregator")
    
    workflow.add_edge("aggregator", END)
    
    return workflow.compile()
