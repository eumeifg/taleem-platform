function getAlarmTimeLabel (count) {
  var defaultLabel = 'Alarm Time: ';
  var labels = {
        1: 'First Alarm Time: ',
        2: 'Second Alarm Time: ',
        3: 'Third Alarm Time: ',
        4: 'Fourth Alarm Time: ',
        5: 'Fifth Alarm Time: ',
    };

  return labels[count] || defaultLabel;
}

function disableAll(count){
  if(count<=5 && count > 1) {
    count--;
    $(".delete_count_"+count).addClass("btn-disable");
  }
}


function enableDelete(count){
  if(count > 1) {
    var notFound = true;
    while(notFound && count > 0) {
      var el = $(".delete_count_"+count);
      if (el.text()) {
        notFound = false;
      } else {
        count--;
      }
    }
    $(".delete_count_"+count).removeClass("btn-disable");
  }
}

function getNewTimeExamAlarmInput(count){
  var id = 'alarm_time_' + count;

  var inputField = $(
    '<input type="number" min="5" max="60" style="width: 10em;" required placeholder="Alarm time" />'
  ).attr('name', id).attr('id', id);
  var emptyDiv = $('<div></div>');
  var inputLabel = $('<label></label>').attr('for', id).text(getAlarmTimeLabel(count));
  var deleteButton = $('<a href="#delete" class="deletelink">Delete</a>').addClass('delete_count_'+count).css('margin-left', '15px');
  disableAll(count);
  var divvv = $('<div class="form-row"></div>').append(emptyDiv);
  emptyDiv.append(inputLabel).append(inputField).append(deleteButton);
  return divvv;
}

function getDeletedTimeExamAlarmInput(count, value){
  var id = 'alarm_time_remove_' + count;

  return  $(
    '<input type="number" placeholder="Alarm time" />'
  ).attr('name', id).attr('id', id).attr('value', value);
}

function showError($form, text) {
  if (text) {
    $form.prepend($('<p class="errornote timed-exam-alarm-config-error"></p>').text(text));
  } else {
    $('.timed-exam-alarm-config-error').remove();
  }
}

function deleteInputField(event, count) {
  var id = $(event.target).attr('id');
  $(event.target).parent().parent().remove();

  enableDelete(count);
  var $form = $('#timed-exam-alarm-configuration-form');
  var currentCount = $form.data('alarm-count');

  if (id) {
    var $form = $('#timed-exam-alarm-configuration-form');
    var currentCount = $form.data('alarm-count');

    $('#removed-alarm-time-input-container').append(
      getDeletedTimeExamAlarmInput(currentCount, id)
    );
  }
  $form.data('alarm-count', currentCount-1)

}
// Make sure there are no duplicate alarm times selected.
function validateAlarmTimes () {
  var inputFields = $('.form-row input');
  var selectedValues = new Set();
  var isValid = true;

  for(var i=0; i< inputFields.length; i++) {
    if (selectedValues.has(inputFields[i].value)) {
      var $div = $(inputFields[i]).parent().addClass('errors');
      if ($($div).find('.timed-exam-alarm-value-error').length === 0) {
        $div.append($('<p class="errornote timed-exam-alarm-value-error"></p>').text("This time has already been selected, please select another."))
      }

      isValid = false;
    } else {
      var $div = $(inputFields[i]).parent().removeClass('errors');
      $($div).find('.timed-exam-alarm-value-error').remove();

      selectedValues.add(inputFields[i].value);
    }
  }

  return isValid;
}

$(function(){
  // Add new input fields for timed exam alarm configuration.
  $("#add-timed-exam-alarm-configuration").on('click', function (event) {
    event.preventDefault();
    var $form = $('#timed-exam-alarm-configuration-form');
    var currentCount = $form.data('alarm-count');

    if (currentCount >= 5){
      if ( $('.timed-exam-alarm-config-error').length === 0 ){
        showError($form,"You can only add up-to five alarm times.");
      }
      return;
    } else {
      showError($form, "");
    }

    $('#alarm-time-input-container').append(
      getNewTimeExamAlarmInput(currentCount+1)
    );
    $form.data('alarm-count', currentCount+1);
  });

  $("#timed-exam-alarm-configuration-form").submit(function (event){
    if(!validateAlarmTimes()) {
      event.preventDefault();
    }
  });

  $('#alarm-time-input-container').on('click', '.deletelink', function (event){
    event.preventDefault();
    var $form = $('#timed-exam-alarm-configuration-form');
    var currentCount = $form.data('alarm-count');
    deleteInputField(event, currentCount+1);
  })


});
