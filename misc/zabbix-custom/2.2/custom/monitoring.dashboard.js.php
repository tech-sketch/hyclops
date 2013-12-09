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

		confirmation = confirmation + " [" + scriptname + "]? :" + hostnames;
        
		if (confirmation == '') {
			execute();
		}
		else {
			var scriptDialog = jQuery('#scriptDialog');

			if (scriptDialog.length == 0) {
				scriptDialog = jQuery('<div>', {
					id: 'scriptDialog',
					css: {
						display: 'none',
						'white-space': 'normal',
						'z-index': 1000
					}
				});

				jQuery('body').append(scriptDialog);
			}

			scriptDialog
				.text(confirmation)
				.dialog({
					buttons: [
						{text: t('Execute'), click: function() {
							jQuery(this).dialog('destroy');
							execute();
						}},
						{text: t('Cancel'), click: function() {
							jQuery(this).dialog('destroy');
						}}
					],
					draggable: false,
					modal: true,
					width: (scriptDialog.outerWidth() + 20 > 600) ? 600 : 'inherit',
					resizable: false,
					minWidth: 200,
					minHeight: 100,
					title: t('Execution confirmation'),
					close: function() {
						jQuery(this).dialog('destroy');
					}
				});

			if (empty(hostids)) {
				jQuery('.ui-dialog-buttonset button:first').prop('disabled', true).addClass('ui-state-disabled');
				jQuery('.ui-dialog-buttonset button:last').addClass('main').focus();
				jQuery('.ui-dialog').css('z-index',1000);
			}
			else {
				jQuery('.ui-dialog-buttonset button:first').addClass('main');
				jQuery('.ui-dialog').css('z-index',1000);
			}
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
		confirmation = confirmation + "[Answer the Question] ? : your choice is '" + choicename + "'";

		if (confirmation == '') {
			execute();
		}
		else {
			var scriptDialog = jQuery('#scriptDialog');

			if (scriptDialog.length == 0) {
				scriptDialog = jQuery('<div>', {
					id: 'scriptDialog',
					css: {
						display: 'none',
						'white-space': 'normal',
						'z-index': 1000
					}
				});

				jQuery('body').append(scriptDialog);
			}

			scriptDialog
				.text(confirmation)
				.dialog({
					buttons: [
						{text: t('Execute'), click: function() {
							jQuery(this).dialog('destroy');
							execute();
						}},
						{text: t('Cancel'), click: function() {
							jQuery(this).dialog('destroy');
						}}
					],
					draggable: false,
					modal: true,
					width: (scriptDialog.outerWidth() + 20 > 600) ? 600 : 'inherit',
					resizable: false,
					minWidth: 200,
					minHeight: 100,
					title: t('Execution confirmation'),
					close: function() {
						jQuery(this).dialog('destroy');
					}
				});

			if (empty(hostname)) {
				jQuery('.ui-dialog-buttonset button:first').prop('disabled', true).addClass('ui-state-disabled');
				jQuery('.ui-dialog-buttonset button:last').addClass('main').focus();
				jQuery('.ui-dialog').css('z-index',1000);
			}
			else {
				jQuery('.ui-dialog-buttonset button:first').addClass('main');
				jQuery('.ui-dialog').css('z-index',1000);
			}
        }
		
	}
</script>
