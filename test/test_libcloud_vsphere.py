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


import sys
import unittest
from mock import patch, Mock, MagicMock
from libcloud.compute.base import Node
from hyclops.libcloud_driver.vsphere import VSphereNodeDriver
from .mock_psphere import MockVirtualMachine, MockDatastore, MockHostSystem


class VSphereTests(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        self.patchers.append(patch('hyclops.libcloud_driver.vsphere.Client'))
        self.patchers.append(patch('hyclops.libcloud_driver.vsphere.HostSystem', new=MockHostSystem))
        for patcher in self.patchers:
            patcher.start()
        self.driver = VSphereNodeDriver(key="key", secret="secret", host="127.0.0.1")
        self._set_libcloud_mock()

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def _set_libcloud_mock(self):
        MockHostSystem.clear_mock()
        MockVirtualMachine.clear_mock()
        vm1 = MockVirtualMachine({
            "name": "vm1",
            "summary": Mock(**{
                "quickStats.overallCpuUsage": 100,
                "quickStats.guestMemoryUsage": 300,
                "config.numCpu": 1,
                "config.memorySizeMB": 2048,
                "config.vmPathName": "[datastore1] /foo/bar.vmx",
                "config.guestFullName": "CentOS 4/5/6 (64bit)",
                "runtime.maxCpuUsage": 2000}),
            "runtime": Mock(**{
                "powerState": "poweredOn",
                "question": Mock(spec=['id', 'choice', 'text'],
                                 **{'id': 1,
                                 'choice.choiceInfo': [Mock(**{'key': 1, 'label': 'choice1', 'summary': 'choice1'})],
                                 'text': 'question message'})}),
            "config": Mock(**{
                "uuid": "vsphere_uuid",
                "extraConfig": [MagicMock()]}),
            "guest": Mock(**{
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "toolsVersionCurrent",
                "net": [MagicMock()]})
        })
        vm2 = MockVirtualMachine({
            "name": "vm2",
            "summary": Mock(**{
                "quickStats.overallCpuUsage": 100,
                "quickStats.guestMemoryUsage": 300,
                "config.numCpu": 1,
                "config.memorySizeMB": 2048,
                "config.vmPathName": "[datastore1] /foo/bar.vmx",
                "config.guestFullName": "CentOS 4/5/6 (64bit)",
                "runtime.maxCpuUsage": 2000}),
            "runtime": Mock(**{
                "powerState": "poweredOn",
                "question": Mock(spec=['id', 'choice', 'message'],
                                 **{'id': 1,
                                    'choice.choiceInfo': [Mock(**{'key': 1, 'label': 'choice1', 'summary': 'choice1'})],
                                    'message': [Mock(text="question message"), Mock(text="with line feed")]})}),
            "config": Mock(**{
                "uuid": "vsphere_uuid",
                "extraConfig": [MagicMock()]}),
            "guest": Mock(**{
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "toolsVersionCurrent",
                "net": [Mock(spec=["ipAddress"], **{"ipAddress": ["127.0.0.1"]})]}),
        })
        vm3 = MockVirtualMachine({
            "name": "vm3",
            "summary": Mock(**{
                "quickStats.overallCpuUsage": 100,
                "quickStats.guestMemoryUsage": 300,
                "config.numCpu": 1,
                "config.memorySizeMB": 2048,
                "config.vmPathName": "[datastore1] /foo/bar.vmx",
                "config.guestFullName": "CentOS 4/5/6 (64bit)",
                "runtime.maxCpuUsage": 2000}),
            "runtime": Mock(spec=["powerState"], **{"powerState": "poweredOn"}),
            "config": Mock(**{
                "uuid": "vsphere_uuid",
                "extraConfig": [MagicMock()]}),
            "guest": Mock(spec=["toolsRunningStatus", "toolsVersionStatus", "ipAddress"], **{
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "toolsVersionCurrent",
                "ipAddress": "127.0.0.1"}),
        })
        vm4 = MockVirtualMachine({
            "name": "vm4",
            "summary": Mock(**{
                "quickStats.overallCpuUsage": 100,
                "quickStats.guestMemoryUsage": 300,
                "config.numCpu": 1,
                "config.memorySizeMB": 2048,
                "config.vmPathName": "[datastore1] /foo/bar.vmx",
                "config.guestFullName": "CentOS 4/5/6 (64bit)",
                "runtime.maxCpuUsage": 2000}),
            "runtime": Mock(**{
                "powerState": "poweredOn",
                "question": Mock(spec=['id', 'choice', 'text'],
                                 **{'id': 1,
                                 'choice.choiceInfo': [Mock(**{'key': 1, 'label': 'choice1', 'summary': 'choice1'})],
                                 'text': 'question message'})}),
            "config": Mock(**{
                "uuid": "vsphere_uuid",
                "extraConfig": [MagicMock()]}),
            "guest": Mock(**{
                "toolsRunningStatus": "guestToolsRunning",
                "toolsVersionStatus": "toolsVersionCurrent",
                "net": [MagicMock()]}),
        })
        MockVirtualMachine.add_mock_vm(vm1)
        MockVirtualMachine.add_mock_vm(vm2)
        MockVirtualMachine.add_mock_vm(vm3)
        MockVirtualMachine.add_mock_vm(vm4)
        self.vm = vm1
        self.host = MockHostSystem({
            "name": "host name",
            "datastore": [
                MockDatastore({
                    "name": "datastore name",
                    "summary": Mock(**{"freeSpace": 400 * 1024**3,
                                        "capacity": 800 * 1024**3,
                                        "type": "nfs"})
                })
            ],
            "summary": Mock(**{
                'hardware.uuid': "hardware_uuid",
                'hardware.cpuMhz': 2000,
                'hardware.numCpuCores': 8,
                'quickStats.overallCpuUsage': 300,
                'quickStats.overallMemoryUsage': 1000}),
            "hardware": Mock(**{
                'cpuInfo.numCpuThreads': 16,
                'memorySize': 16 * 1024**3}),
            "vm": [vm1, vm2, vm3] # not include vm4
        })
        MockHostSystem.add_mock_host(self.host)
        self.node = Node(
            id="vsphere_uuid",
            name="vm1",
            state=0,
            public_ips=[],
            private_ips=[],
            driver=self.driver,
            extra={
                'managedObjectReference': self.vm,
                'status': 'running',
                'cpu': 1,
                'cpu_usage': 5.0,
                'memory': 2048 * 1024**2,
                'memory_usage': 300 * 1024**2,
                'toolsRunningStatus': 'guestToolsRunning',
                'toolsVersionStatus': 'toolsVersionCurrent',
                'vmpath': '[datastore1] /foo/bar.vmx',
                'stuck_state': 1,
                'stuck_question_id': 1,
                'stuck_question': "question message",
                'stuck_choices': [{'label': 'choice1', 'key': 1, 'summary': 'choice1'}],
                'platform': "CentOS 4/5/6 (64bit)",
            }
        )

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def test_to_node(self):
        # pattern 1
        vm = MockVirtualMachine.get(name="vm1")
        expect = self.node
        node = self.driver._to_node(vm)
        self.assertEqual(expect.id, node.id)
        self.assertEqual(expect.name, node.name)
        self.assertEqual(expect.state, node.state)
        self.assertEqual(expect.public_ips, node.public_ips)
        self.assertEqual(expect.private_ips, node.private_ips)
        self.assertEqual(expect.driver, node.driver)
        self.assertDictEqual(expect.extra, node.extra)
        # pattern 2
        vm = MockVirtualMachine.get(name="vm2")
        node = self.driver._to_node(vm)
        self.assertEqual(node.extra["stuck_question"], "Message: question message\nwith line feed\n")
        self.assertListEqual(node.public_ips, ["127.0.0.1"])
        # pattern 3
        vm = MockVirtualMachine.get(name="vm3")
        node = self.driver._to_node(vm)
        self.assertEqual(node.extra["stuck_state"], 0)
        self.assertListEqual(node.public_ips, ["127.0.0.1"])

    def test_to_hardware_profile(self):
        expect = {
            'id': 'hardware_uuid',
            'name': 'host name',
            'cpu': 16,
            'cpu_assigned': 1 * len(self.host.vm),
            'cpu_usage': 1.875,
            'memory': 16 * 1024**3,
            'memory_assigned': 2 * 1024**3 * len(self.host.vm),
            'memory_usage': 1000 * 1024**2,
            'datastores': [{'name': 'datastore name', 'freeSpace': 400 * 1024**3, 'capacity': 800 * 1024**3, 'type': 'nfs'}]
        }
        hardware_profile = self.driver._to_hardware_profile(self.host)
        self.assertDictEqual(expect, hardware_profile)

    def test_list_nodes(self):
        nodes = self.driver.list_nodes()
        self.assertIsInstance(nodes, list)
        self.assertEqual(len(nodes), len(self.host.vm))
        self.assertIsInstance(nodes[0], Node)
        self.assertEqual(nodes[0].driver, self.driver)
        # duplicate uuid pattern
        self.host.vm.append(MockVirtualMachine.get(name="vm4"))
        with self.assertRaises(Exception):
            self.driver.list_nodes(ex_node_ids="vsphere_uuid")

    def test_reboot_node(self):
        result = self.driver.reboot_node(self.node)
        self.assertTrue(result)
        self.vm.RebootGuest = Mock(side_effect=RuntimeError())
        result = self.driver.reboot_node(self.node)
        self.assertFalse(result)

    def test_destroy_node(self):
        result = self.driver.destroy_node(self.node)
        self.assertTrue(result)
        self.vm.UnregisterVM = Mock(side_effect=RuntimeError())
        result = self.driver.destroy_node(self.node)
        self.assertFalse(result)

    def test_ex_start_node(self):
        result = self.driver.ex_start_node(self.node)
        self.assertTrue(result)
        self.vm.PowerOnVM_Task = Mock(side_effect=RuntimeError())
        result = self.driver.ex_start_node(self.node)
        self.assertFalse(result)

    def test_ex_stop_node(self):
        result = self.driver.ex_stop_node(self.node)
        self.assertTrue(result)
        self.vm.PowerOffVM_Task = Mock(side_effect=RuntimeError())
        result = self.driver.ex_stop_node(self.node)
        self.assertFalse(result)

    def test_ex_shutdown_node(self):
        result = self.driver.ex_shutdown_node(self.node)
        self.assertTrue(result)
        self.vm.ShutdownGuest = Mock(side_effect=RuntimeError())
        result = self.driver.ex_shutdown_node(self.node)
        self.assertFalse(result)

    def test_ex_suspend_node(self):
        result = self.driver.ex_suspend_node(self.node)
        self.assertTrue(result)
        self.vm.SuspendVM_Task = Mock(side_effect=RuntimeError())
        result = self.driver.ex_suspend_node(self.node)
        self.assertFalse(result)

    def test_ex_answer_node(self):
        result = self.driver.ex_answer_node(self.node, 1)
        self.assertTrue(result)
        question = self.vm.runtime.question
        del self.vm.runtime.question
        result = self.driver.ex_answer_node(self.node, 1)
        self.assertFalse(result)
        self.vm.runtime.question = question
        self.vm.AnswerVM = Mock(side_effect=RuntimeError())
        result = self.driver.ex_answer_node(self.node, 1)
        self.assertFalse(result)

    def test_ex_hardware_profiles(self):
        hardware_profiles = self.driver.ex_hardware_profiles()
        self.assertIsInstance(hardware_profiles, list)
        self.assertEqual(len(hardware_profiles), 1)
        self.assertIsInstance(hardware_profiles[0], dict)
        self.assertEqual(hardware_profiles[0]["id"], "hardware_uuid")


if __name__ == '__main__':
    sys.exit(unittest.main())
