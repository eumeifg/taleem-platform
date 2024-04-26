define(
  ['domReady', 'jquery', 'underscore', 'gettext', 'moment', 'js/views/utils/bulk_registration_utils', 'dataTables'],
  function(domReady, $, _, gettext, moment, BulkRegistrationUtilsFactory) {
      'use strict';

      var BulkRegistrationUtils = new BulkRegistrationUtilsFactory({
            csv: '.csv',
            without_email: '.without_email',
            save: '.register-users',
            errorWrapper: '.bulk-register-form .wrap-error',
            errorMessage: '#bulk-register-error',
            tipError: '.bulk-register-form span.tip-error',
            error: '.bulk-register-form .error',
            allowUnicode: '.allow-unicode-register-users'
        }, {
            shown: 'show',
            showing: 'show',
            hiding: 'hidden',
            disabled: 'is-disabled',
            error: 'error'
        });

      var registerUsers = function (e) {
        e.preventDefault();

        if (BulkRegistrationUtils.hasInvalidRequiredFields()) {
          return;
        }
        var registerUsersInfo = new FormData(e.currentTarget);

        analytics.track('Bulk user registration', registerUsersInfo);
        $('.register-users').addClass('is-disabled').attr('aria-disabled', true);
        BulkRegistrationUtils.create(registerUsersInfo, function(errorMessage) {
            var msg = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), errorMessage, edx.HtmlUtils.HTML('</p>'));
            edx.HtmlUtils.setHtml($('#bulk-register-error'), msg);
            $('.register-users').addClass('is-disabled').attr('aria-disabled', true);
        });

      };

      var onReady = function() {
          $('.bulk-register-form').bind('submit', registerUsers);
          $('.bulk-register-form .without_email').on('change', function (event) {
            if ($(event.target).is(':checked')) {
              $('.sample-csv-without-email').removeClass('hidden');
              $('.sample-csv-with-email').addClass('hidden');
            } else {
              $('.sample-csv-without-email').addClass('hidden');
              $('.sample-csv-with-email').removeClass('hidden');
            }
          });
          BulkRegistrationUtils.configureHandlers();
      };

      domReady(onReady);

      return {
          onReady: onReady
      };
  }
);
