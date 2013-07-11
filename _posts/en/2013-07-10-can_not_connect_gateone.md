---
layout: post
title: Q. I can't access GateOne. What is the cause?
category: en 
---

## Answer

It is likely to be generated under the following 4 reasons.
Please check your system situation.

* Problem of security credential
* Problem of time gap between Zabbix Server & GateOne Server
* Problem of API key configuration
* Problem of settings allowing access server

### Problem of security credential

When the GateOne server security credential is not reliable, GateOne does not display anything.
So, you can take two approaches.

* Register the reliable security credential to GateOne server
* Register the GateOne server as exception

### Problem of time gap between Zabbix Server & GateOne Server

GateOne use datetime information at the two timings (generate auth token & authenticate token).
Genarating auth token is executed in Zabbix Server.
Authenticating token is executed in GateOne Server.
So, both of Zabbix Server time & GateOne server time must be same.

GateOne log(/opt/gateone/logs/webserver.log)

    API authentication failed due to an expired auth object.
    If you just restarted the server this is normal (users just need to reload the page).
    If  this problem persists it could be a problem with the server's clock (either this server or the server(s) embedding Gate One).

### Problem of API key configuration

Please check api_keys settings in "/opt/gateone/server.conf" and Zabbix global macro settings.

2 global macros:

* {$GATEONE_KEY}
* {$GATEONE_SECRET}

If there is wrong settings, the following logs are written in GateOne log.

    Error running plugin WebSocket action: ssh_get_connect_string

### Problem of settings allowing access server

GateOne is implemented the feature which control access.
This is set at "origins" in "/opt/gateone/server.conf".
Please check this settings.

If there is wrong settings, the following logs are written in GateOne log.

    Access denied for origin: http://zabbix-server-hostname

In this error case, please set the following "origins" settings.

    origins = "http://zabbix-server-hostname"

After setting, please restart GateOne.

