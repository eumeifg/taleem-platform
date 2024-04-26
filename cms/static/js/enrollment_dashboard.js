define(
  [
    'domReady', 'jquery', 'underscore', 'gettext', 'moment',
    'js/views/utils/enroll_users_utils', 'common/js/components/utils/view_utils',
    'dataTables'
  ],
  function(domReady, $, _, gettext, moment, EnrollUsersUtilsFactory, ViewUtils) {
      'use strict';

      var EnrollUsersUtils = new EnrollUsersUtilsFactory({
            email: '.email',
            csv: '.csv',
            save: '.enroll-users',
            errorWrapper: '.enroll-users-form .wrap-error',
            errorMessage: '#user-enrollment-error',
            tipError: '.enroll-users-form span.tip-error',
            error: '.enroll-users-form .error',
            allowUnicode: '.allow-unicode-enroll-users'
        }, {
            shown: 'show',
            showing: 'show',
            hiding: 'hidden',
            disabled: 'is-disabled',
            error: 'error'
        });

      var enrollReqSuccessHandler = function(data) {
        ViewUtils.redirect(data.url);
      };

      var enrollReqErrorHandler = function(errorMessage) {
          var msg = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), errorMessage, edx.HtmlUtils.HTML('</p>'));
          $('.enroll-users-form .wrap-error').addClass('is-shown');
          edx.HtmlUtils.setHtml($('#user-enrollment-error'), msg);
          $('.enroll-users').addClass('is-disabled').attr('aria-disabled', true);
      };

      var enrollUsers = function (e) {
        e.preventDefault();

        if (EnrollUsersUtils.hasInvalidRequiredFields()) {
          return;
        }
        var enrollUsersInfo = new FormData(e.currentTarget);
        $('.enroll-users').addClass('is-disabled').attr('aria-disabled', true);
        EnrollUsersUtils.create(enrollUsersInfo, enrollReqSuccessHandler, enrollReqErrorHandler);

      };

      // Process enrollments to format data differently or to add new columns etc.
      var processEnrollmentsForDataTable = function (enrollments) {
        var courseKey = $("input[type='hidden'][name='course_key_string']").val();
        enrollments = enrollments.map(function (row){
          var unEnrollURL = '/timed-exam/' + courseKey + '/unenroll-learner/?email=' + encodeURIComponent(row[0]);
          var resendNotificationURL = '/timed-exam/' + courseKey + '/resend-notification/?email=' + row[0];
          var unEnrollButtonText = gettext('Un-Enroll');
          var resendButtonText = gettext('Resend');
          row[1] = moment(row[1]).format('MMM Do YYYY [at] h:mm:ss a');

          // Add un-enroll button
          row = row.concat(
            '<a class="btn btn-primary" href="' + unEnrollURL + '">' + unEnrollButtonText + '</a>' +
            '&nbsp;&nbsp;<a class="btn btn-default" href="' + resendNotificationURL + '">' + resendButtonText + '</a>'
          );
          return row;
        });
        return enrollments;
      };

      // Process enrollments to format data differently or to add new columns etc.
      var processPendingEnrollmentsForDataTable = function (pendingEnrollments) {
        var courseKey = $("input[type='hidden'][name='course_key_string']").val();
        pendingEnrollments = pendingEnrollments.map(function (row){
          var deleteButtonText = gettext('Remove');
          var resendNotificationURL = '/timed-exam/' + courseKey + '/resend-pending-notification/?email=' + encodeURIComponent(row[0]);
          var deleteURL = '/timed-exam/' + courseKey + '/delete-pending-enrollment/?email=' + encodeURIComponent(row[0]);
          var resendButtonText = gettext('Resend');
          row[1] = moment(row[1]).format('MMM Do YYYY [at] h:mm:ss a');

          // Add un-enroll button
          row = row.concat(
            '<a class="btn btn-primary" href="' + deleteURL + '">' + deleteButtonText + '</a>' +
            '&nbsp;&nbsp;<a class="btn btn-default" href="' + resendNotificationURL + '">' + resendButtonText + '</a>'
          );
          return row;
        });
        return pendingEnrollments;
      };

      var showEnrollments = function (dataTable) {
        var courseKey = $("input[type='hidden'][name='course_key_string']").val();

        EnrollUsersUtils.fetchEnrollments(
          courseKey,
          function (data){
            $(dataTable).DataTable({
              data: processEnrollmentsForDataTable(data.enrollments),
              language: {
                url: (typeof datatablesLangPath !== 'undefined') ? datatablesLangPath : "",
              },
              columns: [
                  { title: gettext("Email") },
                  { title: gettext("Enrollment Date") },
                  { title: gettext("Actions") }
              ]
            });
        },
          function (error) {
            console.log('Error while fetching the question tags.\n', error);
          }
        );
      };

      var showPendingEnrollments = function (dataTable) {
        var courseKey = $("input[type='hidden'][name='course_key_string']").val();

        EnrollUsersUtils.fetchPendingEnrollments(
          courseKey,
          function (data){
            $(dataTable).DataTable({
              data: processPendingEnrollmentsForDataTable(data.pending_enrollments),
              language: {
                url: (typeof datatablesLangPath !== 'undefined') ? datatablesLangPath : "",
              },
              columns: [
                  { title: gettext("Email") },
                  { title: gettext("Enrollment Date") },
                  { title: gettext("Actions") }
              ]
            });
        },
          function (error) {
            console.log('Error while fetching the question tags.\n', error);
          }
        );
      };

      var addNewEnrollment = function (e) {
        e.preventDefault();
        $('.new-enrollment-button').addClass('is-disabled').attr('aria-disabled', true);
        $('.wrapper-enroll-users').addClass('is-shown');
      };

      var showEnrollmentTab = function() {
        $('.enrollments-tab').addClass('active');
        $('.pending-enrollments-tab').removeClass('active');
        $('.pending-enrollments').addClass('hidden');
        $('.linked-course-enrollments-tab').removeClass('active');
        $('.linked-course-enrollments').addClass('hidden');
        $('.enrollments').removeClass('hidden');
      };

      var showPendingEnrollmentTab = function () {
        $('.pending-enrollments-tab').addClass('active');
        $('.enrollments-tab').removeClass('active');
        $('.enrollments').addClass('hidden');
        $('.linked-course-enrollments-tab').removeClass('active');
        $('.linked-course-enrollments').addClass('hidden');
        $('.pending-enrollments').removeClass('hidden');
      };

      var showLinkedCourseEnrollmentTab = function () {
        $('.linked-course-enrollments-tab').addClass('active');
        $('.pending-enrollments-tab').removeClass('active');
        $('.pending-enrollments').addClass('hidden');
        $('.enrollments-tab').removeClass('active');
        $('.enrollments').addClass('hidden');
        $('.linked-course-enrollments').removeClass('hidden');
      };

      var showTab = function(tab) {
        return function(e) {
          e.preventDefault();
          if (tab == 'enrollments') {
            showEnrollmentTab();
          } else if (tab == 'pending-enrollments') {
            showPendingEnrollmentTab();
          } else {
            showLinkedCourseEnrollmentTab();
          }
        };
      };

      var onReady = function() {
          $('.enroll-users-form').bind('submit', enrollUsers);
          $('.new-enrollment-button').bind('click', addNewEnrollment);

          EnrollUsersUtils.configureHandlers();
          showEnrollments('#user-enrollments');
          showPendingEnrollments('#pending-enrollments');
          $("#linked-course-enrollments").DataTable({
            columnDefs: [{
                "targets": -1,
                "render": function (data, type, row) {
                    var sData = data.split(",");
                    var button = '<span>' + gettext('Already enrolled') + '</span>';
                    if (sData[1] != 'enrolled') {
                      button = '<button class="btn btn-primary enroll" data-username="' + sData[0] + '">' + gettext('Enroll to exam') + '</button>';
                    }
                    return button;
                }
            }],
            language: {
              url: (typeof datatablesLangPath !== 'undefined') ? datatablesLangPath : "",
            }
          });
          showEnrollmentTab();

          $('.enrollment-index-tabs .enrollments-tab').bind('click', showTab('enrollments'));
          $('.enrollment-index-tabs .pending-enrollments-tab').bind('click', showTab('pending-enrollments'));
          $('.enrollment-index-tabs .linked-course-enrollments-tab').bind('click', showTab('linked-course-enrollments'));

          const urlParams = new URLSearchParams(window.location.search);
          const tab = urlParams.get('tab');
          if (tab) {
            showTab(tab);
          }
      };

      domReady(onReady);

      return {
          onReady: onReady
      };
  }
);
