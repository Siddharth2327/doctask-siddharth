from typing import Any, Literal,NotRequired, TypedDict


ReviewStatus = Literal[
    "pending",
    "approved",
    "rejected",
]

RunStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "paused",
]

RetryState = TypedDict(
    "RetryState",
    {
        "attempt": int,
        "max_attempts": int,
        "reason": str | None,
        "escalated": bool,
    },
)

UsageState = TypedDict(
    "UsageState",
    {
        "input_tokens": int,
        "output_tokens": int,
        "total_tokens": int,
        "estimated_cost": float,
    },
)

PromptMetadata = TypedDict(
    "PromptMetadata",
    {
        "prompt_name": str,
        "prompt_version": str,
        "model": str,
        "model_version": str | None,
    },
)

AgentState = TypedDict(
    "AgentState",
    {
        "run_id": str,
        "document_id": str,
        "document_version_id": str,
        "parsed_content": NotRequired[str],
        "status": RunStatus,
        "extracted_facts": list[dict[str, Any]],
        "evidence": list[dict[str, Any]],
        "conflicts": list[dict[str, Any]],
        "validation_results": list[dict[str, Any]],
        "findings": list[dict[str, Any]],
        "proposed_changes": list[dict[str, Any]],
        "review_status": ReviewStatus,
        "retry_state": RetryState,
        "errors": list[dict[str, Any]],
        "usage": UsageState,
        "prompt_metadata": list[PromptMetadata],
    },
)

