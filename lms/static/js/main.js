// Once generated by CoffeeScript 1.9.3, but now lives as pure JS
/* eslint-disable */
(function() {
  AjaxPrefix.addAjaxPrefix(jQuery, function() {
    return $("meta[name='path_prefix']").attr('content');
  });

  $(function() {
    $.ajaxSetup({
      headers: {
        'X-CSRFToken': $.cookie('csrftoken')
      },
      dataType: 'json'
    });
    window.onTouchBasedDevice = function() {
      return navigator.userAgent.match(/iPhone|iPod|iPad|Android/i);
    };

    if (onTouchBasedDevice()) {
      $('body').addClass('touch-based-device');
    }

    /*
    $("a[rel*=leanModal]").leanModal()
     */
    $('#csrfmiddlewaretoken').attr('value', $.cookie('csrftoken'));
    new Calculator;
    new FeedbackForm;
    if ($('body').hasClass('courseware')) {
      Courseware.start();
    }
    window.postJSON = function(url, data, callback) {
      return $.postWithPrefix(url, data, callback);
    };
    $('#login').click(function() {
      $('#login_form input[name="email"]').focus();
      return false;
    });
    $('#signup').click(function() {
      $('#signup-modal input[name="email"]').focus();
      return false;
    });

    /*
    fix for ie
     */
    if (!Array.prototype.indexOf) {
      return Array.prototype.indexOf = function(obj, start) {
        var ele, i, j, len, ref;
        if (start == null) {
          start = 0;
        }
        ref = this.slice(start);
        for (i = j = 0, len = ref.length; j < len; i = ++j) {
          ele = ref[i];
          if (ele === obj) {
            return i + start;
          }
          return -1;
        }
      };
    }
  });

}).call(this);
