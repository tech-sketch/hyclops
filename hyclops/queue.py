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

import zmq
import json
import logging
import threading
from hyclops.connector.ec2 import EC2Connector
from hyclops.connector.vsphere import VSphereConnector
from hyclops.connector.ipmi import IPMIConnector


class MessageQueue():

    def __init__(self, config):
        self.connectors = {
            "ec2": EC2Connector(config),
            "vsphere": VSphereConnector(config),
            "ipmi": IPMIConnector(config),
        }
        self.socket = None
        self.threads = []
        self.logger = logging.getLogger("hyclops.queue")

    def _recv_message(self):
        if self.socket is None:
            return None
        message = self.socket.recv_pyobj()
        self.logger.debug("recieved request: [%s]" % str(message))
        if not isinstance(message, list) or len(message) < 2:
            self.logger.warning("bad message: [%s]" % str(message))
            return None
        driver = message[0]
        zabbix_hostname = message[1]
        if len(message) > 2:
            try:
                params = json.loads(message[2])
            except ValueError, e:
                self.logger.warning("%s: %s" % (str(e), message[2]))
                params = {}
        else:
            params = {}
        return {"driver": driver, "zabbix_hostname": zabbix_hostname, "params": params}

    def bind(self, listen_address="127.0.0.1", listen_port=5555, max_queue_size=100):
        context = zmq.Context()
        socket = context.socket(zmq.PULL)
        try:
            socket.setsockopt(zmq.HWM, max_queue_size)
        except AttributeError:
            socket.setsockopt(zmq.SNDHWM, max_queue_size)
            socket.setsockopt(zmq.RCVHWM, max_queue_size)
        try:
            socket.bind("tcp://%s:%s" % (listen_address, listen_port))
            self.socket = socket
            self.logger.info("Start message queue")
        except Exception, e:
            self.logger.error("Failed to bind ZeroMQ socket: %s" % str(e))
            socket.close()
            raise

    def poll(self):
        self.logger.debug("polling...")
        msg = self._recv_message()
        if msg is None:
            return
        for thread in self.threads:
            if not thread.isAlive():
                self.threads.remove(thread)
        command = msg["params"].get("command", "monitor")
        thread_name = "%s-%s-%s" % (msg["driver"], msg["zabbix_hostname"], command)
        alive_thread_names = [thread.name for thread in self.threads]
        if thread_name in alive_thread_names:
            self.logger.debug("thread %s already running. skipped." % thread_name)
        elif msg["driver"] in self.connectors:
            self.logger.debug("run %s thread" % thread_name)
            th = threading.Thread(name=thread_name, target=self.connectors[msg["driver"]],
                                  kwargs={"hostname": msg["zabbix_hostname"], "params": msg["params"]})
            th.start()
            self.threads.append(th)
        else:
            self.logger.warning("'%s' driver is not supported" % str(msg["driver"]))
        self.logger.debug("running threads: %s" % [{thread.name: thread.isAlive()} for thread in self.threads])

    def close(self):
        self.logger.info("SystemExit")
        if self.socket is not None:
            self.socket.close()
            self.socket = None
        for thread in self.threads:
            # Bad practice. but no idea
            thread._Thread__stop()
