---
layout: post
title: Q. Is it possible to reduce the high load of HyClops?
category: en
---

## Answer

In current HyClops, it is high load to some extent.  
Followings should be considered not to influence to monitoring in Zabbix server.

### Adjust monitoring interval

- Set the monitoring interval of push message item(push_message.py item) as long as possible.
  - Default is 5 minutes
  -

**Notes**

    Synchronization with each environment is delayed.

### Divided HyClops server from Zabbix server

HyClops can be divided into HyClops server and  Zabbix server.
Because HyClops communicates with http.

**Notes**

    It may be high cost for this divided management.

