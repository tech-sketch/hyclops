---
layout: post
title: Q. Operations(start/stop/reboot) timed out.Is there a solution?
category: en
---

## Answer

HyClops uses Zabbix GlobalScript feature for operation of start/stop/reboot.
Zabbix GlobalScript is executed by Zabbix Frontend.
So,you should change timeout settings in Zabbix frontend configuration.

Please check the following settings.

(Zabbix_frontend_directory]/include/defines.inc.php

    define('ZBX_SCRIPT_TIMEOUT',            60); // in seconds

Default settings is 60 seconds.

