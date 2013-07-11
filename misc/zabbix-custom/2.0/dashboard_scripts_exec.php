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

require_once dirname(__FILE__).'/include/config.inc.php';
require_once dirname(__FILE__).'/include/hosts.inc.php';
require_once dirname(__FILE__).'/include/forms.inc.php';

$page['title'] = _('Scripts');
$page['file'] = 'dashboard_scripts_exec.php';

define('ZBX_PAGE_NO_MENU', 1);

require_once dirname(__FILE__).'/include/page_header.php';

// VAR	TYPE	OPTIONAL	FLAGS	VALIDATION	EXCEPTION
$fields = array(
	'hostids' =>	array(T_ZBX_STR, O_OPT, P_SYS, DB_ID,		'isset({execute})'),
	'hostname' =>	array(T_ZBX_STR, O_OPT, P_SYS, DB_ID,		'isset({answer})'),
	'scriptid' =>	array(T_ZBX_INT, O_OPT, P_SYS, DB_ID,		'isset({execute})'),
	'choiceid' =>	array(T_ZBX_STR, O_OPT, P_SYS, DB_ID,		'isset({answer})'),
	'execute' =>	array(T_ZBX_INT, O_OPT, P_ACT, IN('0,1'),	null),
	'answer' =>	array(T_ZBX_INT, O_OPT, P_ACT, IN('0,1'),	null)
);
check_fields($fields);

if (isset($_REQUEST['execute'])) {
	$json = new CJSON();
	$scriptid = get_request('scriptid');
	$hostids = $json->decode(get_request('hostids'), true);
	$hostids = $json->decode($hostids, true);

	$data = array(
		'message' => '',
		'info' => DBfetch(DBselect('SELECT s.name FROM scripts s WHERE s.scriptid='.$scriptid))
	);

	$results = array();
	foreach ($hostids as $hostid) {
		$results[] = API::Script()->execute(array('hostid' => $hostid, 'scriptid' => $scriptid));
	}

	$isErrorExist = false;
	foreach ($results as $result) {
		if (empty($result)) {
			$isErrorExist = true;
		}
		elseif ($result['response'] == 'failed') {
			error($result['value']);
			$isErrorExist = true;
		}
		else {
			$data['message'] .= convert_json_message($result['value'])."\n";
		}
	}

	if ($isErrorExist) {
		show_error_message(_('Cannot connect to the trapper port of zabbix server daemon, but it should be available to run the script.'));
	}

	// render view
	$scriptView = new CView('general.script.execute', $data);
	$scriptView->render();
	$scriptView->show();
}elseif (isset($_REQUEST['answer'])) {
	$hostname = get_request('hostname');
	$choiceid = get_request('choiceid');
	$script = 'python /opt/hyclops/globalscripts/request_action.py vsphere '.$hostname.' \'{"command": "answer", "choiceid":"'.$choiceid.'"}\' 2>&1';
	$result = array();
	$ret = null;
	exec($script, $result, $ret);
	$message = '';
	if($ret == 0){
		$message = convert_json_message($result[0]);
	}else{
		$message = $result;
	}
	$data = array(
		'message' => $message,
		'info' => array("name" => 'Answer the question')
	);
	$scriptView = new CView('general.script.execute', $data);
	$scriptView->render();
	$scriptView->show();
}

function convert_json_message($original_msg){
	$message = '';
	$tmp_msg = str_replace('\'', '"', $original_msg);
	$tmp_msg = str_replace('u"', '"', $tmp_msg);
	$tmp_msg = json_decode($tmp_msg, true);
	if($tmp_msg['result']){
		$message = "Result: ";
		$message .= $tmp_msg['result'];
		$message .= "\nMessage: ";
		$message .= $tmp_msg['message'];
		$message .= "\n\n* Please wait a few minutes until the result is reflected in Dashboard.";
	}else{
		$message = $original_msg;
	}
	return $message;
}

require_once dirname(__FILE__).'/include/page_footer.php';
