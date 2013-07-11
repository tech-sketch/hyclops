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

from libcloud.compute.providers import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.base import Node, NodeDriver, NodeLocation
from psphere.client import Client
from psphere.managedobjects import HostSystem


class VSphereNodeDriver(NodeDriver):
    """
    VMware vSphere node driver
    """

    NODE_STATE_MAP = {
        'poweredOn': NodeState.RUNNING,
        'poweredOff': NodeState.UNKNOWN,
        'suspended': NodeState.PENDING,
    }
    NODE_STATUS_MAP = {
        'poweredOn': 'running',
        'poweredOff': 'stopped',
        'suspended': 'suspended',
    }

    def __init__(self, key, secret=None, secure=True, host=None):
        self.key = key
        self.secret = secret
        self.host = host
        self.connection = Client(server=host, username=key, password=secret)

    def _to_node(self, vm):
        public_ips = []
        if vm.guest.toolsRunningStatus == "guestToolsRunning" and hasattr(vm.guest, "net"):
            for network in vm.guest.net:
                if hasattr(network, "ipConfig"):
                    public_ips.extend([ip.ipAddress for ip in network.ipConfig.ipAddress if ip.state == "preferred"])
                elif hasattr(network, "ipAddress"):
                    public_ips.extend([ip for ip in network.ipAddress])
        elif hasattr(vm.guest, "ipAddress"):
            public_ips.append(vm.guest.ipAddress)
        quickStats = vm.summary.quickStats
        cpu_usage = quickStats.overallCpuUsage if hasattr(quickStats, "overallCpuUsage") else 0
        memory_usage = quickStats.guestMemoryUsage * 1024**2 if hasattr(quickStats, "guestMemoryUsage") else 0
        if hasattr(vm.runtime, "question"):
            stuck_state = 1
            question_id = vm.runtime.question.id
            choices = [{"key": info.key, "label": info.label, "summary": info.summary} for info in vm.runtime.question.choice.choiceInfo]
            if hasattr(vm.runtime.question, "message"):
                question = "Message: "
                for message in vm.runtime.question.message:
                    if hasattr(message, "text"):
                        question += message.text + "\n"
            else:
                question = vm.runtime.question.text
        else:
            stuck_state = 0
            question_id = None
            question = None
            choices = None
        node = Node(
            id=vm.config.uuid,
            name=vm.name,
            state=self.NODE_STATE_MAP[vm.runtime.powerState],
            public_ips=public_ips,
            private_ips=[],
            driver=self,
            extra={
                'managedObjectReference': vm,
                'status': self.NODE_STATUS_MAP[vm.runtime.powerState],
                'cpu': vm.summary.config.numCpu,
                'memory': vm.summary.config.memorySizeMB * 1024**2,
                'toolsRunningStatus': str(vm.guest.toolsRunningStatus),
                'toolsVersionStatus': str(vm.guest.toolsVersionStatus),
                'cpu_usage': 100 * float(cpu_usage) / vm.summary.runtime.maxCpuUsage,
                'memory_usage': memory_usage,
                'vmpath': vm.summary.config.vmPathName,
                'stuck_state': stuck_state,
                'stuck_question_id': question_id,
                'stuck_question': question,
                'stuck_choices': choices,
                'platform': vm.summary.config.guestFullName,
            }
        )
        return node

    def _to_hardware_profile(self, host):
        datastores = []
        for ds in host.datastore:
            datastores.append({
                'name': ds.name,
                'freeSpace': ds.summary.freeSpace,
                'capacity': ds.summary.capacity,
                'type': ds.summary.type,
            })
        hardware_profile = {
            'id': host.summary.hardware.uuid,
            'name': host.name,
            'cpu': host.hardware.cpuInfo.numCpuThreads,
            'cpu_usage': 100 * float(host.summary.quickStats.overallCpuUsage) / (host.summary.hardware.cpuMhz * host.summary.hardware.numCpuCores),
            'cpu_assigned': sum([vm.summary.config.numCpu for vm in host.vm if vm.runtime.powerState == "poweredOn"]),
            'memory': host.hardware.memorySize,
            'memory_usage': host.summary.quickStats.overallMemoryUsage * 1024**2,
            'memory_assigned': sum([vm.summary.config.memorySizeMB * 1024**2 for vm in host.vm if vm.runtime.powerState == "poweredOn"]),
            'datastores': datastores,
        }
        return hardware_profile

    def list_nodes(self, ex_node_ids=None, ex_vmpath=None):
        nodes = []
        hosts = HostSystem.all(self.connection)
        for host in hosts:
            for vm in host.vm:
                node = self._to_node(vm)
                if ex_node_ids is None or node.id in ex_node_ids:
                    if ex_vmpath is None or vm.summary.config.vmPathName == ex_vmpath:
                        nodes.append(node)
        uuids = [node.id for node in nodes]
        if ex_node_ids is not None and len(uuids) != len(set(uuids)):
            raise Exception("Cannot identify target node. Duplicate uuid exists")
        else:
            return nodes

    def reboot_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            vm.RebootGuest()
            return True
        except:
            return False

    def destroy_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            vm.UnregisterVM()
            return True
        except:
            return False

    def ex_start_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            task = vm.PowerOnVM_Task()
            return task.info.state != "error"
        except:
            return False

    def ex_stop_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            task = vm.PowerOffVM_Task()
            return task.info.state != "error"
        except:
            return False

    def ex_shutdown_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            vm.ShutdownGuest()
            return True
        except:
            return False

    def ex_suspend_node(self, node):
        vm = node.extra['managedObjectReference']
        try:
            task = vm.SuspendVM_Task()
            return task.info.state != "error"
        except:
            return False

    def ex_answer_node(self, node, choice):
        vm = node.extra['managedObjectReference']
        try:
            if hasattr(vm.runtime, "question"):
                vm.AnswerVM(questionId=vm.runtime.question.id, answerChoice=choice)
                return True
            else:
                return False
        except:
            return False

    def ex_hardware_profiles(self):
        hardware_profiles = []
        hosts = HostSystem.all(self.connection)
        for host in hosts:
            hardware_profiles.append(self._to_hardware_profile(host))
        return hardware_profiles
