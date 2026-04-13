import aiohttp
from datetime import timedelta
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, AIRPORTS_ENDPOINT, CONFIG_ENDPOINT, SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "number", "text"]

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
    pi_ip = entry.data["pi_ip"].rstrip("/")
    airports_url = pi_ip + AIRPORTS_ENDPOINT
    config_url = pi_ip + CONFIG_ENDPOINT

    async def _fetch_airports():
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(airports_url) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    return await resp.json()
        except aiohttp.ClientError as exc:
            raise UpdateFailed(f"connection error: {exc}") from exc

    async def _fetch_config():
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(config_url) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    return await resp.json()
        except aiohttp.ClientError as exc:
            raise UpdateFailed(f"connection error: {exc}") from exc

    airports_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"metarmap25_airports_{entry.entry_id}",
        update_method=_fetch_airports,
        update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
    )

    config_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"metarmap25_config_{entry.entry_id}",
        update_method=_fetch_config,
        update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
    )

    await airports_coordinator.async_config_entry_first_refresh()
    await config_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "airports": airports_coordinator,
        "config": config_coordinator,
        "pi_ip": pi_ip,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_patch_config(pi_ip: str, config_coordinator: DataUpdateCoordinator, field: str, value) -> None:
    """Update a single config field on the Pi and refresh the coordinator."""
    current = dict(config_coordinator.data or {})
    current[field] = value
    config_url = pi_ip + CONFIG_ENDPOINT
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(config_url, json=current) as resp:
            if resp.status not in (200, 204):
                text = await resp.text()
                raise Exception(f"Pi returned HTTP {resp.status}: {text}")
    await config_coordinator.async_request_refresh()
