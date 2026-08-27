from typing import get_type_hints
from langgraph.graph import StateGraph

from app.agents.state import (
    AgentState,
    RetryState,
    UsageState,
)

def test_agent_state_is_accepted_by_langgraph():
    graph = StateGraph(AgentState)

    assert graph is not None
    
def test_agent_state_contains_required_fields():
    annotations = get_type_hints(AgentState)

    expected_fields = {
        "run_id",
        "document_id",
        "document_version_id",
        "status",
        "extracted_facts",
        "evidence",
        "conflicts",
        "validation_results",
        "findings",
        "proposed_changes",
        "review_status",
        "retry_state",
        "errors",
        "usage",
    }

    assert expected_fields.issubset(annotations.keys())


def test_retry_state_is_typed():
    annotations = get_type_hints(RetryState)

    assert annotations["attempt"] is int
    assert annotations["max_attempts"] is int


def test_usage_state_is_typed():
    annotations = get_type_hints(UsageState)

    assert annotations["input_tokens"] is int
    assert annotations["output_tokens"] is int
    assert annotations["total_tokens"] is int
    assert annotations["estimated_cost"] is float


def test_agent_state_can_represent_initial_run():
    state: AgentState = {
        "run_id": "run-001",
        "document_id": "document-001",
        "document_version_id": "version-001",
        "status": "pending",
        "extracted_facts": [],
        "evidence": [],
        "conflicts": [],
        "validation_results": [],
        "findings": [],
        "proposed_changes": [],
        "review_status": "pending",
        "retry_state": {
            "attempt": 0,
            "max_attempts": 3,
        },
        "errors": [],
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
        },
    }

    assert state["status"] == "pending"
    assert state["review_status"] == "pending"
    assert state["retry_state"]["max_attempts"] == 3
    assert state["usage"]["total_tokens"] == 0