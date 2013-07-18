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
import hashlib
import configobj
from mock import patch, Mock, MagicMock
from zabbix_api import ZabbixAPIException
from hyclops.connector.vsphere import VSphereConnector
from .mock_zabbix import MockZabbixAPI
from .mock_libcloud import MockVSphereNodeDriver, MockNode


class TestVSphereConnector(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger('hyclops.connector.vsphere')
        logger.addHandler(logging.NullHandler())
        self.patchers = [
            patch('hyclops.libcloud_driver.vsphere.VSphereNodeDriver', new=MockVSphereNodeDriver),
            patch('hyclops.connector.base.ZabbixAPI', new=MockZabbixAPI),
        ]
        for patcher in self.patchers:
            patcher.start()
        config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test.conf")
        self.config = configobj.ConfigObj(config_path, file_error=True)
        self.connector = VSphereConnector(config=self.config)
        self.connector.zabbix_api = MockZabbixAPI()
        self.driver = MockVSphereNodeDriver("key", "secret")
        self._set_libcloud_mock()
        self._set_zabbix_mock()

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def _set_libcloud_mock(self):
        MockVSphereNodeDriver.clear_mock()
        node = MockNode(**{
            "id": "vsphere_uuid",
            "name": "vSphereVM",
            "state": 0,
            "public_ips": [],
            "private_ips": [],
            "driver": self.driver,
            "extra": {
                "managedObjectReference": MagicMock(),
                "vmpath": "[datastore1] /foo/bar.vmx",
                "status": "running",
                "cpu": 1,
                "cpu_usage": 12.34,
                "memory": 2 * 1024 ** 3,
                "memory_usage": 600 * 1024 ** 2,
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "guestToolsCurrent",
                "stuck_state": False,
                "stuck_question_id": None,
                "stuck_question": None,
                "stuck_choices": None,
                "platform": "CentOS 4/5/6 (64bit)",
            }
        })
        MockVSphereNodeDriver.add_mock_node(node)
        node = MockNode(**{
            "id": "duplicate_uuid1",
            "name": "Duplicate1 (update uuid host)",
            "state": 0,
            "public_ips": [],
            "private_ips": [],
            "driver": self.driver,
            "extra": {
                "managedObjectReference": MagicMock(),
                "vmpath": "[datastore1] /dup1/dup.vmx",
                "status": "running",
                "cpu": 1,
                "cpu_usage": 12.34,
                "memory": 2 * 1024 ** 3,
                "memory_usage": 600 * 1024 ** 2,
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "guestToolsCurrent",
                "stuck_state": False,
                "stuck_question_id": None,
                "stuck_question": None,
                "stuck_choices": None,
                "platform": "Microsoft Windows Server 2008 R2 (64-bit)",
            }
        })
        MockVSphereNodeDriver.add_mock_node(node)
        node = MockNode(**{
            "id": "duplicate_uuid1",
            "name": "Duplicate (update duplicate host)",
            "state": 0,
            "public_ips": [],
            "private_ips": [],
            "driver": self.driver,
            "extra": {
                "managedObjectReference": MagicMock(),
                "vmpath": "[datastore1] /dup/dup.vmx",
                "status": "running",
                "cpu": 1,
                "cpu_usage": 12.34,
                "memory": 2 * 1024 ** 3,
                "memory_usage": 600 * 1024 ** 2,
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "guestToolsCurrent",
                "stuck_state": False,
                "stuck_question_id": None,
                "stuck_question": None,
                "stuck_choices": None,
                "platform": "Microsoft Windows Server 2008 R2 (64-bit)",
            }
        })
        MockVSphereNodeDriver.add_mock_node(node)
        node = MockNode(**{
            "id": "duplicate_uuid1",
            "name": "Duplicate2 (create as duplicate host)",
            "state": 0,
            "public_ips": [],
            "private_ips": [],
            "driver": self.driver,
            "extra": {
                "managedObjectReference": MagicMock(),
                "vmpath": "[datastore1] /dup2/dup.vmx",
                "status": "running",
                "cpu": 1,
                "cpu_usage": 12.34,
                "memory": 2 * 1024 ** 3,
                "memory_usage": 600 * 1024 ** 2,
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "guestToolsCurrent",
                "stuck_state": False,
                "stuck_question_id": None,
                "stuck_question": None,
                "stuck_choices": None,
                "platform": "Microsoft Windows Server 2008 R2 (64-bit)",
            }
        })
        MockVSphereNodeDriver.add_mock_node(node)
        node = MockNode(**{
            "id": "duplicate_uuid2",
            "name": "Duplicate3 (update duplicate host to uuid host)",
            "state": 0,
            "public_ips": [],
            "private_ips": [],
            "driver": self.driver,
            "extra": {
                "managedObjectReference": MagicMock(),
                "vmpath": "[datastore1] /dup3/dup.vmx",
                "status": "running",
                "cpu": 1,
                "cpu_usage": 12.34,
                "memory": 2 * 1024 ** 3,
                "memory_usage": 600 * 1024 ** 2,
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "guestToolsCurrent",
                "stuck_state": False,
                "stuck_question_id": None,
                "stuck_question": None,
                "stuck_choices": None,
                "platform": "Red Hat Enterprise Linux 6 (64-bit)",
            }
        })
        MockVSphereNodeDriver.add_mock_node(node)
        node = MockNode(**{
            "id": "duplicate_uuid3",
            "name": "Duplicate4 (Create uuid host)",
            "state": 0,
            "public_ips": [],
            "private_ips": [],
            "driver": self.driver,
            "extra": {
                "managedObjectReference": MagicMock(),
                "vmpath": "[datastore1] /dup4/dup.vmx",
                "status": "running",
                "cpu": 1,
                "cpu_usage": 12.34,
                "memory": 2 * 1024 ** 3,
                "memory_usage": 600 * 1024 ** 2,
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "guestToolsCurrent",
                "stuck_state": False,
                "stuck_question_id": None,
                "stuck_question": None,
                "stuck_choices": None,
                "platform": "Red Hat Enterprise Linux 6 (64-bit)",
            }
        })
        MockVSphereNodeDriver.add_mock_node(node)
        node = MockNode(**{
            "id": "duplicate_uuid3",
            "name": "Duplicate5 (Create duplicate host at same time)",
            "state": 0,
            "public_ips": [],
            "private_ips": [],
            "driver": self.driver,
            "extra": {
                "managedObjectReference": MagicMock(),
                "vmpath": "[datastore1] /dup5/dup.vmx",
                "status": "running",
                "cpu": 1,
                "cpu_usage": 12.34,
                "memory": 2 * 1024 ** 3,
                "memory_usage": 600 * 1024 ** 2,
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "guestToolsCurrent",
                "stuck_state": False,
                "stuck_question_id": None,
                "stuck_question": None,
                "stuck_choices": None,
                "platform": "Red Hat Enterprise Linux 6 (64-bit)",
            }
        })
        MockVSphereNodeDriver.add_mock_node(node)
        hardware_profile = {
            "id": "hardware_uuid",
            "name": "host name",
            "cpu": 8,
            "cpu_usage": 12.34,
            "cpu_assigned": 4,
            "memory": 16 * 1024 ** 3,
            "memory_usage": 8 * 1024 ** 3,
            "memory_assigned": 8 * 1024 ** 3,
            "datastores": [
                {"name": "datastore1", "freeSpace": 600 * 1024 ** 3,
                 "capacity": 2 * 1024 ** 4, "type": "nfs"}
            ]
        }
        MockVSphereNodeDriver.add_mock_hardware_profile(hardware_profile)

    def _set_zabbix_mock(self):
        zabbix_api = self.connector.zabbix_api
        # create vSphereESXi Group
        response = zabbix_api.hostgroup.create({
            "name": "vSphereESXi"
        })
        groupid_vsphere_esxi = response["groupids"][0]
        # create vSphereVM Group
        response = zabbix_api.hostgroup.create({
            "name": "vSphereVM"
        })
        groupid_vsphere_vm = response["groupids"][0]
        # create vSphereESXi Template
        response = zabbix_api.template.create({
            "host": "vSphereESXi",
            "groups": [{"groupid": groupid_vsphere_esxi}],
            "macros": [
                {"macro": "{$VM_GROUPS}", "value": "vSphereVM"},
                {"macro": "{$VM_TEMPLATES}", "value": "vSphereVM"},
                {"macro": "{$VM_TEMPLATES_LINUX}", "value": "Template OS Linux"},
                {"macro": "{$VM_TEMPLATES_WINDOWS}", "value": "Template OS Windows"},
            ]
        })
        templateid_vsphere_esxi = response["templateids"][0]
        # create vSphereVM Template
        response = zabbix_api.template.create({
            "host": "vSphereVM",
            "groups": [{"groupid": groupid_vsphere_vm}],
        })
        templateid_vsphere_vm = response["templateids"][0]
        # create Template OS Linux
        response = zabbix_api.template.create({
            "host": "Template OS Linux",
            "groups": [],
        })
        # create ESXi Host
        zabbix_api.host.create({
            "host": "ESXi",
            "name": "ESXi",
            "interfaces": [
                {"type": 2, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161},
            ],
            "groups": [{"groupid": groupid_vsphere_esxi}],
            "parentTemplates": [{"templateid": templateid_vsphere_esxi}],
            "inventory": [],
            "macros": {
                "1": {"macro": "{$KEY}", "value": "key"},
                "2": {"macro": "{$SECRET}", "value": "secret"},
            },
        })
        # create vSphereVM(vsphere_uuid) Host
        zabbix_api.host.create({
            "host": "vsphere_uuid",
            "name": "ESXi_vSphereVM",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 0, "ip": "", "dns": "dummy-interface.invalid", "port": 10050},
                {"type": 2, "main": 1, "useip": 1, "ip": "", "dns": "dummy-interface.invalid", "port": 161},
            ],
            "groups": [{"groupid": groupid_vsphere_vm}],
            "parentTemplates": [{"templateid": templateid_vsphere_vm}],
            "inventory": {
                "name": "vSphereVM",
                "type": "vsphere",
                "tag": "ESXi",
                "location": "[datastore1] /foo/bar.vmx",
                "serialno_a": "vsphere_uuid",
            },
            "macros": [],
        })
        # create Duplicate1(duplicate_uuid1) Host
        zabbix_api.host.create({
            "host": "duplicate_uuid1",
            "name": "ESXi_Duplicate1",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
                {"type": 2, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161},
            ],
            "groups": [{"groupid": groupid_vsphere_vm}],
            "parentTemplates": [{"templateid": templateid_vsphere_vm}],
            "inventory": {
                "name": "Duplicate1",
                "type": "vsphere",
                "tag": "ESXi",
                "location": "[datastore1] /dup1/dup.vmx",
                "serialno_a": "duplicate_uuid1",
            },
            "macros": [],
        })
        # create Duplicate(duplicate_uuid1) Host
        zabbix_api.host.create({
            "host": hashlib.sha1("hardware_uuid" + "[datastore1] /dup/dup.vmx").hexdigest(),
            "name": "ESXi_Duplicate",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
                {"type": 2, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161},
            ],
            "groups": [{"groupid": groupid_vsphere_vm}],
            "parentTemplates": [{"templateid": templateid_vsphere_vm}],
            "inventory": {
                "name": "Duplicate",
                "type": "vsphere",
                "tag": "ESXi",
                "location": "[datastore1] /dup/dup.vmx",
                "serialno_a": "duplicate_uuid1",
            },
            "macros": [],
        })
        # create Duplicate3(duplicate_uuid2) Host
        zabbix_api.host.create({
            "host": hashlib.sha1("hardware_uuid" + "[datastore1] /dup3/dup.vmx").hexdigest(),
            "name": "ESXi_Duplicate3",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
                {"type": 2, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161},
            ],
            "groups": [{"groupid": groupid_vsphere_vm}],
            "parentTemplates": [{"templateid": templateid_vsphere_vm}],
            "inventory": {
                "name": "Duplicate1",
                "type": "vsphere",
                "tag": "ESXi",
                "location": "[datastore1] /dup3/dup.vmx",
                "serialno_a": "duplicate_uuid2",
            },
            "macros": [],
        })
        # create Dummy Host
        zabbix_api.host.create({
            "host": "dummy_uuid",
            "name": "ESXi_Dummy",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 0, "ip": "", "dns": "dummy-interface.invalid", "port": 10050},
                {"type": 2, "main": 1, "useip": 0, "ip": "", "dns": "dummy-interface.invalid", "port": 161},
            ],
            "groups": [{"groupid": groupid_vsphere_vm}],
            "parentTemplates": [{"templateid": templateid_vsphere_vm}],
            "inventory": {
                "name": "Dummy",
                "type": "vsphere",
                "tag": "ESXi",
                "location": "[datastore1] /dummy/dummy.vmx",
                "serialno_a": "dummy_uuid",
            },
            "macros": [],
        })
        # create Terminated Host
        zabbix_api.host.create({
            "host": "terminated_uuid",
            "name": "terminated",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
                {"type": 2, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161},
            ],
            "groups": [{"groupid": groupid_vsphere_vm}],
            "parentTemplates": [{"templateid": templateid_vsphere_vm}],
            "inventory": {
                "name": "terminated",
                "type": "vsphere",
                "tag": "ESXi",
                "location": "[datastore1] /terminated/terminated.vmx",
                "serialno_a": "terminated_uuid",
            },
            "macros": [],
        })
        # create NoParent Host
        zabbix_api.host.create({
            "host": "noparent_uuid",
            "name": "NoParent",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
                {"type": 2, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 161},
            ],
            "groups": [{"groupid": groupid_vsphere_vm}],
            "parentTemplates": [{"templateid": templateid_vsphere_vm}],
            "inventory": {
                "name": "terminated",
                "type": "vsphere",
                "tag": "NotExist",
                "location": "[datastore1] /noparent/noparent.vmx",
                "serialno_a": "noparent_uuid",
            },
            "macros": [],
        })
        # create Zabbix Server Host
        zabbix_api.host.create({
            "host": "Zabbix Server",
            "name": "Zabbix Server",
            "interfaces": [
                {"type": 1, "main": 1, "useip": 1, "ip": "127.0.0.1", "dns": "", "port": 10050},
            ],
            "groups": [],
            "parentTemplates": [],
            "inventory": [],
            "macros": [],
        })
        # create Global Macro
        zabbix_api.usermacro.create({
            "globalmacro": True,
            "macro": "{$GLOBAL}",
            "value": "global macro",
        })

    def test_init(self):
        self.assertIsInstance(self.connector, VSphereConnector)
        self.assertIsInstance(self.connector.zabbix_api, MockZabbixAPI)
        self.assertEqual(self.connector.type, "vsphere")

    def test_call(self):
        self.connector.logger = Mock(debug=Mock(), warning=Mock(), error=Mock())
        self.connector.run_command = Mock(return_value=True)
        self.connector(hostname="ESXi", params={})
        self.connector.logger.debug.assert_called()
        self.connector.run_command = Mock(return_value=False)
        self.connector(hostname="vsphere_uuid", params={"command": "start"})
        self.connector.logger.warning.assert_called()
        self.connector.run_command = Mock(side_effect=RuntimeError())
        self.connector(hostname="not found", params={})
        self.connector.logger.error.assert_called()

    def test_run_command(self):
        self.connector.monitor = MagicMock()
        correct_messages = [
            {"hostname": "ESXi", "params": {"command": "monitor"}},
            {"hostname": "vsphere_uuid", "params": {"command": "reboot"}},
            {"hostname": "vsphere_uuid", "params": {"command": "destroy"}},
            {"hostname": "vsphere_uuid", "params": {"command": "start"}},
            {"hostname": "vsphere_uuid", "params": {"command": "stop"}},
        ]
        invalid_messages = [
            {"hostname": "vsphere_uuid", "params": {"command": "invalid"}},
            {"hostname": "terminated_uuid", "params": {"command": "stop"}},
            {"hostname": "Zabbix Server", "params": {}},
        ]
        for message in correct_messages:
            self.assertTrue(self.connector.run_command(**message))
        for message in invalid_messages:
            result = self.connector.run_command(**message)
            self.assertFalse(result["result"])
            self.assertIsInstance(result["message"], str)
        self.connector.get_libcloud_node = Mock(return_value=None)
        result = self.connector.run_command(**correct_messages[1])
        self.assertFalse(result["result"])
        self.assertIsInstance(result["message"], str)

    def test_get_libcloud_node(self):
        result = self.connector.get_libcloud_node(hostname="vsphere_uuid", conn=self.driver)
        self.assertIsInstance(result, MockNode)
        result = self.connector.get_libcloud_node(hostname="duplicate_uuid1", conn=self.driver)
        self.assertFalse(result)
        result = self.connector.get_libcloud_node(hostname="terminated_uuid", conn=self.driver)
        self.assertFalse(result)
        result = self.connector.get_libcloud_node(hostname="Zabbix Server", conn=self.driver)
        self.assertFalse(result)
        result = self.connector.get_libcloud_node(hostname="not found", conn=self.driver)
        self.assertFalse(result)
        self.driver.list_nodes = Mock(side_effect=RuntimeError())
        result = self.connector.get_libcloud_node(hostname="vsphere_uuid", conn=self.driver)
        self.assertFalse(result)

    def test_get_connection_parameters(self):
        result = self.connector.get_connection_parameters(hostname="ESXi")
        self.assertDictEqual(result, {"host": "127.0.0.1", "key": "key", "secret": "secret"})
        result = self.connector.get_connection_parameters(hostname="vsphere_uuid")
        self.assertDictEqual(result, {"host": "127.0.0.1", "key": "key", "secret": "secret"})
        result = self.connector.get_connection_parameters(hostname="noparent_uuid")
        self.assertIsNone(result)
        result = self.connector.get_connection_parameters(hostname="not found")
        self.assertIsNone(result)

    def test_monitor(self):
        result = self.connector.monitor(owner_hostname="ESXi", conn=self.driver)
        self.assertTrue(result)
        zabbix_hosts = self.connector.zabbix_api.host.get({})
        zabbix_hostnames = [host["host"] for host in zabbix_hosts]
        self.assertTrue("vsphere_uuid" in zabbix_hostnames)
        self.assertTrue("duplicate_uuid1" in zabbix_hostnames)
        self.assertTrue(hashlib.sha1("hardware_uuid" + "[datastore1] /dup2/dup.vmx").hexdigest() in zabbix_hostnames)
        self.assertTrue("duplicate_uuid2" in zabbix_hostnames)
        self.assertFalse(hashlib.sha1("hardware_uuid" + "[datastore1] /dup3/dup.vmx").hexdigest() in zabbix_hostnames)
        self.assertTrue("duplicate_uuid3" in zabbix_hostnames)
        self.assertTrue(hashlib.sha1("hardware_uuid" + "[datastore1] /dup5/dup.vmx").hexdigest() in zabbix_hostnames)
        zabbix_hosts = self.connector.zabbix_api.host.get({})
        self.assertEqual(len([host for host in zabbix_hosts if host["host"] == "terminated_uuid"]), 0)
        self.connector.create_zabbix_host = Mock(return_value=False)
        self.connector.update_zabbix_host = Mock(return_value=False)
        self.connector.logger.warning = Mock()
        result = self.connector.monitor(owner_hostname="ESXi", conn=self.driver)
        self.connector.logger.warning.assert_called()

    def test_create_zabbix_host(self):
        node = MockNode(**{
            "id": "new_uuid",
            "name": "New Host",
            "state": 0,
            "public_ips": [],
            "private_ips": [],
            "driver": MockVSphereNodeDriver("key", "secret"),
            "extra": {
                "vmpath": "[datastore1] /hoge/hoge.vmx",
                "platform": "CentOS 4/5/6 (64bit)",
            }
        })
        result = self.connector.create_zabbix_host("ESXi", "new_uuid", node)
        self.assertTrue(result)
        host = self.connector.zabbix_api.host.get({"filter": {"host": node.id}})[0]
        self.assertEqual(host["host"], node.id)
        self.connector.zabbix_api.host.update = Mock(side_effect=ZabbixAPIException())
        result = self.connector.create_zabbix_host("ESXi", "new_uuid", node)
        self.assertFalse(result)
        self.connector.zabbix_api.host.create = Mock(side_effect=ZabbixAPIException())
        result = self.connector.create_zabbix_host("ESXi", "new_uuid", node)
        self.assertFalse(result)

    def test_update_zabbix_host(self):
        host = self.connector.zabbix_api.host.get({"filter": {"host": "vsphere_uuid"}})[0]
        node = self.driver.list_nodes(ex_node_ids=["vsphere_uuid"])[0]
        node.name = "vSphereVM_Updated"
        node.public_ips = ["127.0.0.1", "192.168.0.1", "localhost"]
        result = self.connector.update_zabbix_host("ESXi", "vsphere_uuid", node, host)
        self.assertTrue(result)
        self.assertEqual(host["name"], "ESXi_vSphereVM_Updated")
        self.connector.zabbix_api.host.update = Mock(side_effect=ZabbixAPIException())
        result = self.connector.update_zabbix_host("ESXi", "vsphere_uuid", node, host)
        self.assertFalse(result)
        self.connector.zabbix_api.hostinterface.update = Mock(side_effect=ZabbixAPIException())
        host = self.connector.zabbix_api.host.get({"filter": {"host": "dummy_uuid"}})[0]
        result = self.connector.update_zabbix_host("ESXi", "vsphere_uuid", node, host)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
