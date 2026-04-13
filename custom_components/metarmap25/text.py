from dataclasses import dataclass

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN
from . import async_patch_config

HEX_PATTERN = r"^#[0-9a-fA-F]{6}$"


@dataclass(frozen=True)
class METARMapTextDescription(TextEntityDescription):
    config_key: str = ""


COLORS: tuple[METARMapTextDescription, ...] = (
    METARMapTextDescription(key="vfr_color",        name="VFR Color",         config_key="vfr_color",        pattern=HEX_PATTERN),
    METARMapTextDescription(key="mvfr_color",       name="MVFR Color",        config_key="mvfr_color",       pattern=HEX_PATTERN),
    METARMapTextDescription(key="ifr_color",        name="IFR Color",         config_key="ifr_color",        pattern=HEX_PATTERN),
    METARMapTextDescription(key="lifr_color",       name="LIFR Color",        config_key="lifr_color",       pattern=HEX_PATTERN),
    METARMapTextDescription(key="stale_color",      name="Stale Color",       config_key="stale_color",      pattern=HEX_PATTERN),
    METARMapTextDescription(key="no_network_color", name="No Network Color",  config_key="no_network_color", pattern=HEX_PATTERN),
    METARMapTextDescription(key="snowy_color",      name="Snow Color",        config_key="snowy_color",      pattern=HEX_PATTERN),
    METARMapTextDescription(key="lightning_color",  name="Lightning Color",   config_key="lightning_color",  pattern=HEX_PATTERN),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    config_coordinator = data["config"]
    pi_ip = data["pi_ip"]

    entities = [
        METARMapColor(config_coordinator, entry, pi_ip, desc)
        for desc in COLORS
    ]
    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data["name"],
        manufacturer="METARMap",
        model="METARMap 2.5",
    )


class METARMapColor(CoordinatorEntity, TextEntity):
    """Writable text entity for a hex color field in /api/config."""

    _attr_native_min = 7
    _attr_native_max = 7

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        pi_ip: str,
        description: METARMapTextDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._pi_ip = pi_ip
        self._attr_name = f"{entry.data['name']} {description.name}"
        self._attr_unique_id = f"metarmap_{entry.entry_id}_{description.key}"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self.entity_description.config_key)

    async def async_set_value(self, value: str) -> None:
        await async_patch_config(self._pi_ip, self.coordinator, self.entity_description.config_key, value)
