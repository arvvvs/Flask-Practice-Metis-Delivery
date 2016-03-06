$(function() {
//submits phone information
	var submit_phone = function(e) {
		$.getJSON($SCRIPT_ROOT + '/_order', {
			name: $('input:checked').parent().next().text(),
			address: $('input:checked').parent().next().next().text(),
			phone: $('input:checked').parent().next().next().next().text(),
		}, function(data) {
			console.log('DONE');
			$('#edit-modal').append('<p>Done</p>');
			$('#edit-modal').append(data);
		});
		};
		$('#calculate').bind('click', submit_phone);
	
	$('#edit').bind('click', edit_customer);
	//edits phone and customer info
	var edit_customer= function(e) {
		$.getJSON($SCRIPT_ROOT + '/_edit_customer', {
			name: $('input:checked').parent().next().text(),
			address: $('input:checked').parent().next().next().text(),
			phone: $('input:checked').parent().next().next().next().text(),
		}, function(data) {
			$('#edit-modal').append(data);
			$('#editing').bind('click', submit_edit);
		});
		};
	$('#edit').bind('click', edit_customer);
	$('#editing').bind('click', submit_edit);
	//submits the edits to customer
	var submit_edit = function(e) {
		$.getJSON($SCRIPT_ROOT + '/_finish_edit', {
			phone: $('#phone').val(), 
			address: $('#address').val(),
			name: $('#name').val(),
			phone_value: $('#phone').attr('value')
			}, function (data) {
				location.reload();
		       });
		};





});
