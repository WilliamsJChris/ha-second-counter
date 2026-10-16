"""Second Counter integration setup."""
from __future__ import annotations

import logging
from typing import Set

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    DOMAIN,
    SERVICE_PAUSE,
    SERVICE_RESET,
    SERVICE_SET_VALUE,
    SERVICE_START,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Second Counter from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unloaded and entry.entry_id in hass.data.get(DOMAIN, {}):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


# ---------------------------------------------------------------------------
# Service registration
# ---------------------------------------------------------------------------



def _resolve_targets(hass: HomeAssistant, call: ServiceCall):
    """Yield sensor objects that match the service call's entity_id filter.

    If no entity_id is provided all registered counters are yielded.
    Accepts either a single entity_id string or a list of strings.
    """
    raw = call.data.get("entity_id")
    if raw is None:
        target_ids: Set[str] | None = None
    elif isinstance(raw, str):
        target_ids = {raw}
    else:
        target_ids = set(raw)

    for sensor in hass.data.get(DOMAIN, {}).values():
        if target_ids is None or sensor.entity_id in target_ids:
            yield sensor


def _register_services(hass: HomeAssistant) -> None:
    """Register domain-level services (idempotent — skips if already registered)."""

    if hass.services.has_service(DOMAIN, SERVICE_START):
        return  # Services already registered (multiple entries sharing one domain)

    # Shared base schema: optional entity_id targeting
    _BASE_SCHEMA = vol.Schema(
        {vol.Optional("entity_id"): vol.Any(str, [str])},
        extra=vol.ALLOW_EXTRA,
    )

    async def handle_start(call: ServiceCall) -> None:
        """Handle the start service call."""
        for sensor in _resolve_targets(hass, call):
            await sensor.async_start()

    async def handle_pause(call: ServiceCall) -> None:
        """Handle the pause service call."""
        for sensor in _resolve_targets(hass, call):
            await sensor.async_pause()

    async def handle_reset(call: ServiceCall) -> None:
        """Handle the reset service call."""
        for sensor in _resolve_targets(hass, call):
            await sensor.async_reset()

    async def handle_set_value(call: ServiceCall) -> None:
        """Handle the set_value service call."""
        value: int = call.data["value"]
        for sensor in _resolve_targets(hass, call):
            await sensor.async_set_value(value)

    hass.services.async_register(
        DOMAIN, SERVICE_START, handle_start, schema=_BASE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PAUSE, handle_pause, schema=_BASE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESET, handle_reset, schema=_BASE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_VALUE,
        handle_set_value,
        schema=_BASE_SCHEMA.extend(
            {vol.Required("value"): vol.Coerce(int)}
        ),
    )
