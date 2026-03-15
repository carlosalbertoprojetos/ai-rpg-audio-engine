from __future__ import annotations

from pcbagent.generated.task_manager.taskmanagermodule import TaskManagerModule


def test_task_manager_starter_class_executes() -> None:
    instance = TaskManagerModule()
    result = instance.execute()

    assert result["module"] == "task_manager"
    assert result["class"] == "TaskManagerModule"
    assert result["status"] == "ready"
