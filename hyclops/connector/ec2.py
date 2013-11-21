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
from libcloud.compute.types import Provider, NodeState
from libcloud.compute.providers import get_driver
from hyclops.connector.base import BaseConnector
from zabbix_api import ZabbixAPIException


class EC2Connector(BaseConnector):

    PROVIDERS = {
        'us-east-1': Provider.EC2,
        'us-west-1': Provider.EC2_US_WEST,
        'us-west-2': Provider.EC2_US_WEST_OREGON,
        'eu-west-1': Provider.EC2_EU_WEST,
        'ap-southeast-1': Provider.EC2_AP_SOUTHEAST,
        'ap-northeast-1': Provider.EC2_AP_NORTHEAST,
        'sa-east-1': Provider.EC2_SA_EAST,
        'sa-southeast-2': Provider.EC2_AP_SOUTHEAST2,
    }

    def __init__(self, config):
        self.type = "ec2"
        super(EC2Connector, self).__init__(config)
        self.logger = logging.getLogger("hyclops.connector." + self.type)

    def __call__(self, hostname, params):
        try:
            result = self.run_command(hostname, params)
            if result is not None and result["result"]:
                self.logger.debug("success. thread finished.")
            else:
                self.logger.warning("failed. thread finished.")
        except Exception:
            if traceback:
                self.logger.error(traceback.format_exc())

    def run_command(self, hostname, params):
        command = params.get("command", "monitor")
        conn_params = self.get_connection_parameters(hostname)
        if conn_params is None:
            self.logger.warning("Failed to get credentials from zabbix")
            return {"result": False, "message": "Failed to get credentials from zabbix"}
        if command == "monitor":
            result = self.monitor(hostname, conn_params)
            message = "Succeeded" if result is True else "Failed"
            self.zabbix_sender(hostname, "monitor.status", message)
            return {"result": result, "message": message}
        else:
            node = self.get_libcloud_node(hostname, conn_params)
            if not node:
                self.logger.warning("Instance %s does not exist on EC2" % hostname)
                return {"result": False, "message": "Instance %s does not exist on EC2" % hostname}
            method = command + "_node" if command in self.LIBCLOUD_BASE_METHODS else "ex_" + command + "_node"
            try:
                result = getattr(node.driver, method)(node)
                message = "Succeeded" if result is True else "Failed"
                message += " to %s %s" % (command, hostname)
                result = "Succeeded" if result is True else "Failed"
                return {"result": result, "message": message}
            except Exception, e:
                self.logger.warning("Failed to %s %s: %s" % (command, hostname, str(e)))
                return {"result": False, "message": "Failed to %s %s: %s" % (command, hostname, str(e))}

    def get_connection_parameters(self, hostname):
        host = self.get_zabbix_host(hostname)
        if not host:
            self.logger.warning("zabbix host %s does not exist" % hostname)
            return None
        if host["inventory"] and host["inventory"]["type"] == self.type:
            owner_hostname = host["inventory"]["tag"]
        else:
            owner_hostname = hostname
        key = self.get_user_macro(owner_hostname, self.MACRO_KEY)
        secret = self.get_user_macro(owner_hostname, self.MACRO_SECRET)
        return {"key": key, "secret": secret}

    def get_libcloud_node(self, hostname, conn_params):
        host = self.get_zabbix_host(hostname)
        if host is None or not host["inventory"]:
            return None
        region = host["inventory"]["location"]
        provider = self.PROVIDERS[region]
        driver = get_driver(provider)
        conn = driver(**conn_params)
        nodes = conn.list_nodes(ex_node_ids=[hostname])
        return nodes[0] if nodes else None

    def monitor(self, owner_hostname, conn_params):
        # Connect AWS EC2 (all region) API
        nodes = []
        for provider in self.PROVIDERS.values():
            driver = get_driver(provider)
            conn = driver(**conn_params)
            nodes.extend(conn.list_nodes())
        # Register node information
        zbx_hosts = self.zabbix_api.host.get({
            "output": "extend",
            "selectInventory": "extend",
            "selectInterfaces": "extend",
            "selectParentTemplates": "extend"
        })
        zbx_same_owner_hosts = [host for host in zbx_hosts if len(host["inventory"]) > 0 and host["inventory"]["tag"] == owner_hostname]
        zbx_unchecked_hostids = [host["hostid"] for host in zbx_same_owner_hosts]

        for node in nodes:
            self.set_ami_info(node, conn_params)
            hostname = node.id
            exist_hosts = [host for host in zbx_hosts if host["host"] == hostname]
            if not exist_hosts:
                result = self.create_zabbix_host(owner_hostname, hostname, node)
            else:
                host = exist_hosts[0]
                result = self.update_zabbix_host(owner_hostname, hostname, node, host)
                if host["hostid"] in zbx_unchecked_hostids:
                    zbx_unchecked_hostids.remove(host["hostid"])
                if not result:
                    self.logger.warning("Failed to update %s status" % host["name"])

                # update zabbix items
                self.zabbix_sender(hostname, "instance.state", node.state)
                self.zabbix_sender(hostname, "instance.availability_zone", node.extra["availability"])
                self.zabbix_sender(hostname, "instance.security_groups", node.extra["groups"])
                self.zabbix_sender(hostname, "instance.type", node.extra["instancetype"])
                self.zabbix_sender(hostname, "instance.keyname", node.extra["keyname"])
                self.zabbix_sender(hostname, "instance.ramdisk_id", node.extra["ramdiskid"])
                self.zabbix_sender(hostname, "instance.kernel_id", node.extra["kernelid"])
                self.zabbix_sender(hostname, "instance.ami_id", node.extra["imageId"])
                self.zabbix_sender(hostname, "instance.private_dns", node.extra["private_dns"])
                self.zabbix_sender(hostname, "instance.launch_time", node.extra["launchdatetime"])
                self.zabbix_sender(hostname, "instance.elastic_ips", list(set(node.public_ips)))
                self.zabbix_sender(hostname, "instance.private_ips", list(set(node.private_ips)))
                self.zabbix_sender(hostname, "instance.platform", node.extra["platform"])
                self.zabbix_sender(hostname, "instance.ami_name", node.extra["ami_name"])

        # move to "Not exist hosts" group old zabbix hosts
        not_existed_groupid = self.zabbix_api.hostgroup.get({"filter": {"name": "Not exist hosts"}})[0]
        for hostid in zbx_unchecked_hostids:
            target_host = self.zabbix_api.host.get({"output": ["host", "name"], "hostids": [hostid]})[0]
            self.logger.debug("Move to 'Not exist hosts' group %s" % hostid)
            self.zabbix_api.host.update({
                "hostid": hostid,
                "host": self.NOT_EXIST_HOST_NAME_PREFIX + target_host["host"],
                "name": self.NOT_EXIST_HOST_NAME_PREFIX + target_host["name"],
                "groups": [not_existed_groupid],
                "status": 1,
                "inventory": {
                    "tag": ""
                }
            })
        return True

    def set_ami_info(self, node, conn_params):
        images = node.driver.list_images(ex_image_ids=[node.extra["imageId"]])
        if images:
            node.extra["platform"] = images[0].extra["platform"] if images[0].extra["platform"] else "unknown"
            node.extra["ami_name"] = images[0].name if images[0].name else "unknown"
        else:
            node.extra["platform"] = "unknown"
            node.extra["ami_name"] = "unknown"

    def create_zabbix_host(self, owner_hostname, hostname, node):
        visible_name = owner_hostname + "_" + node.name
        if len(visible_name) < (64 - len("_" + node.id)):
            visible_name += "_" + node.id
        else:
            visible_name = visible_name[0:64 - len(".._" + node.id)] + ".._" + node.id
        templateids = self.get_template_ids(owner_hostname)
        # create host
        response = None
        try:
            response = self.zabbix_api.host.create({
                "host": hostname,
                "name": visible_name,
                "interfaces": self.addresses_to_interfaces([node.extra["dns_name"]] + node.private_ips),
                "groups": self.get_group_ids(owner_hostname),
                "templates": templateids,
                "inventory_mode": 1,
                "inventory": {
                    "name": node.name,
                    "type": self.type,
                    "tag": owner_hostname,
                    "location": node.extra["availability"][:-1],  # region
                },
            })
            self.logger.debug("Create zabbix host %s (%s)" % (hostname, visible_name))
        except ZabbixAPIException, e:
            self.logger.error("Failed to create zabbix host: %s" % str(e))
            return False
        # get additional os template
        user_templateids = self.get_user_template_ids(owner_hostname, node)
        if response and user_templateids:
            try:
                self.zabbix_api.host.update({
                    "hostid": response["hostids"][0],
                    "templates": templateids + user_templateids,
                })
                self.logger.debug("Update zabbix host templates: %s" % (templateids + user_templateids))
            except ZabbixAPIException, e:
                self.logger.warning("Failed to link templates: %s" % str(e))
                return False
        return True

    def update_zabbix_host(self, owner_hostname, hostname, node, host):
        region = node.extra["availability"][:-1]
        visible_name = owner_hostname + "_" + node.name
        if len(visible_name) < (64 - len("_" + node.id)):
            visible_name += "_" + node.id
        else:
            visible_name = visible_name[0:64 - len(".._" + node.id)] + ".._" + node.id
        try:
            if node.state == NodeState.RUNNING:
                for type in [1, 2]:
                    interfaces = host["interfaces"]
                    if isinstance(interfaces, dict):
                        interfaces = interfaces.values()
                    old_interfaces = [interface for interface in interfaces if int(interface["type"]) == type]
                    old_interfaces = sorted(old_interfaces, key=lambda x: x["interfaceid"])
                    is_main = False if old_interfaces else True
                    for new_addr, old_interface in map(None, [node.extra["dns_name"]] + node.private_ips, old_interfaces):
                        if new_addr and old_interface:
                            interface = self.addresses_to_interfaces(new_addr, interface_types=[type])[0]
                            interface["interfaceid"] = old_interface["interfaceid"]
                            del interface["main"]
                            self.zabbix_api.hostinterface.update(interface)
                        elif new_addr:
                            interface = self.addresses_to_interfaces(new_addr, interface_types=[type], main=is_main)[0]
                            interface["hostid"] = host["hostid"]
                            self.zabbix_api.hostinterface.create(interface)
                            is_main = False
                        elif old_interface:
                            self.zabbix_api.hostinterface.delete([old_interface["interfaceid"]])
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
                    "location": region,
                }
            })
            self.logger.debug("Update zabbix host %s (%s)" % (hostname, visible_name))
            return True
        except ZabbixAPIException, e:
            self.logger.error("Failed to update zabbix host: %s" % str(e))
            return False
