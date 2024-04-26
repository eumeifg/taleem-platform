function getCookie(cname) {
  var name = cname + "=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i <ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

$(document).ready(function() {
    'use strict';
    // Toggling visibility for the notification dropdown
    $('.notify .toggle-notify-dropdown').click(function(e) {
        var $dropdownMenu = $('.notify .dropdown-notify-menu');
        var $notifyDropdown = $('.notify .toggle-notify-dropdown');
        if ($dropdownMenu.is(':visible')) {
            $dropdownMenu.addClass('hidden');
            $notifyDropdown.attr('aria-expanded', 'false');
        } else {
            $dropdownMenu.removeClass('hidden');
            if($dropdownMenu.find('.notification-item').length > 0) $dropdownMenu.find('.notification-item')[0].focus();
            $notifyDropdown.attr('aria-expanded', 'true');
        }
        $('.notify .toggle-notify-dropdown').toggleClass('open');
        e.stopPropagation();
    });

    // Hide notification dropdown on click away
    if ($('.notify .dropdown-notify-menu').length) {
        $(window).click(function(e) {
            var $dropdownMenu = $('.notify .dropdown-notify-menu');
            var $notifyDropdown = $('.notify .toggle-notify-dropdown');
            if ($notifyDropdown.is(':visible') && !$(e.target).is('.notification-item, .toggle-notify-dropdown')) {
                $dropdownMenu.addClass('hidden');
                $notifyDropdown.attr('aria-expanded', 'false');
            }
        });
    }

    // Ajax setup
    $.ajaxSetup({
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        dataType: 'json',
        content: {
            script: false
        }
    });

});
