#!/usr/bin/env python3
# Copyright 2021 sergiomanso
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging
import re
import pytz
import string
import secrets

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus


logger = logging.getLogger(__name__)


class TransmissionCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.get_password_action, self._on_get_password_action)

        self.ingress = IngressRequires(self, self._ingress_config)
        self._stored.set_default(
            external_url=self.app.name,
            tls_secret_name="",
            username="admin",
            timezone="Europe/London",
            password=self._generate_password(),
        )

    def _on_config_changed(self, event):
        """Just an example to show how to deal with changed configuration.

        Learn more about config at https://juju.is/docs/sdk/config
        """

        container = self.unit.get_container("transmission")

        layer = self._transmission_layer()

        if "error" in layer:
            self.unit.status = BlockedStatus(layer["error"])
            logger.warning(layer["error"])
            return

        if "external-url" in self.model.config and \
                self.model.config["external-url"] != self._stored.external_url:
            self._stored.external_url = self.model.config["external-url"]
            self.ingress.update_config(self._ingress_config)

        if "tls-secret-name" in self.model.config and \
                self.model.config["tls-secret-name"] != self._stored.tls_secret_name:
            self._stored.tls_secret_name = self.model.config["tls-secret-name"]
            self.ingress.update_config(self._ingress_config)

        plan = container.get_plan()

        if plan.services != layer["services"]:
            container.add_layer("transmission", layer, combine=True)
            logger.info("Added updated layer 'transmission' to Pebble plan")

            if container.get_service("transmission").is_running():
                container.stop("transmission")

            container.start("transmission")
            logging.info("Restarted transmission service")

        self.unit.status = ActiveStatus()

    def _generate_password(self):
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(10))

    def _transmission_layer(self):

        # username validation
        if not re.match("^[a-zA-Z0-9_.-]+$", self._username):
            return {"error": "Invalid username defined."}

        # password handling
        if 'password' in self.model.config:
            self._stored.password = self.model.config["password"]

        # timezone validation
        if "timezone" in self.model.config and \
                self.model.config["timezone"] not in pytz.all_timezones:
            return {"error": "Invalid timezone defined."}

        layer = {
            "summary": "transmission layer",
            "description": "pebble config layer for transmission",
            "services": {
                "transmission": {
                    "override": "replace",
                    "summary": "transmission",
                    "command": "/init",
                    "startup": "enabled",
                    "environment": {
                        "PUID": 1000,
                        "PGID": 1000,
                        "TZ": self._timezone,
                        "USER": self._username,
                        "PASS": self._password,
                    }
                }
            },
        }

        # optional configurations
        if "ui-theme" in self.model.config:
            if self.model.config["ui-theme"] in self._ui_themes:
                layer["services"]["transmission"]["environment"]["TRANSMISSION_WEB_HOME"] = \
                    self.model.config["ui-theme"]
            else:
                return {"error": "Invalid ui theme defined."}
        # no validation for ips
        if "whitelist" in self.model.config:
            layer["services"]["transmission"]["environment"]["WHITELIST"] = \
                self.model.config["whitelist"]
        # no validation for the FQDNs
        if "host-whitelist" in self.model.config:
            layer["services"]["transmission"]["environment"]["HOST_WHITELIST"] = \
                self.model.config["host-whitelist"]

        return layer

    def _on_get_password_action(self, event):
        return event.set_results({"password": self._password})

    @property
    def _username(self):
        return self.config.get("username") or self._stored.username

    @property
    def _password(self):
        return self.config.get("password") or self._stored.password

    @property
    def _timezone(self):
        return self.config.get("timezone") or self._stored.timezone

    @property
    def _ui_themes(self):
        return ["/combustion-release/", "/transmission-web-control/",
                "/kettu/", "/flood-for-transmission/"]

    @property
    def _external_url(self):
        return self.config.get("external-url") or self.app.name

    @property
    def _ingress_config(self):
        ingress_config = {
            "service-hostname": self._external_url,
            "service-name": self.app.name,
            "service-port": 9091,
        }
        tls_secret_name = self.config.get("tls-secret-name")
        if tls_secret_name:
            ingress_config["tls-secret-name"] = tls_secret_name
        return ingress_config


if __name__ == "__main__":
    main(TransmissionCharm)
