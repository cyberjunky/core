"""Tests for the FireServiceRota integration setup."""

from unittest.mock import AsyncMock, patch

from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.fireservicerota.const import DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_TOKEN, CONF_URL, CONF_USERNAME
from homeassistant.core import HomeAssistant


async def test_setup_token_refresh_failure(hass: HomeAssistant) -> None:
    """Test setup fails and starts reauth when refreshing tokens failed."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "my@email.address",
            CONF_PASSWORD: "mypassw0rd",
            CONF_URL: "www.brandweerrooster.nl",
        },
        unique_id="my@email.address",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.fireservicerota.FireServiceRotaClient"
    ) as mock_client:
        mock_client.return_value.setup = AsyncMock()
        mock_client.return_value.token_refresh_failure = True
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert entry.reason == "Failed to refresh the FireServiceRota authentication tokens"
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_REAUTH


async def test_websocket_connect_failed_requests_refresh(hass: HomeAssistant) -> None:
    """Test a failed websocket connection attempt requests a refresh."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "my@email.address",
            CONF_URL: "www.brandweerrooster.nl",
            CONF_TOKEN: {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
            },
        },
        unique_id="my@email.address",
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.fireservicerota.coordinator.FireServiceRota"
        ) as mock_fsr,
        patch(
            "homeassistant.components.fireservicerota.coordinator.FireServiceRotaIncidents"
        ) as mock_incidents,
    ):
        get_availability = mock_fsr.return_value.get_availability
        get_availability.return_value = {"available": True}
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED
        assert get_availability.call_count == 1

        # The library calls this from its listener thread
        await hass.async_add_executor_job(
            mock_incidents.call_args.kwargs["on_connect_failed"]
        )
        await hass.async_block_till_done()

        assert get_availability.call_count == 2
