from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.agents.state import AgentState
from app.agents.extraction import StructuredExtractionService
from app.integrations.ai.factory import create_ai_provider
from app.integrations.ai.pricing import estimate_cost
from app.core.config import settings
from app.integrations.ai.errors import AIOutputValidationError


def ingest_node(state: AgentState) -> dict:
    return {
        "status": "running",
    }


def classify_node(state: AgentState) -> dict:
    return {
        "status": "running",
    }


def extract_node(
    state: AgentState,
    *,
    provider=None,
) -> dict:
    parsed_content = state.get("parsed_content")

    if not parsed_content:
        return {
            "status": "running",
        }

    provider = provider or create_ai_provider()

    extraction_service = StructuredExtractionService(
        provider=provider,
    )

    try:
        result, prompt_metadata, usage = extraction_service.extract(
            document_id=state["document_id"],
            document_version_id=state["document_version_id"],
            content=parsed_content,
            model=settings.ai_model,
        )

    except AIOutputValidationError as exc:
        return {
            "validation_results": [
                *state.get("validation_results", []),
                {
                    "valid": False,
                    "stage": "output_validation",
                    "reason": str(exc),
                },
            ],
        }

    current_usage = state.get("usage", {})

    call_cost = estimate_cost(
        prompt_metadata.get("model", settings.ai_model),
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
    )

    return {
        "status": "running",
        "extracted_facts": [
            fact.model_dump()
            for fact in result.facts
        ],
        "prompt_metadata": [
            *state.get("prompt_metadata", []),
            prompt_metadata,
        ],
        "usage": {
            "input_tokens": (
                current_usage.get("input_tokens", 0)
                + usage.input_tokens
            ),
            "output_tokens": (
                current_usage.get("output_tokens", 0)
                + usage.output_tokens
            ),
            "total_tokens": (
                current_usage.get("total_tokens", 0)
                + usage.total_tokens
            ),
            "estimated_cost": round(
                current_usage.get("estimated_cost", 0.0) + call_cost,
                6,
            ),
        },
    }

def validate_output_node(state: AgentState) -> dict:
    validation_results = state.get("validation_results", [])

    if validation_results:
        latest_result = validation_results[-1]
    else:
        latest_result = {
            "valid": True,
            "stage": "output_validation",
        }

    retry_state = state["retry_state"]

    # Invalid output
    if latest_result.get("valid") is False:
        attempt = retry_state["attempt"] + 1
        max_attempts = retry_state["max_attempts"]

        return {
            # Preserve existing validation history.
            # Do NOT append latest_result again because it
            # is already the latest validation result.
            "validation_results": [
                *validation_results,
            ],
            "retry_state": {
                "attempt": attempt,
                "max_attempts": max_attempts,
                "reason": latest_result.get(
                    "reason",
                    "invalid_output",
                ),
                "escalated": attempt >= max_attempts,
            },
        }

    # Valid output
    return {
        "validation_results": [
            *validation_results,
            latest_result,
        ],
    }


def route_after_output_validation(
    state: AgentState,
) -> Literal[
    "extract",
    "detect_conflicts",
    "escalate",
]:
    validation_results = state.get("validation_results", [])

    if not validation_results:
        return "extract"

    latest_result = validation_results[-1]

    if latest_result.get("valid") is False:
        retry_state = state["retry_state"]

        if retry_state["escalated"]:
            return "escalate"

        return "extract"

    return "detect_conflicts"


def escalation_node(state: AgentState) -> dict:
    return {
        "status": "failed",
        "errors": [
            *state.get("errors", []),
            {
                "code": "RETRY_LIMIT_EXCEEDED",
                "message": "Maximum retry attempts exceeded",
            },
        ],
        "retry_state": {
            **state["retry_state"],
            "escalated": True,
        },
    }


def detect_conflicts_node(state: AgentState) -> dict:
    return {
        "conflicts": [],
    }


def route_after_conflict_detection(
    state: AgentState,
) -> Literal["human_conflict_review", "rule_validation"]:
    if state.get("conflicts"):
        return "human_conflict_review"

    return "rule_validation"


def human_conflict_review_node(state: AgentState) -> dict:
    return {
        "review_status": "pending",
    }


def rule_validation_node(state: AgentState) -> dict:
    return {
        "validation_results": state.get("validation_results", [])
        + [
            {
                "valid": True,
                "stage": "rule_validation",
            }
        ],
    }


def generate_findings_node(state: AgentState) -> dict:
    return {
        "findings": [],
        "proposed_changes": [],
    }


def human_review_gate_node(state: AgentState) -> dict:
    return {}


def route_after_human_review(
    state: AgentState,
) -> Literal["commit", "end"]:
    if state.get("review_status") == "approved":
        return "commit"

    return "end"


def commit_node(state: AgentState) -> dict:
    return {
        "status": "completed",
    }


def build_workflow(checkpointer=None):
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("ingest", ingest_node)
    graph.add_node("classify", classify_node)
    graph.add_node("extract", extract_node)
    graph.add_node("validate_output", validate_output_node)
    graph.add_node("detect_conflicts", detect_conflicts_node)
    graph.add_node(
        "human_conflict_review",
        human_conflict_review_node,
    )
    graph.add_node("rule_validation", rule_validation_node)
    graph.add_node("generate_findings", generate_findings_node)
    graph.add_node(
        "human_review_gate",
        human_review_gate_node,
    )
    graph.add_node("commit", commit_node)
    graph.add_node("escalate", escalation_node)

    # Main workflow
    graph.add_edge(START, "ingest")
    graph.add_edge("ingest", "classify")
    graph.add_edge("classify", "extract")
    graph.add_edge("extract", "validate_output")

    # Output validation routing
    graph.add_conditional_edges(
        "validate_output",
        route_after_output_validation,
        {
            "extract": "extract",
            "detect_conflicts": "detect_conflicts",
            "escalate": "escalate",
        },
    )

    # Conflict detection routing
    graph.add_conditional_edges(
        "detect_conflicts",
        route_after_conflict_detection,
        {
            "human_conflict_review": "human_conflict_review",
            "rule_validation": "rule_validation",
        },
    )

    graph.add_edge(
        "human_conflict_review",
        "rule_validation",
    )

    graph.add_edge(
        "rule_validation",
        "generate_findings",
    )

    graph.add_edge(
        "generate_findings",
        "human_review_gate",
    )

    # Human review routing
    graph.add_conditional_edges(
        "human_review_gate",
        route_after_human_review,
        {
            "commit": "commit",
            "end": END,
        },
    )

    # Terminal edges
    graph.add_edge("commit", END)
    graph.add_edge("escalate", END)

    return graph.compile(
    checkpointer=checkpointer,
    )