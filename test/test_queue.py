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


import unittest
import logging
import threading
import time
import configobj
from mock import Mock, patch
from hyclops.queue import MessageQueue


class TestMessageQueue(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger('queue')
        logger.addHandler(logging.NullHandler())
        self.patchers = [
            patch('hyclops.connector.ec2.EC2Connector.__new__'),
            patch('hyclops.connector.vsphere.VSphereConnector.__new__'),
            patch('hyclops.connector.ipmi.IPMIConnector.__new__'),
        ]
        for patcher in self.patchers:
            patcher.start()
        self.queue = MessageQueue(config=configobj.ConfigObj("test/conf/test.conf"))

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def test_init(self):
        self.assertIsInstance(self.queue.logger, logging.Logger)
        self.assertListEqual(self.queue.threads, [])
        self.assertIsNotNone(self.queue.connectors["ec2"])
        self.assertIsNotNone(self.queue.connectors["vsphere"])
        self.assertIsNotNone(self.queue.connectors["ipmi"])
        self.assertIsNone(self.queue.socket)

    def test_recv_message(self):
        test_data = [
            {"config": {"recv_pyobj.return_value": "bad_message"},
             "expect": None},
            {"config": {"recv_pyobj.return_value": ["ec2", "AWSAccount", "bad params"]},
             "expect": {"driver": "ec2", "zabbix_hostname": "AWSAccount", "params": {}}},
            {"config": {"recv_pyobj.return_value": ["ec2", "AWSAccount", '{"command":"monitor"}']},
             "expect": {"driver": "ec2", "zabbix_hostname": "AWSAccount", "params": {"command": "monitor"}}},
            {"config": {"recv_pyobj.return_value": ["ec2", "AWSAccount"]},
             "expect": {"driver": "ec2", "zabbix_hostname": "AWSAccount", "params": {}}},
        ]
        # queue is not opened
        self.assertIsNone(self.queue._recv_message())
        for data in test_data:
            self.queue.socket = Mock(**data["config"])
            if data["expect"] is None:
                self.assertIsNone(self.queue._recv_message())
            else:
                self.assertDictEqual(self.queue._recv_message(), data["expect"])

    def test_bind(self):
        with patch("zmq.Context") as m:
            # bind success
            mock_socket = Mock(**{"setsockopt.return_value": True, "bind.return_value": True})
            m.return_value = Mock(**{"socket.return_value": mock_socket})
            self.queue.bind()
            self.assertEqual(self.queue.socket, mock_socket)
            # bind failure
            mock_socket = Mock(**{"setsockopt.return_value": True, "bind.side_effect": Exception()})
            m.return_value = Mock(**{"socket.return_value": mock_socket})
            with self.assertRaises(Exception):
                self.queue.bind()

    def test_poll(self):
        with patch("hyclops.queue.MessageQueue._recv_message") as m:
            # message does not exist
            m.return_value = None
            self.assertIsNone(self.queue.poll())
            self.assertListEqual(self.queue.threads, [])
            # driver does not exist
            m.return_value = {"driver": "not exist", "zabbix_hostname": "", "params": {}}
            self.assertIsNone(self.queue.poll())
            self.assertListEqual(self.queue.threads, [])
            # receive correct message
            mock_connector = Mock(side_effect=(lambda hostname, params: time.sleep(1)))
            self.queue.connectors["ec2"] = mock_connector
            self.queue.connectors["vsphere"] = mock_connector
            self.queue.connectors["ipmi"] = mock_connector
            test_messages = [
                {"driver": "ec2", "zabbix_hostname": "Hostname", "params": {}},
                {"driver": "vsphere", "zabbix_hostname": "Hostname", "params": {}},
                {"driver": "ipmi", "zabbix_hostname": "Hostname", "params": {}},
                {"driver": "ipmi", "zabbix_hostname": "Hostname", "params": {}},
            ]
            for test_message in test_messages:
                m.return_value = test_message
                self.queue.poll()
                thread_name = test_message["driver"] + "-" + test_message["zabbix_hostname"] + "-" + test_message["params"].get("command", "monitor")
                self.assertTrue(thread_name in [thread.name for thread in self.queue.threads])
            self.assertEqual(len(self.queue.threads), 3)
            time.sleep(1)
            m.return_value = {"driver": "unknown", "zabbix_hostname": "unknown", "params": {}}
            self.queue.poll()
            self.assertTrue(len(self.queue.threads) < 3)

    def test_close(self):
        # queue is already closed
        self.queue.close()
        self.assertIsNone(self.queue.socket)
        self.assertEqual(len([thread for thread in self.queue.threads if thread.isAlive()]), 0)
        # close running queue
        self.queue.socket = Mock(**{"close.return_value": True})
        mock_connector = Mock(side_effect=(lambda: time.sleep(10)))
        self.queue.threads.append(threading.Thread(target=mock_connector))
        self.queue.close()
        self.assertIsNone(self.queue.socket)
        self.assertEqual(len([thread for thread in self.queue.threads if thread.isAlive()]), 0)


if __name__ == '__main__':
    unittest.main()
