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

from mock import MagicMock


class MockHostSystem(object):

    hosts = []

    @classmethod
    def clear_mock(cls):
        cls.hosts = []

    @classmethod
    def add_mock_host(cls, host):
        cls.hosts.append(host)

    @classmethod
    def all(cls, client):
        return cls.hosts

    def __init__(self, params={}):
        for key, value in params.items():
            setattr(self, key, value)


class MockDatastore(object):

    def __init__(self, params={}):
        for key, value in params.items():
            setattr(self, key, value)


class MockVirtualMachine(object):

    vms = []

    @classmethod
    def clear_mock(cls):
        cls.vms = []

    @classmethod
    def add_mock_vm(cls, vm):
        cls.vms.append(vm)

    @classmethod
    def all(cls, client):
        return cls.vms

    @classmethod
    def get(cls, client=None, name=None):
        list = [vm for vm in cls.vms if vm.name == name]
        if list:
            return list[0]
        else:
            return None

    def __init__(self, params={}):
        for key, value in params.items():
            setattr(self, key, value)

    def RebootGuest(self):
        pass

    def ShutdownGuest(self):
        pass

    def UnregisterVM(self):
        pass

    def AnswerVM(self, questionId, answerChoice):
        pass

    def PowerOnVM_Task(self):
        return MagicMock()

    def PowerOffVM_Task(self):
        return MagicMock()

    def SuspendVM_Task(self):
        return MagicMock()
