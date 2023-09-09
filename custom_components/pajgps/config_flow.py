"""Config flow for PAJ GPS Tracker integration."""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

big_int = vol.All(vol.Coerce(int), vol.Range(min=300))

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = vol.Schema(
            {
                vol.Required('email', default=''): cv.string,
                vol.Required('password', default=''): cv.string,
            }
        )

class CustomFlow(config_entries.ConfigFlow, domain=DOMAIN):
    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        errors: Dict[str, str] = {}
        if user_input is not None:
            self.data = user_input
            # If email is null or empty string, add error
            if not self.data['email'] or self.data['email'] == '':
                errors['base'] = 'email_required'
            # If password is null or empty string, add error
            if not self.data['password'] or self.data['password'] == '':
                errors['base'] = 'password_required'
            if not errors:
                return self.async_create_entry(title="PAJ GPS Tracker", data=self.data)

        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        errors: Dict[str, str] = {}

        if user_input is not None:
            self.data = user_input
            # If email is null or empty string, add error
            if not self.data['email'] or self.data['email'] == '':
                errors['base'] = 'email_required'
            # If password is null or empty string, add error
            if not self.data['password'] or self.data['password'] == '':
                errors['base'] = 'password_required'
            if not errors:
                return self.async_create_entry(title="PAJ GPS Tracker", data={'email': user_input['email'], 'password': user_input['password']})

        default_email = ''
        if 'email' in self.config_entry.data:
            default_email = self.config_entry.data['email']
        if 'email' in self.config_entry.options:
            default_email = self.config_entry.options['email']
        default_password = False
        if 'password' in self.config_entry.data:
            default_password = self.config_entry.data['password']
        if 'password' in self.config_entry.options:
            default_password = self.config_entry.options['password']

        OPTIONS_SCHEMA = vol.Schema(
            {
                vol.Required('email', default=default_email): cv.string,
                vol.Required('password', default=default_password): cv.string,
            }
        )
        return self.async_show_form(step_id="init", data_schema=OPTIONS_SCHEMA, errors=errors)
