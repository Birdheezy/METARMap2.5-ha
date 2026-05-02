from datetime import datetime
import re

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
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
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = entry_data["airports"]

    entities = []

    if coordinator.data and coordinator.data.get("airports"):
        for airport in coordinator.data["airports"]:
            entities.append(METARMapAirportSensor(coordinator, entry, airport["icao"]))

    entities.append(METARMapStatusSensor(coordinator, entry))
    entities.append(METARMapLastUpdatedSensor(coordinator, entry))
    entities.append(METARMapVersionSensor(coordinator, entry))

    papa_coordinator = entry_data.get("papa")
    if papa_coordinator is not None:
        entities.append(METARMapPapaSensor(papa_coordinator, entry))

    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data["name"],
        manufacturer="METARMap",
        model="METARMap 2.5",
    )


class METARMapAirportSensor(CoordinatorEntity, SensorEntity):
    """Flight category sensor for one airport."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry, icao: str) -> None:
        super().__init__(coordinator)
        self._icao = icao
        self._attr_name = f"{entry.data['name']} {icao}"
        self._attr_unique_id = f"metarmap_{entry.entry_id}_{icao}"
        self._attr_device_info = _device_info(entry)

    def _airport_data(self):
        if not self.coordinator.data:
            return None
        for ap in self.coordinator.data.get("airports", []):
            if ap["icao"] == self._icao:
                return ap
        return None

    @property
    def native_value(self):
        ap = self._airport_data()
        return ap["category"] if ap else None

    @property
    def extra_state_attributes(self):
        ap = self._airport_data()
        if not ap:
            return {}
        colors = (self.coordinator.data or {}).get("colors", {})
        category_color_map = {
            "VFR": colors.get("vfr"),
            "MVFR": colors.get("mvfr"),
            "IFR": colors.get("ifr"),
            "LIFR": colors.get("lifr"),
        }
        return {
            "raw_metar": ap.get("raw_metar", ""),
            "wind_speed_kt": ap.get("wind_speed_kt", 0),
            "wind_gust_kt": ap.get("wind_gust_kt", 0),
            "is_windy": bool(ap.get("is_windy", False)),
            "has_snow": bool(ap.get("has_snow", False)),
            "has_thunder": bool(ap.get("has_thunder", False)),
            "is_stale": bool(ap.get("is_stale", False)),
            "obs_time": ap.get("obs_time"),
            "led_index": ap.get("led_index", 0),
            "color": category_color_map.get(ap.get("category")),
        }


class METARMapStatusSensor(CoordinatorEntity, SensorEntity):
    """Overall data health sensor for the METARMap unit."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.data['name']} Status"
        self._attr_unique_id = f"metarmap_{entry.entry_id}_status"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("status")

    @property
    def extra_state_attributes(self):
        colors = (self.coordinator.data or {}).get("colors", {})
        if not colors:
            return {}
        return {
            "vfr_color": colors.get("vfr"),
            "mvfr_color": colors.get("mvfr"),
            "ifr_color": colors.get("ifr"),
            "lifr_color": colors.get("lifr"),
        }


class METARMapVersionSensor(CoordinatorEntity, SensorEntity):
    """Firmware version of the METARMap unit."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.data['name']} Version"
        self._attr_unique_id = f"metarmap_{entry.entry_id}_version"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("version")


class METARMapLastUpdatedSensor(CoordinatorEntity, SensorEntity):
    """Timestamp of the last successful weather snapshot."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.data['name']} Last Updated"
        self._attr_unique_id = f"metarmap_{entry.entry_id}_last_updated"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        raw = self.coordinator.data.get("built_at")
        if not raw:
            return None
        # Truncate sub-second precision to 6 digits (microseconds) so Python can parse it
        raw = re.sub(r"(\.\d{6})\d+", r"\1", raw)
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None


class METARMapPapaSensor(CoordinatorEntity, SensorEntity):
    """Pilot Tracker state sensor — shows where dad is right now."""

    _STATUS_LABELS = {
        "none":       "Off Duty",
        "enroute":    "Enroute",
        "at_airport": "At Airport",
        "layover":    "Layover",
        "reserve":    "Reserve",
    }

    _STATUS_ICONS = {
        "enroute":    "mdi:airplane",
        "at_airport": "mdi:airplane-marker",
        "layover":    "mdi:bed",
        "reserve":    "mdi:phone-alert",
    }

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.data['name']} Papa Status"
        self._attr_unique_id = f"metarmap_{entry.entry_id}_papa_status"
        self._attr_device_info = _device_info(entry)

    def _data(self) -> dict:
        return self.coordinator.data or {}

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self._data().get("enabled", False)

    @property
    def native_value(self) -> str | None:
        d = self._data()
        if not d.get("enabled"):
            return None
        return self._STATUS_LABELS.get(d.get("status", ""), d.get("status"))

    @property
    def icon(self) -> str:
        return self._STATUS_ICONS.get(self._data().get("status", ""), "mdi:home-account")

    @property
    def extra_state_attributes(self) -> dict:
        d = self._data()
        return {
            "raw_status":    d.get("status"),
            "origin":        d.get("origin"),
            "destination":   d.get("dest"),
            "airport":       d.get("airport"),
            "flight_number": d.get("flight_number"),
            "is_deadhead":   d.get("is_deadhead", False),
            "arrives_at":    d.get("arrives_at"),
            "departs_at":    d.get("departs_at"),
            "trip_end":      d.get("trip_end"),
            "last_sync":     d.get("last_sync"),
        }
