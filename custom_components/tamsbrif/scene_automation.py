import logging
import voluptuous as vol

from homeassistant.helpers import config_validation as cv
from homeassistant.components.scene import DOMAIN as SCENE_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN, ATTR_RGB_COLOR, ATTR_BRIGHTNESS, SERVICE_TURN_ON
from homeassistant.const import CONF_ENTITY_ID, EVENT_STATE_CHANGED, CONF_EVENT, STATE_ON, STATE_OFF
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tamsbrif"

CONF_NIGHT_SCENE = "night_scene"
CONF_EARLY_MORNING_SCENE = "early_morning_scene"
CONF_MORNING_SCENE = "morning_scene"
CONF_DAY_SCENE = "day_scene"
CONF_EARLY_EVENING_SCENE = "early_evening_scene"
CONF_EVENING_SCENE = "evening_scene"
CONF_LATE_EVENING_SCENE = "late_evening_scene"
CONF_EARLY_NIGHT_SCENE = "early_night_scene"
CONF_OFF_SCENE = "off_scene"
CONF_SENSOR = "binary_sensor"
CONF_DISABLE_SENSOR = "disable_sensor"
CONF_ENABLE_EVENT = "enable_event"
CONF_DISABLE_EVENT = "disable_event"
CONF_RGB_LIGHT = "rgb_light"
CONF_ENABLE_COLOR = "enable_color"
CONF_DISABLE_COLOR = "disable_color"
CONF_ALREADY_COLOR = "already_color"
CONF_COLOR_DURATION = "color_duration"
CONF_OFF_DELAY = "off_delay"
DEFAULT_OFF_DELAY = 0  # Default delay is 0 seconds
CONF_BRIGHTER_EVENT = "brighter_event"
CONF_DIMMER_EVENT = "dimmer_event"

DEFAULT_ENABLE_COLOR = [0, 255, 0]  # Green
DEFAULT_DISABLE_COLOR = [255, 0, 0]  # Red
DEFAULT_ALREADY_COLOR = [0, 0, 255]  # Blue
DEFAULT_COLOR_DURATION = 5  # seconds

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_NIGHT_SCENE): cv.entity_id,
        vol.Required(CONF_EARLY_MORNING_SCENE): cv.entity_id,
        vol.Required(CONF_MORNING_SCENE): cv.entity_id,
        vol.Required(CONF_DAY_SCENE): cv.entity_id,
        vol.Required(CONF_EARLY_EVENING_SCENE): cv.entity_id,
        vol.Required(CONF_EVENING_SCENE): cv.entity_id,
        vol.Required(CONF_LATE_EVENING_SCENE): cv.entity_id,
        vol.Required(CONF_EARLY_NIGHT_SCENE): cv.entity_id,
        vol.Required(CONF_OFF_SCENE): cv.entity_id,
        vol.Required(CONF_SENSOR): cv.entity_id,
        vol.Optional(CONF_DISABLE_SENSOR): cv.entity_id,
        vol.Optional(CONF_ENABLE_EVENT): cv.string,
        vol.Optional(CONF_DISABLE_EVENT): cv.string,
        vol.Optional(CONF_RGB_LIGHT): cv.entity_id,
        vol.Optional(CONF_ENABLE_COLOR, default=DEFAULT_ENABLE_COLOR): vol.All(cv.ensure_list, [cv.positive_int]),
        vol.Optional(CONF_DISABLE_COLOR, default=DEFAULT_DISABLE_COLOR): vol.All(cv.ensure_list, [cv.positive_int]),
        vol.Optional(CONF_ALREADY_COLOR, default=DEFAULT_ALREADY_COLOR): vol.All(cv.ensure_list, [cv.positive_int]),
        vol.Optional(CONF_COLOR_DURATION, default=DEFAULT_COLOR_DURATION): cv.positive_int,
        vol.Optional(CONF_OFF_DELAY, default=DEFAULT_OFF_DELAY): cv.positive_int,
        vol.Optional(CONF_BRIGHTER_EVENT): cv.string,
        vol.Optional(CONF_DIMMER_EVENT): cv.string
    })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, config):
    conf = config[DOMAIN]
    scenes = {
        "binary_sensor.night_tod": conf[CONF_NIGHT_SCENE],
        "binary_sensor.early_morning_tod": conf[CONF_EARLY_MORNING_SCENE],
        "binary_sensor.morning_tod": conf[CONF_MORNING_SCENE],
        "binary_sensor.day_tod": conf[CONF_DAY_SCENE],
        "binary_sensor.early_evening_tod": conf[CONF_EARLY_EVENING_SCENE],
        "binary_sensor.evening_tod": conf[CONF_EVENING_SCENE],
        "binary_sensor.late_evening_tod": conf[CONF_LATE_EVENING_SCENE],
        "binary_sensor.early_night_tod": conf[CONF_EARLY_NIGHT_SCENE]
    }
    off_scene = conf[CONF_OFF_SCENE]
    motion_sensor = conf[CONF_SENSOR]
    disable_sensor = conf.get(CONF_DISABLE_SENSOR)
    enable_event = conf.get(CONF_ENABLE_EVENT)
    disable_event = conf.get(CONF_DISABLE_EVENT)
    rgb_light = conf.get(CONF_RGB_LIGHT)
    enable_color = conf[CONF_ENABLE_COLOR]
    disable_color = conf[CONF_DISABLE_COLOR]
    already_color = conf[CONF_ALREADY_COLOR]
    color_duration = conf[CONF_COLOR_DURATION]
    off_delay = conf[CONF_OFF_DELAY]
    brighter_event = conf.get(CONF_BRIGHTER_EVENT)
    dimmer_event = conf.get(CONF_DIMMER_EVENT)

    motion_enabled = True
    off_scene_timer = None
    scene_offset = 0

    async def set_light_color(color, restore_state=True):
        if rgb_light:
            # Save current state of the light
            current_state = hass.states.get(rgb_light)
            if current_state:
                _LOGGER.info("Saving current state of RGB light %s", rgb_light)
                state_attrs = current_state.attributes
                saved_state = {
                    ATTR_RGB_COLOR: state_attrs.get(ATTR_RGB_COLOR, [255, 255, 255]),
                    ATTR_BRIGHTNESS: state_attrs.get(ATTR_BRIGHTNESS, 255)
                }

                _LOGGER.info("Setting RGB light %s to color %s", rgb_light, color)
                await hass.services.async_call(
                    LIGHT_DOMAIN, SERVICE_TURN_ON, {
                        CONF_ENTITY_ID: rgb_light,
                        ATTR_RGB_COLOR: color,
                        ATTR_BRIGHTNESS: 255
                    }
                )

                if restore_state:
                    async def restore_light(_):
                        _LOGGER.info("Restoring RGB light %s to previous state", rgb_light)
                        await hass.services.async_call(
                            LIGHT_DOMAIN, SERVICE_TURN_ON, {
                                CONF_ENTITY_ID: rgb_light,
                                ATTR_RGB_COLOR: saved_state[ATTR_RGB_COLOR],
                                ATTR_BRIGHTNESS: saved_state[ATTR_BRIGHTNESS]
                            }
                        )

                    async_call_later(hass, color_duration, restore_light)

    async def activate_scene(scene):
        _LOGGER.info("Activating scene: %s", scene)
        await hass.services.async_call(SCENE_DOMAIN, "turn_on", {CONF_ENTITY_ID: scene})

    async def adjust_scene(offset_change):
        nonlocal scene_offset
        scene_offset += offset_change
        scene_offset = max(min(scene_offset, len(scenes) - 1), -(len(scenes) - 1))
        _LOGGER.info("Adjusted scene offset to %d", scene_offset)
        current_tod_sensor = None
        for tod_sensor, scene in scenes.items():
            tod_state = hass.states.get(tod_sensor)
            if tod_state is not None and tod_state.state == "on":
                current_tod_sensor = tod_sensor
                break

        if current_tod_sensor:
            current_index = list(scenes.keys()).index(current_tod_sensor)
            new_index = current_index + scene_offset
            new_index = max(0, min(new_index, len(scenes) - 1))
            await activate_scene(list(scenes.values())[new_index])

    @callback
    async def handle_motion(event):
        nonlocal off_scene_timer
        if not motion_enabled:
            _LOGGER.info("Motion activation is disabled.")
            return

        new_state = event.data.get("new_state")
        if new_state is None:
            return

        if disable_sensor:
            disable_state = hass.states.get(disable_sensor)
            if disable_state is not None and disable_state.state == "on":
                _LOGGER.info("Disable sensor %s is on, motion activation is disabled.", disable_sensor)
                return

        if new_state.state == "on":
            _LOGGER.info("Motion sensor turned on, checking tod sensors for appropriate scene.")
            if off_scene_timer:
                off_scene_timer()
                off_scene_timer = None
            for tod_sensor, scene in scenes.items():
                tod_state = hass.states.get(tod_sensor)
                if tod_state is not None and tod_state.state == "on":
                    await activate_scene(scene)
                    break
        elif new_state.state == "off":
            _LOGGER.info("Motion sensor turned off, delaying off scene activation by %s seconds.", off_delay)
            off_scene_timer = async_call_later(hass, off_delay, lambda _: hass.async_create_task(activate_scene(off_scene)))

    @callback
    async def handle_disable_sensor(event):
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None or old_state is None:
            return

        if old_state.state == "on" and new_state.state == "off":
            motion_state = hass.states.get(motion_sensor)
            if motion_state is not None and motion_state.state == "on":
                _LOGGER.info("Disable sensor turned off and motion detected, checking tod sensors for appropriate scene.")
                for tod_sensor, scene in scenes.items():
                    tod_state = hass.states.get(tod_sensor)
                    if tod_state is not None and tod_state.state == "on":
                        await activate_scene(scene)
                        break
            else:
                _LOGGER.info("Disable sensor turned off and no motion detected, activating off scene: %s", off_scene)
                await activate_scene(off_scene)

    @callback
    async def handle_enable_event(event):
        nonlocal motion_enabled
        if motion_enabled:
            _LOGGER.info("Enable event triggered but motion activation is already enabled, setting light to already color.")
            await set_light_color(already_color)
        else:
            _LOGGER.info("Enable event triggered, enabling motion activation and setting light to enable color.")
            motion_enabled = True
            await set_light_color(enable_color)

    @callback
    async def handle_disable_event(event):
        nonlocal motion_enabled
        if not motion_enabled:
            _LOGGER.info("Disable event triggered but motion activation is already disabled, setting light to already color.")
            await set_light_color(already_color)
        else:
            _LOGGER.info("Disable event triggered, disabling motion activation and setting light to disable color.")
            motion_enabled = False
            await set_light_color(disable_color)

    if enable_event:
        hass.bus.async_listen(enable_event, handle_enable_event)
    if disable_event:
        hass.bus.async_listen(disable_event, handle_disable_event)

    async_track_state_change_event(hass, motion_sensor, handle_motion)

    if disable_sensor:
        async_track_state_change_event(hass, disable_sensor, handle_disable_sensor)

    return True