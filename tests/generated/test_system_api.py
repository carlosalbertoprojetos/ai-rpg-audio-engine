from __future__ import annotations

from pcbagent.generated.api.system import get_status


def test_generated_system_api_status() -> None:
    payload = get_status()

    assert payload["product"] == "Meu Sistema"
    assert payload["status"] == "ready"
