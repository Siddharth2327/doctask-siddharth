from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.checkpoint import create_checkpointer
from app.agents.workflow import build_workflow
from tests.test_agent_workflow import create_initial_state


def test_checkpoint_persists_workflow_state():
    state = create_initial_state()
    state["review_status"] = "approved"

    with create_checkpointer() as checkpointer:
        checkpointer.setup()

        workflow = build_workflow(checkpointer)

        config = {
            "configurable": {
                "thread_id": state["run_id"],
            }
        }

        result = workflow.invoke(
            state,
            config=config,
        )

        assert result["status"] == "completed"

        checkpoint = workflow.get_state(config)

        assert checkpoint.values["run_id"] == state["run_id"]
        assert (
            checkpoint.values["document_id"]
            == state["document_id"]
        )
        assert (
            checkpoint.values["document_version_id"]
            == state["document_version_id"]
        )
def test_checkpoint_survives_workflow_recreation():
    state = create_initial_state()
    state["review_status"] = "approved"

    config = {
        "configurable": {
            "thread_id": state["run_id"],
        }
    }

    with create_checkpointer() as checkpointer:
        checkpointer.setup()

        workflow = build_workflow(checkpointer)

        result = workflow.invoke(
            state,
            config=config,
        )

        assert result["status"] == "completed"

    # Simulate a process restart by creating a completely
    # new checkpointer and workflow instance.
    with create_checkpointer() as new_checkpointer:
        new_checkpointer.setup()

        restarted_workflow = build_workflow(
            new_checkpointer
        )

        checkpoint = restarted_workflow.get_state(
            config
        )

        assert checkpoint.values["run_id"] == state["run_id"]
        assert (
            checkpoint.values["document_id"]
            == state["document_id"]
        )
        assert (
            checkpoint.values["document_version_id"]
            == state["document_version_id"]
        )
        assert checkpoint.values["status"] == "completed"

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class ResumeTestState(TypedDict):
    value: int


def test_completed_node_is_not_reexecuted_after_checkpoint():
    execution_count = {"count": 0}

    def work_node(state: ResumeTestState) -> dict:
        execution_count["count"] += 1
        return {
            "value": state["value"] + 1,
        }

    graph = StateGraph(ResumeTestState)
    graph.add_node("work", work_node)
    graph.add_edge(START, "work")
    graph.add_edge("work", END)

    with create_checkpointer() as checkpointer:
        checkpointer.setup()

        workflow = graph.compile(
            checkpointer=checkpointer,
        )

        config = {
            "configurable": {
                "thread_id": "resume-test-001",
            }
        }

        result = workflow.invoke(
            {"value": 0},
            config=config,
        )

        assert result["value"] == 1
        assert execution_count["count"] == 1

    # Simulate process restart.
    with create_checkpointer() as new_checkpointer:
        new_checkpointer.setup()

        restarted_workflow = graph.compile(
            checkpointer=new_checkpointer,
        )

        checkpoint = restarted_workflow.get_state(config)

        assert checkpoint.values["value"] == 1

        # The completed node must not have executed again.
        assert execution_count["count"] == 1

def test_failed_node_can_resume_from_checkpoint():
    execution_counts = {
        "completed": 0,
        "failing": 0,
    }

    class FailureState(TypedDict):
        value: int

    should_fail = {"value": True}

    def completed_node(state: FailureState) -> dict:
        execution_counts["completed"] += 1

        return {
            "value": state["value"] + 1,
        }

    def failing_node(state: FailureState) -> dict:
        execution_counts["failing"] += 1

        if should_fail["value"]:
            should_fail["value"] = False
            raise RuntimeError("Simulated node failure")

        return {
            "value": state["value"] + 1,
        }

    graph = StateGraph(FailureState)

    graph.add_node("completed", completed_node)
    graph.add_node("failing", failing_node)

    graph.add_edge(START, "completed")
    graph.add_edge("completed", "failing")
    graph.add_edge("failing", END)

    config = {
        "configurable": {
            "thread_id": "failed-node-resume-001",
        }
    }

    with create_checkpointer() as checkpointer:
        checkpointer.setup()

        workflow = graph.compile(
            checkpointer=checkpointer,
        )

        try:
            workflow.invoke(
                {"value": 0},
                config=config,
            )
        except RuntimeError as exc:
            assert str(exc) == "Simulated node failure"

        checkpoint = workflow.get_state(config)

        assert checkpoint.values["value"] == 1
        assert execution_counts["completed"] == 1

    # Simulate process restart.
    with create_checkpointer() as new_checkpointer:
        new_checkpointer.setup()

        restarted_workflow = graph.compile(
            checkpointer=new_checkpointer,
        )

        result = restarted_workflow.invoke(
            None,
            config=config,
        )

        assert result["value"] == 2

        # Completed node must not run again.
        assert execution_counts["completed"] == 1

        # Failed node runs again after restart.
        assert execution_counts["failing"] == 2

def test_checkpoint_preserves_complete_state():
    state = create_initial_state()

    state["extracted_facts"] = [
        {
            "field": "outcome",
            "value": "won",
        }
    ]

    state["evidence"] = [
        {
            "document_version_id": state["document_version_id"],
            "source": "page-1",
        }
    ]

    state["findings"] = [
        {
            "type": "competitive",
            "summary": "Competitor appeared in the deal.",
        }
    ]

    state["proposed_changes"] = [
        {
            "field": "competitor",
            "value": "Competitor X",
        }
    ]

    state["retry_state"] = {
        "attempt": 1,
        "max_attempts": 3,
        "reason": "temporary_validation_failure",
        "escalated": False,
    }

    state["usage"] = {
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150,
        "estimated_cost": 0.01,
    }

    config = {
        "configurable": {
            "thread_id": "checkpoint-integrity-001",
        }
    }

    with create_checkpointer() as checkpointer:
        checkpointer.setup()

        class IntegrityState(TypedDict):
            run_id: str
            document_id: str
            document_version_id: str
            extracted_facts: list[dict]
            evidence: list[dict]
            findings: list[dict]
            proposed_changes: list[dict]
            retry_state: dict
            usage: dict

        graph = StateGraph(IntegrityState)

        def checkpoint_node(state: IntegrityState) -> dict:
            return {}

        graph.add_node(
            "checkpoint_node",
            checkpoint_node,
        )

        graph.add_edge(START, "checkpoint_node")
        graph.add_edge("checkpoint_node", END)

        workflow = graph.compile(
            checkpointer=checkpointer,
        )

        workflow.invoke(
            {
                "run_id": state["run_id"],
                "document_id": state["document_id"],
                "document_version_id": state[
                    "document_version_id"
                ],
                "extracted_facts": state["extracted_facts"],
                "evidence": state["evidence"],
                "findings": state["findings"],
                "proposed_changes": state[
                    "proposed_changes"
                ],
                "retry_state": state["retry_state"],
                "usage": state["usage"],
            },
            config=config,
        )

        checkpoint = workflow.get_state(config)

        assert checkpoint.values["run_id"] == state["run_id"]

        assert (
            checkpoint.values["document_id"]
            == state["document_id"]
        )

        assert (
            checkpoint.values["document_version_id"]
            == state["document_version_id"]
        )

        assert (
            checkpoint.values["extracted_facts"]
            == state["extracted_facts"]
        )

        assert (
            checkpoint.values["evidence"]
            == state["evidence"]
        )

        assert (
            checkpoint.values["findings"]
            == state["findings"]
        )

        assert (
            checkpoint.values["proposed_changes"]
            == state["proposed_changes"]
        )

        assert (
            checkpoint.values["retry_state"]
            == state["retry_state"]
        )

        assert (
            checkpoint.values["usage"]
            == state["usage"]
        )