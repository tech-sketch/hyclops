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

require_once(dirname(__FILE__).'/additional_func.inc.php');
require_once(dirname(__FILE__).'/additional_blocks_func.inc.php');
require_once(dirname(__FILE__).'/../include/items.inc.php');

function make_ipmistat_summary($preloading = false){
	$form_name = 'ipmi_control';
	$table = new CTableInfo();
	$ipmicontrol_form = new CForm();
	$ipmicontrol_form->setName('ipmi_control');
	$ipmicontrol_form->setAttribute('id','ipmi_control');
	$ipmicontrol_form->addVar('driver', 'ipmi');
	$script_itemkey = 'push_message.py[{$HYCLOPS_SERVER},{$HYCLOPS_PORT},ipmi,{HOST.HOST}]';

	$table->setHeader(array(
		is_show_all_nodes() ? S_NODE : null,
		new CCheckBox('all_physical_hosts', null, "checkAllHosts('".$ipmicontrol_form->getName()."', 'all_physical_hosts', '');"),
		_('Host name'),
		_('IPMI interface'),
		_('Status'),
		_('Problems'),
	));

	$hosts = get_ipmi_hosts();
	if(empty($hosts)){
		return null;
	}

	foreach( $hosts as $host ){
		$triggers = get_triggers($host['hostid']);
		$trigger_count = count($triggers);

		// get State
		if(!$preloading){
			if(is_script_success($host['hostid'], $script_itemkey)){
				$state = strtolower(get_item_value($host['hostid'], "ipmi.state.text"));
			}else{
				$state = _('script failed');
			}
		}else{
			$state = _('loading...');
		}

		// Check box
		$checkbox_col = new CCheckBox("hostids[]",null,null,$host['hostid']);
		if(!is_operation_available("ipmi", $state)){
			$checkbox_col->attributes['disabled'] = 'disabled';
		}

		// Host name
		if($trigger_count == 0){
			$hostname_col = new CCol(new CSpan($host['host']));
		}else{
			$hostname_col = new CLink(new CSpan($host['host']), 'tr_status.php?&hostid='.$host['hostid'].'&show_triggers='.TRIGGERS_OPTION_ONLYTRUE);
		}

		// IPMI Interfaces
		$ipmi_addresses = get_addresses($host['hostid'], INTERFACE_TYPE_IPMI);
		$ipmi_ip_col = new CCol(reset($ipmi_addresses));

		// Status
		$state_col = new CCol($state, get_item_level($state));

		// Problem
		if($trigger_count == 0){
			$problem_col = new CCol($trigger_count,'normal');
		}else{
			$problem_col = new CCol($trigger_count,'high');
			$problem_col->setHint(make_trigger_table($triggers,$hostname_col));
		}

		$r = new CRow();
		$r->addItem($checkbox_col);
		$r->addItem($hostname_col);
		$r->addItem($ipmi_ip_col);
		$r->addItem($state_col);
		$r->addItem($problem_col);
		$table->addRow($r);
	}

	$table->setFooter(new CCol(make_operation_box_footer(zbx_objectValues($hosts, 'hostid'), $form_name)));
	$ipmicontrol_form->addItem($table);
	$script = new CJSScript(get_js("jQuery('#hat_ipmistat_footer').html('"._s('Updated: %s', zbx_date2str(_('H:i:s')))."')"));
	return new CDiv(array($ipmicontrol_form, $script));
}

function make_vspherestat_summary($preloading = false){
	$table = new CTableInfo();
	$table->setHeader(array(
		is_show_all_nodes() ? S_NODE : null,
		_('Host name'),
		_('Interface'),
		_('CPU threads [used/total]'),
		_('Memory(GB) [used/total]'),
		_('Datastores'),
		_('PoweredOn'),
		_('Suspended'),
		_('PoweredOff'),
		_('Others'),
	));
	$hidden = new CDiv(null, "hidden");
	$hidden->setAttribute("type", "hidden");
	$script_itemkey = 'push_message.py[{$HYCLOPS_SERVER},{$HYCLOPS_PORT},vsphere,{HOST.HOST}]';
	$hosts = get_vsphere_hosts();
	if(empty($hosts)){
		return null;
	}
	foreach( $hosts as $host ){
		if(!$preloading){
			if(is_script_success($host['hostid'], $script_itemkey)){
				$hardware_profiles = get_hardware_profiles($host['hostid']);
				$datastores = get_datastores($host['hostid']);
				$instances = get_instances($host['hostid']);
				$instances = filter_instances($instances);

				$r = new CRow();

				// Host name
				$col = new CCol($host['host'], 'vsphere');
				$col->setAttribute("hostid", $host['hostid']);
				$r->addItem($col);

				// IP
				$snmp_addresses = get_addresses($host['hostid'], INTERFACE_TYPE_SNMP);
				$r->addItem(reset($snmp_addresses));

				// CPU thread
				$r->addItem(level_check($hardware_profiles['cpu_assigned'], $hardware_profiles['cpu']));

				// Memory
				$r->addItem(level_check($hardware_profiles['memory_assigned'], $hardware_profiles['memory']));

				// Datastores
				$datastores_count = new CSpan(count($datastores), 'pointer');
				if(!empty($datastores)) $datastores_count->setHint(make_datastore_table($host['hostid'], $datastores));
				$r->addItem(new CCol($datastores_count));

				// PowerOn
				$poweron_vms = $instances["running"];
				$poweron_count = new CSpan(count($poweron_vms), 'pointer');
				if(!empty($poweron_vms)) $poweron_count->setHint(make_vm_table('poweron', $poweron_vms));
				$r->addItem(new CCol($poweron_count));

				// Suspended
				$suspend_vms = $instances["pending"];
				$suspend_count = new CSpan(count($suspend_vms), 'pointer');
				if(!empty($suspend_vms)) $suspend_count->setHint(make_vm_table('suspend', $suspend_vms));
				$r->addItem(new CCol($suspend_count));

				// PowerOff
				$poweroff_vms = $instances["stopped"];
				$poweroff_count = new CSpan(count($poweroff_vms), 'pointer');
				if(!empty($poweroff_vms)) $poweroff_count->setHint(make_vm_table('poweroff', $poweroff_vms));
				$r->addItem(new CCol($poweroff_count));

				// Other
				$other_vms = $instances["other"];
				$other_count = new CSpan(count($other_vms), 'pointer');
				if(!empty($other_vms)) $other_count->setHint(make_vm_table('other', $other_vms));
				$other_state_col = new CCol($other_count, count($other_vms) > 0 ? 'high' : null);
				$r->addItem($other_state_col);

				$table->addRow($r);
				zbx_add_post_js('chkbxRange.pageGoName = "vms";');
			}else{
				$snmp_addresses = get_addresses($host['hostid'], INTERFACE_TYPE_SNMP);
				$r = new CRow();
				$r->addItem($host['host']);
				$r->addItem(reset($snmp_addresses));
				$r->addItem(new CCol(_('script failed'), "high"));
				$r->addItem(array("-", "-", "-", "-", "-", "-"));
				$table->addRow($r);
			}
		}else{
			// display loading message
			$snmp_addresses = get_addresses($host['hostid'], INTERFACE_TYPE_SNMP);
			$r = new CRow();
			$r->addItem($host['host']);
			$r->addItem(reset($snmp_addresses));
			$r->addItem(_('loading...'));
			$r->addItem(array("-", "-", "-", "-", "-", "-"));
			$table->addRow($r);
		}
	}

	#insert_js('init_vsphere_contextmenu()');
	$script = new CJSScript(get_js("jQuery('#hat_vspherestat_footer').html('"._s('Updated: %s', zbx_date2str(_('H:i:s')))."')"));
	return new CDiv(array($table, $script));
}

function make_awsstat_summary($preloading = false){
	$table = new CTableInfo();
	$table->setHeader(array(
		is_show_all_nodes() ? S_NODE : null,
		_('Account name'),
		_('PoweredOn'),
		_('PoweredOff'),
		_('Billing/Month'),
	));
	$script_itemkey = 'push_message.py[{$HYCLOPS_SERVER},{$HYCLOPS_PORT},ec2,{HOST.HOST}]';
	
	$aws_accounts = get_aws_accounts();
	if(empty($aws_accounts)){
		return null;
	}
	foreach( $aws_accounts as $host ){
		if(!$preloading){
			if(is_script_success($host['hostid'], $script_itemkey)){
				$instances = get_instances($host['hostid']);
				$instances = filter_instances($instances);
				$r = new CRow();

				// Account name
				$col = new CCol($host['host']);
				$r->addItem($col);

				// Poweron (running + pending)
				$poweron_vms = array_merge($instances["running"], $instances["pending"]);
				$poweron_count = new CSpan(count($poweron_vms), 'pointer');
				if(!empty($poweron_vms)) $poweron_count->setHint(make_ec2_table('ec2_poweron', $poweron_vms));
				$r->addItem(new CCol($poweron_count));

				// Poweroff (stopped + terminated + stopping + shutting-down)
				$poweroff_vms = $instances["stopped"];
				$poweroff_count = new CSpan(count($poweroff_vms), 'pointer');
				if(!empty($poweroff_vms)) $poweroff_count->setHint(make_ec2_table('ec2_poweroff', $poweroff_vms));
				$r->addItem(new CCol($poweroff_count));

				// AWS Charges
				$item = get_item_by_key('get_aws_charges.py[{$KEY},{$SECRET}]', $host["host"]);
				$r->addItem(new CLink($item["lastvalue"], "history.php?action=showgraph&itemid={$item["itemid"]}"));

				$table->addRow($r);
				zbx_add_post_js('chkbxRange.pageGoName = "vms";');
			}else{
				$r = new CRow();
				$r->addItem($host['host']);
				$r->addItem(new CCol(_('script failed'), "high"));
				$r->addItem(array("-"));
				$table->addRow($r);
			}
		}else{
			$r = new CRow();
			$r->addItem($host['host']);
			$r->addItem(new CCol(_('loading...')));
			$r->addItem(array("-"));
			$table->addRow($r);
		}
	}
	$script = new CJSScript(get_js("jQuery('#hat_awsstat_footer').html('"._s('Updated: %s', zbx_date2str(_('H:i:s')))."')"));
	return new CDiv(array($table, $script));
}

?>
