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

import logging
import traceback
import hashlib
from libcloud.compute.providers import set_driver, get_driver
from hyclops.connector.base import BaseConnector
from zabbix_api import ZabbixAPIException


class VSphereConnector(BaseConnector):

    def __init__(self, config):
        super(VSphereConnector, self).__init__(config)
        self.type = "vsphere"
        self.logger = logging.getLogger("hyclops.connector." + self.type)
        try:
            self.driver = get_driver("vsphere")
        except AttributeError:
            set_driver("vsphere", 'hyclops.libcloud_driver.vsphere', 'VSphereNodeDriver')
            self.driver = get_driver("vsphere")

    def __call__(self, hostname, params):
        try:
            result = self.run_command(hostname, params)
            if result:
                self.logger.debug("success. thread finished.")
            else:
                self.logger.warning("failed. thread finished.")
        except Exception:
            if traceback:
                self.logger.error(traceback.format_exc())

    def run_command(self, hostname, params={}):
        command = params.get("command", "monitor")
        conn_params = self.get_connection_parameters(hostname)
        if conn_params is None:
            self.logger.warning("Failed to get credentials from zabbix")
            return {"result": False, "message": "Failed to get credentials from zabbix"}
        conn = self.driver(**conn_params)
        if command == "monitor":
            result = self.monitor(hostname, conn)
            message = "Succeeded" if result is True else "Failed"
            self.zabbix_sender(hostname, "monitor.status", message)
            return {"result": result, "message": message}
        else:
            node = self.get_libcloud_node(hostname, conn)
            if not node:
                self.logger.warning("Could not find vSphere virtual machine: %s" % hostname)
                return {"result": False, "message": "Could not find vSphere virtual machine: %s" % hostname}
            method = command + "_node" if command in self.LIBCLOUD_BASE_METHODS else "ex_" + command + "_node"
            try:
                if command == "answer":
                    result = getattr(conn, method)(node, params.get("choiceid"))
                else:
                    result = getattr(conn, method)(node)
                message = "Succeeded" if result is True else "Failed"
                message += " to %s %s" % (command, hostname)
                result = "Succeeded" if result is True else "Failed"
                return {"result": result, "message": message}
            except Exception, e:
                self.logger.warning("Failed to %s %s: %s" % (command, hostname, str(e)))
                return {"result": False, "message": "Failed to %s %s: %s" % (command, hostname, str(e))}

    def get_libcloud_node(self, hostname, conn):
        # get parameters from zabbix
        host = self.get_zabbix_host(hostname)
        if not host:
            self.logger.warning("host not found")
            return False
        if len(host["inventory"]) > 0:
            node_id = host["inventory"]["serialno_a"]
            vmpath = host["inventory"]["location"]
        else:
            node_id = host["host"]
            vmpath = None
        # get libcloud node
        try:
            nodes = conn.list_nodes(ex_node_ids=[node_id], ex_vmpath=vmpath)
        except Exception, e:
            self.logger.error(str(e))
            return False
        if len(nodes) == 1:
            return nodes[0]
        elif len(nodes) > 1:
            self.logger.warning("found same node id: %s" % str(nodes))
            return False
        else:
            self.logger.warning("libcloud node does not found")
            return False

    def get_connection_parameters(self, hostname):
        host = self.get_zabbix_host(hostname)
        if not host:
            self.logger.warning("target host %s does not exist" % hostname)
            return
        if host["inventory"] and host["inventory"]["type"] == self.type:
            owner_hostname = host["inventory"]["tag"]
            owner_host = self.get_zabbix_host(owner_hostname)
            if not owner_host:
                self.logger.warning("%s's owner host does not exist" % hostname)
                return
        else:
            owner_hostname = hostname
        interfaces = self.get_zabbix_interfaces(owner_hostname, interface_type=2, main=True)  # SNMP Interface
        addresses = self.interfaces_to_addresses(interfaces)
        if addresses:
            target_addr = addresses[0]
        else:
            self.logger.warning("target interface does not exist on %s" % owner_hostname)
            return
        key = self.get_user_macro(owner_hostname, self.MACRO_KEY)
        secret = self.get_user_macro(owner_hostname, self.MACRO_SECRET)
        return {"host": target_addr, "key": key, "secret": secret}

    def monitor(self, owner_hostname, conn):
        # Get informations from target server
        hardware_profiles = conn.ex_hardware_profiles()
        nodes = conn.list_nodes()

        # Register hardware information
        # (for ESXi. vCenter does not supported yet)
        hardware = hardware_profiles[0]
        self.zabbix_sender(owner_hostname, "hardware.cpu", hardware["cpu"])
        self.zabbix_sender(owner_hostname, "hardware.cpu.usage", hardware["cpu_usage"])
        self.zabbix_sender(owner_hostname, "hardware.cpu.assigned", hardware["cpu_assigned"])
        self.zabbix_sender(owner_hostname, "hardware.memory", hardware["memory"])
        self.zabbix_sender(owner_hostname, "hardware.memory.usage", hardware["memory_usage"])
        self.zabbix_sender(owner_hostname, "hardware.memory.assigned", hardware["memory_assigned"])
        self.zabbix_sender(owner_hostname, "hardware.datastores", hardware["datastores"])

        # Register node information
        zbx_hosts = self.zabbix_api.host.get({
            "output": "extend",
            "selectInventory": "extend",
            "selectInterfaces": "extend",
            "selectParentTemplates": "extend"
        })
        zbx_same_owner_hosts = [host for host in zbx_hosts if len(host["inventory"]) > 0 and host["inventory"]["tag"] == owner_hostname]
        zbx_unchecked_hostids = [host["hostid"] for host in zbx_same_owner_hosts]
        zbx_new_host_uuids = []
        for node in nodes:
            hostname = node.id
            duplicate_hash = hashlib.sha1(hardware["id"] + node.extra["vmpath"]).hexdigest()
            host = None
            hosts = [host for host in zbx_hosts if host["host"] == hostname]
            duplicate_hosts = [host for host in zbx_hosts if host["host"] == duplicate_hash]
            if len(duplicate_hosts) > 0:
                if len(hosts) > 0:
                    # update duplicate host
                    host = duplicate_hosts[0]
                    hostname = duplicate_hash
                    result = self.update_zabbix_host(owner_hostname, duplicate_hash, node, host)
                else:
                    # update duplicate host to normal host
                    host = duplicate_hosts[0]
                    result = self.update_zabbix_host(owner_hostname, hostname, node, host)
            else:
                if len(hosts) > 0:
                    if hosts[0]["inventory"]["location"] == node.extra["vmpath"]:
                        # update host
                        host = hosts[0]
                        result = self.update_zabbix_host(owner_hostname, hostname, node, host)
                    else:
                        # create duplicate host
                        hostname = duplicate_hash
                        result = self.create_zabbix_host(owner_hostname, duplicate_hash, node)
                else:
                    if hostname in zbx_new_host_uuids:
                        # create duplicate host
                        hostname = duplicate_hash
                        result = self.create_zabbix_host(owner_hostname, duplicate_hash, node)
                    else:
                        # create host
                        result = self.create_zabbix_host(owner_hostname, hostname, node)
                        zbx_new_host_uuids.append(hostname)

            if host and host["hostid"] in zbx_unchecked_hostids:
                zbx_unchecked_hostids.remove(host["hostid"])
            if not result:
                self.logger.warning("Failed to update %s status" % host["name"])

            # update zabbix items
            self.zabbix_sender(hostname, "instance.state", node.state)
            self.zabbix_sender(hostname, "instance.owner_hostname", owner_hostname)
            self.zabbix_sender(hostname, "instance.cpu", node.extra["cpu"])
            self.zabbix_sender(hostname, "instance.cpu.usage", node.extra["cpu_usage"])
            self.zabbix_sender(hostname, "instance.memory", node.extra["memory"])
            self.zabbix_sender(hostname, "instance.memory.usage", node.extra["memory_usage"])
            self.zabbix_sender(hostname, "instance.tools_running_status", node.extra["toolsRunningStatus"])
            self.zabbix_sender(hostname, "instance.tools_version_status", node.extra["toolsVersionStatus"])
            self.zabbix_sender(hostname, "instance.stuck.state", node.extra["stuck_state"])
            self.zabbix_sender(hostname, "instance.stuck.question", node.extra["stuck_question"])
            self.zabbix_sender(hostname, "instance.stuck.choices", node.extra["stuck_choices"])
            self.zabbix_sender(hostname, "instance.platform", node.extra["platform"])

        # move to "Not exist hosts" group old zabbix hosts
        not_existed_groupid = self.zabbix_api.hostgroup.get({"filter": {"name": "Not exist hosts"}})[0]
        for hostid in zbx_unchecked_hostids:
            target_host = self.zabbix_api.host.get({"output": ["host", "name"], "hostids": [hostid]})[0]
            # for the case of zabbix visible name is empty.
            target_visible_name = self.NOT_EXIST_HOST_NAME_PREFIX + target_host["name"] if "name" in target_host else ""
            self.logger.debug("Move to 'Not exist hosts' group %s" % hostid)
            self.zabbix_api.host.update({
                "hostid": hostid,
                "host": self.NOT_EXIST_HOST_NAME_PREFIX + target_host["host"],
                "name": self.adjust_string_length(target_visible_name, "", self.VISIBLE_NAME_MAX_LENGTH),
                "groups": [not_existed_groupid],
                "status": 1,
                "inventory": {
                    "tag": ""
                }
            })
        return True

    def create_zabbix_host(self, owner_hostname, hostname, node):
        visible_name = self.adjust_string_length(owner_hostname, node.name, self.VISIBLE_NAME_MAX_LENGTH)
        same_visible_name_hosts = self.zabbix_api.host.get({"filter": {"name": visible_name}})
        if len(same_visible_name_hosts) > 0:
            # delete old host
            self.zabbix_api.host.delete([{"hostid": same_visible_name_hosts[0]["hostid"]}])
        template_ids = self.get_template_ids(owner_hostname)
        # create host
        response = None
        try:
            response = self.zabbix_api.host.create({
                "host": hostname,
                "name": visible_name,
                "interfaces": self.addresses_to_interfaces(node.public_ips),
                "groups": self.get_group_ids(owner_hostname),
                "templates": template_ids,
                "inventory_mode": 1,
                "inventory": {
                    "name": node.name,
                    "type": self.type,
                    "tag": owner_hostname,
                    "location": node.extra["vmpath"],
                    "serialno_a": node.id,
                },
            })
            self.logger.debug("Create zabbix host %s (%s)" % (hostname, visible_name))
        except ZabbixAPIException, e:
            self.logger.error("Failed to create zabbix host: %s" % str(e))
            return False
        user_template_ids = self.get_user_template_ids(owner_hostname, node)
        if response and user_template_ids:
            try:
                self.zabbix_api.host.update({
                    "hostid": response["hostids"][0],
                    "templates": template_ids + user_template_ids,
                })
                self.logger.debug("Update zabbix host templates: add %s" % user_template_ids)
            except ZabbixAPIException, e:
                self.logger.warning("Failed to link templates: %s" % str(e))
                return False
        return True

    def update_zabbix_host(self, owner_hostname, hostname, node, host):
        visible_name = self.adjust_string_length(owner_hostname, node.name, self.VISIBLE_NAME_MAX_LENGTH)
        if node.public_ips and [interface for interface in host["interfaces"].values() if interface["dns"] == "dummy-interface.invalid"]:
            for type in [1, 2]:
                old_interfaces = [interface for interface in host["interfaces"].values() if int(interface["type"]) == type]
                old_interfaces = sorted(old_interfaces, key=lambda x: x["interfaceid"])
                is_main = False if old_interfaces else True
                for new_ip, old_interface in map(None, node.public_ips, old_interfaces):
                    try:
                        if new_ip and old_interface:
                            self.zabbix_api.hostinterface.update({
                                "interfaceid": old_interface["interfaceid"],
                                "useip": 1,
                                "ip": new_ip,
                                "dns": "",
                            })
                            self.logger.debug("Update zabbix host interface (%s to %s)" % (old_interface, new_ip))
                        elif new_ip:
                            interface = self.addresses_to_interfaces(new_ip, interface_types=[type], main=is_main)[0]
                            interface["hostid"] = host["hostid"]
                            self.zabbix_api.hostinterface.create(interface)
                            is_main = False
                        self.logger.debug("Create zabbix host interface (%s)" % new_ip)
                    except ZabbixAPIException, e:
                        self.logger.error("Failed to update zabbix host interface: %s" % str(e))
        try:
            assigned_template_ids = self.get_assigned_template_ids(host)
            user_template_ids = self.get_user_template_ids(owner_hostname, node)
            unassigned_template_ids = []
            for templateid in user_template_ids:
                if templateid not in assigned_template_ids:
                    unassigned_template_ids.append(templateid)
            self.zabbix_api.host.update({
                "hostid": host["hostid"],
                "host": hostname,
                "name": visible_name,
                "templates": assigned_template_ids + unassigned_template_ids,
                "inventory": {
                    "name": node.name,
                    "type": self.type,
                    "tag": owner_hostname,
                    "location": node.extra["vmpath"],
                    "serialno_a": node.id,
                },
            })
            self.logger.debug("Update zabbix host %s (%s)" % (hostname, visible_name))
            return True
        except ZabbixAPIException, e:
            self.logger.error("Failed to update zabbix host: %s" % str(e))
            return False
