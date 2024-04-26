/* Timer */
let timerId = null;
let timerTick = 0;
let secondsLeft = 0;
let alarms = [];
let grace_period_secs = 5;
let low_threshold_sec = 300;
let critically_low_threshold_sec = 60;

var getFormattedRemainingTime = function(secondsLeft) {
  var secsLeft = secondsLeft,
    hours, minutes, seconds;
  /* since we can have a small grace period, we can end in the negative numbers */
  if (secondsLeft < 0) {
    secsLeft = 0;
  }

  hours = Math.floor(secsLeft / 3600);
  minutes = Math.floor(secsLeft / 60) % 60;
  seconds = Math.floor(secsLeft % 60);

  return (hours < 10 ? '0' + hours : hours) +
    ':' + (minutes < 10 ? '0' + minutes : minutes) +
    ':' + (seconds < 10 ? '0' + seconds : seconds);
}

var getRemainingTimeState = function(secondsLeft) {
  if (secondsLeft > low_threshold_sec) {
    return null;
  } else if (secondsLeft <= low_threshold_sec &&
    secondsLeft > critically_low_threshold_sec) {
    // returns the class name that has some css properties
    // and it displays the user with the waring message if
    // total seconds is less than the low_threshold value.
    return 'text-warning';
  } else {
    // returns the class name that has some css properties
    // and it displays the user with the critical message if
    // total seconds is less than the critically_low_threshold_sec value.
    return 'text-danger';
  }
}

var updateRemainingTime = function() {
  timerTick += 1;
  secondsLeft -= 1;

  if (alarms.indexOf(parseInt(secondsLeft)) > -1) {
    swal({
      title: translateMessage("title"),
      text: parseInt(secondsLeft / 60) + translateMessage("warning"),
      icon: "warning",
      button: translateMessage("ok")
    });
  }

  $('#exam-timer').attr('class');
  let newState = getRemainingTimeState(secondsLeft);

  if (newState !== null && !$('#exam-timer').hasClass(newState)) {
    $('#exam-timer').removeClass('text-warning text-danger');
    $('#exam-timer').addClass('low-time ' + newState);
  }

  $('#exam-timer').html(getFormattedRemainingTime(secondsLeft));
  if (secondsLeft <= -grace_period_secs) {
    clearInterval(timerId); // stop the timer once the time finishes.
    timerId = null;
    var submitButton = document.getElementsByClassName('exam-submit')[0];

    if (!submitButton.disabled) {
      submitButton.click();
    }

    // decide what to do with the page when the timer expired
  }
}
/* Timer End */

/* Attempt */
var startAttempt = function() {
  $.ajax({
    type: "POST",
    url: attemptStatusEndpoint,
    data: {
      'status': 'started'
    },
    success: function(res) {
      secondsLeft = res.time_remaining_seconds;
      alarms = res.alarms;
      timerId = setInterval(updateRemainingTime, 1000);
    },
    error: function(xhr) { // if error occured
      console.error(xhr.statusText + xhr.responseText);
    },
    complete: function() {
      $("#loading-overlay").hide();
    },
  });
}

var endAttempt = function() {
  $.ajax({
    type: "POST",
    url: attemptStatusEndpoint,
    data: {
      'status': 'submitted'
    },
    success: function(res) {
      location.reload();
    },
    error: function(xhr) { // if error occured
      console.error(xhr.statusText + xhr.responseText);
    },
    complete: function() {
      $("#loading-overlay").hide();
    },
  });
}
/* End Attempt */

/* render question */
var renderQuestion = function(el) {
  let questionEl = el.find(".question-body");
  if (!questionEl.children().length) {
    $.get(el.data("url"), function(data) {
      questionEl.html(data.html);
      XBlock.initializeBlocks(el.find('.course-content'));
    });
  }
  el.show();
}
/* End render question */

/* Tab switch event */
var TabSwitch = {};

var logBrowserTabSwitch = function() {
  // Log only during the exam
  if (timerId != null) {
    $.ajax({
      data: {
        event_type: document[self.hidden] ? 'out' : 'in',
        exam_id: examID
      },
      url: logTabActivityEndpoint,
      type: 'POST'
    });
  }
}

// Set the name of the hidden property and the change event for visibility
if (typeof document.hidden !== "undefined") {
  TabSwitch.hidden = "hidden";
  TabSwitch.visibilityChange = "visibilitychange";
} else if (typeof document.msHidden !== "undefined") {
  TabSwitch.hidden = "msHidden";
  TabSwitch.visibilityChange = "msvisibilitychange";
} else if (typeof document.webkitHidden !== "undefined") {
  TabSwitch.hidden = "webkitHidden";
  TabSwitch.visibilityChange = "webkitvisibilitychange";
}
// Handle page visibility change
if (isProctored && typeof document.addEventListener !== "undefined" && TabSwitch.hidden !== undefined) {
  $(window).bind(TabSwitch.visibilityChange, logBrowserTabSwitch);
}
/* End Tab switch event */

/* Connection status log */
var wentOfflineTimestamp = null;

var logConnectionStatus = function() {
  // Log only during the exam
  if (timerId != null) {
    $.ajax({
      data: {
        offline_timestamp: wentOfflineTimestamp,
        online_timestamp: + new Date(),
        exam_id: examID
      },
      url: logConnectionStatusEndpoint,
      type: 'POST'
    });
  }
}
/* End connection status log */


$(document).ready(function() {
  $("#loading-overlay").show();

  renderQuestion($(".exam-problem").first());

  startAttempt();

  if ($(".exam-problem").length < 2) {
    $(".button-next").attr('disabled', true);
  }
  $(".button-next").click(function() {
    renderQuestion($(".exam-problem:visible").next());
    $(".exam-problem:visible").prev().hide();
    $(".button-previous").attr('disabled', false);
    if ($(".exam-problem:visible").next().length == 0) {
      $(".button-next").attr('disabled', true);
    }
  });
  $(".button-previous").click(function() {
    renderQuestion($(".exam-problem:visible").prev());
    $(".exam-problem:visible").next().hide();
    $(".button-next").attr('disabled', false);
    if ($(".exam-problem:visible").prev().length == 0) {
      $(".button-previous").attr('disabled', true);
    }
  });

  window.addEventListener('offline', function(e) {
    wentOfflineTimestamp = + new Date();
    $("#connection-status").removeClass("bg-success").addClass("bg-danger");
    $(".exam-submit").attr('disabled', true);
  });
  window.addEventListener('online', function(e) {
    $("#connection-status").removeClass("bg-danger").addClass("bg-success");
    $(".exam-submit").attr('disabled', false);
    wentOfflineTimestamp && logConnectionStatus();
  });

  $(".exam-submit").click(function() {
    endAttempt();
  });

});
