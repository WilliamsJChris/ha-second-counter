"""Second Counter sensor platform."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_INITIAL_VALUE, CONF_START_IMMEDIATELY, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Second Counter sensor from a config entry."""
    name: str = entry.data.get("name", "Second Counter")
    initial_value: int = entry.data.get(CONF_INITIAL_VALUE, 0)
    start_immediately: bool = entry.data.get(CONF_START_IMMEDIATELY, True)

    sensor = SecondCounterSensor(
        entry_id=entry.entry_id,
        name=name,
        initial_value=initial_value,
        start_immediately=start_immediately,
    )

    # Store reference so __init__.py service handlers can reach it
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = sensor

    async_add_entities([sensor])



def _format_duration(total_seconds: int) -> str:
    """Format an integer number of seconds as a human-readable duration.

    Returns ``"Y s"`` for values ≤ 59, otherwise ``"X m Y s"``.
    Negative values are prefixed with ``"-"``.
    """
    sign = ""
    value = total_seconds
    if value < 0:
        sign = "-"
        value = abs(value)

    if value <= 59:
        return f"{sign}{value} s"

    minutes = value // 60
    seconds = value % 60
    return f"{sign}{minutes} m {seconds} s"


class SecondCounterSensor(SensorEntity):

    """A sensor that counts up by 1 every second with drift compensation."""

    _attr_icon = "mdi:timer-stop"  # fallback; icon.svg / icons.json takes precedence

    def __init__(
        self,
        entry_id: str,
        name: str,
        initial_value: int,
        start_immediately: bool,
    ) -> None:
        """Initialise the sensor."""
        self._entry_id = entry_id
        self._attr_name = name
        self._attr_unique_id = entry_id
        self._initial_value = initial_value
        self._counter: int = initial_value
        self._is_running: bool = start_immediately
        self._last_ticked_at: str | None = None
        self._tick_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # SensorEntity properties
    # ------------------------------------------------------------------

    @property
    def native_value(self) -> str:
        """Return the counter as a human-readable duration string.

        Examples:
            42       →  "42 s"
            60       →  "1 m 0 s"
            90       →  "1 m 30 s"
            -10      →  "-10 s"
        """
        return _format_duration(self._counter)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes exposed to HA."""
        return {
            "count": self._counter,          # raw integer for automations / templates
            "is_running": self._is_running,
            "last_ticked_at": self._last_ticked_at,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        """Start background tick loop when entity is added to HA."""
        self._tick_task = self.hass.async_create_background_task(
            self._tick_loop(),
            name=f"second_counter_tick_{self._entry_id}",
        )

    async def async_will_remove_from_hass(self) -> None:
        """Cancel the tick loop to prevent orphaned tasks or memory leaks."""
        if self._tick_task is not None and not self._tick_task.done():
            self._tick_task.cancel()
            try:
                await self._tick_task
            except asyncio.CancelledError:
                pass
            self._tick_task = None

    # ------------------------------------------------------------------
    # Core tick loop (drift-compensated)
    # ------------------------------------------------------------------

    async def _tick_loop(self) -> None:
        """Continuous loop that increments the counter once per second.

        Uses clock-compensated sleep to prevent drift over long runtimes.
        """
        loop = asyncio.get_running_loop()

        while True:
            tick_start = loop.time()

            if self._is_running:
                self._counter += 1
                self._last_ticked_at = datetime.now(timezone.utc).isoformat()
                self.async_write_ha_state()

            # Compensate for the execution time consumed by the tick
            elapsed = loop.time() - tick_start
            sleep_duration = max(0.0, 1.0 - elapsed)
            await asyncio.sleep(sleep_duration)

    # ------------------------------------------------------------------
    # Service-callable entity methods
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        """Start (or resume) the counter."""
        self._is_running = True
        self.async_write_ha_state()

    async def async_pause(self) -> None:
        """Pause the counter without resetting it."""
        self._is_running = False
        self.async_write_ha_state()

    async def async_reset(self) -> None:
        """Reset the counter to its configured initial value."""
        self._counter = self._initial_value
        self._last_ticked_at = None
        self.async_write_ha_state()

    async def async_set_value(self, value: int) -> None:
        """Override the counter with an arbitrary integer value."""
        self._counter = value
        self.async_write_ha_state()
