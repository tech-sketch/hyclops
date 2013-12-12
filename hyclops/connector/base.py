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
import re
import json
import logging
from zabbix_api import ZabbixAPI, ZabbixAPISubClass, ZabbixAPIException


class BaseConnector(object):

    LIBCLOUD_BASE_METHODS = ["reboot", "destroy"]
    MACRO_KEY = "{$KEY}"
    MACRO_SECRET = "{$SECRET}"
    MACRO_GROUPS = "{$VM_GROUPS}"
    MACRO_REQUIRED_TEMPLATES = "{$REQUIRED_TEMPLATES}"
    MACRO_TEMPLATES = "{$VM_TEMPLATES}"
    MACRO_TEMPLATES_LINUX = "{$VM_TEMPLATES_LINUX}"
    MACRO_TEMPLATES_WINDOWS = "{$VM_TEMPLATES_WINDOWS}"
    NOT_EXIST_HOST_NAME_PREFIX = "_DELETED_"
    VISIBLE_NAME_MAX_LENGTH = 64

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("hyclops.connector.base")
        self.zabbix_server = config["zabbix"].get('zabbix_server', 'localhost')
        self.zabbix_port = config["zabbix"].get('zabbix_port', '10051')
        self.zabbix_sender_path = config["zabbix"].get('zabbix_sender', '/usr/bin/zabbix_sender')
        frontend_url = config["zabbix"].get('frontend_url', "http://%s/zabbix" % self.zabbix_server)
        zabbix_user = config["zabbix"].get('zabbix_user', '')
        zabbix_password = config["zabbix"].get('zabbix_password', '')
        self.zabbix_api = ZabbixAPI(frontend_url)
        self.zabbix_api.hostinterface = ZabbixAPISubClass(self.zabbix_api, dict({"prefix": "hostinterface"}))
        try:
            self.zabbix_api.login(zabbix_user, zabbix_password)
        except:
            self.logger.error("Cannot login zabbix server")
            raise

    def __call__(self, hostname, params):
        raise NotImplementedError("this connector is not implemented")

    # Zabbix Utils

    def zabbix_sender(self, zabbix_hostname, key, value):
        if value is None:
            value = ""
        elif not isinstance(value, str):
            value = json.dumps(value)
        args = (self.zabbix_sender_path, self.zabbix_server, self.zabbix_port, zabbix_hostname, key, value)
        cmd = "%s -z %s -p %s -s %s -k %s -o %s > /dev/null 2>&1" % self.escape_shell_args(args)
        return_code = os.system(cmd)
        if return_code != 0:
            raise Exception("Failed to run zabbix_sender")

    # TODO: use subprocess
    def escape_shell_args(self, args):
        if not isinstance(args, tuple) and not isinstance(args, list):
            args = [args]
        return tuple(["\\'".join("'" + p + "'" for p in str(arg).split("'")) for arg in args])

    def addresses_to_interfaces(self, addresses, interface_types=[1, 2], main=True):
        ports = {1: 10050, 2: 161, 3: 623, 4: 12345}  # 1: Zabbix Agent, 2: SNMP, 3: IPMI, 4: JMX
        interfaces = []
        if not isinstance(addresses, list):
            addresses = [addresses]
        for addr in addresses:
            if (not isinstance(addr, basestring)) or addr == "":
                continue
            if re.match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', addr):
                for type in interface_types:
                    interfaces.append({"type": type, "useip": 1, "ip": addr, "dns": "", "port": ports[type], "main": 0})
            else:
                for type in interface_types:
                    interfaces.append({"type": type, "useip": 0, "ip": "", "dns": addr, "port": ports[type], "main": 0})
        if interfaces:
            if main:
                for type in interface_types:
                    type_interfaces = [interface for interface in interfaces if interface["type"] == type]
                    main_interfaces = [interface for interface in type_interfaces if interface["useip"] == 0]
                    if main_interfaces:
                        main_interfaces[0]["main"] = 1
                    elif type_interfaces:
                        type_interfaces[0]["main"] = 1
            return interfaces
        else:
            for type in interface_types:
                interfaces.append({"type": type, "useip": 0, "ip": "", "dns": "dummy-interface.invalid", "port": ports[type], "main": 1 if main else 0})
            return interfaces

    def interfaces_to_addresses(self, interfaces):
        addresses = []
        if not isinstance(interfaces, list):
            interfaces = [interfaces]
        for interface in interfaces:
            if (not isinstance(interface, dict)) or "useip" not in interface:
                continue
            addr = interface["ip"] if int(interface["useip"]) == 1 else interface["dns"]
            addresses.append(addr)
        return addresses

    def get_zabbix_host(self, hostname):
        hosts = self.zabbix_api.host.get({
            "filter": {"host": hostname},
            "output": "extend",
            "selectInterfaces": "extend",
            "selectMacros": "extend",
            "selectGroups": "extend",
            "selectInventory": "extend",
        })
        if hosts:
            return hosts[0]
        else:
            return None

    def get_zabbix_interfaces(self, hostname, interface_type=None, main=False):
        hosts = self.zabbix_api.host.get({
            "filter": {"host": hostname},
            "selectInterfaces": "extend",
        })
        if hosts:
            interfaces = hosts[0]["interfaces"]
            if isinstance(interfaces, dict):
                interfaces = interfaces.values()
            if interface_type:
                interfaces = [interface for interface in interfaces if int(interface["type"]) == interface_type]
            if main:
                interfaces = [interface for interface in interfaces if int(interface["main"]) == 1]
            return interfaces
        else:
            return []

    def get_user_macro(self, hostname, key):
        if not key:
            return None
        if hostname:
            hosts = self.zabbix_api.host.get({"filter": {"host": hostname}, "selectMacros": "extend", "selectParentTemplates": ["templateid"]})
            if hosts:
                # search host macro
                if "macros" in hosts[0]:
                    # host macro format on Zabbix 2.0:
                    #   {'1': {'macro': '{$MACRO_NAME}', 'hostmacroid': '1', 'hostid': '10001', 'value': 'Macro value'}}
                    # host macro format on Zabbix 2.2
                    #   [{'macro': '{$MACRO_NAME}', 'hostmacroid': '1', 'hostid': '10001', 'hosts': [{'hostid': '10001'}], 'value': 'Macro value'}
                    macros = hosts[0]["macros"]
                    if isinstance(macros, dict):
                        macros = macros.values()
                    macros = [macro for macro in macros if macro["macro"] == key]
                    if macros:
                        return macros[0]["value"]
                # search template macro
                template_ids = [template["templateid"] for template in hosts[0]["parentTemplates"]]
                templates = self.zabbix_api.template.get({"templateids": template_ids, "selectMacros": "extend"})
                for template in templates:
                    if "macros" in template:
                        # template macro format on Zabbix 2.0:
                        #   [{'macro': '{$MACRO_NAME}', 'hostmacroid': '1', 'hostid': '10001', 'value': 'Macro value'}]
                        macros = [macro for macro in template["macros"] if macro["macro"] == key]
                        if macros:
                            return macros[0]["value"]
        global_macros = self.zabbix_api.usermacro.get({"globalmacro": True, "filter": {"macro": key}})
        if global_macros:
            return global_macros[0]["value"]
        else:
            return None

    def get_group_ids(self, owner_hostname, key=None):
        if not key:
            key = self.MACRO_GROUPS
        macro_value = self.get_user_macro(owner_hostname, key)
        group_names = [group_name.strip() for group_name in macro_value.split(',')] if macro_value else []
        groups = []
        for group_name in group_names:
            grp = self.zabbix_api.hostgroup.get({"filter": {"name": group_name}})
            if grp:
                groups.append({"groupid": grp[0]["groupid"]})
            else:
                self.logger.info("Group '%s' does not exist. Create group." % group_name)
                try:
                    response = self.zabbix_api.hostgroup.create({"name": group_name})
                    groups.append({"groupid": response["groupids"][0]})
                except ZabbixAPIException, e:
                    self.logger.warning("Cannot create group: %s" % str(e))
        return groups

    def get_template_ids(self, owner_hostname, key=None):
        if not key:
            key = self.MACRO_REQUIRED_TEMPLATES
        macro_value = self.get_user_macro(owner_hostname, key)
        template_names = [template_name.strip() for template_name in macro_value.split(',')] if macro_value else []
        templates = []
        for template_name in template_names:
            tmpl = self.zabbix_api.template.get({"filter": {"host": template_name}})
            if tmpl:
                templates.append({"templateid": tmpl[0]["templateid"]})
            else:
                self.logger.warning("Template '%s' does not exist" % template_name)
        return templates

    def get_user_template_ids(self, owner_hostname, node):
        templates = self.get_template_ids(owner_hostname, self.MACRO_TEMPLATES)
        if "platform" not in node.extra:
            self.logger.warning("Unknown platform: %s" % node.id)
            return templates
        else:
            if node.extra["platform"] is not None and node.extra["platform"].lower().find("windows") != -1:
                key = self.MACRO_TEMPLATES_WINDOWS
            else:
                key = self.MACRO_TEMPLATES_LINUX
            return templates + self.get_template_ids(owner_hostname, key)

    def get_assigned_template_ids(self, host):
        templates = []
        for tmpl in host['parentTemplates']:
            templates.append({"templateid": tmpl["templateid"]})
        return templates

    def adjust_string_length(self, base_string, suffix, max_length):
        if len(suffix) == 0:
            if len(base_string) > max_length:
                return base_string[0:max_length - len("..")] + ".."
            else:
                return base_string
        else:
            if len(base_string) + len(suffix) > max_length:
                if max_length < len(suffix):
                    return ".." + suffix[len(suffix) - max_length + len(".."):]
                return base_string[0:max_length - len(".._" + suffix)] + ".._" + suffix
            else:
                return base_string + "_" + suffix
