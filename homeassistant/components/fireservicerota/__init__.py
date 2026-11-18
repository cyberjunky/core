"""The FireServiceRota integration."""

from datetime import timedelta

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN
from .coordinator import (
    FireServiceConfigEntry,
    FireServiceRotaClient,
    FireServiceUpdateCoordinator,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: FireServiceConfigEntry) -> None:
    """Set up FireServiceRota from a config entry."""

    client = FireServiceRotaClient(hass, entry)
    coordinator = FireServiceUpdateCoordinator(hass, client, entry)
    # Needed by the websocket listener, which starts in client.setup()
    entry.runtime_data = coordinator

    await client.setup()

    if client.token_refresh_failure:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="token_refresh_failed",
        )

    entry.async_on_unload(client.async_stop_listener)

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_unload_entry(
    hass: HomeAssistant, entry: FireServiceConfigEntry
) -> None:
    """Unload FireServiceRota config entry."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)
