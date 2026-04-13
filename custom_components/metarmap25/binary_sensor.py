from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["airports"]

    entities = []

    if coordinator.data and coordinator.data.get("airports"):
        for airport in coordinator.data["airports"]:
            icao = airport["icao"]
            entities.append(METARMapWindySensor(coordinator, entry, icao))
            entities.append(METARMapSnowSensor(coordinator, entry, icao))
            entities.append(METARMapThunderSensor(coordinator, entry, icao))

    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data["name"],
        manufacturer="METARMap",
        model="METARMap 2.5",
    )


class _METARMapBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base binary sensor for a single airport condition."""

    _attribute: str

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry, icao: str, suffix: str) -> None:
        super().__init__(coordinator)
        self._icao = icao
        self._attr_name = f"{entry.data['name']} {icao} {suffix}"
        self._attr_unique_id = f"metarmap_{entry.entry_id}_{icao}_{suffix}"
        self._attr_device_info = _device_info(entry)

    def _airport_data(self):
        if not self.coordinator.data:
            return None
        for ap in self.coordinator.data.get("airports", []):
            if ap["icao"] == self._icao:
                return ap
        return None

    @property
    def is_on(self):
        ap = self._airport_data()
        return bool(ap.get(self._attribute)) if ap else False


class METARMapWindySensor(_METARMapBinarySensor):
    _attribute = "is_windy"

    def __init__(self, coordinator, entry, icao):
        super().__init__(coordinator, entry, icao, "windy")


class METARMapSnowSensor(_METARMapBinarySensor):
    _attribute = "has_snow"

    def __init__(self, coordinator, entry, icao):
        super().__init__(coordinator, entry, icao, "snow")


class METARMapThunderSensor(_METARMapBinarySensor):
    _attribute = "has_thunder"

    def __init__(self, coordinator, entry, icao):
        super().__init__(coordinator, entry, icao, "thunder")
