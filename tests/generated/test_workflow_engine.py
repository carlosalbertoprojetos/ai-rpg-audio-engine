from __future__ import annotations

from pcbagent.generated.workflow_engine.workflowenginemodule import WorkflowEngineModule


def test_workflow_engine_starter_class_executes() -> None:
    instance = WorkflowEngineModule()
    result = instance.execute()

    assert result["module"] == "workflow_engine"
    assert result["class"] == "WorkflowEngineModule"
    assert result["status"] == "ready"
