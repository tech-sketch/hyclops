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

$hostid = $_GET['hostid'];
$gateone_url = get_global_macro('{$GATEONE_URL}');
$gateone_url = rtrim($gateone_url, "/");
$hosts = API::Host()->get(array(
	"hostids" => $hostid,
	"selectInterfaces" => "extend"
));
$ssh_con_url = "";
if(isset($hosts[0]["interfaces"])){
	$ssh_con_url =get_ssh_interface($hosts[0]);
}
$user = CWebUser::$data['alias'];
$auth = get_authobj($user);

function get_ssh_interface($host){
	foreach( $host["interfaces"] as $interface ){
		if($interface["main"] == 1){
			$ssh_interface = $interface["useip"] == 0 ? $interface["dns"] : $interface["ip"];
			if($ssh_interface == 'dummy-interface.invalid'){
				continue;
			}else{
				return $ssh_interface;
			}
		}
	}
	return null;
}

function get_global_macro($name){
	$macros = API::UserMacro()->get(array(
		'output' => API_OUTPUT_EXTEND,
		'globalmacro' => true
	));
	$macros = zbx_toHash($macros,'macro');
	return $macros[$name]['value'];
}

function get_authobj($upn){
	$api_key = get_global_macro('{$GATEONE_KEY}');
	$secret = get_global_macro('{$GATEONE_SECRET}');
	$authobj = array(
		'api_key' => $api_key,
		'upn' => $upn,
		'timestamp' => (string)ceil(microtime(true)*1000),
		'signature_method' => 'HMAC-SHA1',
		'api_version' => '1.0'
	);
	$authobj['signature'] = hash_hmac('sha1', $api_key.$upn.$authobj['timestamp'], $secret);
	return json_encode($authobj);
}

print<<<EOF
<html>
<head>
<script src="$gateone_url/static/gateone.js"></script>
<script>
function GateOneConnect(){
	GateOne.init({url: '$gateone_url/',auth: $auth });
	if('$ssh_con_url'){ 
		setTimeout(function(){ OpenSSHConnection(); }, 2000);
	}else{
		setTimeout(function(){ GateOne.Terminal.newTerminal(); }, 2000);
	}
}

function OpenSSHConnection(init){
	GateOne.Terminal.newTerminal();
	GateOne.Bookmarks.openBookmark('ssh://$ssh_con_url');
	setTimeout(function(){GateOne.Visual.togglePanel();},10);
	AddBookmark('ssh://$ssh_con_url');
}

function AddBookmark(url){
	var new_bookmark = {
		'url': url,
		'name': url,
		'tags': [],
		'notes': '',
		'visits': 0,
		'updated': new Date().getTime(),
		'created': new Date().getTime(),
		'updateSequenceNum': 0,
		'images': {'favicon': null}
	}

	GateOne.Bookmarks.createOrUpdateBookmark(new_bookmark);
}
</script>

</head>
<body onLoad="GateOneConnect();">
<div style="width: 1024px; height: 800px;">
	<div id="gateone"></div>
</div>
</body>
</html>
EOF;
?>
