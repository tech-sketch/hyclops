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

require_once dirname(__FILE__).'/../include/views/js/general.script.confirm.js.php';
?>
<script type="text/javascript">
	function executeScriptOnMultipleHosts(form_id, selectbox_name, checkbox_name, confirmation) {
		// checkbox value
		var hostids = [];
		var hostnames = [];
		var checked = jQuery('#'+form_id+' [name="'+checkbox_name+'"]:checked');
		checked.map(function() {
			hostids.push(jQuery(this).val());
			hostnames.push(jQuery(this).parents("tr").children("td").children("span").text());
		});
		hostids = JSON.stringify(hostids);
		// selectbox value
		var scriptid = jQuery('#'+form_id+' [name='+selectbox_name+']').val();
		var scriptname = jQuery('#'+form_id+' [name='+selectbox_name+'] :selected').text();

		var execute = function() {
			openWinCentered('dashboard_scripts_exec.php?execute=1&hostids=' + hostids + '&scriptid=' + scriptid, 'Tools', 560, 470, 'titlebar=no, resizable=yes, scrollbars=yes, dialog=no'
			);
		};

		if (confirmation == '') {
			execute();
		}
		else {
			var buttons = [
				{text: <?php echo CJs::encodeJson(_('Execute')); ?>, click: function() {
					jQuery(this).dialog('destroy');
					execute();
				}},
				{text: <?php echo CJs::encodeJson(_('Cancel')); ?>, click: function() {
					jQuery(this).dialog('destroy');
				}}
			];
			var confirmation_msg = confirmation + " [" + scriptname + "]? :" + hostnames;
			var d = showScriptDialog(confirmation_msg, buttons);

			jQuery(d).find('button:first').addClass('main');
		}
	}

	function checkAllHosts(form_name, chkMain, shkName){
		var frmForm = document.forms[form_name];
		var value = frmForm.elements[chkMain].checked;
		var elementCount = frmForm.elements.length;
		for( i=0 ; i<elementCount ; i++ ){
			frmForm.elements[i].checked = value;
		}
		return true;
	}
	
	function checkAnswer(form_id, input_name, hostname, confirmation){
		var checked = jQuery('#'+form_id+' [name='+input_name+']:checked');
		var choiceid = checked.val();
		var choicename = checked.parents("tr").children("td").children("label").text();
		var execute = function() {
			openWinCentered('dashboard_scripts_exec.php?answer=1&hostname=' + hostname + '&choiceid=' + choiceid, 'Tools', 560, 470, 'titlebar=no, resizable=yes, scrollbars=yes, dialog=no'
			);
		};

		if (confirmation == '') {
			execute();
		}
		else {
			var buttons = [
				{text: <?php echo CJs::encodeJson(_('Execute')); ?>, click: function() {
					jQuery(this).dialog('destroy');
					execute();
				}},
				{text: <?php echo CJs::encodeJson(_('Cancel')); ?>, click: function() {
					jQuery(this).dialog('destroy');
				}}
			];
			var confirmation_msg = confirmation + "[Answer the Question] ? : your choice is '" + choicename + "'";
			var d = showScriptDialog(confirmation_msg, buttons);

			jQuery(d).find('button:first').addClass('main');
		}
		
	}
</script>
