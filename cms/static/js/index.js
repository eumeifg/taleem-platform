define(['domReady', 'jquery', 'underscore', 'gettext', 'moment', 'js/utils/date_utils',
    'js/utils/cancel_on_escape', 'js/views/utils/create_course_utils',
    'js/views/utils/create_library_utils', 'js/views/utils/create_timed_exam_utils',
    'common/js/components/utils/view_utils',
    'select2', 'jquery.ui', 'jquery.timepicker', 'jqueryModal'],
    function(domReady, $, _, gettext, moment, DateUtils, CancelOnEscape, CreateCourseUtilsFactory, CreateLibraryUtilsFactory, CreateTimedExamUtilsFactory, ViewUtils) {
        'use strict';
        var CreateCourseUtils = new CreateCourseUtilsFactory({
            name: '.new-course-name',
            org: '.new-course-org',
            number: '.new-course-number',
            run: '.new-course-run',
            price: '.new-course-price',
            skill: '.course-skill',
            save: '.new-course-save',
            errorWrapper: '.create-course .wrap-error',
            errorMessage: '#course_creation_error',
            tipError: '.create-course span.tip-error',
            error: '.create-course .error',
            allowUnicode: '.allow-unicode-course-id'
        }, {
            shown: 'is-shown',
            showing: 'is-showing',
            hiding: 'is-hiding',
            disabled: 'is-disabled',
            error: 'error'
        });

        var CreateLibraryUtils = new CreateLibraryUtilsFactory({
            name: '.new-library-name',
            org: '.new-library-org',
            number: '.new-library-number',
            college: '.new-library-college',
            department: '.new-library-department',
            save: '.new-library-save',
            errorWrapper: '.create-library .wrap-error',
            errorMessage: '#library_creation_error',
            tipError: '.create-library  span.tip-error',
            error: '.create-library .error',
            allowUnicode: '.allow-unicode-library-id'
        }, {
            shown: 'is-shown',
            showing: 'is-showing',
            hiding: 'is-hiding',
            disabled: 'is-disabled',
            error: 'error'
        });

        var CreateTimedExamUtils = new CreateTimedExamUtilsFactory({
            name: '.new-timed-exam-name',
            question_bank: '.question-bank',
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
            optional_easy_question_count: '.optional-easy-question-count',
            question_count_of_medium_difficulty: '.question-count-of-medium-difficulty',
            optional_medium_question_count: '.optional-medium-question-count',
            question_count_of_hard_difficulty: '.question-count-of-hard-difficulty',
            optional_hard_question_count: '.optional-hard-question-count',
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
        learning_output_include_exclude: $newTimedExamForm.find('input[name="learning_output_include_exclude"]:checked'),
      };


        var saveNewCourse = function(e) {
            e.preventDefault();

            if (CreateCourseUtils.hasInvalidRequiredFields()) {
                return;
            }

            var $newCourseForm = $(this).closest('#create-course-form');
            var display_name = $newCourseForm.find('.new-course-name').val();
            var org = $newCourseForm.find('.new-course-org').val();
            var number = $newCourseForm.find('.new-course-number').val();
            var run = $newCourseForm.find('.new-course-run').val();
            var price = $newCourseForm.find('.new-course-price').val();
            var skill = $newCourseForm.find('.course-skill').val();

            var course_info = {
                org: org,
                number: number,
                display_name: display_name,
                run: run,
                price: price,
                skill: skill
            };

            analytics.track('Created a Course', course_info);
            CreateCourseUtils.create(course_info, function(errorMessage) {
                var msg = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), errorMessage, edx.HtmlUtils.HTML('</p>'));
                $('.create-course .wrap-error').addClass('is-shown');
                edx.HtmlUtils.setHtml($('#course_creation_error'), msg);
                $('.new-course-save').addClass('is-disabled').attr('aria-disabled', true);
            });
        };

        var rtlTextDirection = function() {
            var Selectors = {
                new_course_run: '#new-course-run'
            };

            if ($('body').hasClass('rtl')) {
                $(Selectors.new_course_run).addClass('course-run-text-direction placeholder-text-direction');
                $(Selectors.new_course_run).on('input', function() {
                    if (this.value === '') {
                        $(Selectors.new_course_run).addClass('placeholder-text-direction');
                    } else {
                        $(Selectors.new_course_run).removeClass('placeholder-text-direction');
                    }
                });
            }
        };

        var makeCancelHandler = function(addType) {
            return function(e) {
                e.preventDefault();
                $('.new-' + addType + '-button').removeClass('is-disabled').attr('aria-disabled', false);
                $('.wrapper-create-' + addType).removeClass('is-shown');
                // Clear out existing fields and errors
                $('#create-' + addType + '-form input[type=text]').val('');
                $('#' + addType + '_creation_error').html('');
                $('.create-' + addType + ' .wrap-error').removeClass('is-shown');
                $('.new-' + addType + '-save').off('click');
            };
        };

        var addNewCourse = function(e) {
            var $newCourse,
                $cancelButton,
                $courseName;
            e.preventDefault();
            $('.new-course-button').addClass('is-disabled').attr('aria-disabled', true);
            $('.new-course-save').addClass('is-disabled').attr('aria-disabled', true);
            $newCourse = $('.wrapper-create-course').addClass('is-shown');
            $cancelButton = $newCourse.find('.new-course-cancel');
            $courseName = $('.new-course-name');
            $courseName.focus().select();
            $('.new-course-save').on('click', saveNewCourse);
            $cancelButton.bind('click', makeCancelHandler('course'));
            CancelOnEscape($cancelButton);
            CreateCourseUtils.setupOrgAutocomplete();
            CreateCourseUtils.configureHandlers();
            rtlTextDirection();
        };

        var saveNewLibrary = function(e) {
            e.preventDefault();

            if (CreateLibraryUtils.hasInvalidRequiredFields()) {
                return;
            }

            var $newLibraryForm = $(this).closest('#create-library-form');
            var display_name = $newLibraryForm.find('.new-library-name').val();
            var org = $newLibraryForm.find('.new-library-org').val();
            var college = $newLibraryForm.find('.new-library-college').val();
            var department = $newLibraryForm.find('.new-library-department').val();
            var number = $newLibraryForm.find('.new-library-number').val();

            var universities = $newLibraryForm.find('#new-library-college-field').data('universities');

            if (universities.includes(org)) {
              var hasErrors = _.reduce(
                ['.new-library-college', '.new-library-department'],
                function(acc, element) {
                    var $element = $(element);
                    var error = CreateLibraryUtils.validateRequiredField($element.val());
                    CreateLibraryUtils.setFieldInErr($element.parent(), error);
                    return error ? true : acc;
                },
                false
              );
              if (hasErrors) {
                return;
              }

              org = org + ':' + college + ':' + department;
            }

            var lib_info = {
                org: org.replaceAll(" ", "-"),
                number: number.replaceAll(" ", "-"),
                display_name: display_name.replaceAll(" ", "-")
            };

            analytics.track('Created a Library', lib_info);
            CreateLibraryUtils.create(lib_info, function(errorMessage) {
                var msg = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), errorMessage, edx.HtmlUtils.HTML('</p>'));
                $('.create-library .wrap-error').addClass('is-shown');
                edx.HtmlUtils.setHtml($('#library_creation_error'), msg);
                $('.new-library-save').addClass('is-disabled').attr('aria-disabled', true);
            });
        };

        var populateCollegesField = function (university) {
          CreateLibraryUtils.fetchColleges(
            university,
            function (data) {
                var $newLibraryForm = $('#create-library-form');
                $newLibraryForm.find('.new-library-college').select2('destroy').empty().select2({data: data.colleges, width: '100%'});
            },
            function (error) {
              console.log(error);
            }
          );
        };

        var populateDepartmentsField = function (university, college) {
          CreateLibraryUtils.fetchDepartments(
            university,
            college,
            function (data) {
                var $newLibraryForm = $('#create-library-form');
                $newLibraryForm.find('.new-library-department').select2('destroy').empty().select2({data: data.departments, width: '100%'});
            },
            function (error) {
              console.log(error);
            }
          );
        };

        var handleOrganizationChange = function (e) {
          var $collegeField = $('#new-library-college-field');
          var $departmentField = $('#new-library-department-field');
          var universities = $collegeField.data('universities');
          $('.new-library-college').empty();
          $('.new-library-department').empty();

          if (universities.includes(e.target.value)) {
            $collegeField.removeClass('hidden').addClass('required');
            $departmentField.removeClass('hidden').addClass('required');
            populateCollegesField(e.target.value);
          } else {
            $collegeField.addClass('hidden').removeClass('required');
            $departmentField.addClass('hidden').removeClass('required');
          }
        };

        var handleOptionalFieldChange = function (e) {
          var universities = $('#new-library-college-field').data('universities');
          var org = $('.new-library-org').val();

          if (universities.includes(org)) {
            var $element = $('#' + e.target.id);
            var error = CreateLibraryUtils.validateRequiredField($element.val());
            CreateLibraryUtils.setFieldInErr($element.parent(), error);
          } else {
            CreateLibraryUtils.setFieldInErr($('.new-library-college').parent(), '');
            CreateLibraryUtils.setFieldInErr($('.new-library-department').parent(), '');
          }
        };

        var addNewLibrary = function(e) {
            e.preventDefault();
            $('.new-library-button').addClass('is-disabled').attr('aria-disabled', true);
            $('.new-library-save').addClass('is-disabled').attr('aria-disabled', true);
            var $newLibrary = $('.wrapper-create-library').addClass('is-shown');
            var $cancelButton = $newLibrary.find('.new-library-cancel');
            var $libraryName = $('.new-library-name');
            $libraryName.focus().select();
            $('.new-library-save').on('click', saveNewLibrary);
            $cancelButton.bind('click', makeCancelHandler('library'));
            CancelOnEscape($cancelButton);

            $('.new-library-org').on('change', handleOrganizationChange);
            $('.new-library-college, .new-library-department').on('change', handleOptionalFieldChange);

            // Populate departments on college change.
            $('.new-library-college').on('change', function (e) {
              var universities = $('#new-library-college-field').data('universities');
              var university = $('.new-library-org').val();
              if (universities.includes(university)) {
                populateDepartmentsField(university, e.target.value);
              }
            });

            CreateLibraryUtils.configureHandlers();
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

         var saveNewTimedExam = function(e, ignoreWarnings) {
            e.preventDefault();

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

            var performTimedExamCreation = function(){
              analytics.track('Created a Timed Exam', timed_exam_info);
              $('.new-timed-exam-save').addClass('is-disabled').attr('aria-disabled', true);

              CreateTimedExamUtils.create(timed_exam_info, function(errorMessage, errorsList) {
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
                  $('.new-timed-exam-save').addClass('is-disabled').attr('aria-disabled', true);
                }
              });
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

                var feedback = {easy: [], moderate: [], hard: []};

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
                   performTimedExamCreation();
                }
              },
              function (){
                // Ignore errors and save the timed exam.
                performTimedExamCreation();
              });
            }
            else {
              // User wants to ignore errors and save the timed exam
              performTimedExamCreation();
            }
         };

        var addNewTimedExam = function(e) {
            e.preventDefault();
            $('.new-timed-exam-button').addClass('is-disabled').attr('aria-disabled', true);
            var $newLibrary = $('.wrapper-create-timed-exam').addClass('is-shown');
            var $cancelButton = $newLibrary.find('.new-timed-exam-cancel');
            var $libraryName = $('.new-timed-exam-name');
            $libraryName.focus().select();
            $('.new-timed-exam-save').on('click', saveNewTimedExam);
            $('#save-ignoring-errors').on('click', function (e){saveNewTimedExam(e, true);});
            $cancelButton.bind('click', makeCancelHandler('timed-exam'));
            CancelOnEscape($cancelButton);

            CreateTimedExamUtils.configureHandlers();
        };

        var showTab = function(tab) {
            return function(e) {
                e.preventDefault();
                $('.courses-tab').toggleClass('active', tab === 'courses');
                $('.archived-courses-tab').toggleClass('active', tab === 'archived-courses');
                $('.libraries-tab').toggleClass('active', tab === 'libraries');
                $('.timed-exam-tab').toggleClass('active', tab === 'timed-exam');

            // Also toggle this course-related notice shown below the course tab, if it is present:
                $('.wrapper-creationrights').toggleClass('is-hidden', tab !== 'courses');
            };
        };

        var onQuestionBankChange = function (event) {
          CreateTimedExamUtils.fetchQuestionTags(
            event.target.value,
            function (data) {
              var $newTimedExamForm = $('#create-timed-exam-form');
              $("#question-count-of-easy-difficulty").val(0);
              $("#optional-easy-question-count").attr('disabled', true);
              $("#optional-easy-question-count").val(0);

              $("#question-count-of-medium-difficulty").val(0);
              $("#optional-medium-question-count").attr('disabled', true);
              $("#optional-medium-question-count").val(0);

              $("#question-count-of-hard-difficulty").val(0);
              $("#optional-hard-question-count").attr('disabled', true);
              $("#optional-hard-question-count").val(0);

              $newTimedExamForm.find('.chapters').select2('destroy').empty().select2({data: data.chapter, width: '100%'});
              $newTimedExamForm.find('.topics').select2('destroy').empty().select2({data: data.topic, width: '100%'});
              $newTimedExamForm.find('.learning_output').select2('destroy').empty().select2({data: data.learning_output, width: '100%'});

              $('input[name="topics_include_exclude"][value="all"]').prop("checked", true).change();
              $('input[name="chapters_include_exclude"][value="all"]').prop("checked", true).change();
              $('input[name="learning_output_include_exclude"][value="all"]').prop("checked", true).change();
            },
            function (msg) {
              console.log("Error while fetching the question tags.\n", msg);
            }
          );

          CreateTimedExamUtils.fetchQuestionBankStats(
            event.target.value,
            function (data) {
              var number_of_question_in_bank = data['easy'] + data['moderate'] + data['hard'];
              if (number_of_question_in_bank <= 0){
                $("#tip-error-question-bank").show();
                $("#tip-error-question-bank").text(
                  edx.StringUtils.interpolate(
                  gettext('Number of questions in the selected question bank is {count}. Please select another question bank or add question first.'), {count: number_of_question_in_bank})
                );
                $("#tip-error-question-bank").css('color', 'red');
                $('.new-timed-exam-save').addClass('is-disabled').attr('aria-disabled', true);
              } else {
                $("#tip-error-question-bank").hide();
                $('.new-timed-exam-save').removeClass('is-disabled').attr('aria-disabled', false);
                $("#tip-available-easy-questions").text(
                  edx.StringUtils.interpolate(
                    gettext('Available number of easy questions is {count}'), {count: data.easy})
                );
                $("#tip-available-medium-questions").text(
                  edx.StringUtils.interpolate(
                    gettext('Available number of moderate questions is {count}'), {count: data.moderate})
                );
                $("#tip-available-hard-questions").text(
                  edx.StringUtils.interpolate(
                    gettext('Available number of hard questions is {count}'), {count: data.hard})
                );
                $("#optional-easy-question-count").data('has-same-weightage', data['has_same_weightage']).attr('max', data['easy']);
                $("#optional-medium-question-count").data('has-same-weightage', data['has_same_weightage']).attr('max', data['moderate']);
                $("#optional-hard-question-count").data('has-same-weightage', data['has_same_weightage']).attr('max', data['hard']);

                if (data['easy'] === 0) {
                  $("#question-count-of-easy-difficulty").attr('disabled', true);
                } else {
                  $("#question-count-of-easy-difficulty").removeAttr('disabled').attr('max', data['easy']);
                }
                if (data['moderate'] === 0) {
                  $("#question-count-of-medium-difficulty").attr('disabled', true);
                } else {
                  $("#question-count-of-medium-difficulty").removeAttr('disabled').attr('max', data['moderate']);
                }
                if (data['hard'] === 0) {
                  $("#question-count-of-hard-difficulty").attr('disabled', true);
                }
                else {
                  $("#question-count-of-hard-difficulty").removeAttr('disabled').attr('max', data['hard']);
                }
              }
            },
            function (msg) {
              console.log("Error while fetching the question tags.\n", msg);
            }
          );
        };

        var updateIncludeExclude = function (radioInputName) {
          return function (event) {
            var value = event.target.value;
            if (value && value.length > 0) {
              var include_exclude_value = $('input[name="' + radioInputName + '"]:checked').val();
              if (include_exclude_value === 'all'){
                $('input[name="' + radioInputName + '"][value="include"]').prop("checked", true).change();
              }
            } else {
               $('input[name="' + radioInputName + '"][value="all"]').prop("checked", true).change();
            }
          };
        };

        var onQuestionCountChange = function (option_question_input) {
          return function (event) {
            var hasSameWeightage = $(option_question_input).data('hasSameWeightage');

            if (hasSameWeightage && event.target.value > 0) {
              $(option_question_input).attr('disabled', false);
            } else {
               $(option_question_input).val(0);
               $(option_question_input).attr('disabled', true);
            }
          };
        };

        var validateReleaseAndDueDate = function () {
          let releaseDate = DateUtils.getDate(timedExamFieldMap.start_date, timedExamFieldMap.start_time);
          let dueDate = DateUtils.getDate(timedExamFieldMap.end_date, timedExamFieldMap.end_time);
          if (releaseDate && dueDate && releaseDate >= dueDate) {
            return false;
          }
          return true;
         };

        var onReady = function() {
            $('.new-course-button').bind('click', addNewCourse);
            $('.new-library-button').bind('click', addNewLibrary);
            $('.new-timed-exam-button').bind('click', addNewTimedExam);
            $('.question-bank').bind('change', onQuestionBankChange);
            $('.question-count-of-easy-difficulty').bind('change', onQuestionCountChange('.optional-easy-question-count'));
            $('.question-count-of-medium-difficulty').bind('change', onQuestionCountChange('.optional-medium-question-count'));
            $('.question-count-of-hard-difficulty').bind('change', onQuestionCountChange('.optional-hard-question-count'));

             $('.chapters').bind('change', updateIncludeExclude('chapters_include_exclude'));
             $('.topics').bind('change', updateIncludeExclude('topics_include_exclude'));
             $('.learning_output').bind('change', updateIncludeExclude('learning_output_include_exclude'));

            $('.select2').select2({
              width: '100%'
            });

            $('.dismiss-button').bind('click', ViewUtils.deleteNotificationHandler(function() {
                ViewUtils.reload();
            }));

            $('.action-reload').bind('click', ViewUtils.reload);

            $('#course-index-tabs .courses-tab').bind('click', showTab('courses'));
            $('#course-index-tabs .archived-courses-tab').bind('click', showTab('archived-courses'));
            $('#course-index-tabs .libraries-tab').bind('click', showTab('libraries'));
            $('#course-index-tabs .timed-exam-tab').bind('click', showTab('timed-exam'));

            $('.timepicker').timepicker({
              'showDuration': true,
              'timeFormat': 'H:i',
              'scrollDefaultNow': false
            });

            $('.datepicker').datepicker({
              'dateFormat': 'dd-mm-yy',
              'autoclose': true
            });

            // $(fieldsWithMinMaxValidation.join(', ')).on('keyup change', function (e) {
            //   var $element = $('#' + e.target.id);
            //   var error = validateMinMax($element);
            //   CreateTimedExamUtils.setFieldInErr($element.parent(), error);
            // });

            $('.timed-exam-time-allotted').on('keyup change', function (e) {
              var $element = $('#' + e.target.id);
              var error = validateNonZeroTime($element.val());
              CreateTimedExamUtils.setFieldInErr($element.parent(), error);
            });

            $('.start-date, .end-date').on('keyup change', function (e) {
              var lessThanReleaseErrorString = gettext('The exam end date must be later than the exam start date.');
              if (!validateReleaseAndDueDate()) {
                CreateTimedExamUtils.setFieldInErr($("#exam-end-date").parent(), lessThanReleaseErrorString);
              } else {
                CreateTimedExamUtils.setFieldInErr($("#exam-end-date").parent(), '');
              }
            });

        };

        domReady(onReady);

        return {
            onReady: onReady
        };
    });
