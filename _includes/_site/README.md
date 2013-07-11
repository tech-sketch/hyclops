Product Name
=================================

About {#about}
--------------

HyClops is Zabbix extention that provide functions to management Amazon EC2 and VMware vSphere on Zabbix.
It extends Zabbix capability by using externalscripts, zabbix sender and message queue.

HyClops provides following features:

- automatically register EC2 instances and vSphere virtual machines to zabbix.
- monitor basic instance informations without zabbix agent. (using EC2 API or vSphere API)
- start/stop instances from Zabbix global script.
- (Experiments) display EC2 and vSphere informations on Zabbix dashboard by replacing dashboard to customized one.
- (Experiments) connect SSH console of each instances from customized dashboard by using [Gate One](https://github.com/liftoff/GateOne).


Release Notes {#releases}
-------------------------

- 2013/06/01 ver.0.1.0
  - Beta release

Architecture {#archtecture}
---------------------------

Install {#install}
------------------

### Requirements 

The following requirements exist for running this product:

- Zabbix (>= 2.0) with zabbix sender
- Python (>= 2.6) (developed on python 2.7)
- python-setuptools
- ZeroMQ
- ipmitool
- Gate One (if you want to use ssh console from browser)

### Install Zabbix

see <https://www.zabbix.com/documentation/2.0/manual/installation>

### Install Python

    yum install python-devel python-setuptools

### Install ZeroMQ and ipmitool

    wget -O /etc/yum.repos.d/zeromq.repo http://download.opensuse.org/repositories/home:/fengshuo:/zeromq/CentOS_CentOS-6/home:fengshuo:zeromq.repo
    yum install zeromq-devel ipmitool

### Install GateOne (Optional)

see <http://liftoff.github.io/GateOne/About/index.html>

### Install HyClops

    wget https://github.com/xxxx/
    tar xvzf hyclops-0.1.0.tar.gz
    cd hyclops-0.1.0
    python setup.py install

#### Copy init script

for RHEL/CentOS

    cp ./misc/init.d/redhat/hyclops /etc/init.d/

#### Copy external scripts for Zabbix

    cp ./misc/externalscripts/* /usr/lib/zabbix/externalscripts/

#### Replace some Zabbix dashboard files

    python setup.py replace -d (zabbix frontend document root path) -z (2.0 or 2.2)


Install requirements
--------------------

### Install Zabbix


### Install Python


### Install ZeroMQ and ipmitool

### (Optional) Install Gate One

see <http://liftoff.github.io/GateOne/About/index.html>


Install HyClops
----------------------

### Install HyClops

    python setup.py install

### Install init script

for RHEL/CentOS

    cp ./misc/init.d/redhat/hyclops /etc/init.d/

### Install external scripts

    cp ./misc/externalscripts/* /usr/lib/zabbix/externalscripts/

### (Optional) Install Zabbix custom dashboard

    python setup.py replace -d (zabbix frontend document root path)


HyClops Settings
-----------------------

### Setting zabbix information

    vi /opt/hyclops/hyclops.conf
        [zabbix]
        zabbix_server = (zabbix server ip or dns)
        zabbix_port = (zabbix server port)
        frontend_url = (zabbix frontend url)
        zabbix_user = (zabbix username)
        zabbix_password = (zabbix password)
        zabbix_sender = (zabbix sender path)


Zabbix settings
---------------

### Import templates and scripts

    python setup.py import -f <zabbix frontend url> -u <zabbix username> -p <zabbix password>
    (e.g. python setup.py import -f http://localhost/zabbix -u Admin -p zabbix)

### Create value mapping

Open "Administration > General > Value mapping"

- Script return code
  - 0 => success
  - 1 => failure
- Libcloud Node State
  - 0 => running
  - 1 => rebooting
  - 2 => terminated
  - 3 => pending
  - 4 => stopped

### Create zabbix host

for AWS EC2

- Templates: 'AWSAccount'
- Macros:
  - {$KEY}: AWS Access key
  - {$SECRET}: AWS Secret Key

for vSphere ESXi

- SNMP interfaces: vSphere ESXi management interface
- Templates: 'vSphereESXi'
- Macros:
  - {$KEY}: vSphere username
  - {$SECRET}: vSphere password


(Optional) Gate One settings
----------------------------

Gate One setting

    /opt/gateone/gateone.py --new_api_key
    vi /opt/gateone/server.conf
        auth = "api"

Zabbix Setting

- Open "Administration > General > Macros"
- Register global macros
  - {$GATEONE_URL} => (gateone server URL)
  - {$GATEONE_KEY} => (gateone api key)
  - {$GATEONE_SECRET} => (gateone secret key)

(api key and secret key are described in /opt/gateone/server.conf)


Start HyClops
--------------------

    (optional) sudo service gateone start
    sudo service hyclops start


Contact
-------

Please send feedback to the mailing list at <xxx@example.com>.


License
-------

[Link to Requirements](#requirements)

Copyright &copy; 2013 TIS Inc.
Licensed under the [GPL](http://www.gnu.org/licenses/gpl.html)

