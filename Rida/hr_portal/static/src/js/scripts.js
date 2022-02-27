$(document).ready(function(){
    // Leave: set required attribute based on leave type
    $("select.searchable").select2();
    $('#holiday_status_id').on('change', function() {
      var required = $(this).children("option:selected").data("attachment");
      if(required){
        $('#attachment').prop('required',true);
      }
      else{
        $('#attachment').prop('required',false);
      }
    });

    // Expense: set product price on product change
    $('#expense_product_id').on('change', function() {
      var unit_price = $(this).children("option:selected").data("unit_price");
      var product_name = $(this).children("option:selected").text();

      $('#expense_unit_price').val(unit_price);
      $('#expenseName').val(product_name.trim());
    });

    $('.circle-tile').on('click', function(){
        var href = $(this).find("a").attr("href");
        if(href) {
            window.location = href;
        }
    });

    $('.o_portal_my_doc_table tr').on('click', function(){
        var href = $(this).find("a").attr("href");
        if(href) {
            window.location = href;
        }
    });

    $('.trayToggle').on('click', function(e){
         e.preventDefault();
        $('#wrapwrap').hide();
        $('#iconTray').show();
    });

    $('#closeIconTray').on('click', function(e){
        e.preventDefault();
        $('#wrapwrap').show();
        $('#iconTray').hide();
    });


    $('button.view-switch').on('click', function(){
        $('button.view-switch').removeClass('disabled');
        $(this).addClass('disabled');
        $('.view-container').addClass('hidden');
        to_show = $("#" + $(this).data('id'));
        to_show.removeClass('hidden');
        loadLeavesCalendar();
    });

    getExpenseDate();

    function getExpenseDate() {
      var today = new Date();
      var dd = today.getDate();
      var mm = today.getMonth()+1; //January is 0!
      var yyyy = today.getFullYear();

      if(dd<10) {
          dd = '0'+dd
      }

      if(mm<10) {
          mm = '0'+mm
      }

      today = yyyy + '-' + mm + '-' + dd;;
      $('#expense_date').val(today)
    }

});

var getParams = function (url) {
	var params = {};
	var parser = document.createElement('a');
	parser.href = url;
	var query = parser.search.substring(1);
	var vars = query.split('&');
	for (var i = 0; i < vars.length; i++) {
		var pair = vars[i].split('=');
		params[pair[0]] = decodeURIComponent(pair[1]);
	}
	return params;
};

function loadLeavesCalendar() {
    var calendarEl = document.getElementById('calendar');
    $('#calendar').html('');
    var today = new Date();
    var calendar = new FullCalendar.Calendar(calendarEl, {
      plugins: [ 'interaction', 'dayGrid', 'timeGrid'],
      header: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
      },
      defaultDate: today,
      editable: false,
      navLinks: true, // can click day/week names to navigate views
      eventLimit: true, // allow "more" link when too many events
      events: {
        url: '/my/leave/json',
        failure: function() {
          console.log()
        }
      },
      loading: function(bool) {
        console.log()
      }
    });

    calendar.render();
  }

function onchange_leave_dates(){
    var date_from = $('#date_from').val();
    var date_to = $('#date_to').val();
    if (date_from && date_to){
        var date1 = new Date(date_from);
        var date2 = new Date(date_to);
        var Difference_In_Time = date2.getTime() - date1.getTime();
        var Difference_In_Days = (Difference_In_Time / (1000 * 3600 * 24)) + 1;
        var duration = Difference_In_Days.toString() + " Days";
        $('input#duration').val(duration);
    }
}