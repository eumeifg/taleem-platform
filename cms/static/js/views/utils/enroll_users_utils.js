/**
 * Provides utilities for validating user enrollments.
 */
define(
  ['jquery', 'gettext', 'common/js/components/utils/view_utils'],
  function($, gettext, ViewUtils) {
    'use strict';
    return function(selectors, classes) {
      var requiredFields = [
        selectors.email,
        selectors.csv
      ];
      var self = this;

      this.toggleSaveButton = function (is_enabled) {
        var is_disabled = !is_enabled;
        $(selectors.save).toggleClass(classes.disabled, is_disabled).attr('aria-disabled', is_disabled);
      };

      this.setError = function (message) {
        var element = $(selectors.errorWrapper);
        if (message) {
            element.addClass(classes.error);
            element.children(selectors.errorMessage).addClass(classes.showing).removeClass(classes.hiding).text(message);
            self.toggleSaveButton(false);
        } else {
          element.removeClass(classes.error);
          element.children(selectors.errorMessage).addClass(classes.hiding).removeClass(classes.showing);
          self.toggleSaveButton(true);
        }
      };

      // Ensure that at-least one of fields is not empty.
      this.hasInvalidRequiredFields = function() {
        for (let i=0; i < requiredFields.length; i++) {
          var $element = $(requiredFields[i]);
          if ($element.val().length !== 0) {
            self.setError(false);
            return false;
          }
        }
        self.setError('At-least one of the fields must be provided.');
        return true;
      };

      this.configureHandlers = function() {
        _.each(
          requiredFields,
          function(element) {
            var $element = $(element);
            $element.on('keyup change', function(event) {
              self.hasInvalidRequiredFields();
            });
          }
        );
      };

      this.create = function(enrollmentInfo, successHandler, errorHandler) {
        ViewUtils.showLoadingIndicator();
        $.ajax({
          dataType: 'json',
          type: 'POST',
          url: '/api/enrollment/v1/bulk/enrollment/',
          data: enrollmentInfo,
          processData: false,
          contentType: false,
          success: function(data) {
            successHandler(data);
          },
          error: function (jqXHR, textStatus, errorThrown) {
            var reason = errorThrown;
            if (jqXHR.responseText) {
              try {
                var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                if (detailedReason) {
                  reason = detailedReason;
                }
              } catch (e) {}
            }
            errorHandler(reason);
          },
          complete: function() {
            ViewUtils.hideLoadingIndicator();
          }
        });
      };

      this.fetchEnrollments = function(courseKey, successHandler, errorHandler) {
        $.getJSON(
            '/timed-exam/'+ courseKey +'/learner-enrollments/'
        ).done(function(data) {
            successHandler(data);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            var reason = errorThrown;
            if (jqXHR.responseText) {
                try {
                    var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                    if (detailedReason) {
                        reason = detailedReason;
                    }
                } catch (e) {}
            }
            errorHandler(reason);
        });
      };

      this.fetchPendingEnrollments = function(courseKey, successHandler, errorHandler) {
        $.getJSON(
            '/timed-exam/'+ courseKey +'/learner-pending-enrollments/'
        ).done(function(data) {
            successHandler(data);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            var reason = errorThrown;
            if (jqXHR.responseText) {
                try {
                    var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                    if (detailedReason) {
                        reason = detailedReason;
                    }
                } catch (e) {}
            }
            errorHandler(reason);
        });
      };

    };
  }
);
