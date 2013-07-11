---
layout: post
title: Q. Is it possible to assign VM to ESXi host name Zabbix HostGroup?
category: en 
---

## Answer

It is possible.  
HyClops realize the automatic assignment to Zabbix Hostgroup with MACRO information.
The assignment Hostgroup is decided by the MACRO {$VM_GROUPS}.
In "vSphereESXi" template, {$VM_GROUPS} is set "vSphereVM" by default.

Please change this MACRO setting in vSphereESXi host macro.

    {$VM_GROUPS} => vSphereVM,"HOST NAME"(*Not supported to expand {HOST.HOST}macro)

Note: Don't forget to set "vSphereVM"
