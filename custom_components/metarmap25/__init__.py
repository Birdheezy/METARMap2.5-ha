import aiohttp
from datetime import timedelta
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, AIRPORTS_ENDPOINT, SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]

CARD_URL = "/metarmap25/metarmap25-card.js"
CARD_PATH = Path(__file__).parent / "metarmap25-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(CARD_URL, str(CARD_PATH), False)
        ])
    except Exception:
        pass  # Already registered from a previous load
    add_extra_js_url(hass, CARD_URL)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    pi_ip = entry.data["pi_ip"]
    url = pi_ip.rstrip("/") + AIRPORTS_ENDPOINT

    async def _fetch():
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    return await resp.json()
        except aiohttp.ClientError as exc:
            raise UpdateFailed(f"connection error: {exc}") from exc

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"metarmap25_{entry.entry_id}",
        update_method=_fetch,
        update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
