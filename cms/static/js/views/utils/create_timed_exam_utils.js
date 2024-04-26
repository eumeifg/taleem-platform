/**
 * Provides utilities for validating libraries during creation.
 */
define(['jquery', 'underscore', 'gettext', 'common/js/components/utils/view_utils', 'js/views/utils/create_utils_base'],
    function($, _, gettext, ViewUtils, CreateUtilsFactory) {
        'use strict';
        return function(selectors, classes) {
            var keyLengthViolationMessage = gettext('The length of the question bank name' +
              ' cannot be more than <%- limit %> characters.');
            var keyFieldSelectors = [selectors.name];
            var nonEmptyCheckFieldSelectors = [
              selectors.name,
              selectors.question_bank,
              selectors.start_date,
              selectors.start_time,
              selectors.end_date,
              selectors.end_time,
              selectors.timed_exam_allotted_time,
              selectors.allowed_disconnection_window,
              selectors.is_randomized,
              selectors.is_bidirectional,
              selectors.exam_mode,
              selectors.skill,
              selectors.round,
              selectors.exam_type,
              selectors.generate_enrollment_code,
              selectors.enable_monitoring,
            ];
            var requiredFields = [
              selectors.question_bank,
              selectors.skill,
            ];

            var conditionallyRequiredFields = {
              fields: [
                {
                  field: selectors.chapters,
                  conditional_field: selectors.chapters_include_exclude
                },
                {
                  field: selectors.topics,
                  conditional_field: selectors.topics_include_exclude
                },
                {
                  field: selectors.learning_output,
                  conditional_field: selectors.learning_output_include_exclude
                }
              ],
              condition: function(field, conditional_field) {
                var $condition = $(conditional_field + ":checked");

                if ($condition.val() === 'all') {
                  // no validation required
                  return true;
                }
                // validate that field is not empty.
                return $(field).val() && $(field).val().length !== 0;
              }
            };

            this.validateRequiredField = ViewUtils.validateRequiredField;
            var self = this;

            CreateUtilsFactory.call(this, selectors, classes, keyLengthViolationMessage, keyFieldSelectors, nonEmptyCheckFieldSelectors);

            // Ensure that all fields are not empty
            this.validateFilledFields = function() {
                var value = _.reduce(
                  conditionallyRequiredFields.fields,
                  function(acc, element) {
                    return conditionallyRequiredFields.condition(element.field, element.conditional_field) ? acc : false;
                  },
                  true
                );
              if (value === false) {
                return value;
              }

                return _.reduce(
                    nonEmptyCheckFieldSelectors,
                    function(acc, element) {
                        var $element = $(element);
                        return $element.val().length !== 0 ? acc : false;
                    },
                    true
                );
            };

            this.toggleSaveButton = function(is_enabled) {
                var is_disabled = !is_enabled;
                $(selectors.save).toggleClass(classes.disabled, is_disabled).attr('aria-disabled', is_disabled);
            };

            this.setFieldInErr = function(element, message) {
                if (message) {
                    element.addClass(classes.error);
                    element.children(selectors.tipError).addClass(classes.showing).removeClass(classes.hiding).text(message);
                    self.toggleSaveButton(false);
                } else {
                    element.removeClass(classes.error);
                    element.children(selectors.tipError).addClass(classes.hiding).removeClass(classes.showing);
                    // One "error" div is always present, but hidden or shown
                    if ($(selectors.error).length === 1) {
                        self.toggleSaveButton(true);
                    }
                }
            };

            var $fields = $(requiredFields.join(', '));
            $fields.on('keyup change', function() {
                var error = self.validateRequiredField($fields.val());
                self.setFieldInErr($fields.parent(), error);
                if (!self.validateFilledFields()) {
                    self.toggleSaveButton(false);
                }
            });

            let fields = conditionallyRequiredFields.fields;
            for (let i=0; i< fields.length; i++) {
              $(fields[i].field + ", " + fields[i].conditional_field).on('keyup change', function() {
                var $fieldToCheck = $(fields[i].field);

                var error = self.validateRequiredField($fieldToCheck.val() || "");
                if ($(fields[i].conditional_field + ":checked").val() === 'all') {
                  error = '';
                }

                self.setFieldInErr($fieldToCheck.parent(), error);
                if (!self.validateFilledFields()) {
                    self.toggleSaveButton(false);
                }
              });
            }

            this.create = function(timedExamInfo, errorHandler) {
                $.postJSON(
                    '/timed-exams/',
                    timedExamInfo
                ).done(function(data) {
                    ViewUtils.redirect(data.url);
                }).fail(function(jqXHR, textStatus, errorThrown) {
                    var reason = errorThrown;
                    var detailedErrors = [];
                    if (jqXHR.responseText) {
                        try {
                            var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                            detailedErrors = $.parseJSON(jqXHR.responseText).errors;
                            if (detailedReason) {
                                reason = detailedReason;
                            }
                        } catch (e) {}
                    }
                    errorHandler(reason, detailedErrors);
                });
            };

            this.update = function(timedExam, timedExamInfo, errorHandler) {
                $.postJSON(
                    '/timed-exams/' + timedExam,
                    timedExamInfo
                ).done(function(data) {
                    ViewUtils.redirect(data.url);
                }).fail(function(jqXHR, textStatus, errorThrown) {
                    var reason = errorThrown;
                    var detailedErrors = [];
                    if (jqXHR.responseText) {
                        try {
                            var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                            detailedErrors = $.parseJSON(jqXHR.responseText).errors;
                            if (detailedReason) {
                                reason = detailedReason;
                            }
                        } catch (e) {}
                    }
                    errorHandler(reason, detailedErrors);
                });
            };

            this.updateTimedExamFields = function(timedExam, timedExamInfo, successHandler, errorHandler) {
                $.postJSON(
                    '/timed-exam/' + timedExam + '/fields/',
                    timedExamInfo
                ).done(function(data) {
                    successHandler();
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

            this.fetchQuestionTags = function(questionBank, successHandler, errorHandler) {
                $.getJSON(
                    '/question-bank/' + questionBank + '/tags/'
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

            this.fetchQuestionBankStats = function(questionBank, successHandler, errorHandler) {
                $.getJSON(
                    '/question-bank/' + questionBank + '/statistics/'
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

            this.fetchTimedExamQuestionStats = function(timedExamInfo, successHandler, errorHandler) {
                $.postJSON(
                    '/question-bank/statistics-with-tags/',
                  timedExamInfo
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
    });
