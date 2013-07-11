---
layout: post
title: Q. Is it possible to use GateOne for hosts in addition to EC2 instance or vSphere VM?
category: en
---

## Answer

It is possible to use Zabbix map and map icon url.
The process is following.

### 1: Create Map

- Create map to be displayed the connection target host on this map.
  - At Zabbix management Web page (Configuration->Maps->Create map)
  - 
- Set host type icon or hostgroup type icon on this created map.

### 2: Set GateOne URL to target map icon  

- Set GateOne access URL to map icons.
  - URL is GateOne page URL(gateone.php).
  - gateone.php can receive zabbix host ID GET parameter.

e.g.) http://zabbix-server-hostname/zabbix/gateone.php?hostid={HOST.ID}  
(You can set Zabbix Macro at map icon url)

### 3: Connect to SSH console with GateOne

- Click target host at the map view page.
- Click GateOne URL link in displayed menu.

