"""Config flow for the DWD Rain Radar integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.const import CONF_NAME

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
from .radar import get_dwd_grid_cell


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
    data: dict,
) -> tuple[dict, dict[str, str]]:
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


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for DWD Rain Radar."""

    VERSION = 1

    MINOR_VERSION = 4

    def __init__(
        self,
    ) -> None:
        """Initialize the config flow."""

        super().__init__()

        self._entry_data: dict = {}

    async def async_step_user(self, user_input=None) -> FlowResult:
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

                self._entry_data = data

                return await self.async_step_sensor_groups()

        return self.async_show_form(
            step_id="user",
            data_schema=self.get_schema_user_step(),
            errors=errors,
        )

    async def async_step_sensor_groups(
        self,
        user_input=None,
    ) -> FlowResult:
        """Select enabled sensor groups."""

        if user_input is not None:

            self._entry_data[
                CONF_SENSOR_GROUPS
            ] = user_input[
                CONF_SENSOR_GROUPS
            ]

            return self.async_create_entry(
                title=self._entry_data[
                    CONF_NAME
                ],
                data=self._entry_data,
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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Return the options flow."""

        return OptionsFlow(
            config_entry,
        )

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

    def __init__(
        self,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize options flow."""

        self._config_entry = config_entry

        self._updated_location: dict = {}

    async def async_step_init(
        self,
        user_input=None,
    ) -> FlowResult:
        """Edit general settings."""

        errors: dict[str, str] = {}

        if user_input is not None:

            data, errors = _validate_location(
                user_input,
            )

            if not errors:

                duplicate_location = any(
                    entry.entry_id
                    != self._config_entry.entry_id
                    and entry.data.get(
                        "latitude"
                    )
                    == data[
                        "latitude"
                    ]
                    and entry.data.get(
                        "longitude"
                    )
                    == data[
                        "longitude"
                    ]
                    for entry
                    in self.hass.config_entries.async_entries(
                        DOMAIN,
                    )
                )

                if duplicate_location:

                    errors["base"] = (
                        "already_configured"
                    )

                else:

                    self._updated_location = data

                    return await self.async_step_sensor_groups()

        return self.async_show_form(
            step_id="init",
            data_schema=self.get_schema_user_step(),
            errors=errors,
        )

    @callback
    def get_schema_user_step(
        self,
    ) -> vol.Schema:
        """Return the schema for the options location step."""

        return vol.Schema(
            {
                vol.Required(
                    CONF_NAME,
                    default=self._config_entry.title,
                ): str,

                vol.Required(
                    CONF_COORDS,
                    default={
                        "latitude": self._config_entry.data[
                            "latitude"
                        ],
                        "longitude": self._config_entry.data[
                            "longitude"
                        ],
                    },
                ): selector.LocationSelector(
                    selector.LocationSelectorConfig(),
                ),
            }
        )

    async def async_step_sensor_groups(
        self,
        user_input=None,
    ) -> FlowResult:
        """Manage sensor groups."""

        if user_input is not None:

            updated_data = dict(
                self._config_entry.data,
            )

            updated_data.update(
                self._updated_location,
            )

            updated_data[
                CONF_SENSOR_GROUPS
            ] = user_input[
                CONF_SENSOR_GROUPS
            ]

            self.hass.config_entries.async_update_entry(
                self._config_entry,
                title=updated_data[
                    CONF_NAME
                ],
                data=updated_data,
            )

            return self.async_create_entry(
                title="",
                data={},
            )

        enabled_groups = self._config_entry.data.get(
            CONF_SENSOR_GROUPS,
            DEFAULT_SENSOR_GROUPS,
        )

        return self.async_show_form(
            step_id="sensor_groups",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SENSOR_GROUPS,
                        default=enabled_groups,
                    ): _sensor_group_selector(),
                }
            ),
        )
