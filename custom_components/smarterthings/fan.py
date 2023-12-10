"""Support for fans through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
import math
from typing import Any

from pysmartthings import Attribute, Capability

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    int_states_in_range,
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

SPEED_RANGE = (1, 3)  # off is not included


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add fans for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    async_add_entities(
        [
            SmartThingsFan(device)
            for device in broker.devices.values()
            if broker.any_assigned(device.device_id, "fan")
        ]
    )


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    # Must have switch
    supported = [Capability.switch]

    # These are all optional
    optional = [
        Capability.air_conditioner_fan_mode,
        Capability.fan_speed,
    ]

    for capability in capabilities:
        if capability in optional:
            supported.append(capability)

    if all(capability in capabilities for capability in supported):
        return supported
    return None


class SmartThingsFan(SmartThingsEntity, FanEntity):
    """Define a SmartThings Fan."""

    _attr_supported_features = FanEntityFeature(0)
    _attr_speed_count = int_states_in_range(SPEED_RANGE)

    def __init__(self, device):
            """Init the class."""
            super().__init__(device)
            self._attr_supported_features = self._determine_features()


    def _determine_features(self):
        flags = FanEntityFeature(0)

        if self._device.get_capability(Capability.fan_speed):
            flags |= FanEntityFeature.SET_SPEED
        if self._device.get_capability(Capability.air_conditioner_fan_mode):
            flags |= FanEntityFeature.PRESET_MODE

        return flags

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        await self._async_set_percentage(percentage)

    async def _async_set_percentage(self, percentage: int | None) -> None:
        if percentage is None:
            await self._device.switch_on(set_status=True)
        elif percentage == 0:
            await self._device.switch_off(set_status=True)
        else:
            value = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
            await self._device.set_fan_speed(value, set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset_mode of the fan."""
        if (preset_mode in self.preset_modes):
            await self._device.set_fan_mode(preset_mode, set_status=True)

        self.async_write_ha_state()

    async def async_turn_on(self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any) -> None:
        """Turn the fan on."""
        if percentage is not None:
            await self._async_set_percentage(percentage)
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        else:
            await self._device.switch_on(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self._device.switch_off(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if fan is on."""
        return self._device.status.switch

    @property
    def percentage(self) -> int:
        """Return the current speed percentage."""
        if (FanEntityFeature.SET_SPEED in self._attr_supported_features):
            return ranged_value_to_percentage(SPEED_RANGE, self._device.status.fan_speed)

        return None

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode, e.g., auto, smart, interval, favorite.

        Requires FanEntityFeature.SET_SPEED.
        """
        if (FanEntityFeature.PRESET_MODE in self._attr_supported_features):
            return self._device.status.fan_mode

        return None

    @property
    def preset_modes(self) -> list[str] | None:
        """Return a list of available preset modes.

        Requires FanEntityFeature.SET_SPEED.
        """
        if (FanEntityFeature.PRESET_MODE in self._attr_supported_features):
            return self._device.status.supported_ac_fan_modes

        return None
