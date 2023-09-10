#  PAJ GPS Tracker Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/skipperro/pajgps-homeassistant.svg)](https://GitHub.com/skipperro/pajgps-homeassistant/releases/)
![](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.pajgps.total)


This integration allows you to use PAJ GPS devices (www.paj-gps.de) in Home Assistant.

## Disclaimer

This integration is not official software from PAJ GPS.
It's a custom integration created entirely by me (Skipperro), and thus PAJ UG is not responsible for any damage/issues caused by this integration, nor it offers any end-user support for it.

## Features

- [x] Device tracking (Longitude, Latitude)
- [x] Device battery level

## Supported devices

This integration was tested only with single **Allround Finder 2G 2.0**, but it is using standard API provided by PAJ, so it should work with other devices. Please report an issue if you will find any problems with other devices. 

## Installation

1. **Make a proper setup of your PAJ GPS device**. You need to have an account on www.v2.finder-portal.com and your device must be properly configured and connected to the platform.
2. Install this integration with HACS (adding this repository may be required), or copy the contents of this
repository into the `custom_components/pajgps` directory.
2. Restart Home Assistant.
3. Start the configuration flow:
   - [![Start Config Flow](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=pajgps)
   - Or: Go to `Configuration` -> `Integrations` and click the `+ Add Integration`. Select `PAJ GPS` from the list.
   - If the integration is not found try to refresh the HA page without using cache (Ctrl+F5).
4. Provide your email and password used to login on www.v2.finder-portal.com. This data will be saved only in your Home Assistant and is required to generate API token.
5. Device Tracker Entities will be created for all your devices.

## Configuration

The integration will automatically discover all your devices connected to your account on www.v2.finder-portal.com. 
They will be added as entities to Home Assistant based on their ID from the API (not the number on the device).