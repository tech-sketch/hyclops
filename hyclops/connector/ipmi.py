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
import subprocess
import traceback
from libcloud.compute.types import NodeState
from hyclops.connector.base import BaseConnector


class IPMIConnector(BaseConnector):

    def __init__(self, config):
        super(IPMIConnector, self).__init__(config)
        self.type = "ipmi"
        self.logger = logging.getLogger('connector.ipmi')
        self.ipmitool = config["ipmi"].get('ipmitool', 'ipmitool')

    def __call__(self, hostname, params):
        try:
            result = self.run_command(hostname, params)
            if result:
                self.logger.debug("success. thread finished.")
            else:
                self.logger.warning("failed. thread finished.")
        except Exception:
            self.logger.error(traceback.format_exc())

    def run_command(self, hostname, params):
        command = params.get('command', 'monitor')
        conn_params = self.get_connection_parameters(hostname)
        if conn_params is None:
            self.logger.warning("Failed to get credentials from zabbix")
            return False
        if command == "monitor":
            return self.monitor(hostname, conn_params)
        else:
            allow_commands = {"start": "on", "stop": "off", "reboot": "reset"}
            if not command in allow_commands.keys():
                self.logger.warning("command %s is not supported" % command)
                return False
            else:
                output = self.run_ipmitool(allow_commands[command], **conn_params)
                return output is not None

    def get_connection_parameters(self, hostname):
        host = self.get_zabbix_host(hostname)
        if not host:
            self.logger.warning("zabbix host %s does not exist" % hostname)
            return
        interfaces = self.get_zabbix_interfaces(hostname, interface_type=3)
        ipmi_ip = self.interfaces_to_addresses(interfaces)
        if not ipmi_ip:
            self.logger.warning("ipmi interfaces does not exist on %s" % hostname)
            return
        else:
            ipmi_ip = ipmi_ip[0]
        key = host["ipmi_username"]
        secret = host["ipmi_password"]
        return {"ipmi_ip": ipmi_ip, "key": key, "secret": secret}

    def run_ipmitool(self, command, ipmi_ip, key, secret):
        cmd = [self.ipmitool, "-H", ipmi_ip, "-U", key, "-P", secret, "chassis", "power", command]
        try:
            output, error = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            output = output.strip()
            return output
        except subprocess.CalledProcessError:
            self.logger.error("Failed to %s target server" % command)
            return None

    def monitor(self, hostname, conn_params):
        output = self.run_ipmitool("status", **conn_params)
        if output == "Chassis Power is on":
            state = NodeState.RUNNING
            state_text = "running"
            result = True
        elif output == "Chassis Power is off":
            state = NodeState.TERMINATED
            state_text = "stopped"
            result = True
        else:
            self.logger.error("Failed to get IPMI status: %s" % output)
            state = NodeState.UNKNOWN
            state_text = "unknown"
            result = False
        # Update zabbix item
        self.zabbix_sender(hostname, "ipmi.state", state)
        self.zabbix_sender(hostname, "ipmi.state.text", state_text)
        return result
