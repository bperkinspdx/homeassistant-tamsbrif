import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from . import DOMAIN

class TamsbrifConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TamsbrifOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="TaMSBRIF", data=user_input)

        data_schema = vol.Schema({
            vol.Required("night_scene"): cv.entity_id,
            vol.Required("early_morning_scene"): cv.entity_id,
            vol.Required("morning_scene"): cv.entity_id,
            vol.Required("day_scene"): cv.entity_id,
            vol.Required("early_evening_scene"): cv.entity_id,
            vol.Required("evening_scene"): cv.entity_id,
            vol.Required("late_evening_scene"): cv.entity_id,
            vol.Required("early_night_scene"): cv.entity_id,
            vol.Required("off_scene"): cv.entity_id,
            vol.Required("binary_sensor"): cv.entity_id,
            vol.Optional("disable_sensor"): cv.entity_id,
            vol.Optional("enable_event"): cv.string,
            vol.Optional("disable_event"): cv.string,
            vol.Optional("rgb_light"): cv.entity_id,
            vol.Optional("enable_color", default=[0, 255, 0]): vol.All(cv.ensure_list, [cv.positive_int]),
            vol.Optional("disable_color", default=[255, 0, 0]): vol.All(cv.ensure_list, [cv.positive_int]),
            vol.Optional("already_color", default=[0, 0, 255]): vol.All(cv.ensure_list, [cv.positive_int]),
            vol.Optional("color_duration", default=5): cv.positive_int,
            vol.Optional("off_delay", default=0): cv.positive_int,
            vol.Optional("brighter_event"): cv.string,
            vol.Optional("dimmer_event"): cv.string
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)

class TamsbrifOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({
            vol.Required("night_scene", default=self.config_entry.options.get("night_scene")): cv.entity_id,
            vol.Required("early_morning_scene", default=self.config_entry.options.get("early_morning_scene")): cv.entity_id,
            vol.Required("morning_scene", default=self.config_entry.options.get("morning_scene")): cv.entity_id,
            vol.Required("day_scene", default=self.config_entry.options.get("day_scene")): cv.entity_id,
            vol.Required("early_evening_scene", default=self.config_entry.options.get("early_evening_scene")): cv.entity_id,
            vol.Required("evening_scene", default=self.config_entry.options.get("evening_scene")): cv.entity_id,
            vol.Required("late_evening_scene", default=self.config_entry.options.get("late_evening_scene")): cv.entity_id,
            vol.Required("early_night_scene", default=self.config_entry.options.get("early_night_scene")): cv.entity_id,
            vol.Required("off_scene", default=self.config_entry.options.get("off_scene")): cv.entity_id,
            vol.Required("binary_sensor", default=self.config_entry.options.get("binary_sensor")): cv.entity_id,
            vol.Optional("disable_sensor", default=self.config_entry.options.get("disable_sensor")): cv.entity_id,
            vol.Optional("enable_event", default=self.config_entry.options.get("enable_event")): cv.string,
            vol.Optional("disable_event", default=self.config_entry.options.get("disable_event")): cv.string,
            vol.Optional("rgb_light", default=self.config_entry.options.get("rgb_light")): cv.entity_id,
            vol.Optional("enable_color", default=self.config_entry.options.get("enable_color", [0, 255, 0])): vol.All(cv.ensure_list, [cv.positive_int]),
            vol.Optional("disable_color", default=self.config_entry.options.get("disable_color", [255, 0, 0])): vol.All(cv.ensure_list, [cv.positive_int]),
            vol.Optional("already_color", default=self.config_entry.options.get("already_color", [0, 0, 255])): vol.All(cv.ensure_list, [cv.positive_int]),
            vol.Optional("color_duration", default=self.config_entry.options.get("color_duration", 5)): cv.positive_int,
            vol.Optional("off_delay", default=self.config_entry.options.get("off_delay", 0)): cv.positive_int,
            vol.Optional("brighter_event", default=self.config_entry.options.get("brighter_event")): cv.string,
            vol.Optional("dimmer_event", default=self.config_entry.options.get("dimmer_event")): cv.string
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)
