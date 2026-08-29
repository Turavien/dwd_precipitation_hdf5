"""Config flow for the DWD Rain Radar integration."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_COORDS,
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
    DOMAIN,
    SENSOR_GROUP_CURRENT,
    SENSOR_GROUP_EVENT,
    SENSOR_GROUP_FORECAST,
    SENSOR_GROUP_HISTORY,
    SENSOR_GROUP_ROLLING,
)
from .fetcher import Fetcher
from .radar import get_dwd_grid_cell

_LOGGER = logging.getLogger(__name__)


def _sensor_group_selector(
) -> selector.SelectSelector:
    """Return the sensor group selector."""

    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            multiple=True,
            mode=selector.SelectSelectorMode.LIST,
            options=[
                SENSOR_GROUP_CURRENT,
                SENSOR_GROUP_FORECAST,
                SENSOR_GROUP_EVENT,
                SENSOR_GROUP_HISTORY,
                SENSOR_GROUP_ROLLING,
            ],
            translation_key="sensor_groups",
        ),
    )


def _validate_location(
    data: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Validate name and coordinates."""

    errors: dict[str, str] = {}

    result = data.copy()

    result[CONF_NAME] = (
        result[CONF_NAME].strip()
    )

    if not result[CONF_NAME]:
        errors["base"] = "invalid_name"

    coords = result.get(CONF_COORDS)

    if coords is None:

        errors["base"] = "invalid_coordinates"

        return result, errors

    latitude = round(
        coords["latitude"],
        6,
    )

    longitude = round(
        coords["longitude"],
        6,
    )

    try:

        grid_cell = get_dwd_grid_cell(
            latitude,
            longitude,
        )

    except ValueError:

        errors["base"] = (
            "outside_dwd_coverage"
        )

        return result, errors

    result["latitude"] = latitude
    result["longitude"] = longitude
    result["grid_cell"] = grid_cell

    result.pop(
        CONF_COORDS,
        None,
    )

    return (
        result,
        errors,
    )


async def _async_check_connection(
    hass: HomeAssistant,
) -> str | None:
    """Check access to the DWD radar service."""

    try:
        await Fetcher(
            hass,
        ).async_check_connection()

    except (
        ClientError,
        TimeoutError,
    ):
        return "cannot_connect"

    except Exception:  # noqa: BLE001
        _LOGGER.exception(
            "Unexpected error while checking DWD radar service"
        )
        return "unknown"

    return None


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for DWD Rain Radar."""

    VERSION = 1

    MINOR_VERSION = 5

    def __init__(
        self,
    ) -> None:
        """Initialize the config flow."""

        super().__init__()

        self._entry_data: dict[str, Any] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the user step."""

        errors: dict[str, str] = {}

        if user_input is not None:

            data, errors = _validate_location(
                user_input,
            )

            if not errors:

                self._async_abort_entries_match(
                    {
                        "latitude": data[
                            "latitude"
                        ],
                        "longitude": data[
                            "longitude"
                        ],
                    }
                )

                connection_error = await _async_check_connection(
                    self.hass,
                )

                if connection_error is None:

                    self._entry_data = data

                    return await self.async_step_sensor_groups()

                errors["base"] = connection_error

        return self.async_show_form(
            step_id="user",
            data_schema=self.get_schema_user_step(),
            errors=errors,
        )

    async def async_step_sensor_groups(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Select enabled sensor groups."""

        if user_input is not None:

            return self.async_create_entry(
                title=self._entry_data[
                    CONF_NAME
                ],
                data=self._entry_data,
                options={
                    CONF_SENSOR_GROUPS: user_input[
                        CONF_SENSOR_GROUPS
                    ],
                },
            )

        return self.async_show_form(
            step_id="sensor_groups",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SENSOR_GROUPS,
                        default=DEFAULT_SENSOR_GROUPS,
                    ): _sensor_group_selector(),
                }
            ),
            description_placeholders={},
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Reconfigure name and location."""

        reconfigure_entry = self._get_reconfigure_entry()

        errors: dict[str, str] = {}

        if user_input is not None:

            data, errors = _validate_location(
                user_input,
            )

            if not errors:

                self._async_abort_entries_match(
                    {
                        "latitude": data[
                            "latitude"
                        ],
                        "longitude": data[
                            "longitude"
                        ],
                    }
                )

                updated_data = dict(
                    reconfigure_entry.data,
                )

                updated_data.update(
                    data,
                )

                updated_data.pop(
                    CONF_SENSOR_GROUPS,
                    None,
                )

                self.hass.config_entries.async_update_entry(
                    reconfigure_entry,
                    title=data[
                        CONF_NAME
                    ],
                    data=updated_data,
                )

                return self.async_abort(
                    reason="reconfigure_successful",
                )

        suggested_values: dict[str, Any] = {
            CONF_NAME: reconfigure_entry.data.get(
                CONF_NAME,
                reconfigure_entry.title,
            ),
            CONF_COORDS: {
                "latitude": reconfigure_entry.data[
                    "latitude"
                ],
                "longitude": reconfigure_entry.data[
                    "longitude"
                ],
            },
        }

        if user_input is not None:
            suggested_values.update(
                user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(
                            CONF_NAME,
                        ): str,
                        vol.Required(
                            CONF_COORDS,
                        ): selector.LocationSelector(
                            selector.LocationSelectorConfig(),
                        ),
                    }
                ),
                suggested_values,
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        _config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Return the options flow."""

        return OptionsFlow()

    @callback
    def get_schema_user_step(self) -> vol.Schema:
        """Return the schema for the user step."""

        schema = {
            vol.Required(
                CONF_NAME,
                default=self.hass.config.location_name
            ): str,

            vol.Required(
                CONF_COORDS,
                default={
                    "latitude": round(
                        self.hass.config.latitude,
                        6
                    ),
                    "longitude": round(
                        self.hass.config.longitude,
                        6
                    ),
                },
            ): selector.LocationSelector(
                selector.LocationSelectorConfig(),
            ),
         }

        return vol.Schema(schema)


class OptionsFlow(config_entries.OptionsFlow):
    """Handle DWD Rain Radar options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage enabled sensor groups."""

        if user_input is not None:

            return self.async_create_entry(
                title="",
                data={
                    CONF_SENSOR_GROUPS: user_input[
                        CONF_SENSOR_GROUPS
                    ],
                },
            )

        enabled_groups = self.config_entry.options.get(
            CONF_SENSOR_GROUPS,
            self.config_entry.data.get(
                CONF_SENSOR_GROUPS,
                DEFAULT_SENSOR_GROUPS,
            ),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SENSOR_GROUPS,
                        default=enabled_groups,
                    ): _sensor_group_selector(),
                }
            ),
        )
