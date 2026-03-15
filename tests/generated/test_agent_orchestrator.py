from __future__ import annotations

from pcbagent.generated.agent_orchestrator.agentorchestratormodule import AgentOrchestratorModule


def test_agent_orchestrator_starter_class_executes() -> None:
    instance = AgentOrchestratorModule()
    result = instance.execute()

    assert result["module"] == "agent_orchestrator"
    assert result["class"] == "AgentOrchestratorModule"
    assert result["status"] == "ready"
