/**
 * Provides utilities for validating user enrollments.
 */
define(
  ['jquery', 'gettext', 'common/js/components/utils/view_utils'],
  function($, gettext, ViewUtils) {
    'use strict';
    return function(selectors, classes) {
      var requiredFields = [selectors.csv];
      var self = this;

      this.toggleSaveButton = function (is_enabled) {
        var is_disabled = !is_enabled;
        $(selectors.save).toggleClass(classes.disabled, is_disabled).attr('aria-disabled', is_disabled);
      };

      this.setError = function (message) {
        var element = $(selectors.errorWrapper);
        if (message) {
            element.addClass(classes.error);
            element.children(selectors.errorMessage).addClass(classes.showing).removeClass(classes.hiding);
            element.children(selectors.errorMessage).html(message);
            self.toggleSaveButton(false);
        } else {
          element.removeClass(classes.error);
          element.children(selectors.errorMessage).addClass(classes.hiding).removeClass(classes.showing);
          self.toggleSaveButton(true);
        }
      };

      this.downloadCSV = function (content) {
        var csvContent = '';

        content.forEach(function(rowContent) {
            let row = rowContent.join(",");
            csvContent += row + "\r\n";
        });
        // Create a blob
        var blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' });
        var url = URL.createObjectURL(blob);

        // Create a link to download it
        var downloadBtn = document.createElement('a');
        downloadBtn.href = url;
        downloadBtn.setAttribute('download', 'students-data.csv');
        downloadBtn.click();
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
        var msg = edx.HtmlUtils.joinHtml(
          edx.HtmlUtils.HTML('<p>'),
          'The required fields must be provided.',
           edx.HtmlUtils.HTML('</p>')
           );
        self.setError(msg.text);
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

      this.create = function(bulkRegistrationInfo, errorHandler) {
        $.ajax({
          dataType: 'json',
          type: 'POST',
          url: '/bulk-registration/',
          data: bulkRegistrationInfo,
          processData: false,
          contentType: false,
          success: function(data) {
            if (data.status === 200) {
              self.setError(false);
              self.downloadCSV(data.csvData);
              location.reload();
            } else {
              var msg = '';
              data.errors.forEach(error => {
                msg += edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), error, edx.HtmlUtils.HTML('</p>'));
              });
              self.setError(msg);
            }
          },
          error: function (jqXHR, textStatus, errorThrown){
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
          }
        });
      };

    };
  }
);
