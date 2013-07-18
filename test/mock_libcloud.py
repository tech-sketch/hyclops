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


class MockNode(object):

    def __init__(self, id, name, state, public_ips, private_ips,
                 driver, size=None, image=None, extra=None):
        self.id = str(id) if id else None
        self.name = name
        self.state = state
        self.public_ips = public_ips if public_ips else []
        self.private_ips = private_ips if private_ips else []
        self.driver = driver
        self.size = size
        self.image = image
        self.extra = extra or {}

    def __repr__(self):
        return "MockNode<id=%s, name=%s, state=%s, public_ips=%s, private_ips=%s, driver=%s, size=%s, image=%s, extra=%s>" % (
               self.id, self.name, self.state, self.public_ips, self.private_ips, self.driver, self.size, self.image, self.extra)


class MockNodeDriver(object):

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 api_version=None, **kwargs):
        pass

    def list_nodes(self, ex_node_ids=None):
        return []

    def destroy_node(self, node):
        return True

    def reboot_node(self, node):
        return True


class MockEC2NodeDriver(MockNodeDriver):

    nodes = []
    images = []

    @classmethod
    def clear_mock(cls):
        cls.nodes = []
        cls.images = []

    @classmethod
    def add_mock_node(cls, node):
        cls.nodes.append(node)

    @classmethod
    def add_mock_image(cls, image):
        cls.images.append(image)

    def list_nodes(self, ex_node_ids=None):
        return [node for node in self.nodes if ex_node_ids is None or node.id in ex_node_ids]

    def list_images(self, location=None, ex_image_ids=None):
        return [image for image in self.images if ex_image_ids is None or image.id in ex_image_ids]

    def ex_start_node(self, node):
        return True

    def ex_stop_node(self, node):
        return True


class MockVSphereNodeDriver(MockNodeDriver):

    nodes = []
    hardware_profiles = []

    @classmethod
    def clear_mock(cls):
        cls.nodes = []
        cls.hardware_profiles = []

    @classmethod
    def add_mock_node(cls, node):
        cls.nodes.append(node)

    @classmethod
    def add_mock_hardware_profile(cls, hardware_profile):
        cls.hardware_profiles.append(hardware_profile)

    def list_nodes(self, ex_node_ids=None, ex_vmpath=None):
        return [node for node in self.nodes if ex_node_ids is None or node.id in ex_node_ids]

    def ex_start_node(self, node):
        return True

    def ex_stop_node(self, node):
        return True

    def ex_shutdown_node(self, node):
        return True

    def ex_hardware_profiles(self):
        return self.hardware_profiles
