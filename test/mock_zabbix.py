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

from mock import Mock, MagicMock
from zabbix_api import ZabbixAPIException


class MockZabbixAPI(object):

    def __init__(self, server='http://localhost/zabbix', user=None, passwd=None,
                 log_level=None, timeout=10, r_query_len=10, **kwargs):
        self.hostid_seq = 10001
        self.interfaceid_seq = 1
        self.groupid_seq = 1
        self.macroid_seq = 1
        self.mock_hosts = []
        self.mock_templates = []
        self.mock_groups = []
        self.mock_macros = []

        self.host = Mock(**{
            'get.side_effect': self._host_get,
            'create.side_effect': self._host_create,
            'update.side_effect': self._host_update,
            'delete.side_effect': self._host_delete,
        })
        self.hostgroup = Mock(**{
            'get.side_effect': self._hostgroup_get,
            'create.side_effect': self._hostgroup_create,
        })
        self.hostinterface = Mock(**{
            'create.side_effect': self._hostinterface_create,
            'update.side_effect': self._hostinterface_update,
            'delete.side_effect': self._hostinterface_delete,
        })
        self.template = Mock(**{
            'get.side_effect': self._template_get,
            'create.side_effect': self._template_create,
        })
        self.usermacro = Mock(**{
            'get.side_effect': self._usermacro_get,
            'create.side_effect': self._usermacro_create,
        })

    def login(self, user='', password='', save=True):
        if user == 'Admin' and password == 'zabbix':
            return True
        else:
            raise ZabbixAPIException()

    def _host_create(self, params):
        host = params
        host["hostid"] = self.hostid_seq
        self.hostid_seq += 1
        if host["interfaces"]:
            interfaces = host["interfaces"]
            host["interfaces"] = {}
            for interface in interfaces:
                interface["interfaceid"] = self.interfaceid_seq
                index = self.interfaceid_seq
                self.interfaceid_seq += 1
                interface["hostid"] = host["hostid"]
                host["interfaces"][index] = interface
        self.mock_hosts.append(host)
        return {"hostids": [host["hostid"]]}

    def _template_create(self, params):
        template = params
        template["templateid"] = self.hostid_seq  # use hostid_seq
        self.hostid_seq += 1
        self.mock_templates.append(template)
        return {"templateids": [template["templateid"]]}

    def _hostgroup_create(self, params):
        group = params
        group["groupid"] = self.groupid_seq
        self.groupid_seq += 1
        self.mock_groups.append(group)
        return {"groupids": [group["groupid"]]}

    def _hostinterface_create(self, params):
        interface = params
        if interface["hostid"]:
            hosts = [host for host in self.mock_hosts if host["hostid"] == interface["hostid"]]
            if hosts:
                interface["interfaceid"] = self.interfaceid_seq
                index = self.interfaceid_seq
                self.interfaceid_seq += 1
                hosts[0]["interfaces"][index] = interface
                return {"interfaceids": [interface["interfaceid"]]}
        raise ZabbixAPIException()

    def _usermacro_create(self, params):
        macro = params
        macro["hostmacroids"] = self.macroid_seq
        self.macroid_seq += 1
        self.mock_macros.append(macro)
        return {"hostmacroids": [macro["hostmacroids"]]}

    def _host_update(self, params):
        if "hostid" not in params:
            raise ZabbixAPIException("hostid does not specified")
        elif params["hostid"] not in [host["hostid"] for host in self.mock_hosts]:
            raise ZabbixAPIException("host '%s' does not exist" % params["hostid"])
        host = [host for host in self.mock_hosts if host["hostid"] == params["hostid"]][0]
        for key, value in params.items():
            if key == "interfaces":
                continue
            host[key] = value
        return {"hostids": [host["hostid"]]}

    def _hostinterface_update(self, params):
        if "interfaceid" not in params:
            raise ZabbixAPIException("interfaceid does not specified")
        interfaces = [host["interfaces"] for host in self.mock_hosts]
        interfaces = reduce(lambda a, b: dict(a.items() + b.items()), interfaces)
        if params["interfaceid"] not in interfaces:
            raise ZabbixAPIException("interface '%s' does not exist" % params["interfaceid"])
        interface = interfaces[params["interfaceid"]]
        for key, value in params.items():
            interface[key] = value
        return {"interfaceids": [interface["interfaceid"]]}

    def _host_delete(self, params):
        if not isinstance(params, list):
            raise ZabbixAPIException("invalid format")
        deleted = []
        for hostid in params:
            id = hostid["hostid"] if isinstance(hostid, dict) else hostid
            host = [host for host in self.mock_hosts if host["hostid"] == id][0]
            self.mock_hosts.remove(host)
            deleted.append(id)
        return {"hostids": deleted}

    def _hostinterface_delete(self, params):
        if not isinstance(params, list):
            raise ZabbixAPIException("invalid format")
        deleted = []
        for host in self.mock_hosts:
            interfaces = host["interfaces"]
            for interfaceid in params:
                if interfaceid in interfaces:
                    del interfaces[interfaceid]
                    deleted.append(interfaceid)
        return {"interfaceids": deleted}

    def _host_get(self, params):
        hosts = self.mock_hosts[:]
        if "filter" in params:
            if "host" in params["filter"]:
                hosts = [host for host in hosts if host["host"] == params["filter"]["host"]]
            if "name" in params["filter"]:
                hosts = [host for host in hosts if host["name"] == params["filter"]["name"]]
        return hosts

    def _template_get(self, params):
        templates = self.mock_templates[:]
        if "filter" in params:
            if "host" in params["filter"]:
                templates = [template for template in templates if template["host"] == params["filter"]["host"]]
        if "templateids" in params:
            templates = [template for template in templates if int(template["templateid"]) in params["templateids"]]
        return templates

    def _usermacro_get(self, params):
        macros = self.mock_macros[:]
        if "globalmacro" in params:
            macros = [macro for macro in macros if macro["globalmacro"] == params["globalmacro"]]
        if "filter" in params:
            if "macro" in params["filter"]:
                macros = [macro for macro in macros if macro["macro"] == params["filter"]["macro"]]
        return macros

    def _hostgroup_get(self, params):
        groups = self.mock_groups[:]
        if "filter" in params:
            if "name" in params["filter"]:
                groups = [group for group in groups if group["name"] == params["filter"]["name"]]
        return groups
