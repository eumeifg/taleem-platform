var FullCalendarMoment=function(e,t,a){"use strict";function n(e){return e&&"object"==typeof e&&"default"in e?e:{default:e}}var r=n(a);var l=t.createPlugin({cmdFormatter:function(e,t){var a=function e(t){var a=t.match(/^(.*?)\{(.*)\}(.*)$/);if(a){var n=e(a[2]);return{head:a[1],middle:n,tail:a[3],whole:a[1]+n.whole+a[3]}}return{head:null,middle:null,tail:null,whole:t}}(e);if(t.end){var n=o(t.start.array,t.timeZone,t.start.timeZoneOffset,t.localeCodes[0]),r=o(t.end.array,t.timeZone,t.end.timeZoneOffset,t.localeCodes[0]);return function e(t,a,n,r){if(t.middle){var l=a(t.head),u=e(t.middle,a,n,r),o=a(t.tail),i=n(t.head),d=e(t.middle,a,n,r),f=n(t.tail);if(l===i&&o===f)return l+(u===d?u:u+r+d)+o}var c=a(t.whole),m=n(t.whole);if(c===m)return c;return c+r+m}(a,u(n),u(r),t.defaultSeparator)}return o(t.date.array,t.timeZone,t.date.timeZoneOffset,t.localeCodes[0]).format(a.whole)}});function u(e){return function(t){return t?e.format(t):""}}function o(e,t,a,n){var l;return"local"===t?l=r.default(e):"UTC"===t?l=r.default.utc(e):r.default.tz?l=r.default.tz(e,t):(l=r.default.utc(e),null!=a&&l.utcOffset(a)),l.locale(n),l}return t.globalPlugins.push(l),e.default=l,e.toMoment=function(e,a){if(!(a instanceof t.CalendarApi))throw new Error("must supply a CalendarApi instance");var n=a.getCurrentData().dateEnv;return o(e,n.timeZone,null,n.locale.codes[0])},e.toMomentDuration=function(e){return r.default.duration(e)},Object.defineProperty(e,"__esModule",{value:!0}),e}({},FullCalendar,moment);

var calendarWrapper = $('.calendar-wrapper');

function calendarGetUserEvents(info, successCallback, failureCallback) {
	console.log("'calendarGetUserEvents' function not implemented!");
}

function addEventReminder(id, type, title, description, datetime) {
    console.log("'addEventReminder' function not implemented!");
}

function eventDidMount(info) {
  console.log("'eventDidMount' function not implemented!");
}

function eventWillUnmount(info) {
  console.log("'eventWillUnmount' function not implemented!");
}

function calendarInit(options) {
	$('.calendar-btn').on('click', function(e){
        calendarWrapper.addClass('calendar-on');
    });
    $('.calendar-wrapper .calendar-overlay, .calendar-wrapper .calendar-panel .calendar-close').on('click', function(e){
        calendarWrapper.removeClass('calendar-on');
    });

    // calendar initialize
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        customButtons: {
            createEventButton: {
                text: 'Create Event',
                click: function() {
                    $('#createEventModal').modal();
                }
            }
        },
        headerToolbar: {
            left: 'title',
            center: '',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listMonth prev,next today createEventButton'
        },
        initialDate: new Date().toJSON().slice(0,10),
        locale: calendarLocale,
        timeZone: calendarTimeZone,
        firstDay: calendarFirstDayOfWeek,
        titleFormat: calendarDateFormat,
        buttonIcons: true, // show the prev/next text
        weekNumbers: false,
        navLinks: true, // can click day/week names to navigate views
        editable: false,
        dayMaxEvents: false, // allow "more" link when too many events
        eventDisplay: 'block',

        eventDidMount: function(info) {
          eventDidMount(info);
        },
        eventWillUnmount: function(info) {
          eventWillUnmount(info);
        },
        loading: function(bool) {
            if(bool) {
                calendarWrapper.addClass('loading');
            } else {
                calendarWrapper.removeClass('loading');
            }
        },

        events: calendarGetUserEvents
    });

    calendar.render();

    if(!calendarObj) {
        calendarObj = calendar;
    }
}
