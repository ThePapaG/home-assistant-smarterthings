"""Support for sensors through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence

from pysmartthings import Attribute, Capability

from homeassistant.components.air_quality import AirQualityEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

AIR_QUALITY_SENSOR_CAPABILITIES = [
    Capability.dust_sensor,
    Capability.air_quality_sensor,
]

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add fans for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    async_add_entities(
        [
            SmartThingsAirQualitySensor(device)
            for device in broker.devices.values()
            if broker.any_assigned(device.device_id, "fan")
        ]
    )

def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    return [
        capability for capability in AIR_QUALITY_SENSOR_CAPABILITIES if capability in capabilities
    ]

class SmartThingsAirQualitySensor(SmartThingsEntity, AirQualityEntity):
    """Define a SmartThings Air Quality Sensor."""

    @property
    def particulate_matter_2_5(self) -> StateType:
        """Return the particulate matter 2.5 level."""

        if (Attribute.fine_dust_level in self._device.status.attributes):
            return self._device.status.attributes[Attribute.fine_dust_level].value

        return None

    @property
    def particulate_matter_10(self) -> StateType:
        """Return the particulate matter 10 level."""

        if (Attribute.dust_level in self._device.status.attributes):
            return self._device.status.attributes[Attribute.dust_level].value

        return None

    @property
    def particulate_matter_0_1(self) -> StateType:
        """Return the particulate matter 0.1 level."""

        if ("veryFineDustLevel" in self._device.status.attributes):
            return self._device.status.attributes["veryFineDustLevel"].value

        return None

    @property
    def air_quality_index(self) -> StateType:
        """Return the Air Quality Index (AQI)."""

        if (Attribute.air_quality in self._device.status.attributes):
            return self._device.status.attributes[Attribute.air_quality].value

        return None

