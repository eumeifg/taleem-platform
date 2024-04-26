define(
  ['domReady', 'jquery', 'select2', 'dataTables', 'jqueryModal'],
  function(domReady, $, select2) {
      'use strict';

      var showNewTeacherBox, addNewCoTeacher;

      showNewTeacherBox = function(e) {
          e.preventDefault();
          $('#newCoTeacherButton').addClass('is-disabled').attr('aria-disabled', true);
          $('.wrapper-course-filter').addClass('is-shown');
      };

      addNewCoTeacher = function(e) {
          var teacherEmail = $('#selectCoTeacher').val();
          var url = $('#add_new_teacher').attr('data-link');
          e.preventDefault();
          if (teacherEmail !== '') {
              $.ajax({
                  url: url,
                  type: 'POST',
                  data: {
                      teacher_email: teacherEmail
                  },
                  success: function(response) {
                      if (response.can_add_without_consent) {
                          $('#co-teacher-form').submit();
                      } else {
                          $('#consent-modal').jqueryModal({
                              escapeClose: false,
                              clickClose: false,
                              showClose: false
                          });
                      }
                  }
              });
          }
      };

      var onReady = function() {
          $('.nav-course.nav-dd.ui-left').remove();
          $('.course-link').remove();
          $('#newCoTeacherButton').bind('click', showNewTeacherBox);
          $('#add_new_teacher').bind('click', addNewCoTeacher);
          $('#create_after_consent').bind('click', function(e) {
              e.preventDefault();
              $('#co-teacher-form').submit();
          });
          $('#selectCoTeacher').select2({
              width: '100%',
              matcher: function(params, data) {
                  // If there are no search terms, return all of the data
                  if ($.trim(params.term) === '') { return data; }

                  // Do not display the item if there is no 'text' property
                  if (typeof data.text === 'undefined') { return null; }

                  // `params.term` is the user's search term
                  // `data.id` should be checked against
                  // `data.text` should be checked against
                  var q = params.term.toLowerCase();
                  if (data.text.toLowerCase().indexOf(q) > -1 || data.id.toLowerCase().indexOf(q) > -1) {
                      return $.extend({}, data, true);
                  }

                  // Return `null` if the term should not be displayed
                  return null;
              }
          });
          $('#coTeacherListTable').DataTable({
            language: {
                url: (typeof datatablesLangPath !== 'undefined') ? datatablesLangPath : "",
            },
          });
      };

      domReady(onReady);

      return {
          onReady: onReady
      };
  }
);
