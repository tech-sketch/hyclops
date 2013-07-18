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
import logging
import configobj
import argparse
from zabbix_api import ZabbixAPI
from datetime import datetime
import time

# get options
parser = argparse.ArgumentParser(description='Delete Zabbix hosts tool')
parser.add_argument('-u', '--username', help='Zabbix API access username')
parser.add_argument('-p', '--password', help='Zabbix API access password')
parser.add_argument('-f', '--url', help='Zabbix frontend url')
parser.add_argument('-g', '--group', help='Target Zabbix host group name')
parser.add_argument('-d', '--days', help='Set expire period (days)')
parser.add_argument('-s', '--seconds', help='Set expire period (seconds)')
args = parser.parse_args()

# load config
config_file = "/opt/hyclops/hyclops.conf"
config = configobj.ConfigObj(config_file)
log_level = config["logging"]["log_level"]
log_file = config["logging"]["log_file"]
log_format = '[%(asctime)s] %(name)s (%(threadName)s) %(levelname)s: %(message)s'
logging.basicConfig(filename=log_file, level=logging.WARNING, format=log_format)
logger = logging.getLogger('delete_hosts')
logger.setLevel(getattr(logging, log_level))

frontend_url = args.url if args.url else config["zabbix"]["frontend_url"]
username = args.username if args.url else config["zabbix"]["zabbix_user"]
password = args.password if args.password else config["zabbix"]["zabbix_password"]
group_name = args.group if args.group else "Not exist hosts"

if args.days:
    expire_period = int(args.days) * 24 * 60 * 60
elif args.seconds:
    expire_period = int(args.seconds)
else:
    expire_period = 2592000  # (2592000seconds = 30days)

zabbix_api = ZabbixAPI(frontend_url)
zabbix_api.login(username, password)

group = zabbix_api.hostgroup.get({"filter": {"name": group_name}})[0]
hosts = zabbix_api.host.get({"groupids": group["groupid"], "filter": {"status": 1}})
for host in hosts:
    item = zabbix_api.item.get({"hostids": host["hostid"], "search": {"key_": "instance.state"}})
    if item:
        history = zabbix_api.history.get({"itemids": item[0]["itemid"], "limit": 1, "output": "extend"})
        if history:
            now = int(time.mktime(datetime.now().timetuple()))
            if (now - int(history[0]["clock"])) < expire_period:
                continue
    try:
        zabbix_api.host.delete({"hostid": host["hostid"]})
        print "Succeeded delete host :%s" % host["hostid"]
        logger.info("Succeeded delete host :%s" % host["hostid"])
    except Exception, e:
        print "Failed delete host :%s" % host["hostid"]
        logger.error("Failed delete host :%s" % e)
print "finish %s" % os.path.basename(__file__)
logger.debug("finish %s" % os.path.basename(__file__))
