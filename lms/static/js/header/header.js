/**
 * Ensuring collapsible and accessible components on multiple
 * screen sizes for the responsive lms header.
 */
function createMobileMenu() {
    /**
     * Dynamically create a mobile menu from all specified mobile links
     * on the page.
     */
    'use strict';
    $('.mobile-nav-item').each(function() {
        var mobileNavItem = $(this).clone().addClass('mobile-nav-link');
        mobileNavItem.removeAttr('role');
        mobileNavItem.find('a').attr('role', 'menuitem');
        // xss-lint: disable=javascript-jquery-append
        $('.mobile-menu').append(mobileNavItem);
    });
}

var notificationItemTpl = `
<div class="notification-item">
    <div class="notification-body">
        <p><%- notification.message %></p>
        <span class="notification-date"><%- notification.created %> <i class="las la-lg la-calendar mx-2"></i></span>
        <span class="fa fa-times read-icon" data-id="<%- notification.id %>"></span>
    </div>
</div>
`

function fetchNotifications() {
    var shownNotifications = $('#notify-menu .notification-item .read-icon').map(
        function(item) {
            return $(this).data('id');
        }
    ).get();
    var tpl = _.template(notificationItemTpl);

    $.ajax({
        type: "GET",
        url: "/notifications/list-messages-in-json",
        success: function(notifications) {
            if (notifications) {
                for (var i = 0; i < notifications.length; i++) {
                    if (!shownNotifications.includes(notifications[i].id)) {
                        $('#notify-menu .notifications-list').prepend(
                            tpl({
                                notification: notifications[i]
                            })
                        );
                    }

                    if (notifications.length > 0) {
                        $('#no-notification').hide();
                        $('.toggle-notify-dropdown .notification-count').text(notifications.length);
                        $('.toggle-notify-dropdown .notification-count').removeClass('hidden');
                    }
                }
            }
        },
    });
}


$(document).ready(function() {
    'use strict';

    // ************ Notification: Mark as read
    $('.nav-item-dropdown.notify').on('click', '.notification-item .read-icon', function(e) {
        //$(".preloader").show();
        var notification_id = $(this).data('id');
        var $row = $(this).closest('.notification-item');
        jQuery.ajax({
            type: "POST",
            url: "/notifications/mark/as/read/" + notification_id + "/",
            success: function(res) {
                if (res.success) {
                    $row.hide('slow').addClass('hidden');
                    const num_rows = $(".notification-item").not('.action').not('.hidden').length;
                    if (num_rows == 0) {
                        $(".notify .bubble").hide('slow');
                        $(".notification-item.action").html('<span id="no-notification">You are done. No more notifications!</span>');
                    } else {
                        $(".notify .bubble").text(num_rows);
                        $(".notify .bubble").show();
                    }
                } else {
                    alert('Something went wrong!');
                }
            },
        });
        // $(".preloader").hide();
    });


    var $hamburgerMenu;
    var $mobileMenu;
    // Toggling visibility for the user dropdown
    $('.global-header .toggle-user-dropdown, .global-header .toggle-user-dropdown span').click(function(e) {
        var $dropdownMenu = $('.global-header .nav-item .dropdown-user-menu');
        var $userDropdown = $('.global-header .toggle-user-dropdown');
        if ($dropdownMenu.is(':visible')) {
            $dropdownMenu.addClass('hidden');
            $userDropdown.attr('aria-expanded', 'false');
        } else {
            $dropdownMenu.removeClass('hidden');
            $dropdownMenu.find('.dropdown-item')[0].focus();
            $userDropdown.attr('aria-expanded', 'true');
        }
        $('.global-header .toggle-user-dropdown').toggleClass('open');
        e.stopPropagation();
    });

    // Toggling visibility for the notification dropdown
    $('.notify .toggle-notify-dropdown, .notify .toggle-notify-dropdown i, .notify .toggle-notify-dropdown span').click(function(e) {
        var $dropdownMenu = $('.notify .dropdown-notify-menu');
        var $notifyDropdown = $('.notify .toggle-notify-dropdown');
        if ($dropdownMenu.is(':visible')) {
            $dropdownMenu.addClass('hidden');
            $notifyDropdown.attr('aria-expanded', 'false');

        } else {
            fetchNotifications();
            $dropdownMenu.removeClass('hidden');
            if ($dropdownMenu.find('.notification-item').length > 0) $dropdownMenu.find('.notification-item')[0].focus();
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

    // Hide user dropdown on click away
    if ($('.global-header .nav-item .dropdown-user-menu').length) {
        $(window).click(function(e) {
            var $dropdownMenu = $('.global-header .nav-item .dropdown-user-menu');
            var $userDropdown = $('.global-header .toggle-user-dropdown');
            if ($userDropdown.is(':visible') && !$(e.target).is('.dropdown-item, .toggle-user-dropdown')) {
                $dropdownMenu.addClass('hidden');
                $userDropdown.attr('aria-expanded', 'false');
            }
        });
    }

    // Toggling menu visibility with the hamburger menu
    $('.global-header .hamburger-menu').click(function() {
        $hamburgerMenu = $('.global-header .hamburger-menu');
        $mobileMenu = $('.mobile-menu');
        if ($mobileMenu.is(':visible')) {
            $mobileMenu.addClass('hidden');
            $hamburgerMenu.attr('aria-expanded', 'false');
        } else {
            $mobileMenu.removeClass('hidden');
            $hamburgerMenu.attr('aria-expanded', 'true');
        }
        $hamburgerMenu.toggleClass('open');
    });

    // Hide hamburger menu if no nav items (sign in and register pages)
    if ($('.mobile-nav-item').size() === 0) {
        $('.global-header .hamburger-menu').addClass('hidden');
    }

    createMobileMenu();
});


// Accessibility keyboard controls for user dropdown and mobile menu
$('.mobile-menu, .global-header').on('keydown', function(e) {
    'use strict';
    var isNext,
        nextLink,
        loopFirst,
        loopLast,
        $curTarget = $(e.target),
        isLastItem = $curTarget.parent().is(':last-child'),
        isToggle = $curTarget.hasClass('toggle-user-dropdown'),
        isHamburgerMenu = $curTarget.hasClass('hamburger-menu'),
        isMobileOption = $curTarget.parent().hasClass('mobile-nav-link'),
        isDropdownOption = !isMobileOption && $curTarget.parent().hasClass('dropdown-item'),
        $userDropdown = $('.global-header .user-dropdown'),
        $hamburgerMenu = $('.global-header .hamburger-menu'),
        $toggleUserDropdown = $('.global-header .toggle-user-dropdown');

    // Open or close relevant menu on enter or space click and focus on first element.
    if ((e.key === 'Enter' || e.key === 'Space') && (isToggle || isHamburgerMenu)) {
        e.preventDefault();
        e.stopPropagation();

        $curTarget.click();
        if (isHamburgerMenu) {
            if ($('.mobile-menu').is(':visible')) {
                $hamburgerMenu.attr('aria-expanded', true);
                $('.mobile-menu .mobile-nav-link a').first().focus();
            } else {
                $hamburgerMenu.attr('aria-expanded', false);
            }
        } else if (isToggle) {
            if ($('.global-header .nav-item .dropdown-user-menu').is(':visible')) {
                $userDropdown.attr('aria-expanded', 'true');
                $('.global-header .dropdown-item a:first').focus();
            } else {
                $userDropdown.attr('aria-expanded', false);
            }
        }
    }

    // Enable arrow functionality within the menu.
    if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && (isDropdownOption || isMobileOption ||
            (isHamburgerMenu && $hamburgerMenu.hasClass('open')) || isToggle && $toggleUserDropdown.hasClass('open'))) {
        isNext = e.key === 'ArrowDown';
        if (isNext && !isHamburgerMenu && !isToggle && isLastItem) {
            // Loop to the start from the final element
            nextLink = isDropdownOption ? $toggleUserDropdown : $hamburgerMenu;
        } else if (!isNext && (isHamburgerMenu || isToggle)) {
            // Loop to the end when up arrow pressed from menu icon
            nextLink = isHamburgerMenu ? $('.mobile-menu .mobile-nav-link a').last() :
                $('.global-header .dropdown-user-menu .dropdown-nav-item').last().find('a');
        } else if (isNext && (isHamburgerMenu || isToggle)) {
            // Loop to the first element from the menu icon
            nextLink = isHamburgerMenu ? $('.mobile-menu .mobile-nav-link a').first() :
                $('.global-header .dropdown-user-menu .dropdown-nav-item').first().find('a');
        } else {
            // Loop up to the menu icon if first element in menu
            if (!isNext && $curTarget.parent().is(':first-child') && !isHamburgerMenu && !isToggle) {
                nextLink = isDropdownOption ? $toggleUserDropdown : $hamburgerMenu;
            } else {
                nextLink = isNext ?
                    $curTarget.parent().next().find('a') : // eslint-disable-line newline-per-chained-call
                    $curTarget.parent().prev().find('a'); // eslint-disable-line newline-per-chained-call
            }
        }
        nextLink.focus();

        // Don't let the screen scroll on navigation
        e.preventDefault();
        e.stopPropagation();
    }

    // Escape clears out of the menu
    if (e.key === 'Escape' && (isDropdownOption || isHamburgerMenu || isMobileOption || isToggle)) {
        if (isDropdownOption || isToggle) {
            $('.global-header .nav-item .dropdown-user-menu').addClass('hidden');
            $toggleUserDropdown.focus()
                .attr('aria-expanded', 'false');
            $('.global-header .toggle-user-dropdown').removeClass('open');
        } else {
            $('.mobile-menu').addClass('hidden');
            $hamburgerMenu.focus()
                .attr('aria-expanded', 'false')
                .removeClass('open');
        }
    }

    // Loop when tabbing and using arrows
    if ((e.key === 'Tab') && ((isDropdownOption && isLastItem) || (isMobileOption && isLastItem) || (isHamburgerMenu &&
            $hamburgerMenu.hasClass('open')) || (isToggle && $toggleUserDropdown.hasClass('open')))) {
        nextLink = null;
        loopFirst = isLastItem && !e.shiftKey && !isHamburgerMenu && !isToggle;
        loopLast = (isHamburgerMenu || isToggle) && e.shiftKey;
        if (!(loopFirst || loopLast)) {
            return;
        }
        e.preventDefault();
        if (isDropdownOption || isToggle) {
            nextLink = loopFirst ? $toggleUserDropdown :
                $('.global-header .dropdown-user-menu .dropdown-nav-item a').last();
        } else {
            nextLink = loopFirst ? $hamburgerMenu : $('.mobile-menu .mobile-nav-link a').last();
        }
        nextLink.focus();
    }
});
