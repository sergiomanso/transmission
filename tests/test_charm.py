# Copyright 2021 sergiomanso
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import Mock

from charm import TransmissionCharm
from ops.model import ActiveStatus, BlockedStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(TransmissionCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_transmission_layer(self):
        # Test with empty config.
        password = self.harness.charm._stored.password
        expected = {
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
                        "TZ": "Europe/London",
                        "USER": "admin",
                        "PASS": password,
                    },
                }
            },
        }
        self.assertEqual(self.harness.charm._transmission_layer(), expected)
        # And now test with a different value in the redirect-map config option.
        # Disable hook firing first.
        self.harness.disable_hooks()
        self.harness.update_config({"username": "johndoe"})
        expected["services"]["transmission"]["environment"]["USER"] = "johndoe"
        self.assertEqual(self.harness.charm._transmission_layer(), expected)

    def test_on_get_password_action(self):
        # the harness doesn't (yet!) help much with actions themselves
        action_event = Mock()
        self.harness.charm._on_get_password_action(action_event)

    def test_on_config_changed(self):
        plan = self.harness.get_container_pebble_plan("transmission")
        self.assertEqual(plan.to_dict(), {})
        # Trigger a config-changed hook. Since there was no plan initially, the
        # "transmission" service in the container won't be running so we'll be
        # testing the `is_running() == False` codepath.
        self.harness.update_config({
            "username": "john",
            "password": "newpass",
            "timezone": "Europe/Lisbon",
            "whitelist": "127.0.0.1,10.0.0.*",
            "host-whitelist": "localhost,mydomain.com",
            "ui-theme": "/flood-for-transmission/",
        })
        plan = self.harness.get_container_pebble_plan("transmission")
        # Get the expected layer from the transmission_layer method (tested above)
        expected = self.harness.charm._transmission_layer()
        expected.pop("summary", "")
        expected.pop("description", "")
        # Check the plan is as expected
        self.assertEqual(plan.to_dict(), expected)
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
        container = self.harness.model.unit.get_container("transmission")
        self.assertEqual(container.get_service("transmission").is_running(), True)

        # test ingress config changed
        self.harness.update_config({
            "external-url": "transmission.juju",
            "tls-secret-name": "secret"
        })
        expected_ingress_config = self.harness.charm._ingress_config
        self.assertEqual(expected_ingress_config["service-hostname"], "transmission.juju")
        self.assertEqual(expected_ingress_config["tls-secret-name"], "secret")

        # invalid username
        self.harness.update_config({"username": "jo hn"})
        # Get the expected layer from the transmission_layer method (tested above)
        # expected_status = self.harness.charm._transmission_layer()
        self.assertEqual(self.harness.model.unit.status,
                         BlockedStatus("Invalid username defined."))
        # self.assertEqual(expected_status, {'error': 'Invalid username defined.'})

        # invalid timezone
        self.harness.update_config({
            "timezone": "city",
            "username": "john"
        })
        # Get the expected layer from the transmission_layer method (tested above)
        # expected_status = self.harness.charm._transmission_layer()
        self.assertEqual(self.harness.model.unit.status,
                         BlockedStatus("Invalid timezone defined."))

        # invalid ui-theme
        self.harness.update_config({
            "timezone": "Europe/London",
            "ui-theme": "nicetheme"
        })
        # Get the expected layer from the transmission_layer method (tested above)
        # expected_status = self.harness.charm._transmission_layer()
        self.assertEqual(self.harness.model.unit.status,
                         BlockedStatus("Invalid ui theme defined."))
