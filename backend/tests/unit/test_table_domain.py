from app.domain.tableops.entities import Player, PlayerAvailability, Table


def test_update_player_availability_changes_led_state() -> None:
    table = Table.create(organization_id="org-1", name="Mesa Raven")
    player = Player.create(display_name="Aria")
    table.add_player(player)

    updated = table.update_player_availability(player.id, PlayerAvailability.UNAVAILABLE)

    assert updated.availability == PlayerAvailability.UNAVAILABLE
    assert table.players[player.id].availability == PlayerAvailability.UNAVAILABLE

