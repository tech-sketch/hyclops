#!/usr/bin/env python

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
import json
import logging
import configobj
from hyclops.connector.ec2 import EC2Connector
from hyclops.connector.vsphere import VSphereConnector
from hyclops.connector.ipmi import IPMIConnector

if len(sys.argv) < 4:
    print "Usage for zabbix: %s[driver_name, {HOST.HOST}, {'command': command}]" % os.path.basename(sys.argv[0])
    sys.exit()
driver_name = sys.argv[1]
zabbix_hostname = sys.argv[2]
params = json.loads(sys.argv[3]) or {}
config_file = "/opt/hyclops/hyclops.conf"

# load config
config = configobj.ConfigObj(config_file)
log_level = config["logging"]["log_level"]
log_file = config["logging"]["log_file"]
log_format = '[%(asctime)s] %(name)s (%(threadName)s) %(levelname)s: %(message)s'
logging.basicConfig(filename=log_file, level=logging.WARNING, format=log_format)
logger = logging.getLogger('request_action')
logger.setLevel(getattr(logging, log_level))
if "environments" in config:
    for key, value in config["environments"].items():
        os.environ[key] = value

# run command
if driver_name == "ec2":
    connector = EC2Connector(config)
elif driver_name == "vsphere":
    connector = VSphereConnector(config)
elif driver_name == "ipmi":
    connector = IPMIConnector(config)
else:
    print "%s driver does not supported." % driver_name
    sys.exit()
try:
    result = connector.run_command(zabbix_hostname, params)
    print result
except Exception, e:
    print e
