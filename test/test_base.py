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
import re
import logging
import configobj
from mock import patch, Mock
from zabbix_api import ZabbixAPIException
from hyclops.connector.base import BaseConnector
from .mock_zabbix import MockZabbixAPI


class TestBaseConnector(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger('hyclops.connector.base')
        logger.addHandler(logging.NullHandler())
        self.patcher = patch('hyclops.connector.base.ZabbixAPI', new=MockZabbixAPI)
        self.patcher.start()
        config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test.conf")
        self.config = configobj.ConfigObj(config_path, file_error=True)
        self.connector = BaseConnector(config=self.config)
        self.connector.zabbix_api = MockZabbixAPI()
        self._create_zabbix_mock()

    def tearDown(self):
        self.patcher.stop()

    def _create_zabbix_mock(self):
        zabbix_api = self.connector.zabbix_api
        # create AWSAccount Group
        response = zabbix_api.hostgroup.create({
            "name": "AWSAccount"
        })
        groupid_aws_account = response["groupids"][0]
        # create AmazonEC2 Group
        response = zabbix_api.hostgroup.create({
            "name": "AmazonEC2"
        })
        groupid_amazon_ec2 = response["groupids"][0]
        # create AWSAccount Template
        response = zabbix_api.template.create({
            "host": "AWSAccount",
            "groups": [{"groupid": groupid_aws_account}],
            "macros": [
                {"macro": "{$VM_GROUPS}", "value": "AmazonEC2"},
                {"macro": "{$REQUIRED_TEMPLATES}", "value": "AmazonEC2"},
                {"macro": "{$VM_TEMPLATES}", "value": "Template App Zabbix Agent"},
                {"macro": "{$VM_TEMPLATES_LINUX}", "value": "Template OS Linux"},
                {"macro": "{$VM_TEMPLATES_WINDOWS}", "value": "Template OS Windows"},
            ]
        })
        templateid_aws_account = response["templateids"][0]
        # create AmazonEC2 Template
        response = zabbix_api.template.create({
            "host": "AmazonEC2",
            "groups": [{"groupid": groupid_amazon_ec2}],
        })
        templateid_amazon_ec2 = response["templateids"][0]
        # create Template OS Linux
        response = zabbix_api.template.create({
            "host": "Template OS Linux",
            "groups": [],
        })
        # create Template OS Windows
        response = zabbix_api.template.create({
            "host": "Template OS Windows",
            "groups": [],
        })
        # create Template App Zabbix Agent
        response = zabbix_api.template.create({
            "host": "Template App Zabbix Agent",
            "groups": [],
        })
        # create AWS Host
        zabbix_api.host.create({
            "host": "AWS",
            "interfaces": [
                {"interfaceid": 1, "type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
            ],
            "groups": [{"groupid": groupid_aws_account}],
            "parentTemplates": [{"templateid": templateid_aws_account}],
            "inventory": [],
            "macros": {
                "1": {"macro": "{$KEY}", "value": "key"},
                "2": {"macro": "{$SECRET}", "value": "secret"},
            },
        })
        # create EC2Instance(i-aaaaaaaa) Host
        zabbix_api.host.create({
            "host": "i-aaaaaaaa",
            "name": "AWS_EC2Instance",
            "interfaces": [
                {"interfaceid": 1, "type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
                {"interfaceid": 2, "type": 2, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161},
            ],
            "groups": [{"groupid": groupid_amazon_ec2}],
            "parentTemplates": [{"templateid": templateid_amazon_ec2}],
            "inventory": {
                "name": "EC2Instance",
                "type": "ec2",
                "tag": "AWS",
                "location": "us-east-1",
                "serialno_a": "i-aaaaaaaa",
            },
            "macros": [],
        })
        # create Global Macro
        zabbix_api.usermacro.create({
            "globalmacro": True,
            "macro": "{$GLOBAL}",
            "value": "global macro",
        })
        zabbix_api.usermacro.create({
            "globalmacro": True,
            "macro": "{$GLOBAL2}",
            "value": "global macro 2",
        })

    def test_init(self):
        self.assertIsInstance(self.connector.config, configobj.ConfigObj)
        self.assertIsInstance(self.connector.logger, logging.Logger)
        self.assertEqual(self.connector.zabbix_server, '127.0.0.1')
        self.assertEqual(self.connector.zabbix_port, '10051')
        self.assertEqual(self.connector.zabbix_sender_path, '/usr/bin/zabbix_sender')
        self.assertIsInstance(self.connector.zabbix_api, MockZabbixAPI)

        with self.assertRaises(KeyError):
            connector = BaseConnector(config=configobj.ConfigObj("wrong_path"))
        with patch('hyclops.connector.base.ZabbixAPI.login') as m:
            m.side_effect = ZabbixAPIException()
            with self.assertRaises(ZabbixAPIException):
                connector = BaseConnector(config=self.config)
            m.side_effect = Exception()
            with self.assertRaises(Exception):
                connector = BaseConnector(config=self.config)

    def test_call(self):
        with self.assertRaises(NotImplementedError):
            self.connector("hostname", {})

    def test_escape_shell_args(self):
        test_data = ["'",
                     None,
                     "string",
                     [],
                     [None],
                     ["str1", "str2"],
                     ("str1",),
                     (None, None),
                     ("cat", "'; echo 'command injection'; '",)]
        for data in test_data:
            escaped_args = self.connector.escape_shell_args(data)
            self.assertIsInstance(escaped_args, tuple)
            for arg in escaped_args:
                self.assertIsInstance(arg, str)
                self.assertTrue(re.match(r'^\'(.*)\'$', str(arg)))

    def test_zabbix_sender(self):
        test_data = [
            {"zabbix_hostname": None, "key": None, "value": None},
            {"zabbix_hostname": [], "key": {}, "value": (None,)},
            {"zabbix_hostname": "TestHost", "key": "item.key", "value": None},
            {"zabbix_hostname": "TestHost", "key": "item.key", "value": 0},
            {"zabbix_hostname": "TestHost", "key": "item.key", "value": "string"},
            {"zabbix_hostname": "TestHost", "key": "item.key", "value": ["array", None]},
            {"zabbix_hostname": "TestHost", "key": "item.key", "value": {"dict": "string", "none": None}},
        ]
        with patch('os.system') as m:
            m.return_value = 0
            for data in test_data:
                try:
                    self.connector.zabbix_sender(**data)
                except:
                    self.fail("Unexpected Error")
            m.return_value = 1
            for data in test_data:
                with self.assertRaises(Exception):
                    self.connector.zabbix_sender(**data)

    def test_addresses_to_interfaces(self):
        test_data = [
            # one addresses
            {"params": {"addresses": ["127.0.0.1"]},
             "expect": [{"type": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050, "main": 1},
                        {"type": 2, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161, "main": 1}]},
            # two addresses
            {"params": {"addresses": ["127.0.0.1", "localhost.localdomain"]},
             "expect": [{"type": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050, "main": 1},
                        {"type": 2, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161, "main": 1},
                        {"type": 1, "useip": 0, "ip": "", "dns": "localhost.localdomain", "port": 10050, "main": 0},
                        {"type": 2, "useip": 0, "ip": "", "dns": "localhost.localdomain", "port": 161, "main": 0}]},
            # one address with interface_types
            {"params": {"addresses": ["127.0.0.1"], "interface_types": [1]},
             "expect": [{"type": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050, "main": 1}]},
            # one address with main flag
            {"params": {"addresses": ["127.0.0.1"], "main": False},
             "expect": [{"type": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050, "main": 0},
                        {"type": 2, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161, "main": 0}]},
            # not list
            {"params": {"addresses": "127.0.0.1"},
             "expect": [{"type": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050, "main": 1},
                        {"type": 2, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161, "main": 1}]},
            # empty addresses
            {"params": {"addresses": [], "interface_types": [1]},
             "expect": [{"type": 1, "useip": 0, "ip": "", "dns": "dummy-interface.invalid", "port": 10050, "main": 1}]},
            # invalid addresses
            {"params": {"addresses": [None, ""], "interface_types": [1]},
             "expect": [{"type": 1, "useip": 0, "ip": "", "dns": "dummy-interface.invalid", "port": 10050, "main": 1}]},
        ]
        for data in test_data:
            interfaces = self.connector.addresses_to_interfaces(**data["params"])
            self.assertListEqual(interfaces, data["expect"])

    def test_interfaces_to_addresses(self):
        test_data = [
            # not list
            {"params": {"interfaces": {"interfaceid": 1, "hostid": 10002, "dns": "", "ip": "127.0.0.1",
                                       "main": 1, "type": 1, "useip": 1, "port": 10050}},
             "expect": ["127.0.0.1"]},
            # two interfaces
            {"params": {"interfaces": [{"interfaceid": 1, "hostid": 10002, "dns": "", "ip": "127.0.0.1",
                                        "main": 1, "type": 1, "useip": 1, "port": 10050},
                                       {"interfaceid": 2, "hostid": 10002, "dns": "localhost.localdomain", "ip": "",
                                        "main": 0, "type": 1, "useip": 0, "port": 10050}]},
             "expect": ["127.0.0.1", "localhost.localdomain"]},
            # not dict
            {"params": {"interfaces": ["127.0.0.1"]},
             "expect": []},
            # invalid dict
            {"params": {"interfaces": [{"aaa": "bbb"}]},
             "expect": []},
        ]
        for data in test_data:
            addresses = self.connector.interfaces_to_addresses(**data["params"])
            self.assertListEqual(addresses, data["expect"])

    def test_get_zabbix_host(self):
        result = self.connector.get_zabbix_host("i-aaaaaaaa")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["host"], "i-aaaaaaaa")

    def test_get_zabbix_interfaces(self):
        # host exist
        result = self.connector.get_zabbix_interfaces("AWS", interface_type=1, main=True)
        self.assertListEqual(result, [{"interfaceid": 1, "hostid": 10006, "dns": "", "ip": "127.0.0.1",
                                       "main": 1, "type": 1, "useip": 1, "port": 10050}])
        # host does not exist
        result = self.connector.get_zabbix_interfaces("not exist")
        self.assertListEqual(result, [])

    def test_get_user_macro(self):
        test_data = [
            {"params": {"hostname": "AWS", "key": "{$KEY}"},
             "expect": "key"},
            {"params": {"hostname": "AWS", "key": "{$SECRET}"},
             "expect": "secret"},
            {"params": {"hostname": "AWS", "key": "{$VM_TEMPLATES_LINUX}"},
             "expect": "Template OS Linux"},
            {"params": {"hostname": "AWS", "key": "{$GLOBAL}"},
             "expect": "global macro"},
            {"params": {"hostname": "AWS", "key": "not found"},
             "expect": None},
            {"params": {"hostname": "not found", "key": "not found"},
             "expect": None},
            {"params": {"hostname": "AWS", "key": None},
             "expect": None},
        ]
        for data in test_data:
            result = self.connector.get_user_macro(**data["params"])
            self.assertEqual(result, data["expect"])

    def test_get_group_ids(self):
        test_data = [
            {"params": {"owner_hostname": "AWS", "key": "{$VM_GROUPS}"},
             "expect": [{"groupid": 2}]},
            {"params": {"owner_hostname": "AWS", "key": "{$NOT_EXIST}"},
             "expect": []},
            {"params": {"owner_hostname": "AWS", "key": "{$GLOBAL}"},
             "expect": [{"groupid": 3}]},
        ]
        for data in test_data:
            result = self.connector.get_group_ids(**data["params"])
            self.assertEqual(result, data["expect"])
        self.connector.zabbix_api.hostgroup.create = Mock(side_effect=ZabbixAPIException())
        result = self.connector.get_group_ids("AWS", "{$GLOBAL2}")
        self.assertListEqual(result, [])

    def test_get_template_ids(self):
        test_data = [
            {"params": {"owner_hostname": "AWS", "key": "{$REQUIRED_TEMPLATES}"},
             "expect": [{"templateid": 10002}]},
            {"params": {"owner_hostname": "AWS", "key": ""},
             "expect": [{"templateid": 10002}]},
            {"params": {"owner_hostname": "AWS", "key": "{$GLOBAL}"},
             "expect": []},
            {"params": {"owner_hostname": "AWS", "key": "{$NOT_EXIST}"},
             "expect": []},
            {"params": {"owner_hostname": "NotExist", "key": ""},
             "expect": []},
        ]
        for data in test_data:
            result = self.connector.get_template_ids(**data["params"])
            self.assertEqual(result, data["expect"])

    def test_get_user_template_ids(self):
        test_data = [
            {"params": {"owner_hostname": "AWS", "node": Mock(extra={"platform": None})},
             "expect": [{"templateid": 10005}, {"templateid": 10003}]},
            {"params": {"owner_hostname": "AWS", "node": Mock(extra={"platform": "windows"})},
             "expect": [{"templateid": 10005}, {"templateid": 10004}]},
            {"params": {"owner_hostname": "AWS", "node": Mock(extra={"platform": "Red Hat Enterprise Linux 6 (64bit)"})},
             "expect": [{"templateid": 10005}, {"templateid": 10003}]},
            {"params": {"owner_hostname": "AWS", "node": Mock(extra={"platform": "CentOS 4/5/6 (64bit)"})},
             "expect": [{"templateid": 10005}, {"templateid": 10003}]},
            {"params": {"owner_hostname": "AWS", "node": Mock(extra={"platform": "Microsoft Windows Server 2008 R2 (64bit)"})},
             "expect": [{"templateid": 10005}, {"templateid": 10004}]},
        ]
        for data in test_data:
            result = self.connector.get_user_template_ids(**data["params"])
            self.assertListEqual(result, data["expect"])
    def test_adjust_string_length(self):
        test_data = [
                {"params": {"base_string": "1234567890", "suffix": "i-123456", "max_length": 64},
                 "expect": "1234567890_i-123456"},
                {"params": {"base_string": "1234567890", "suffix": "i-123456", "max_length": 15},
                 "expect": "1234.._i-123456"},
                {"params": {"base_string": "1234567890", "suffix": "", "max_length": 64},
                 "expect": "1234567890"},
                {"params": {"base_string": "1234567890", "suffix": "", "max_length": 9},
                 "expect": "1234567.."},
                {"params": {"base_string": "1234567890", "suffix": "i-1234567890", "max_length": 10},
                 "expect": "..34567890"}
        ]
        for data in test_data:
            result = self.connector.adjust_string_length(data["params"]["base_string"], data["params"]["suffix"], data["params"]["max_length"])
            self.assertEqual(result, data["expect"])

if __name__ == '__main__':
    unittest.main()
