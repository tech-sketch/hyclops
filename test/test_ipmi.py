# HyClops for Zabbix
# Copyright 2013 TIS Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import unittest
import logging
import subprocess

import configobj
from mock import patch, Mock
from hyclops.connector.ipmi import IPMIConnector
from .mock_zabbix import MockZabbixAPI


class TestIPMIConnector(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger('hyclops.connector.ipmi')
        logger.addHandler(logging.NullHandler())
        self.patchers = [
            patch('hyclops.connector.base.ZabbixAPI', new=MockZabbixAPI),
            patch('subprocess.check_output')
        ]
        for patcher in self.patchers:
            patcher.start()
        config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test.conf")
        self.config = configobj.ConfigObj(config_path, file_error=True)
        self.connector = IPMIConnector(config=self.config)
        self.connector.zabbix_api = MockZabbixAPI()
        self._set_zabbix_mock()

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def _set_zabbix_mock(self):
        zabbix_api = self.connector.zabbix_api
        # create IPMI Group
        response = zabbix_api.hostgroup.create({
            "name": "IPMI"
        })
        groupid_ipmi = response["groupids"][0]
        # create IPMI Template
        response = zabbix_api.template.create({
            "host": "IPMI",
            "groups": [{"groupid": groupid_ipmi}],
            "macros": [],
        })
        templateid_ipmi = response["templateids"][0]
        # create IPMI Host
        zabbix_api.host.create({
            "host": "IPMIHost",
            "interfaces": [
                {"type": 3, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 623},
            ],
            "ipmi_available": 1,
            "ipmi_authtype": 6,
            "ipmi_username": "username",
            "ipmi_password": "password",
            "groups": [{"groupid": groupid_ipmi}],
            "parentTemplates": [{"templateid": templateid_ipmi}],
            "inventory": [],
            "macros": {
                "1": {"macro": "{$KEY}", "value": "key"},
                "2": {"macro": "{$SECRET}", "value": "secret"},
            },
        })
        # create NoIPMIInterface Host
        zabbix_api.host.create({
            "host": "NoIPMIInterface",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
            ],
            "ipmi_available": 1,
            "ipmi_authtype": 6,
            "ipmi_username": "username",
            "ipmi_password": "password",
            "groups": [{"groupid": groupid_ipmi}],
            "parentTemplates": [{"templateid": templateid_ipmi}],
            "inventory": [],
            "macros": {
                "1": {"macro": "{$KEY}", "value": "key"},
                "2": {"macro": "{$SECRET}", "value": "secret"},
            },
        })

    def test_init(self):
        self.assertIsInstance(self.connector, IPMIConnector)
        self.assertIsInstance(self.connector.zabbix_api, MockZabbixAPI)
        self.assertEqual(self.connector.type, "ipmi")

    def test_call(self):
        self.connector.logger = Mock(debug=Mock(), warning=Mock(), error=Mock())
        self.connector.run_command = Mock(return_value=True)
        self.connector(hostname="IPMIHost", params={})
        self.connector.logger.debug.assert_called()
        self.connector.run_command = Mock(return_value=False)
        self.connector(hostname="IPMIHost", params={"command": "start"})
        self.connector.logger.warning.assert_called()
        self.connector.run_command = Mock(side_effect=RuntimeError())
        self.connector(hostname="not found", params={})
        self.connector.logger.error.assert_called()

    def test_run_command(self):
        correct_messages = [
            {"hostname": "IPMIHost", "params": {"command": "monitor"}},
            {"hostname": "IPMIHost", "params": {"command": "reboot"}},
            {"hostname": "IPMIHost", "params": {"command": "start"}},
            {"hostname": "IPMIHost", "params": {"command": "stop"}},
        ]
        invalid_messages = [
            {"hostname": "IPMIHost", "params": {"command": "invalid"}},
            {"hostname": "NotExist", "params": {"command": "stop"}},
        ]
        self.connector.monitor = Mock(return_value=True)
        for message in correct_messages:
            self.assertTrue(self.connector.run_command(**message))
        for message in invalid_messages:
            self.assertFalse(self.connector.run_command(**message))

    def test_run_ipmi_tool(self):
        with patch('subprocess.Popen.communicate') as m:
            m.return_value = ("output", "error")
            result = self.connector.run_ipmitool(command="start", ipmi_ip="127.0.0.1", key="username", secret="password")
            self.assertEqual(result, "output")
            m.side_effect = subprocess.CalledProcessError(returncode=1, cmd="ipmitool")
            result = self.connector.run_ipmitool(command="start", ipmi_ip="127.0.0.1", key="username", secret="password")
            self.assertIsNone(result)

    def test_get_connection_parameters(self):
        result = self.connector.get_connection_parameters(hostname="IPMIHost")
        self.assertDictEqual(result, {"ipmi_ip": "127.0.0.1", "key": "username", "secret": "password"})
        result = self.connector.get_connection_parameters(hostname="NoIPMIInterface")
        self.assertIsNone(result)
        result = self.connector.get_connection_parameters(hostname="not found")
        self.assertIsNone(result)

    def test_monitor(self):
        self.connector.zabbix_sender = Mock(return_value=True)
        self.connector.run_ipmitool = Mock(return_value="Chassis Power is on")
        result = self.connector.monitor(hostname="IPMIHost", conn_params={"ipmi_ip": "127.0.0.1", "key": "username", "secret": "password"})
        self.assertTrue(result)
        self.connector.run_ipmitool = Mock(return_value="Chassis Power is off")
        result = self.connector.monitor(hostname="IPMIHost", conn_params={"ipmi_ip": "127.0.0.1", "key": "username", "secret": "password"})
        self.assertTrue(result)
        self.connector.run_ipmitool = Mock(return_value="")
        result = self.connector.monitor(hostname="IPMIHost", conn_params={"ipmi_ip": "127.0.0.1", "key": "username", "secret": "password"})
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
