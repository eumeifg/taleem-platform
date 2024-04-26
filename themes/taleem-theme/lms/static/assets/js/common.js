
function fetchAlarms() {
  $.ajax({
    type: "GET",
    url: "/notifications/timed_exam_alarms/",
    success: function (response) {
        if (response.alarm) {
            $("#alarm-message").text(response.message);
            $("#alarm-modal").jqueryModal({
                  escapeClose: false,
                  clickClose: false,
                  showClose: false
            });
        }
    },
  });
}

$(document).ready(function(){
    // On these blacklist URLs we are disabling the long polling for notification.
    var blackListURLs = ['/login', '/register', '/'];
    if (blackListURLs.indexOf(window.location.pathname) < 0) {
      setInterval(function(){
          fetchAlarms(); // this will run after every 1 minutes.
      }, 60000);
    }

});
