from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import DEFAULT_HOST, DEFAULT_PORT, DOMAIN


async def _test_connection(hass: HomeAssistant, host: str, port: int) -> bool:
    # Keep setup lightweight. The media player will establish and maintain the
    # actual WebSocket connection after the config entry is created.
    import asyncio
    import aiohttp

    url = f"ws://{host}:{port}"
    try:
        async with aiohttp.ClientSession() as session:
            async with asyncio.timeout(5):
                async with session.ws_connect(url, heartbeat=20):
                    return True
    except (aiohttp.ClientError, OSError, asyncio.TimeoutError):
        return False


class SpotifySoloistConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            if await _test_connection(self.hass, host, port):
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Spotify Soloist",
                    data=user_input,
                )
            errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
