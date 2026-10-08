"""Config flow for supervisor_container_statistics integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME

from .const import DOMAIN


class SupervisorContainerStatisticsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for supervisor_container_statistics."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user step."""
        if user_input is not None:
            title = user_input[CONF_NAME].strip()
            unique_id = title.lower().replace(" ", "_")
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=title, data={CONF_NAME: title})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default="Supervisor Container Statistics"
                    ): str
                }
            ),
        )
