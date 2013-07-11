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
import sys
import unittest
import logging
import configobj
from mock import patch, Mock, MagicMock
from zabbix_api import ZabbixAPIException
from libcloud.compute.base import Node, NodeImage
from hyclops.connector.ec2 import EC2Connector
from .mock_zabbix import MockZabbixAPI
from .mock_libcloud import MockNodeDriver, MockEC2NodeDriver


class TestEC2Connector(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger('hyclops.connector.ec2')
        logger.addHandler(logging.NullHandler())
        libcloud_drivers = [
            'libcloud.compute.drivers.ec2.EC2EUNodeDriver',
            'libcloud.compute.drivers.ec2.EC2USWestNodeDriver',
            'libcloud.compute.drivers.ec2.EC2USWestOregonNodeDriver',
            'libcloud.compute.drivers.ec2.EC2APSENodeDriver',
            'libcloud.compute.drivers.ec2.EC2APNENodeDriver',
            'libcloud.compute.drivers.ec2.EC2SAEastNodeDriver',
            'libcloud.compute.drivers.ec2.EC2APSESydneyNodeDriver',
        ]
        self.patchers = [patch(driver, new=MockNodeDriver) for driver in libcloud_drivers]
        self.patchers.append(patch('libcloud.compute.drivers.ec2.EC2NodeDriver', new=MockEC2NodeDriver))
        self.patchers.append(patch('hyclops.connector.base.ZabbixAPI', new=MockZabbixAPI))
        for patcher in self.patchers:
            patcher.start()
        config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test.conf")
        self.config = configobj.ConfigObj(config_path, file_error=True)
        self.connector = EC2Connector(config=self.config)
        self.connector.zabbix_api = MockZabbixAPI()
        self.driver = MockEC2NodeDriver("key", "secret")
        self._set_libcloud_mock()
        self._set_zabbix_mock()

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def _set_libcloud_mock(self):
        MockEC2NodeDriver.clear_mock()
        node = Node(
            id="i-aaaaaaaa",
            name="EC2",
            state=0,
            public_ips=["127.0.0.1"],
            private_ips=["127.0.0.1"],
            driver=self.driver,
            extra={
                "dns_name": "ec2.example.com",
                "instanceId": "i-aaaaaaaa",
                "imageId": "ami-aaaaaaaa",
                "private_dns": "",
                "status": "running",
                "keyname": "",
                "launchindex": "",
                "productcode": "",
                "instancetype": "m1.small",
                "launchdatetime": "",
                "availability": "ap-northeast-1a",
                "kernelid": "",
                "ramdiskid": "",
                "clienttoken": "",
                "groups": [],
                "tags": {},
            }
        )
        MockEC2NodeDriver.add_mock_node(node)
        node = Node(**{
            "id": "i-bbbbbbbb",
            "name": "a"*62,
            "state": 0,
            "public_ips": [],
            "private_ips": [],
            "driver": self.driver,
            "extra": {
                "dns_name": "ec2.example.com",
                "instanceId": "i-bbbbbbbb",
                "imageId": "ami-bbbbbbbb",
                "private_dns": "",
                "status": "running",
                "keyname": "",
                "launchindex": "",
                "productcode": "",
                "instancetype": "m1.small",
                "launchdatetime": "",
                "availability": "ap-northeast-1a",
                "kernelid": "",
                "ramdiskid": "",
                "clienttoken": "",
                "groups": [],
                "tags": {},
            }
        })
        MockEC2NodeDriver.add_mock_node(node)
        MockEC2NodeDriver.add_mock_image(NodeImage(id="ami-aaaaaaaa", name="Linux Image", driver=self.driver, extra={"platform": None}))

    def _set_zabbix_mock(self):
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
                {"macro": "{$VM_TEMPLATES}", "value": "AmazonEC2"},
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
        response = zabbix_api.template.create({
            "host": "Template OS Linux",
            "groups": [],
        })
        templateid_os_linux = response["templateids"][0]
        # create AWS Host
        zabbix_api.host.create({
            "host": "AWS",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
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
                {"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
                {"type": 2, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161},
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
        zabbix_api.host.create({
            "host": "i-ffffffff",
            "name": "AWS_TerminatedHost",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
                {"type": 2, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161},
            ],
            "groups": [{"groupid": groupid_amazon_ec2}],
            "parentTemplates": [{"templateid": templateid_amazon_ec2}],
            "inventory": {
                "name": "TerminatedHost",
                "type": "ec2",
                "tag": "AWS",
                "location": "ap-northeast-1",
                "serialno_a": "i-ffffffff",
            },
            "macros": [],
        })
        # create Global Macro
        zabbix_api.usermacro.create({
            "globalmacro": True,
            "macro": "{$GLOBAL}",
            "value": "global macro",
        })

    def test_init(self):
        self.assertIsInstance(self.connector, EC2Connector)
        self.assertIsInstance(self.connector.zabbix_api, MockZabbixAPI)
        self.assertIsInstance(self.connector.logger, logging.Logger)
        self.assertEqual(self.connector.type, "ec2")

    def test_call(self):
        self.connector.logger = Mock(debug=Mock(), warning=Mock(), error=Mock())
        self.connector.run_command = Mock(return_value={"result": True, "message": "Success"})
        self.connector(hostname="AWS", params={})
        self.connector.logger.debug.assert_called()
        self.connector.run_command = Mock(return_value={"result": False, "message": "Falied"})
        self.connector(hostname="not found", params={})
        self.connector.logger.warning.assert_called()
        self.connector.run_command = Mock(side_effect=RuntimeError())
        self.connector(hostname="not found", params={})
        self.connector.logger.error.assert_called()

    def test_run_command(self):
        correct_messages = [
            {"hostname": "AWS", "params": {"command": "monitor"}},
            {"hostname": "i-aaaaaaaa", "params": {"command": "reboot"}},
            {"hostname": "i-aaaaaaaa", "params": {"command": "destroy"}},
            {"hostname": "i-aaaaaaaa", "params": {"command": "start"}},
            {"hostname": "i-aaaaaaaa", "params": {"command": "stop"}},
        ]
        invalid_messages = [
            {"hostname": "i-aaaaaaaa", "params": {"command": "invalid"}},
            {"hostname": "", "params": {}},
            {"hostname": "AWS", "params": {"command": "stop"}},
        ]
        monitor_org = self.connector.monitor
        self.connector.monitor = MagicMock(return_value=True)
        for test_message in correct_messages:
            result = self.connector.run_command(**test_message)
            self.assertIsInstance(result, dict)
            self.assertTrue(result["result"])
        for test_message in invalid_messages:
            result = self.connector.run_command(**test_message)
            self.assertIsInstance(result, dict)
            self.assertFalse(result["result"])
        self.connector.monitor.assert_called_with("AWS", {"secret": "secret", "key": "key"})
        self.connector.monitor = monitor_org

    def test_get_connection_parameters(self):
        result = self.connector.get_connection_parameters(hostname="AWS")
        self.assertDictEqual(result, {"key": "key", "secret": "secret"})
        result = self.connector.get_connection_parameters(hostname="i-aaaaaaaa")
        self.assertDictEqual(result, {"key": "key", "secret": "secret"})
        result = self.connector.get_connection_parameters(hostname="not found")
        self.assertIsNone(result)

    def test_get_libcloud_node(self):
        node = self.connector.get_libcloud_node(hostname="i-aaaaaaaa", conn_params={'key': 'testkey', 'secret': 'testsecret'})
        self.assertIsInstance(node, Node)
        self.assertEqual(node.id, "i-aaaaaaaa")

    def test_monitor(self):
        result = self.connector.monitor(owner_hostname="AWS", conn_params={"key": "testkey", "secret": "testsecret"})
        self.assertTrue(result)

    def test_create_zabbix_host(self):
        node = self.driver.list_nodes(ex_node_ids=["i-aaaaaaaa"])[0]
        node.extra["platform"] = None
        self.assertTrue(self.connector.create_zabbix_host(owner_hostname="AWS", hostname="i-aaaaaaaa", node=node))
        self.connector.zabbix_api.host.update = Mock(side_effect=ZabbixAPIException())
        self.assertFalse(self.connector.create_zabbix_host(owner_hostname="AWS", hostname="i-aaaaaaaa", node=node))
        self.connector.zabbix_api.host.create = Mock(side_effect=ZabbixAPIException())
        self.assertFalse(self.connector.create_zabbix_host(owner_hostname="AWS", hostname="i-aaaaaaaa", node=node))

    def test_update_zabbix_host(self):
        node = self.driver.list_nodes(ex_node_ids=["i-aaaaaaaa"])[0]
        node.name = "a"*62
        host = self.connector.zabbix_api.host.get({"filter": {"host": "i-aaaaaaaa"}})[0]
        self.assertTrue(self.connector.update_zabbix_host(owner_hostname="AWS", hostname="i-aaaaaaaa", node=node, host=host))
        self.assertEqual(host["name"], "AWS_" + "a"*(64-len("AWS_")-len(".._i-aaaaaaaa")) + ".._i-aaaaaaaa")
        host = self.connector.zabbix_api.host.get({"filter": {"host": "i-aaaaaaaa"}})[0]
        self.assertEqual(len(host["interfaces"]), len(node.private_ips)*2+2)
        node.public_ips = []
        node.private_ips = []
        self.assertTrue(self.connector.update_zabbix_host(owner_hostname="AWS", hostname="i-aaaaaaaa", node=node, host=host))
        host = self.connector.zabbix_api.host.get({"filter": {"host": "i-aaaaaaaa"}})[0]
        self.assertEqual(len(host["interfaces"]), len(node.private_ips)*2+2)
        self.connector.zabbix_api.host.update = Mock(side_effect=ZabbixAPIException())
        self.assertFalse(self.connector.update_zabbix_host(owner_hostname="AWS", hostname="i-aaaaaaaa", node=node, host=host))

    def test_set_platform(self):
        node = self.driver.list_nodes(ex_node_ids=["i-aaaaaaaa"])[0]
        image = self.driver.list_images(ex_image_ids=node.extra["imageId"])[0]
        self.connector.set_platform(node, {"key": "key", "secret": "secret"})
        self.assertEqual(node.extra["platform"], image.extra["platform"])
        node = self.driver.list_nodes(ex_node_ids=["i-bbbbbbbb"])[0]
        self.connector.set_platform(node, {"key": "key", "secret": "secret"})
        self.assertEqual(node.extra["platform"], "unknown")


if __name__ == '__main__':
    unittest.main()
