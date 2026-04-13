from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN
from . import async_patch_config


@dataclass(frozen=True)
class METARMapNumberDescription(NumberEntityDescription):
    config_key: str = ""
    value_type: str = "float"  # "int" or "float"


NUMBERS: tuple[METARMapNumberDescription, ...] = (
    METARMapNumberDescription(key="day_brightness",          name="Day Brightness",          config_key="day_brightness",          native_min_value=0,   native_max_value=1,    native_step=0.01, native_unit_of_measurement="%", value_type="float"),
    METARMapNumberDescription(key="night_brightness",        name="Night Brightness",        config_key="night_brightness",        native_min_value=0,   native_max_value=1,    native_step=0.01, native_unit_of_measurement="%", value_type="float"),
    METARMapNumberDescription(key="windy_dim_level",         name="Windy Dim Level",         config_key="windy_dim_level",         native_min_value=0,   native_max_value=1,    native_step=0.01, native_unit_of_measurement="%", value_type="float"),
    METARMapNumberDescription(key="snowy_min_brightness",    name="Snow Min Brightness",     config_key="snowy_min_brightness",    native_min_value=0,   native_max_value=1,    native_step=0.01, native_unit_of_measurement="%", value_type="float"),
    METARMapNumberDescription(key="wind_threshold_kt",       name="Wind Threshold",          config_key="wind_threshold_kt",       native_min_value=0,   native_max_value=200,  native_step=1,    native_unit_of_measurement="kt", value_type="int"),
    METARMapNumberDescription(key="gust_threshold_kt",       name="Gust Threshold",          config_key="gust_threshold_kt",       native_min_value=0,   native_max_value=200,  native_step=1,    native_unit_of_measurement="kt", value_type="int"),
    METARMapNumberDescription(key="stale_threshold_min",     name="Stale Threshold",         config_key="stale_threshold_min",     native_min_value=1,   native_max_value=1440, native_step=1,    native_unit_of_measurement="min", value_type="int"),
    METARMapNumberDescription(key="fetch_interval_sec",      name="Fetch Interval",          config_key="fetch_interval_sec",      native_min_value=60,  native_max_value=3600, native_step=1,    native_unit_of_measurement="s", value_type="int"),
    METARMapNumberDescription(key="network_debounce_count",  name="Network Debounce",        config_key="network_debounce_count",  native_min_value=1,   native_max_value=20,   native_step=1,    value_type="int"),
    METARMapNumberDescription(key="animation_rest_s",        name="Animation Pause",         config_key="animation_rest_s",        native_min_value=0,   native_max_value=300,  native_step=0.5,  native_unit_of_measurement="s", value_type="float"),
    METARMapNumberDescription(key="windy_fade_time_s",       name="Windy Fade Time",         config_key="windy_fade_time_s",       native_min_value=0,   native_max_value=60,   native_step=0.1,  native_unit_of_measurement="s", value_type="float"),
    METARMapNumberDescription(key="windy_hold_time_s",       name="Windy Hold Time",         config_key="windy_hold_time_s",       native_min_value=0,   native_max_value=60,   native_step=0.1,  native_unit_of_measurement="s", value_type="float"),
    METARMapNumberDescription(key="snowy_animation_dur_s",   name="Snow Animation Duration", config_key="snowy_animation_dur_s",   native_min_value=0,   native_max_value=60,   native_step=0.5,  native_unit_of_measurement="s", value_type="float"),
    METARMapNumberDescription(key="snowy_cycle_min_s",       name="Snow Cycle Min",          config_key="snowy_cycle_min_s",       native_min_value=0,   native_max_value=30,   native_step=0.1,  native_unit_of_measurement="s", value_type="float"),
    METARMapNumberDescription(key="snowy_cycle_max_s",       name="Snow Cycle Max",          config_key="snowy_cycle_max_s",       native_min_value=0,   native_max_value=30,   native_step=0.1,  native_unit_of_measurement="s", value_type="float"),
    METARMapNumberDescription(key="snowy_start_offset_max_s",name="Snow Start Offset Max",   config_key="snowy_start_offset_max_s",native_min_value=0,   native_max_value=30,   native_step=0.1,  native_unit_of_measurement="s", value_type="float"),
    METARMapNumberDescription(key="lightning_flash_count",   name="Lightning Flash Count",   config_key="lightning_flash_count",   native_min_value=1,   native_max_value=20,   native_step=1,    value_type="int"),
    METARMapNumberDescription(key="lightning_flash_on_ms",   name="Lightning Flash On",      config_key="lightning_flash_on_ms",   native_min_value=10,  native_max_value=2000, native_step=10,   native_unit_of_measurement="ms", value_type="int"),
    METARMapNumberDescription(key="lightning_flash_off_ms",  name="Lightning Flash Off",     config_key="lightning_flash_off_ms",  native_min_value=10,  native_max_value=2000, native_step=10,   native_unit_of_measurement="ms", value_type="int"),
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
        METARMapNumber(config_coordinator, entry, pi_ip, desc)
        for desc in NUMBERS
    ]
    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data["name"],
        manufacturer="METARMap",
        model="METARMap 2.5",
    )


class METARMapNumber(CoordinatorEntity, NumberEntity):
    """Writable number entity backed by a field in /api/config."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        pi_ip: str,
        description: METARMapNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._pi_ip = pi_ip
        self._attr_name = f"{entry.data['name']} {description.name}"
        self._attr_unique_id = f"metarmap_{entry.entry_id}_{description.key}"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self.entity_description.config_key)

    async def async_set_native_value(self, value: float) -> None:
        typed = int(value) if self.entity_description.value_type == "int" else float(value)
        await async_patch_config(self._pi_ip, self.coordinator, self.entity_description.config_key, typed)
