from app.agents.state import AgentState
from app.agents.workflow import (
    build_workflow,
    route_after_conflict_detection,
    route_after_human_review,
    route_after_output_validation,
    validate_output_node,
    escalation_node,
    extract_node,
)
from app.integrations.ai.mock import MockAIProvider


def create_initial_state() -> AgentState:
    return {
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
            "reason": None,
            "escalated": False,
        },
        "errors": [],
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
        },
    }


def test_workflow_compiles():
    workflow = build_workflow()

    assert workflow is not None


def test_output_validation_routes_invalid_output_back_to_extract():
    state = create_initial_state()

    state["validation_results"] = [
        {
            "valid": False,
            "stage": "output_validation",
        }
    ]

    assert route_after_output_validation(state) == "extract"


def test_output_validation_routes_valid_output_forward():
    state = create_initial_state()

    state["validation_results"] = [
        {
            "valid": True,
            "stage": "output_validation",
        }
    ]

    assert route_after_output_validation(state) == "detect_conflicts"


def test_conflict_detection_routes_conflict_to_human_review():
    state = create_initial_state()

    state["conflicts"] = [
        {
            "type": "contradiction",
        }
    ]

    assert (
        route_after_conflict_detection(state)
        == "human_conflict_review"
    )


def test_conflict_detection_routes_clean_state_forward():
    state = create_initial_state()

    assert (
        route_after_conflict_detection(state)
        == "rule_validation"
    )


def test_human_review_routes_approved_to_commit():
    state = create_initial_state()
    state["review_status"] = "approved"

    assert route_after_human_review(state) == "commit"


def test_human_review_routes_non_approved_to_end():
    state = create_initial_state()

    assert route_after_human_review(state) == "end"


def test_human_review_gate_preserves_review_status():
    state = create_initial_state()
    state["review_status"] = "approved"

    from app.agents.workflow import human_review_gate_node

    result = human_review_gate_node(state)

    assert result == {}


def test_workflow_runs_normal_path():
    workflow = build_workflow()

    state = create_initial_state()
    state["review_status"] = "approved"

    result = workflow.invoke(state)

    assert result["status"] == "completed"


def test_invalid_output_retries_when_attempts_remain():
    state = create_initial_state()

    state["validation_results"] = [
        {
            "valid": False,
            "stage": "output_validation",
            "reason": "missing_required_field",
        }
    ]

    result = validate_output_node(state)

    assert result["retry_state"]["attempt"] == 1
    assert result["retry_state"]["max_attempts"] == 3
    assert (
        result["retry_state"]["reason"]
        == "missing_required_field"
    )
    assert result["retry_state"]["escalated"] is False

    updated_state = {
        **state,
        **result,
    }

    assert route_after_output_validation(updated_state) == "extract"


def test_invalid_output_escalates_after_retry_limit():
    state = create_initial_state()

    state["retry_state"] = {
        "attempt": 2,
        "max_attempts": 3,
        "reason": "missing_required_field",
        "escalated": False,
    }

    state["validation_results"] = [
        {
            "valid": False,
            "stage": "output_validation",
            "reason": "missing_required_field",
        }
    ]

    result = validate_output_node(state)

    assert result["retry_state"]["attempt"] == 3
    assert result["retry_state"]["escalated"] is True

    updated_state = {
        **state,
        **result,
    }

    assert route_after_output_validation(updated_state) == "escalate"


def test_escalation_marks_run_failed():
    state = create_initial_state()

    state["retry_state"] = {
        "attempt": 3,
        "max_attempts": 3,
        "reason": "missing_required_field",
        "escalated": True,
    }

    result = escalation_node(state)

    assert result["status"] == "failed"
    assert result["retry_state"]["escalated"] is True
    assert (
        result["errors"][0]["code"]
        == "RETRY_LIMIT_EXCEEDED"
    )


def test_invalid_output_preserves_validation_history():
    state = create_initial_state()

    first_result = {
        "valid": False,
        "stage": "output_validation",
        "reason": "missing_required_field",
    }

    second_result = {
        "valid": False,
        "stage": "output_validation",
        "reason": "invalid_evidence_reference",
    }

    state["validation_results"] = [
        first_result,
        second_result,
    ]

    result = validate_output_node(state)

    assert result["validation_results"] == [
        first_result,
        second_result,
    ]

    assert len(result["validation_results"]) == 2

def test_extract_node_uses_structured_extraction():
    state = {
        "run_id": "run-1",
        "document_id": "doc-1",
        "document_version_id": "version-1",
        "parsed_content": "We lost the deal to Acme.",
        "status": "running",
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
            "reason": None,
            "escalated": False,
        },
        "errors": [],
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
        },
        "prompt_metadata": [],
    }

    provider = MockAIProvider(
        response={
            "facts": [
                {
                    "field": "competitor",
                    "value": "Acme",
                    "confidence": 0.92,
                    "evidence": [
                        {
                            "document_id": "doc-1",
                            "document_version_id": "version-1",
                            "location": "page 1",
                            "chunk_id": None,
                            "quote": "We lost the deal to Acme.",
                        }
                    ],
                }
            ]
        }
    )

    result = extract_node(
        state,
        provider=provider,
    )

    assert result["extracted_facts"]
    assert result["extracted_facts"][0]["field"] == "competitor"
    assert result["extracted_facts"][0]["value"] == "Acme"

    assert result["prompt_metadata"][0]["prompt_name"] == "extraction"
    assert result["prompt_metadata"][0]["prompt_version"] == "v1"

    assert result["usage"]["input_tokens"] == 10
    assert result["usage"]["output_tokens"] == 5
    assert result["usage"]["total_tokens"] == 15