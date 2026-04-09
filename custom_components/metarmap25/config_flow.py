import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN, AIRPORTS_ENDPOINT

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("pi_ip"): str,
        vol.Required("name"): str,
    }
)


async def _validate_connection(pi_ip: str) -> None:
    """Attempt to reach /api/airports — raises on failure."""
    url = pi_ip.rstrip("/") + AIRPORTS_ENDPOINT
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise ValueError(f"unexpected status {resp.status}")
            data = await resp.json()
            if "airports" not in data:
                raise ValueError("response missing 'airports' key")


class METARMap25ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            pi_ip = user_input["pi_ip"].rstrip("/")

            if not (pi_ip.startswith("http://") or pi_ip.startswith("https://")):
                errors["pi_ip"] = "invalid_url"
            else:
                try:
                    await _validate_connection(pi_ip)
                except Exception:
                    errors["pi_ip"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(pi_ip)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input["name"],
                    data={"pi_ip": pi_ip, "name": user_input["name"]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
