define(
  ['domReady', 'jquery', 'underscore', 'gettext', 'moment', 'js/utils/date_utils',
    'js/views/utils/create_timed_exam_utils', 'common/js/components/utils/view_utils',
    'select2', 'jquery.ui', 'jquery.timepicker', 'jqueryModal', 'js/index'],
  function(domReady, $, _, gettext, moment, DateUtils, CreateTimedExamUtilsFactory, ViewUtils) {
      'use strict';

      var CreateTimedExamUtils = new CreateTimedExamUtilsFactory({
          name: '.new-timed-exam-name',
          question_bank: '.question-bank',
          optional_questions_count: '.optional-question-count',
          start_date: '#exam-start-date',
          start_time: '#exam-start-time',
          end_date: '#exam-end-date',
          end_time: '#exam-end-time',
          timed_exam_allotted_time: '.timed-exam-time-allotted',
          allowed_disconnection_window: '.allowed-disconnection-window',
          is_randomized: '.is-randomized',
          is_bidirectional: '.is-bidirectional',
          exam_mode: '.exam-mode',
          skill: '.skill',
          round: '.round',
          exam_type: '.exam-type',
          generate_enrollment_code: '.generate-enrollment-code',
          enable_monitoring: '.enable-monitoring',
          question_count_of_easy_difficulty: '.question-count-of-easy-difficulty',
          question_count_of_medium_difficulty: '.question-count-of-medium-difficulty',
          question_count_of_hard_difficulty: '.question-count-of-hard-difficulty',
          chapters: '.chapters',
          chapters_include_exclude: 'input[name="chapters_include_exclude"]',
          topics: '.topics',
          topics_include_exclude: 'input[name="topics_include_exclude"]',
          learning_output: '.learning_output',
          learning_output_include_exclude: 'input[name="learning_output_include_exclude"]',
          save: '.new-timed-exam-save',
          errorWrapper: '.create-timed-exam .wrap-error',
          errorMessage: '#timed-exam-creation-error',
          tipError: '.create-timed-exam  span.tip-error',
          error: '.create-timed-exam .error',
          allowUnicode: '.allow-unicode-timed-exam-id'
      }, {
          shown: 'is-shown',
          showing: 'is-showing',
          hiding: 'is-hiding',
          disabled: 'is-disabled',
          error: 'error'
      });

      let $newTimedExamForm = $('#create-timed-exam-form');
      var timedExamFieldMap = {
        display_name: $newTimedExamForm.find('.new-timed-exam-name'),
        question_bank: $newTimedExamForm.find('.question-bank'),
        start_date: $newTimedExamForm.find('#exam-start-date'),
        start_time: $newTimedExamForm.find('#exam-start-time'),
        end_date: $newTimedExamForm.find('#exam-end-date'),
        end_time: $newTimedExamForm.find('#exam-end-time'),
        timed_exam_allotted_time: $newTimedExamForm.find('.timed-exam-time-allotted'),
        allowed_disconnection_window: $newTimedExamForm.find('.allowed-disconnection-window'),
        is_randomized: $newTimedExamForm.find('.is-randomized'),
        is_bidirectional: $newTimedExamForm.find('.is-bidirectional'),
        exam_mode: $newTimedExamForm.find('.exam-mode'),
        skill: $newTimedExamForm.find('.skill'),
        round: $newTimedExamForm.find('.round'),
        exam_type: $newTimedExamForm.find('.exam-type'),
        generate_enrollment_code: $newTimedExamForm.find('.generate-enrollment-code'),
        enable_monitoring: $newTimedExamForm.find('.enable-monitoring'),
        question_count_of_easy_difficulty: $newTimedExamForm.find('.question-count-of-easy-difficulty'),
        optional_easy_question_count: $newTimedExamForm.find('.optional-easy-question-count'),
        question_count_of_medium_difficulty: $newTimedExamForm.find('.question-count-of-medium-difficulty'),
        optional_medium_question_count: $newTimedExamForm.find('.optional-medium-question-count'),
        question_count_of_hard_difficulty: $newTimedExamForm.find('.question-count-of-hard-difficulty'),
        optional_hard_question_count: $newTimedExamForm.find('.optional-hard-question-count'),
        chapters: $newTimedExamForm.find('.chapters'),
        chapters_include_exclude: $newTimedExamForm.find('input[name="chapters_include_exclude"]:checked'),
        topics: $newTimedExamForm.find('.topics'),
        topics_include_exclude: $newTimedExamForm.find('input[name="topics_include_exclude"]:checked'),
        learning_output: $newTimedExamForm.find('.learning_output'),
        learning_output_include_exclude: $newTimedExamForm.find('input[name="learning_output_include_exclude"]:checked')
      };

      var showErrorModal = function (errors) {
          var errorLIs = errors.map(function(item) {
            var feedbackOL = $('<ol style="margin-left: 20px; list-style: square outside;"></ol>').append(
              item.feedback.map(function (feedbackItem){
                return $('<li></li>').text(feedbackItem)
              })
            );
            return $('<li></li>').text(item.message).append(feedbackOL);
          });

          $("#stickyModal .errors-wrapper").html('').append(errorLIs);

           $("#stickyModal").jqueryModal({
            escapeClose: false,
            clickClose: false,
            showClose: false
          });
        };
        // Validate that added value for this field is with-in its defined min-max range.
        // Use this for only inputs with type number.
        // var validateMinMax = function ($element) {
        //   var min = Number($element.attr('min'));
        //   var max = Number($element.attr('max'));
        //   var value = Number($element.attr('value'));
        //
        //   if (isNaN(min) || isNaN(max) || isNaN(value)) {
        //     return '';
        //   }
        //
        //   if (min <= value && value <= max) {
        //     // No Error
        //     return '';
        //   } else if (value <= min) {
        //     return 'Selected value must be greater than ' + (min - 1) + ' .';
        //   } else {
        //     return 'Selected value must be less than ' + (max + 1) + ' .';
        //   }
        // };

        var validateNonZeroTime = function (selectedTime) {
          selectedTime = selectedTime.split(':');
          var time = Number(selectedTime[0]) * 60 + Number(selectedTime[1]);

          if (time === 0) {
            return gettext('Selected time should not be zero.');
          }

          return '';
        };

         // var fieldsWithMinMaxValidation = [
         //   '.question-count-of-easy-difficulty', '.optional-easy-question-count',
         //   '.question-count-of-medium-difficulty', '.optional-medium-question-count',
         //   '.question-count-of-hard-difficulty', '.optional-hard-question-count',
         // ];

       var updateTimedExam = function(e, ignoreWarnings) {
          e.preventDefault();
          var timedExamKey = $("input[type='hidden'][name='timed_exam_key_string']").val();

          if (CreateTimedExamUtils.hasInvalidRequiredFields()) {
              return;
          }

          var hasErrors = false;

          //Perform further validation on field values, these validations are specific to business logic.
          // for (let i=0; i < fieldsWithMinMaxValidation.length; i++) {
          //   var $element = $(fieldsWithMinMaxValidation[i]);
          //   var error = validateMinMax($element);
          //
          //   if (error.length > 0) {
          //     CreateTimedExamUtils.setFieldInErr($element.parent(), error);
          //     hasErrors = true;
          //   }
          // }
          var errorMessage = validateNonZeroTime($('.timed-exam-time-allotted').val());
          if (errorMessage) {
            hasErrors = true;
            CreateTimedExamUtils.setFieldInErr($('.timed-exam-time-allotted').parent(), errorMessage);
          }

          if (hasErrors) {
            return;
          }

          let $newTimedExamForm = $('#create-timed-exam-form');
          let examStartDateTime = DateUtils.getLocalDate(timedExamFieldMap.start_date, timedExamFieldMap.start_time);
          let examEndDateTime = DateUtils.getLocalDate(timedExamFieldMap.end_date, timedExamFieldMap.end_time);
          let timed_exam_info = {
              display_name: $newTimedExamForm.find('.new-timed-exam-name').val(),
              question_bank: $newTimedExamForm.find('.question-bank').val(),
              timed_exam_release_date: examStartDateTime || '',
              timed_exam_due_date: examEndDateTime || '',
              timed_exam_allotted_time: $newTimedExamForm.find('.timed-exam-time-allotted').val(),
              allowed_disconnection_window: $newTimedExamForm.find('.allowed-disconnection-window').val(),
              is_randomized: Boolean(Number($newTimedExamForm.find('.is-randomized').val())),
              is_bidirectional: Boolean(Number($newTimedExamForm.find('.is-bidirectional').val())),
              exam_mode: $newTimedExamForm.find('.exam-mode').val(),
              skill: $newTimedExamForm.find('.skill').val(),
              round: $newTimedExamForm.find('.round').val(),
              exam_type: $newTimedExamForm.find('.exam-type').val(),
              generate_enrollment_code: Boolean(Number($newTimedExamForm.find('.generate-enrollment-code').val())),
              enable_monitoring: Boolean(Number($newTimedExamForm.find('.enable-monitoring').val())),
              question_count_of_easy_difficulty: Number($newTimedExamForm.find('.question-count-of-easy-difficulty').val()),
              optional_easy_question_count: Number($newTimedExamForm.find('.optional-easy-question-count').val()),
              question_count_of_medium_difficulty: Number($newTimedExamForm.find('.question-count-of-medium-difficulty').val()),
              optional_medium_question_count: Number($newTimedExamForm.find('.optional-medium-question-count').val()),
              question_count_of_hard_difficulty: Number($newTimedExamForm.find('.question-count-of-hard-difficulty').val()),
              optional_hard_question_count: Number($newTimedExamForm.find('.optional-hard-question-count').val()),
              chapters: $newTimedExamForm.find('.chapters').val(),
              chapters_include_exclude: $newTimedExamForm.find('input[name="chapters_include_exclude"]:checked').val(),
              topics: $newTimedExamForm.find('.topics').val(),
              topics_include_exclude: $newTimedExamForm.find('input[name="topics_include_exclude"]:checked').val(),
              learning_output: $newTimedExamForm.find('.learning_output').val(),
              learning_output_include_exclude: $newTimedExamForm.find('input[name="learning_output_include_exclude"]:checked').val()
          };

          var showFieldErrors = function (errors) {
            for (const key of Object.keys(errors)) {
               var error = errors[key][0];
               var $element = timedExamFieldMap[key];
               if ($element) {
                  CreateTimedExamUtils.setFieldInErr($element.parent(), error);
               }
            }
          };

          var performTimedExamUpdate = function() {
            analytics.track('Updated a Timed Exam', timed_exam_info);
            $('.update-timed-exam').addClass('is-disabled').attr('aria-disabled', true);

            var errorHandler = function(errorMessage, errorsList) {
              if (errorsList) {
                showFieldErrors(errorsList);
                var elementNamesWithError = Object.keys(errorsList);
                if (elementNamesWithError && elementNamesWithError.length > 0) {
                  // Bring the first element with error into focus.
                  var key = elementNamesWithError[0];
                  var $scrollElement = timedExamFieldMap[key];
                  ViewUtils.setScrollOffset($scrollElement, 50);
                }
              } else {
                var msg = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), errorMessage, edx.HtmlUtils.HTML('</p>'));
                $('.create-timed-exam .wrap-error').addClass('is-shown');
                edx.HtmlUtils.setHtml($('#timed-exam-creation-error'), msg);
                $('.update-timed-exam').addClass('is-disabled').attr('aria-disabled', true);
              }
            };

            CreateTimedExamUtils.updateTimedExamFields(
              timedExamKey,
              timed_exam_info,
              function () {
                CreateTimedExamUtils.update(timedExamKey, timed_exam_info, errorHandler);
              },
              errorHandler
            );
          };

          if (!ignoreWarnings) {
              CreateTimedExamUtils.fetchTimedExamQuestionStats(timed_exam_info, function (data) {
                var selected = {
                  easy: timed_exam_info.question_count_of_easy_difficulty,
                  moderate: timed_exam_info.question_count_of_medium_difficulty,
                  hard: timed_exam_info.question_count_of_hard_difficulty
                };
                var errorList = [];
                var selections = [];
                var chapters_selection = timed_exam_info.chapters ? timed_exam_info.chapters.map(item => "Chapter " + item) : timed_exam_info.chapters;
                selections = selections.concat(chapters_selection);
                selections = selections.concat(timed_exam_info.topics);
                selections = selections.concat(timed_exam_info.learning_output);

                if (selected.easy > data.easy) {
                  var error_str = 'Available number of easy questions after applying the tags is {originalEasy}, But you have selected {selectedEasy}.';
                  if (selections.length > 0) {
                    error_str = error_str + ' Following selections could be the cause of the problem.'
                  }
                  errorList.push({
                    message: edx.StringUtils.interpolate(gettext(error_str), {
                      originalEasy: data.easy, selectedEasy: selected.easy}),
                    feedback: selections,
                  });
                }

                if (selected.moderate > data.moderate) {
                  var error_str = 'Available number of moderate questions after applying the tags is {originalModerate}, But you have selected {selectedModerate}.';
                  if (selections.length > 0) {
                    error_str = error_str + ' Following selections could be the cause of the problem.'
                  }
                  errorList.push({
                    message: edx.StringUtils.interpolate(gettext(error_str), {
                      originalModerate: data.moderate, selectedModerate: selected.moderate}),
                    feedback: selections,
                  });
                }

                if (selected.hard > data.hard) {
                  var error_str = 'Available number of hard questions after applying the tags is {originalHard}, But you have selected {selectedHard}.';
                  if (selections.length > 0) {
                    error_str = error_str + ' Following selections could be the cause of the problem.'
                  }
                  errorList.push({
                    message: edx.StringUtils.interpolate(gettext(error_str), {
                      originalHard: data.hard, selectedHard: selected.hard}),
                    feedback: selections,
                  });
                }

                if (errorList.length > 0) {
                  showErrorModal(errorList);
                } else {
                   performTimedExamUpdate();
                }
              },
              function (){
                // Ignore errors and save the timed exam.
                performTimedExamUpdate();
              });
            }
            else {
              // User wants to ignore errors and save the timed exam
              performTimedExamUpdate();
            }
         };

      var cancelTimedExamUpdate = function (e){
        ViewUtils.redirect('/home/');
      };

      var onReady = function() {
        $('.update-timed-exam').on('click', updateTimedExam);
        $('#save-ignoring-errors').on('click', function (e){updateTimedExam(e, true);});
        $('.new-timed-exam-cancel').on('click', cancelTimedExamUpdate);
      };

      domReady(onReady);

      return {
          onReady: onReady
      };
  }
);
