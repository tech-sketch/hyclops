<?php
/*
** HyClops for Zabbix
** Copyright 2013 TIS Inc.
** 
** This program is free software; you can redistribute it and/or
** modify it under the terms of the GNU General Public License
** as published by the Free Software Foundation; either version 2
** of the License, or (at your option) any later version.
** 
** This program is distributed in the hope that it will be useful,
** but WITHOUT ANY WARRANTY; without even the implied warranty of
** MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
** GNU General Public License for more details.
** 
** You should have received a copy of the GNU General Public License
** along with this program; if not, write to the Free Software
** Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
**/


/****** get informations ******/

function get_macro($hostid, $macro_name, $force = false){
	$macros = API::UserMacro()->get(array("output" => API_OUTPUT_EXTEND, "hostids" => array($hostid), "nopermissions" => $force));
	foreach($macros as $macro){
		if($macro['macro'] === $macro_name){
			return $macro['value'];
		}
	}
	return null;
}

function get_inventory_value($hostid, $key){
	$hosts = API::Host()->get(array(
		"hostids" => $hostid,
		"selectInventory" => API_OUTPUT_EXTEND
	));
	if(!empty($hosts)){
		$inventory = $hosts[0]["inventory"];
		if(array_key_exists($key, $inventory)){
			return $inventory[$key];
		}
	}
	return null;
}

function get_item_value($hostid, $key){
	$owner_host = get_owner($hostid);
	$push_message_itemkey = "push_message.py";
	$push_message_items = API::Item()->get(array("hostids" => $owner_host['hostid'], "search" => array("key_" => $push_message_itemkey), "output" => "extend"));
	$max_delay = 0;
	foreach($push_message_items as $item){
		if((int)$item['delay'] > $max_delay)$max_delay = (int)$item['delay'];
	}
	$ZBX_EXPIRED_THRESHOLD = $max_delay * 2;
	if($ZBX_EXPIRED_THRESHOLD < 300){
		$ZBX_EXPIRED_THRESHOLD = 300;
	}
	$items = API::Item()->get(array("hostids" => $hostid, "filter" => array("key_" => $key), "output" => "extend"));
	if(!empty($items)){
		$item = $items[0];
		if(!empty($item["error"])){
			return _('error');
		}
		if(empty($item["lastclock"])){
			return _('no data');
		}
		if(time() - $item["lastclock"] < $ZBX_EXPIRED_THRESHOLD){
			return $item["lastvalue"];
		}else{
			return _('data too old');
		}
	}
	return null;
}

function is_script_success($hostid, $script_itemkey){
	$items = API::Item()->get(array(
		"hostids" => $hostid,
		"filter" => array(
			"type" => ITEM_TYPE_EXTERNAL,
			"status" => HOST_STATUS_MONITORED,
		),
		"search" => array(
			"key_" => $script_itemkey,
		),
		"output" => "extend"
	));
	if(!empty($items)){
		$result = true;
		foreach($items as $item){
			$result = $result && empty($item["error"]) && $item["lastvalue"] == 0;
		}
	}else{
		$result = false;
	}
	return $result;
}

function get_hardware_profiles($hostid){
	$json = new CJSON();
	$networks = $json->decode(get_item_value($hostid, "deltacloud.hardware_profiles.networks"),true);
	if(empty($network)) $networks = array();
	$hardware_profiles = array(
		"cpu" => get_item_value($hostid, "hardware.cpu"),
		"cpu_assigned" => get_item_value($hostid, "hardware.cpu.assigned"),
		"memory" => round(get_item_value($hostid, "hardware.memory")/pow(1024,3),3),
		"memory_assigned" => round(get_item_value($hostid, "hardware.memory.assigned")/pow(1024,3),3),
		"networks" => $networks,
	);
	return $hardware_profiles;
}

function get_datastores($hostid, $sortfield = "name", $sortorder = "ASC"){
	$datastores_json = get_item_value($hostid, "hardware.datastores");
	if(empty($datastores_json)){
		return array();
	}
	$json = new CJSON();
	$datastores = $json->decode($datastores_json, true);
	if(is_array($datastores)){
		sort_data_array($datastores, $sortfield, $sortorder);
		return $datastores;
	}else{
		return array();
	}
}

function libcloud_state_mapping($libcloud_state){
	switch($libcloud_state){
		case "0":
			return "running";
			break;
		case "1":
			return "rebooting";
			break;
		case "2":
			return "terminated";
			break;
		case "3":
			return "pending";
			break;
		case "4":
			# stopped or unknown
			return "stopped";
			break;
		default:
			return "others";
			break;
	}
}

function get_instances($owner_hostid, $sortfield = "name", $sortorder = "ASC"){
	$NOT_EXIST_HOSTGROUP_NAME = "Not exist hosts";
	$owner_host = get_owner($owner_hostid);
	$all_hosts = API::Host()->get(array(
				"output" => "extend",
				"selectInventory" => "extend",
				"selectInterfaces" => "extend",
				"selectScreens" => "extend",
				"selectGroups" => "extend",
			));
	$instances = array();
	foreach($all_hosts as $host){
		foreach($host["groups"] as $group){
			if($group["name"] == $NOT_EXIST_HOSTGROUP_NAME){
				continue 2;
			}
		}
		if(!isset($host["inventory"]["tag"])){ continue; }
		if($owner_host["host"] == $host["inventory"]["tag"]){
			$name = get_inventory_value($host["hostid"], "name");
			if(empty($name)){
				$name = empty($host["name"]) ? $host["host"] : $host["name"];
			}
			$instance = array(
				#ALL
				"host" => $host,
				"hostid" => $host["hostid"],
				"owner_hostid" => $owner_host["hostid"],
				"name" => $name,
				"state" => libcloud_state_mapping(get_item_value($host["hostid"],"instance.state")),
				#EC2
				"instance_id" => $host["host"],
				"instance_name" => get_inventory_value($host["hostid"], "name"),
				"type" => get_item_value($host["hostid"], "instance.type"),
				"realm_id" => get_item_value($host["hostid"], "instance.availability_zone"),
				"keyname" => get_item_value($host["hostid"], "instance.keyname"),
				"firewalls" => get_item_value($host["hostid"], "instance.security_groups"),
				"public_dns" => get_main_address($host["hostid"], INTERFACE_TYPE_AGENT),
				"ami_id" => get_item_value($host["hostid"], "instance.ami_id"),
				"private_dns" => get_item_value($host["hostid"], "instance.private_dns"),
				"elastic_ips" => get_item_value($host["hostid"], "instance.elastic_ips"),
				"private_ips" => get_item_value($host["hostid"], "instance.private_ips"),
				"launch_time" => get_item_value($host["hostid"], "instance.launch_time"),
				"ramdisk_id" => get_item_value($host["hostid"], "instance.ramdisk_id"),
				"kernel_id" => get_item_value($host["hostid"], "instance.kernel_id"),
				"platform" => get_item_value($host["hostid"], "instance.platform"),
				"ami_name" => get_item_value($host["hostid"], "instance.ami_name"),
				# vSphereVM
				"cpu" => get_item_value($host["hostid"], "instance.cpu"),
				"memory" => get_item_value($host["hostid"], "instance.memory"),
				"stuck_state" => intval(get_item_value($host["hostid"], "instance.stuck.state")),
				"stuck_question" => get_item_value($host["hostid"], "instance.stuck.question"),
				"stuck_choices" => get_item_value($host["hostid"], "instance.stuck.choices"),
			);
			if(!empty($instance["memory"]) && (int)$instance["memory"] != 0) $instance["memory"] = $instance["memory"]/pow(1024,3);
			array_push($instances, $instance);
		}	
	}
	sort_data_array($instances, $sortfield, $sortorder);
	return $instances;
}

function filter_instances($instances){
	$states = array("running", "pending", "stopped", "other");
	$filtered_instances = array();
	foreach($states as $state){
		$filtered_instances[$state] = array();
	}
	foreach($instances as $instance){
		$state = $instance["state"];
		if($state == NULL || $instance["stuck_state"] == 1){
			array_push($filtered_instances["other"], $instance);
		}elseif(in_array($state, $states)){
			array_push($filtered_instances[$state], $instance);
		}else{
			array_push($filtered_instances["other"], $instance);
		}
	}
	return $filtered_instances;
}

function sort_data_array(&$data, $sortfield, $sortoder){
	$sort_array = array();
	foreach($data as $index => $obj){
		if(array_key_exists($sortfield, $obj)){
			$value = $obj[$sortfield];
			if(is_string($value)){
				$value = strtolower($value);
			}
			$sort_array[$index] = $value;
		}else{
			$sort_array[$index] = null;
		}
	}
	$order = $sortoder == "DESC" ? SORT_DESC : SORT_ASC;
	array_multisort($sort_array, $order, $data);
}

function get_vsphere_hosts($sortfield = "name", $sortorder = "ASC"){
	$templates = API::Template()->get(array(
		"filter" => array("host" => "vSphereESXi"),
		"selectHosts" => "extend"
	));
	$vsphere_hosts = array();
	if(!empty($templates)){
		$all_hosts = array_filter($templates[0]["hosts"], function($h){return $h["status"] == HOST_STATUS_MONITORED;});
		foreach($all_hosts as $host){
			if(check_vsphere_settings($host['hostid'])){
				array_push($vsphere_hosts, $host);
			}
		}
	}
	sort_data_array($vsphere_hosts, $sortfield, $sortorder);
	return $vsphere_hosts;
}

function get_ipmi_hosts($sortfield = "name", $sortorder = "ASC"){
	$templates = API::Template()->get(array(
		"filter" => array("host" => "IPMI"),
		"selectHosts" => "extend"
	));
	$ipmi_hosts = array();
	if(!empty($templates)){
		$all_hosts = array_filter($templates[0]["hosts"], function($h){return $h["status"] == HOST_STATUS_MONITORED;});
		foreach($all_hosts as $host){
			if(check_ipmi_settings($host['hostid'])) array_push($ipmi_hosts, $host);
		}
	}
	sort_data_array($ipmi_hosts, $sortfield, $sortorder);
	return $ipmi_hosts;
}

function get_aws_accounts($sortfield = "name", $sortorder = "ASC"){
	$templates = API::Template()->get(array(
		"filter" => array(
			"host" => "AWSAccount"
		),
		"selectHosts" => API_OUTPUT_EXTEND
	));
	if(!empty($templates)){
		$aws_accounts = array_filter($templates[0]["hosts"], function($h){return $h["status"] == HOST_STATUS_MONITORED;});
		sort_data_array($aws_accounts, $sortfield, $sortorder);
		return $aws_accounts;
	}else{
		return array();
	}
}

function get_owner($hostid){
	if(check_template($hostid, "vSphereESXi") || check_template($hostid, "AWSAccount")){
		$hosts = API::Host()->get(array(
			"hostids" => $hostid,
			"output" => "extend",
			"nopermissions" => "true"
		));
		return $hosts[0];
	}else{
		$owner_hostname = get_inventory_value($hostid, "tag");
		$hosts = API::Host()->get(array(
			"filter" => array("host" => $owner_hostname),
			"output" => "extend",
			"nopermissions" => "true",
		));
		if(empty($hosts)){
			return null;
		}else{
			return $hosts[0];
		}
	}
}

function is_operation_available($driver, $state){
	$ipmi_allowed_state = array("running", "stopped");
	if($driver == "ipmi"){
		return in_array(strtolower($state), $ipmi_allowed_state);
	}else{
		return false;
	}
}

// get zabbix interface informations

function get_interfaces($hostid, $type = INTERFACE_TYPE_ANY){
	$options = array('hostids' => $hostid, 'output' => API_OUTPUT_EXTEND);
	if($type != INTERFACE_TYPE_ANY){
		$options['filter'] = array('type' => $type);
	}
	return API::Hostinterface()->get($options);
}

function get_addresses($hostid, $type = INTERFACE_TYPE_ANY){
	$interfaces = get_interfaces($hostid, $type);
	$addresses = array();
	foreach($interfaces as $interface){
		$address = $interface['useip'] == INTERFACE_USE_IP ? $interface['ip'] : $interface['dns'];
		array_push($addresses, $address);
	}
	return $addresses;
}

function get_main_address($hostid, $type = INTERFACE_TYPE_AGENT){
	$interfaces = get_interfaces($hostid, $type);
	foreach($interfaces as $interface){
		if($interface['main'] == 1){
			return $interface['useip'] == INTERFACE_USE_IP ? $interface['ip'] : $interface['dns'];
		}
	}
	return null;
}

// check settings

function check_template($hostid, $template_name){
	$hosts = API::Host()->get(array(
		"hostids" => $hostid,
		"selectParentTemplates" => API_OUTPUT_EXTEND
	));
	$templates = $hosts[0]["parentTemplates"];
	foreach($templates as $template){
		if($template["host"] == $template_name){
			return true;
		}
	}
	return false;
}

function check_ipmi_settings($hostid){
	if(!check_template($hostid, "IPMI")) return false;
	$interfaces = get_interfaces($hostid, INTERFACE_TYPE_IPMI);
	$hosts = API::Host()->get(array(
		"hostids" => $hostid,
		"output" => API_OUTPUT_EXTEND,
	));
	if(!empty($interfaces) && !empty($hosts) && !empty($hosts[0]['ipmi_username']) && !empty($hosts[0]['ipmi_password'])){
		return true;
	}
	return false;
}

function check_vsphere_settings($hostid){
	if(check_template($hostid, "vSphereVM")){
		$owner = get_owner($hostid);
		if($owner){
			$owner_hostid = $owner["hostid"];
		}else{
			return false;
		}
	}elseif(check_template($hostid, "vSphereESXi")){
		$owner_hostid = $hostid;
	}else{
		return false;
	}
	// check credentials
	$user = get_macro($owner_hostid, '{$KEY}');
	$pass = get_macro($owner_hostid, '{$SECRET}');
	if(!empty($user) && !empty($pass)){
		return true;
	}
	return false;
}

function check_aws_settings($hostid){
	if(check_template($hostid, "AmazonEC2")){
		$owner = get_owner($hostid);
		if(!empty($owner)){
			$owner_hostid = $owner["hostid"];
		}else{
			return false;
		}
	}elseif(check_template($hostid, "AWSAccount")){
		$owner_hostid = $hostid;
	}else{
		return false;
	}
	// check credentials
	$access_key = get_macro($owner_hostid, '{$KEY}');
	$secret_key = get_macro($owner_hostid, '{$SECRET}');
	if(!empty($access_key) && !empty($secret_key)){
		return true;
	}
	return false;
}
?>
