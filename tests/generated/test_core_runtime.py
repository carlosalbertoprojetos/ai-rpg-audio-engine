from __future__ import annotations

from pcbagent.generated.core_runtime.coreruntimemodule import CoreRuntimeModule


def test_core_runtime_starter_class_executes() -> None:
    instance = CoreRuntimeModule()
    result = instance.execute()

    assert result["module"] == "core_runtime"
    assert result["class"] == "CoreRuntimeModule"
    assert result["status"] == "ready"
