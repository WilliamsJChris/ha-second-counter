"""Config flow for Second Counter integration."""
from __future__ import annotations

import uuid
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_INITIAL_VALUE,
    CONF_START_IMMEDIATELY,
    DEFAULT_NAME,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("name", default=DEFAULT_NAME): str,
        vol.Required(CONF_INITIAL_VALUE, default=0): int,
        vol.Required(CONF_START_IMMEDIATELY, default=True): bool,
    }
)


class SecondCounterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Second Counter."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial user setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Generate a unique ID so multiple instances can coexist
            unique_id = str(uuid.uuid4())
            await self.async_set_unique_id(unique_id)

            return self.async_create_entry(
                title=user_input.get("name", DEFAULT_NAME),
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SecondCounterOptionsFlow:
        """Return the options flow handler."""
        return SecondCounterOptionsFlow()


class SecondCounterOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Second Counter (post-setup edits).

    self.config_entry is automatically injected by HA (2024.x+);
    do NOT override __init__ to set it manually.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Prefer previously saved options; fall back to original config data
        current = {**self.config_entry.data, **self.config_entry.options}

        options_schema = vol.Schema(
            {
                vol.Required(
                    "name", default=current.get("name", DEFAULT_NAME)
                ): str,
                vol.Required(
                    CONF_INITIAL_VALUE,
                    default=current.get(CONF_INITIAL_VALUE, 0),
                ): int,
                vol.Required(
                    CONF_START_IMMEDIATELY,
                    default=current.get(CONF_START_IMMEDIATELY, True),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )
