"""Platform for sensor integration."""
from __future__ import annotations

import uuid
from datetime import timedelta, datetime
from homeassistant.components.sensor import (SensorEntity)
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_registry import async_get, async_entries_for_config_entry
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity, DataUpdateCoordinator, UpdateFailed,
)
from custom_components.pajgps.const import DOMAIN
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=120)
API_URL = "https://connect.paj-gps.de/api/"
VERSION = "0.1.0"

TOKEN = None


class LoginResponse:
    token = None
    userID = None
    routeIcon = None

    def __init__(self, json):
        self.token = json["success"]["token"]
        self.userID = json["success"]["userID"]
        self.routeIcon = json["success"]["routeIcon"]

    def __str__(self):
        return f"token: {self.token}, userID: {self.userID}, routeIcon: {self.routeIcon}"


class ApiError:
    error = None
    def __init__(self, json):
        self.error = json["error"]


class PAJGPSTrackerData:
    # From JSON:
    # {
    #       "lat": 49.02193166666667,
    #       "lng": 12.656183333333333,
    #       "direction": 0,
    #       "battery": 70,
    #       "speed": 0,
    #       "iddevice": 1237050,
    #     }
    lat = None
    lng = None
    direction = None
    battery = None
    speed = None
    iddevice = None

    def __init__(self, json):
        self.lat = json["lat"]
        self.lng = json["lng"]
        self.direction = json["direction"]
        self.battery = json["battery"]
        self.speed = json["speed"]
        self.iddevice = json["iddevice"]

    def __str__(self):
        return f"lat: {self.lat}, lng: {self.lng}, direction: {self.direction}, battery: {self.battery}, speed: {self.speed}, iddevice: {self.iddevice}"



async def get_login_token(email, password):
    # Get login token from HTTP Post request to API_URL/login.
    # Use aiohttp instead of requests to avoid blocking
    # Corresponding CURL command:
    # curl -X 'POST' \
    #   'https://connect.paj-gps.de/api/login?email=EMAIL&password=PASSWORD' \
    #   -H 'accept: application/json' \
    #   -H 'X-CSRF-TOKEN: ' \
    #   -d ''
    # Returns LoginResponse.token or None
    url = API_URL + "login"
    payload = {}
    headers = {
        'accept': 'application/json',
        'X-CSRF-TOKEN': ''
    }
    params = {
        'email': email,
        'password': password
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload, params=params) as response:
            try:
                if response.status == 200:
                    json = await response.json()
                    login_response = LoginResponse(json)
                    return login_response.token
                else:
                    # Handle error using ApiError class
                    json = await response.json()
                    api_error = ApiError(json)
                    _LOGGER.error(f"Error {response.status} while getting login token: {api_error.error}")
                    return None
            except Exception as e:
                _LOGGER.error(f"{e}")
                return None

async def get_devices(token):
    # Get GPS devices from HTTP Get request to API_URL/device.
    # Use aiohttp instead of requests to avoid blocking.
    # Corresponding CURL command:
    # curl -X 'GET' \
    #   'https://connect.paj-gps.de/api/device' \
    #   -H 'accept: application/json' \
    #   -H 'Authorization: Bearer TOKEN' \
    #   -H 'X-CSRF-TOKEN: '
    # Returns dictionary of device id, name, imei and model_nr from response.success.

    url = API_URL + "device"
    payload = {}
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {token}',
        'X-CSRF-TOKEN': ''
    }
    params = {}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, data=payload, params=params) as response:
            try:
                if response.status == 200:
                    json = await response.json()
                    devices = json["success"]
                    results = {}
                    for device in devices:
                        results[device["id"]] = {
                            "id": device["id"],
                            "name": device["name"],
                            "imei": device["imei"],
                            "model_nr": device["model_nr"]
                        }
                    return results
                else:
                    # Handle error using ApiError class
                    json = await response.json()
                    api_error = ApiError(json)
                    _LOGGER.error(f"Error {response.status} while getting devices: {api_error.error}")
                    return None
            except Exception as e:
                _LOGGER.error(f"{e}")
                return None


async def get_device_data(token, device_id):
    # Get GPS data from HTTP Get request to API_URL/trackerdata/{DeviceID}/last_points.
    # Use aiohttp instead of requests to avoid blocking.
    # Corresponding CURL command:
    # curl -X 'GET' \
    #   'https://connect.paj-gps.de/api/trackerdata/{DeviceID}/last_points?lastPoints=1' \
    #   -H 'accept: application/json' \
    #   -H 'Authorization: Bearer TOKEN' \
    #   -H 'X-CSRF-TOKEN: '
    # Returns instance of PAJGPSTrackerData object.

    url = API_URL + f"trackerdata/{device_id}/last_points"
    payload = {}
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {token}',
        'X-CSRF-TOKEN': ''
    }
    params = {
        'lastPoints': 1
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, data=payload, params=params) as response:
            try:
                if response.status == 200:
                    json = await response.json()
                    tracker_data = PAJGPSTrackerData(json["success"][0])
                    return tracker_data
                else:
                    # Handle error using ApiError class
                    json = await response.json()
                    api_error = ApiError(json)
                    _LOGGER.error(f"Error {response.status} while getting device data: {api_error.error}")
                    return None
            except Exception as e:
                _LOGGER.error(f"{e}")
                return None

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Add sensors for passed config_entry in HA."""
    # Check if email and password are set. Throw exception if not.
    if config_entry.data["email"] == None or config_entry.data["password"] == None:
        _LOGGER.error("Email or password not set")
        return

    # Get Authoization token
    token = await get_login_token(config_entry.data["email"], config_entry.data["password"])
    if token == None:
        _LOGGER.error("Could not get login token")
        return
    # Get devices
    devices = await get_devices(token)
    if devices == None:
        _LOGGER.error("Could not get devices")
        return
    # Add sensors
    to_add = []
    for device_id, device in devices.items():
        to_add.append(PajGpsSensor(device_id, "mdi:map-marker", f"PAJ GPS {device_id}", token))
    async_add_entities(to_add, update_before_add=True)


# Define a GPS tracker sensor/device class for Home Assistant
class PajGpsSensor(TrackerEntity):

    _last_data = None

    def __init__(self, gps_id: str, icon:str, name: str, token: str):
        self._gps_id = gps_id
        self._token = token
        self._attr_icon = icon
        self._attr_name = name
        self._attr_unique_id = f'pajgps_{gps_id}'
        self._attr_extra_state_attributes = {}

        #self._attr_device_info = DeviceInfo(
        #    entry_type=DeviceEntryType.SERVICE,
        #    identifiers={(DOMAIN, str(gps_id))},
        #    default_name="PAJ GPS Tracker",
        #    default_manufacturer="PAJ GPS",
        #    sw_version=VERSION,
        #)

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        # If _last_data is not None, return latitude from _last_data. Else return None.
        if self._last_data is not None:
            return self._last_data.lat
        else:
            return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        # If _last_data is not None, return longitude from _last_data. Else return None.
        if self._last_data is not None:
            return self._last_data.lng
        else:
            return None

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the device."""
        # If _last_data is not None, return battery level from _last_data. Else return None.
        if self._last_data is not None:
            return self._last_data.battery
        else:
            return None

    async def refresh_token(self):
        global TOKEN
        self._token = await get_login_token(self.hass.config_entries.async_entries(DOMAIN)[0].data["email"],
                                           self.hass.config_entries.async_entries(DOMAIN)[0].data["password"])
        TOKEN = self._token
    async def async_update(self) -> None:
        global TOKEN
        """Fetch new state data for the sensor."""
        # Get the GPS data from the API
        try:
            await self.refresh_token()
            tracker_data = await get_device_data(TOKEN, self._gps_id)
            if tracker_data is not None:
                self._last_data = tracker_data
            else:
                _LOGGER.error(f"No data for PAJ GPS device {self._gps_id}")

        except Exception as e:
            _LOGGER.error(f'{e}')
            self._attr_native_value = None