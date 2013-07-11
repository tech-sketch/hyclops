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
#
# Usage: push_message.py <server_address> <server_port> <driver_name> <zabbix_hostname> [params]
#

import sys
import zmq
import pickle

SUCCESS = 0
FAILURE = 1
DEFAULT_TIMEOUT = 3

if len(sys.argv) <= 4:
    print FAILURE
    sys.exit(1)
server_address = sys.argv[1]
server_port = sys.argv[2]
msg = pickle.dumps(sys.argv[3:])
timeout = DEFAULT_TIMEOUT

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.setsockopt(zmq.LINGER, 0)
try:
    socket.connect("tcp://%s:%s" % (server_address, server_port))
    tracker = socket.send(msg, copy=False, track=True)
    tracker.wait(timeout)
    print SUCCESS
except:
    print FAILURE
finally:
    socket.close()
