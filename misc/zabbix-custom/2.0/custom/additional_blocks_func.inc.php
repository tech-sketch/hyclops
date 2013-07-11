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

// for All
function level_check($guest,$host){
	if($guest > $host*2){
		$item = new CCol($guest.'/'.$host,'high');
	}else if($guest > $host){
		$item = new CCol($guest.'/'.$host,'warning');
	}else{
		$item = new CCol($guest.'/'.$host,'normal');
	}
	return $item;
}

function check_script($form_name, $scriptname){
	if($form_name == "ipmi_control"){
		if(preg_match("/IPMI power/",$scriptname)){
			return true;
		}
	}else if($form_name == "poweron_vms"){
		if(preg_match("/(Stop|Reboot|Suspend) vSphere instance/", $scriptname)){
			return true;
		}
	}else if($form_name == "poweroff_vms"){
		if(preg_match("/Start vSphere instance/", $scriptname)){
			return true;
		}
	}else if($form_name == "suspend_vms"){
		if(preg_match("/vSphere instance/", $scriptname)){
			return true;
		}
	}else if($form_name == "other_vms"){
		if(preg_match("/vSphere instance/", $scriptname)){
			return true;
		}
	}else if($form_name == "ec2_poweron"){
		if(preg_match("/(Stop|Reboot) EC2 instance/", $scriptname)){
			return true;
		}
	}else if($form_name == "ec2_poweroff"){
		if(preg_match("/Start EC2 instance/", $scriptname)){
			return true;
		}
	}
	return false;
}

function make_operation_box_footer($hostids, $form_name){
	$box = new CComboBox("script");
	$hostScripts = API::Script()->getScriptsByHosts($hostids);
	$scripts = array();
	foreach($hostScripts as $hostid => $hscripts){
		foreach($hscripts as $script){
			if(!in_array($script, $scripts) && check_script($form_name, $script['name'])){
				array_push($scripts, $script);
			}
		}
	}
	foreach($scripts as $script){
		$option = new CComboItem($script['scriptid'], $script['name']);
		$box->addItem($option);
	}
	$button = new CButton('execute', _('Execute'), "return executeScriptOnMultipleHosts('${form_name}', 'script', 'hostids[]', 'Execute');");
	$button->setAttribute('id', 'executeButton');
	return array($box, $button);
}

function get_item_level($state){
	switch($state){
	case 'running':
		return 'normal';
	case 'rebooting':
	case 'pending':
	case 'terminated':
		return 'warning';
	case 'stopped':
		return null;
	case 'stuck':
		return 'average';
	case 'loading...':
		return null;
	default:
		return 'unknown';
	}
}

// for EC2

function make_ec2_table($form_name, $instances){
	$form = new CForm();
	$form->setName($form_name);
	$form->setAttribute('id', $form_name);
	$form->addVar('driver', 'ec2');
	$form->setAction('#');

	// Create Table Header
	$table = new CTableInfo();
	if($form_name == "ec2_poweron"){
		$table->setHeader(array(
			is_show_all_nodes() ? _('Node') : null,
			new CCheckBox('all_hosts', null, "checkAllHosts('".$form_name."', 'all_hosts', '');"),
			_('Instance name'),
			_('Status'),
			_('Interface'),
			_('Availability zone'),
			_('SSH Connect'),
		));
	}else{
		$table->setHeader(array(
			is_show_all_nodes() ? _('Node') : null,
			new CCheckBox('all_hosts', null, "checkAllHosts('".$form_name."', 'all_hosts', '');"),
			_('Instance name'),
			_('Status'),
			_('Interface'),
			_('Availability zone'),
		));
	}
	// Create Row
	foreach($instances as $instance){
		$json = new CJSON();
		$r = new CRow();
		$r->addItem(new CCheckBox("hostids[]", null, null, $instance['hostid']));
		$instance_name = new CSpan($instance["name"], 'pointer');
		$instance_name->setHint(make_ec2_detail_table($instance));
		$r->addItem(new CCol($instance_name));
		$r->addItem(new CCol($instance["state"], get_item_level($instance["state"])));
		$r->addItem($instance["public_dns"]);
		$r->addItem($instance["realm_id"]);
		if($form_name == "ec2_poweron"){
			$ssh_link = new CLink(_('connect'), "gateone.php?hostid=$instance[hostid]");
			$ssh_link->setTarget("_blank");
			$r->addItem($ssh_link);
		}
		$table->addRow($r);
	}

	$hostids = array_map(function($instance){return $instance['hostid'];}, $instances);
	$footer = get_table_header(make_operation_box_footer($hostids, $form_name));
	$form->addItem(array('', $table, '', $footer));
	return $form;
}

function make_ec2_detail_table($instance){
	$table = new CTableInfo();
	$table->setHeader(array(
		_('Key'),
		_('Value'),
		));
	foreach($instance as $key => $value){
		if(!is_null($data = filtering_detail_info($key,$value))){
			$r = new CRow();
			$r->addItem($data["key"]);
			$r->addItem($data["value"]);
			$table->addRow($r);
		}
	}
	return $table;
}

function filtering_detail_info($key,$value){
	$translate_table = array(
				"hostid" => _('Host ID'),
				"owner_hostid" => _('AWS account'),
				"instance_name" => _('Instance name'),
				"type" => _('Instance type'),
				"realm_id" => _('Availability zone'),
				"ami_id" => _('AMI ID'),
				"ami_name" => _('AMI name'),
				"private_dns" => _('Private DNS'),
				"launch_time" => _('Launch time'),
				"ramdisk_id" => _('Ramdisk ID'),
				"kernel_id" => _('Kernel ID'),
				"firewalls" => _('Security groups'),
				"instance_id" => _('Instance ID'),
				"elastic_ips" => _('Elastic IP'),
				"private_ips" => _('Private IP'),
				"platform" => _('Platform')
			);
	if(isset($translate_table[$key])){
		if(in_array($key, array("hostid", "owner_hostid"))){
			$value = new CLink($value, "latest.php?hostid={$value}");
		}
		return array("key" => $translate_table[$key], "value" => $value);
	}else{
		return null;
	}
}

// for vSphere

function make_vm_table($type, $instances){
	$form_name = "{$type}_vms";

	// Create Form
	$form = new CForm();
	$form->setName($form_name);
	$form->setAttribute('id', $form_name);
	$form->addVar('driver', 'vsphere');
	$form->setAction('#');

	// Create Table Header
	$table = new CTableInfo();
	switch($type){
	case 'poweron':
		$table->setHeader(array(
			is_show_all_nodes() ? _('Node') : null,
			new CCheckBox('all_hosts', null, "checkAllHosts('".$form_name."','all_hosts','');"),
			_('Instance name'),
			_('Status'),
			_('CPU threads'),
			_('Memory(GB)'),
			_('SSH Connect'),
		));
		break;
	case 'poweroff':
	case 'suspend':
		$table->setHeader(array(
			is_show_all_nodes() ? _('Node') : null,
			new CCheckBox('all_hosts', null, "checkAllHosts('".$form_name."','all_hosts','');"),
			_('Instance name'),
			_('Status'),
			_('CPU threads'),
			_('Memory(GB)'),
		));
		break;
	case 'other':
		$table->setHeader(array(
			is_show_all_nodes() ? _('Node') : null,
			_('Instance name'),
			_('Status'),
			_('CPU thread'),
			_('Memory(GB)'),
			_('Question'),
		));
		break;
	default:
		return null;
	}

	// Create Row
	foreach($instances as $instance){
		$table->addRow(make_hint_row($type, $instance));
	}

	$hostids = array_map(function($instance){return $instance['hostid'];}, $instances);
	$footer = get_table_header(make_operation_box_footer($hostids, $form_name));
	$form->addItem(array('', $table, '', $footer));
	return $form;
}

function make_hint_row($type, $instance){
	$state = $instance['state'];
	if($type == "other" && $instance["stuck_state"] == 1) $state = "stuck";
	$r = new CRow();
	if(in_array($type, array("poweron", "poweroff", "suspend"))){
		$r->addItem(new CCheckBox("hostids[]", null, null, $instance['hostid']));
	}
	$hostScripts = API::Script()->getScriptsByHosts(zbx_objectValues(array($instance['host']), 'hostid'));
	$hostSpan = new CSpan(nbsp($instance['name']), 'link_menu menu-host');
	$hostSpan->setAttribute('data-menu', hostMenuData($instance['host'], $hostScripts[$instance['hostid']]));
	$r->addItem($hostSpan);
	$r->addItem(new CCol($state, get_item_level($state)));
	$r->addItem($instance['cpu']);
	$r->addItem($instance['memory']);
	if($type == "other" && $instance["stuck_state"] == 1){
		$question = $instance['stuck_question'];
		$json = new CJSON();
		$choiceinfos = $json->decode($instance['stuck_choices'], true);
		$answer_form = new CForm();
		$answer_form->setAction('#');
		$answer_form->setAttribute('id', "answer");
		$answer_form->addVar("driver", "vsphere");
		$answer_form->addVar("hostids[]", $instance['hostid']);
		$instancename = $instance['host']['host'];
		$answer_button = new CButton('answer', _('Answer'), "return checkAnswer('answer', 'choice', '${instancename}', 'Execute');");
		$choice_table = new CTableInfo();
		foreach($choiceinfos as $choice){
			$radio = new CRadioButton('choice', $choice['key']);
			$label = new CLabel($choice['label']);
			$choice_table->addRow(new CRow(array($radio, $label)));
		}
		$answer_form->addItem($choice_table);
		$answer_form->addItem($answer_button);
		$question_span = new CSpan($question);
		$question_span->setHint($answer_form);
		$question_col = new CCol($question_span, 'warning');
		$r->addItem($question_col);
	}else if($type == "poweron"){
		$ssh_link = new CLink(_('connect'), "gateone.php?hostid=$instance[hostid]");
		$ssh_link->setTarget("_blank");
		$r->addItem($ssh_link);
	}
	return $r;
}

function make_datastore_table($hostid, $datastores){
	$table = new CTableInfo();
	$table->setHeader(array(
		_('Datastore Name'),
		_('Free Space'),
		_('Capacity'),
	));
	foreach($datastores as $datastore){
		$name_col = new CCol($datastore["name"]);
		$freeSpace = convert_units($datastore["freeSpace"], "B");
		$capacity = convert_units($datastore["capacity"], "B");
		$free_space_col = new CCol($freeSpace);
		$capacity_col = new CCol($capacity);
		$r = new CRow(array($name_col, $free_space_col, $capacity_col));
		$table->addRow($r);
	}
	return $table;
}

// for IPMI

function get_triggers($hostid){
	$options = array(
		'nodeids' => get_current_nodeid(),
		'hostids' => $hostid,
		'monitored' => 1,
		'expandData' => 1,
		'expandDescription' => 1,
		'expandExpression' => 1,
		'filter' => array(
			'value' => TRIGGER_VALUE_TRUE
		),
		'output' => API_OUTPUT_EXTEND,
	);
	return API::Trigger()->get($options);
}

function make_trigger_table($triggers, $host_name){
	$table = new CTableInfo();
	$table->setHeader(array(
			_('Host'),
			_('Problem'),
			_('Age')
	));
	foreach($triggers as $trigger){
		$description = $trigger["description"];
		$r = new CRow();
		$r->addItem($host_name);
		$r->addItem(new CCol($description, getSeverityStyle($trigger['priority'])));
		$r->addItem(zbx_date2age($trigger['lastchange']));
		$table->addRow($r);
	}
	return $table;
}

?>
