#!/usr/bin/env python

import os
import shutil
import commands
from setuptools import setup, Command


class ReplaceCommand(Command):
    description = "replace zabbix dashboard to custom version"
    user_options = [('frontend-dir=', 'd', 'zabbix frontend location'),
                    ('zabbix-version=', 'z', 'zabbix server version')]
    official_files = [
        "dashboard.php",
        "include/menu.inc.php",
    ]

    def initialize_options(self):
        self.frontend_dir = ""
        self.zabbix_version = "2.2"

    def finalize_options(self):
        pass

    def run(self):
        if not os.path.exists(self.frontend_dir):
            print "Target directory does not exist"
            return
        if not os.path.exists(os.path.join(self.frontend_dir, "dashboard.php")):
            print "Could not find dashboard.php"
            return
        if not os.path.exists(os.path.join(self.frontend_dir, "custom")):
            os.makedirs(os.path.join(self.frontend_dir, "custom"))
        if self.zabbix_version not in ['2.0', '2.2']:
            print "Not supported version (Supported only 2.0 or 2.2)"
            return
        from_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "misc/zabbix-custom/%s/" % self.zabbix_version)
        for searchpath, dirs, files in os.walk(from_dir):
            for file in files:
                basename = os.path.join(searchpath, file).replace(from_dir, '')
                src_path = os.path.join(searchpath, file)
                dst_path = os.path.join(self.frontend_dir, basename)
                if basename in self.official_files:
                    backup_path = dst_path.replace('.php', '.org')
                    if os.path.exists(backup_path):
                        print "backup file already exists: %s" % backup_path
                    else:
                        print "backup original file %s to %s" % (dst_path, backup_path)
                        shutil.move(dst_path, backup_path)
                if os.path.exists(dst_path):
                    print "update %s" % dst_path
                else:
                    print "create %s" % dst_path
                shutil.copy2(src_path, dst_path)


class RollbackCommand(Command):
    description = "rollback zabbix dashboard to original version"
    user_options = [('frontend-dir=', 'd', 'zabbix frontend location'),
                    ('zabbix-version=', 'z', 'zabbix server version')]
    official_files = [
        "dashboard.php",
        "include/menu.inc.php",
    ]

    def initialize_options(self):
        self.frontend_dir = ""
        self.zabbix_version = "2.2"

    def finalize_options(self):
        pass

    def run(self):
        if not os.path.exists(self.frontend_dir):
            print "Target directory does not exist"
            return
        if self.zabbix_version not in ['2.0', '2.2']:
            print "Not supported version (Supported only 2.0 or 2.2)"
            return
        from_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "misc/zabbix-custom/%s/" % self.zabbix_version)
        for searchpath, dirs, files in os.walk(from_dir):
            for file in files:
                basename = os.path.join(searchpath, file).replace(from_dir, '')
                dst_path = os.path.join(self.frontend_dir, basename)
                if basename in self.official_files:
                    backup_path = dst_path.replace('.php', '.org')
                    if os.path.exists(backup_path):
                        print "rollback %s to %s" % (backup_path, dst_path)
                        shutil.move(backup_path, dst_path)
                    else:
                        print "%s does not exist" % backup_path
                else:
                    if os.path.exists(dst_path):
                        print "remove %s" % dst_path
                        os.remove(dst_path)
        if os.path.exists(os.path.join(self.frontend_dir, "custom")):
            os.rmdir(os.path.join(self.frontend_dir, "custom"))


class ImportCommand(Command):
    description = "import zabbix global scripts and global macros"
    user_options = [("frontend-url=", "f", "zabbix frontend url"),
                    ("user=", "u", "zabbix user name"),
                    ("password=", "p", "zabbix password")]

    def initialize_options(self):
        # set default value
        self.frontend_url = "http://localhost/zabbix"
        self.user = "Admin"
        self.password = "zabbix"

    def finalize_options(self):
        pass

    def run(self):
        from zabbix_api import ZabbixAPI, ZabbixAPIException
        from xml.etree import ElementTree
        # connect zabbix frontend
        try:
            self.zabbix_api = ZabbixAPI(self.frontend_url)
            self.zabbix_api.login(self.user, self.password)
        except ZabbixAPIException, e:
            print "Failed to connect zabbix frontend: %s" % str(e[0]).partition("while sending")[0]
            return
        # import templates
        print "Import templates"
        try:
            with open(os.path.join(pwd, "misc/import_data/templates.xml")) as f:
                template_xml = f.read()
                req = self.zabbix_api.json_obj("configuration.import", {
                    "format": "xml",
                    "source": template_xml,
                    "rules": {
                        "items": {"createMissing": True},
                        "applications": {"createMissing": True},
                        "graphs": {"createMissing": True},
                        "groups": {"createMissing": True},
                        "templateLinkage": {"createMissing": True},
                        "templates": {"createMissing": True},
                        "triggers": {"createMissing": True},
                    }
                })
                self.zabbix_api.do_request(req)
        except IOError, e:
            print "  " + str(e)
        except ZabbixAPIException, e:
            print "  " + str(e[0]).partition("while sending")[0]
        # import global scripts
        print "Import global scripts"
        tree = ElementTree.parse(os.path.join(pwd, "misc/import_data/globalscripts.xml"))
        for script in tree.find("scripts"):
            try:
                params = {}
                params["name"] = script.findtext("name")
                params["command"] = script.findtext("command")
                params["host_access"] = script.findtext("host_access", 2)
                params["description"] = script.findtext("description", "")
                params["confirmation"] = script.findtext("confirmation", "")
                params["type"] = script.findtext("type", 0)
                params["execute_on"] = script.findtext("execute_on", 1)
                params["usrgrpid"] = self.get_user_group_id(script.find("usergroups"))
                params["groupid"] = self.get_group_id(script.find("groups"))
                self.zabbix_api.script.create(params)
                print "  " + "Create '%s'" % params["name"]
            except ZabbixAPIException, e:
                print "  " + str(e[0]).partition("while sending")[0]
        # import global macros
        print "Import global macros"
        tree = ElementTree.parse(os.path.join(pwd, "misc/import_data/globalmacros.xml"))
        for macro in tree.find("macros"):
            try:
                params = {}
                params["macro"] = macro.findtext("macro")
                params["value"] = macro.findtext("value")
                self.zabbix_api.usermacro.createglobal(params)
                print "  " + "Create '%s'" % params["macro"]
            except ZabbixAPIException, e:
                print "  " + str(e[0]).partition("while sending")[0]

    def get_user_group_id(self, usergroups, default=0):
        if len(usergroups) == 0:
            return default
        else:
            groupids = []
            for group in usergroups:
                name = group.findtext("name")
                grps = self.zabbix_api.usergroup.get({
                    "filter": {"name": name},
                })
                if grps and "groupid" in grps[0]:
                    groupids.append(grps[0]["groupid"])
        return groupids[0] if groupids else default

    def get_group_id(self, groups, default=0):
        if len(groups) == 0:
            return default
        else:
            groupids = []
            for group in groups:
                name = group.findtext("name")
                grps = self.zabbix_api.hostgroup.get({
                    "filter": {"name": name},
                })
                if grps and "groupid" in grps[0]:
                    groupids.append(grps[0]["groupid"])
        return groupids[0] if groupids else default


# setup
pwd = os.path.abspath(os.path.dirname(__file__))
setup(name='hyclops',
      version='0.2.0',
      description='Hybrid cloud operations plugin for Zabbix',
      author='TIS Inc.',
      author_email='hyclops@ml.tis.co.jp',
      url='http://tech-sketch.github.io/hyclops',
      package_dir={'hyclops': os.path.join(pwd, 'hyclops')},
      packages=['hyclops', 'hyclops.connector', 'hyclops.libcloud_driver'],
      data_files=[
          ('/opt/hyclops', [os.path.join(pwd, 'hyclops.conf'), os.path.join(pwd, 'run.py')]),
          ('/opt/hyclops/globalscripts', [os.path.join(pwd, 'misc/globalscripts/request_action.py')]),
          ('/opt/hyclops/logs', []),
          ('/var/run/hyclops', []),
          ('/opt/hyclops/cron_scripts', [os.path.join(pwd, 'misc/cron_scripts/delete_not_exist_hosts.py')])
      ],
      install_requires=['apache_libcloud >=0.12.1', 'zabbix_api', 'pyzmq', 'psphere', 'configobj', 'python_daemon'],
      cmdclass={'replace': ReplaceCommand, 'rollback': RollbackCommand, 'import': ImportCommand})
# hyclops user add
if os.system('/usr/bin/id hyclops') != 0:
    nologin_path = commands.getoutput('/usr/bin/which nologin')
    print nologin_path
    os.system('/usr/sbin/useradd hyclops -s ' + nologin_path)
# change owner /opt/hyclops & /var/run/hyclops
os.system('chown hyclops:hyclops -R /opt/hyclops/')
os.system('chown hyclops:hyclops /var/run/hyclops/')
