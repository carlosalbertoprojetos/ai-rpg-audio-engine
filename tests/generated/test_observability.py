from __future__ import annotations

from pcbagent.generated.observability.observabilitymodule import ObservabilityModule


def test_observability_starter_class_executes() -> None:
    instance = ObservabilityModule()
    result = instance.execute()

    assert result["module"] == "observability"
    assert result["class"] == "ObservabilityModule"
    assert result["status"] == "ready"
